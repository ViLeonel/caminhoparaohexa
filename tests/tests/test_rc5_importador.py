"""Testes da política append-only do importador trimestral."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = BASE_DIR / "scripts" / "importar_avaliacoes_planilha.py"

spec = importlib.util.spec_from_file_location("importador_rc5", SCRIPT)
assert spec and spec.loader
importador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importador)


class TestImportadorRC5(unittest.TestCase):
    def setUp(self) -> None:
        self.registro = {
            "id_atleta": "ATH-0001",
            "nome": "Alisson",
            "periodo": "2026-T2",
            "ano": 2026,
            "trimestre": "T2",
            "data_referencia": "2026-06-30",
            "posicao_snapshot": "Goleiro",
            "clube_snapshot": "Liverpool FC",
            "vini": {
                "capacidade_atual": 7.5,
                "potencial_2030": 6.5,
                "observacao": "",
            },
            "beto": {
                "capacidade_atual": 7.5,
                "potencial_2030": 6.5,
                "observacao": "",
            },
        }
        self.fonte = {
            "arquivo": "teste.xlsm",
            "sha256": "0" * 64,
            "aba": "Avaliações Trimestrais",
            "importado_em_utc": "2026-07-18T00:00:00Z",
            "politica": "teste",
        }

    def _criar_saida(self, pasta: Path) -> Path:
        caminho = pasta / "avaliacoes.json"
        documento = {
            "schema_version": "1.0",
            "projeto": "O Caminho para o Hexa 2030",
            "fonte": self.fonte,
            "historico_importacoes": [self.fonte],
            "avaliacoes": [copy.deepcopy(self.registro)],
        }
        caminho.write_text(
            json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return caminho

    def test_append_only_aceita_repeticao_identica(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = self._criar_saida(Path(pasta))
            documento = importador._mesclar_avaliacoes(
                caminho,
                [copy.deepcopy(self.registro)],
                self.fonte,
                permitir_correcao=False,
            )
            self.assertEqual(documento["avaliacoes"], [self.registro])

    def test_append_only_bloqueia_alteracao_silenciosa(self) -> None:
        alterado = copy.deepcopy(self.registro)
        alterado["vini"]["capacidade_atual"] = 8.0
        with tempfile.TemporaryDirectory() as pasta:
            caminho = self._criar_saida(Path(pasta))
            with self.assertRaises(importador.ImportacaoError):
                importador._mesclar_avaliacoes(
                    caminho,
                    [alterado],
                    self.fonte,
                    permitir_correcao=False,
                )

    def test_correcao_retroativa_exige_flag_explicita(self) -> None:
        alterado = copy.deepcopy(self.registro)
        alterado["vini"]["capacidade_atual"] = 8.0
        with tempfile.TemporaryDirectory() as pasta:
            caminho = self._criar_saida(Path(pasta))
            documento = importador._mesclar_avaliacoes(
                caminho,
                [alterado],
                self.fonte,
                permitir_correcao=True,
            )
            self.assertEqual(
                documento["avaliacoes"][0]["vini"]["capacidade_atual"],
                8.0,
            )

    def test_escrita_atomica_gera_json_valido(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste.json"
            importador._escrever_atomico(caminho, {"ok": True})
            self.assertEqual(
                json.loads(caminho.read_text(encoding="utf-8")),
                {"ok": True},
            )


if __name__ == "__main__":
    unittest.main()
