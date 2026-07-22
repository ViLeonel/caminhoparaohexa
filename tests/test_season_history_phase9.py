"""Testes da Fase 9: histórico sazonal e agenda na ficha individual."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from hexa_dados_esportivos import (
    DocumentoEsportivoError,
    carregar_proximos_jogos,
    carregar_totais_atleta,
    listar_anos_disponiveis,
)
from hexa_config import VERSAO_APLICACAO


class Phase9SeasonHistoryTests(unittest.TestCase):
    def test_versao_phase9(self) -> None:
        self.assertEqual(VERSAO_APLICACAO, "3.0.0-admin-workflow-phase12")

    def test_listar_temporadas_em_ordem_decrescente(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "temporada_2025.json").write_text("{}", encoding="utf-8")
            (raiz / "temporada_2027.json").write_text("{}", encoding="utf-8")
            (raiz / "ignorar.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                listar_anos_disponiveis(raiz, "temporada"),
                (2027, 2025),
            )

    def test_totais_do_atleta_preservam_tres_ambitos(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            documento = {
                "totais": [
                    {"id_atleta": "ATH-1", "ambito": "clube", "jogos": 10},
                    {"id_atleta": "ATH-1", "ambito": "selecao", "jogos": 2},
                    {"id_atleta": "ATH-1", "ambito": "combinado", "jogos": 12},
                    {"id_atleta": "ATH-2", "ambito": "clube", "jogos": 7},
                ]
            }
            (raiz / "temporada_2026.json").write_text(
                json.dumps(documento),
                encoding="utf-8",
            )
            totais = carregar_totais_atleta(
                diretorio=raiz,
                temporada=2026,
                id_atleta="ATH-1",
            )
            self.assertEqual(set(totais), {"clube", "selecao", "combinado"})
            self.assertEqual(totais["combinado"]["jogos"], 12)

    def test_calendarios_de_anos_diferentes_formam_agenda_unica(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            for ano, jogos in {
                2026: [
                    {
                        "data": "2026-12-30",
                        "competicao": "Brasileirão",
                        "mandante": "Clube A",
                        "visitante": "Clube B",
                    }
                ],
                2027: [
                    {
                        "data": "2027-01-05",
                        "competicao": "Campeonato Estadual",
                        "mandante": "Clube B",
                        "visitante": "Clube A",
                    },
                    {
                        "data": "2027-01-12",
                        "competicao": "Copa Sul-Americana",
                        "mandante": "Clube A",
                        "visitante": "Clube C",
                    },
                ],
            }.items():
                (raiz / f"calendario_{ano}.json").write_text(
                    json.dumps({"jogos": jogos}),
                    encoding="utf-8",
                )
            proximos = carregar_proximos_jogos(
                jogador={"clube": "Clube A"},
                diretorio=raiz,
                hoje=date(2026, 12, 1),
                limite=3,
            )
            self.assertEqual(len(proximos), 3)
            self.assertEqual(proximos[0]["data"], "2026-12-30")
            self.assertEqual(proximos[1]["competicao"], "Campeonato Estadual")
            self.assertEqual(proximos[2]["competicao"], "Copa Sul-Americana")

    def test_agenda_nao_expoe_campos_rejeitados(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            documento = {
                "jogos": [
                    {
                        "data": "2026-08-01",
                        "competicao": "Campeonato Estadual",
                        "mandante": "Clube A",
                        "visitante": "Clube B",
                    }
                ]
            }
            (raiz / "calendario_2026.json").write_text(
                json.dumps(documento),
                encoding="utf-8",
            )
            jogo = carregar_proximos_jogos(
                jogador={"clube": "Clube A"},
                diretorio=raiz,
                hoje=date(2026, 7, 1),
            )[0]
            self.assertEqual(
                set(jogo),
                {"data", "competicao", "confronto"},
            )

    def test_json_sazonal_invalido_nao_e_reparado(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            caminho = raiz / "temporada_2026.json"
            original = "{invalido"
            caminho.write_text(original, encoding="utf-8")
            with self.assertRaises(DocumentoEsportivoError):
                carregar_totais_atleta(
                    diretorio=raiz,
                    temporada=2026,
                    id_atleta="ATH-1",
                )
            self.assertEqual(caminho.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
