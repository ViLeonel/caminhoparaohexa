"""Testes de regressão do baseline da Fase 0."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from hexa_avaliacoes import (
    carregar_avaliacoes,
    validar_integridade_avaliacoes,
)
from hexa_data import (
    carregar_jogadores,
    validar_integridade_jogadores,
    validar_posicoes,
)
from hexa_persistencia_local import (
    CHAVE_RESTAURACAO_CONCLUIDA,
    sincronizar_persistencia_local,
)
from hexa_taticas import TATICAS, obter_atletas_compativeis, validar_taticas

ROOT = Path(__file__).resolve().parents[1]


class Phase0DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.jogadores = carregar_jogadores()
        cls.avaliacoes = carregar_avaliacoes(jogadores=cls.jogadores)

    def test_integridade_jogadores(self) -> None:
        relatorio = validar_integridade_jogadores(self.jogadores)
        self.assertFalse(relatorio.problemas, relatorio.mensagens())
        self.assertEqual(validar_posicoes(self.jogadores), [])

    def test_integridade_avaliacoes(self) -> None:
        documento = json.loads(
            (ROOT / "avaliacoes_trimestrais_hexa_2030.json").read_text(
                encoding="utf-8-sig"
            )
        )
        problemas = validar_integridade_avaliacoes(
            documento,
            jogadores=self.jogadores,
        )
        self.assertEqual(problemas, [])

    def test_ids_sao_unicos_e_cobrem_avaliacoes(self) -> None:
        ids_jogadores = [
            str(dados.get("id_atleta") or "")
            for dados in self.jogadores.values()
        ]
        self.assertNotIn("", ids_jogadores)
        self.assertFalse(
            [item for item, total in Counter(ids_jogadores).items() if total > 1]
        )

        ids_avaliacoes = [
            str(item.get("id_atleta") or "")
            for item in self.avaliacoes.avaliacoes
        ]
        self.assertEqual(set(ids_jogadores), set(ids_avaliacoes))

    def test_formacoes_possuem_onze_slots_e_cobertura(self) -> None:
        self.assertEqual(validar_taticas(self.jogadores), [])
        for nome, layout in TATICAS.items():
            with self.subTest(tatica=nome):
                self.assertEqual(len(layout), 11)
                for slot, configuracao in layout.items():
                    compativeis = obter_atletas_compativeis(
                        self.jogadores,
                        configuracao.posicoes,
                    )
                    self.assertTrue(
                        compativeis,
                        f"{nome}/{slot} não possui atleta compatível",
                    )


class Phase0PersistenceTests(unittest.TestCase):
    def test_componente_local_opcional_nao_bloqueia_aplicacao(self) -> None:
        estado: dict[str, object] = {}
        jogadores = {
            "Teste": {
                "id_atleta": "ATH-TESTE",
                "posicao": "Goleiro",
                "posicoes_multiplas": ["Goleiro"],
            }
        }

        def componente_com_falha(**_: object) -> object:
            raise RuntimeError("componente não registrado")

        with patch(
            "hexa_persistencia_local._storage_component",
            componente_com_falha,
        ):
            resultado = sincronizar_persistencia_local(
                estado,
                {},
                jogadores,
            )

        self.assertTrue(resultado.pronta)
        self.assertFalse(resultado.disponivel)
        self.assertTrue(estado[CHAVE_RESTAURACAO_CONCLUIDA])


class Phase0FilesTests(unittest.TestCase):
    def test_jsons_obrigatorios_sao_validos(self) -> None:
        for nome in (
            "jogadores_hexa_2030.json",
            "avaliacoes_trimestrais_hexa_2030.json",
            "enriquecimentos_tm.json",
        ):
            with self.subTest(arquivo=nome):
                json.loads((ROOT / nome).read_text(encoding="utf-8-sig"))

    def test_configuracao_streamlit_no_caminho_padrao(self) -> None:
        self.assertTrue((ROOT / ".streamlit" / "config.toml").is_file())
        self.assertTrue(
            (ROOT / ".streamlit" / "secrets.example.toml").is_file()
        )


if __name__ == "__main__":
    unittest.main()
