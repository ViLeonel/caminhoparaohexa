"""Testes da Fase 10: Agenda Inteligente."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from hexa_agenda import (
    FiltroAgenda,
    carregar_aliases_equipes,
    listar_competicoes_agenda,
    normalizar_identidade_equipe,
    proximos_jogos_inteligentes,
)
from hexa_config import VERSAO_APLICACAO
from hexa_dados_esportivos import carregar_proximos_jogos


class Phase10SmartAgendaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.jogador = {"clube": "São Paulo FC", "clube_id": "SPFC"}
        self.documentos = [
            {
                "jogos": [
                    {
                        "id_jogo": "1",
                        "data": "2026-08-01",
                        "hora": "16:00",
                        "competicao": "Campeonato Brasileiro",
                        "mandante": "Sao Paulo",
                        "visitante": "Palmeiras",
                        "status": "confirmado",
                    },
                    {
                        "id_jogo": "2",
                        "data": "2026-08-05",
                        "competicao": "Copa Sul-Americana",
                        "mandante": "São Paulo FC",
                        "visitante": "LDU",
                        "status": "agendado",
                    },
                    {
                        "id_jogo": "3",
                        "data": "2026-08-09",
                        "competicao": "Seleção",
                        "mandante": "Brasil",
                        "visitante": "Argentina",
                        "status": "agendado",
                    },
                    {
                        "id_jogo": "4",
                        "data": "2026-08-12",
                        "competicao": "Campeonato Paulista",
                        "mandante": "São Paulo FC",
                        "visitante": "Santos",
                        "status": "adiado",
                    },
                ]
            }
        ]
        self.aliases = {
            normalizar_identidade_equipe("Sao Paulo"): normalizar_identidade_equipe(
                "São Paulo FC"
            )
        }

    def test_versao_phase10(self) -> None:
        self.assertEqual(VERSAO_APLICACAO, "2.2.0-indices-rankings-phase11")

    def test_normalizacao_remove_acentos_e_pontuacao(self) -> None:
        self.assertEqual(
            normalizar_identidade_equipe("  São-Paulo F.C. "),
            "sao paulo f c",
        )

    def test_alias_expresso_associa_clube_sem_aproximacao(self) -> None:
        jogos = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            aliases=self.aliases,
        )
        self.assertEqual([item["competicao"] for item in jogos], [
            "Campeonato Brasileiro",
            "Copa Sul-Americana",
            "Seleção",
        ])

    def test_status_adiado_nao_aparece(self) -> None:
        jogos = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            limite=10,
            aliases=self.aliases,
        )
        self.assertNotIn("Campeonato Paulista", {j["competicao"] for j in jogos})

    def test_filtro_separa_clube_e_selecao(self) -> None:
        clube = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            limite=10,
            filtro=FiltroAgenda(escopo="clube"),
            aliases=self.aliases,
        )
        selecao = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            limite=10,
            filtro=FiltroAgenda(escopo="selecao"),
            aliases=self.aliases,
        )
        self.assertEqual(len(clube), 2)
        self.assertEqual(len(selecao), 1)
        self.assertEqual(selecao[0]["confronto"], "Brasil x Argentina")

    def test_filtro_por_competicao(self) -> None:
        jogos = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            limite=10,
            filtro=FiltroAgenda(competicao="Copa Sul-Americana"),
            aliases=self.aliases,
        )
        self.assertEqual(len(jogos), 1)
        self.assertEqual(jogos[0]["competicao"], "Copa Sul-Americana")

    def test_deduplicacao_prioriza_id_jogo(self) -> None:
        duplicado = {"jogos": [dict(self.documentos[0]["jogos"][0])]}
        jogos = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=[*self.documentos, duplicado],
            hoje=date(2026, 7, 1),
            limite=10,
            aliases=self.aliases,
        )
        self.assertEqual(len(jogos), 3)

    def test_competicoes_futuras_sao_listadas_sem_duplicidade(self) -> None:
        competicoes = listar_competicoes_agenda(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            aliases=self.aliases,
        )
        self.assertEqual(
            competicoes,
            ("Campeonato Brasileiro", "Copa Sul-Americana", "Seleção"),
        )

    def test_arquivo_de_aliases_eh_validado(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "aliases_equipes.json"
            caminho.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "equipes": {"São Paulo FC": ["Sao Paulo", "SPFC"]},
                    }
                ),
                encoding="utf-8",
            )
            aliases = carregar_aliases_equipes(caminho)
            self.assertEqual(
                aliases[normalizar_identidade_equipe("SPFC")],
                normalizar_identidade_equipe("São Paulo FC"),
            )

    def test_camada_de_dados_combina_anos_e_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "aliases_equipes.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "equipes": {"São Paulo FC": ["Sao Paulo"]},
                    }
                ),
                encoding="utf-8",
            )
            (raiz / "calendario_2026.json").write_text(
                json.dumps(self.documentos[0]),
                encoding="utf-8",
            )
            jogos = carregar_proximos_jogos(
                jogador=self.jogador,
                diretorio=raiz,
                hoje=date(2026, 7, 1),
                limite=3,
                escopo="clube",
            )
            self.assertEqual(len(jogos), 2)

    def test_saida_publica_contem_apenas_tres_campos(self) -> None:
        jogos = proximos_jogos_inteligentes(
            jogador=self.jogador,
            calendarios=self.documentos,
            hoje=date(2026, 7, 1),
            aliases=self.aliases,
        )
        self.assertTrue(jogos)
        self.assertEqual(
            set(jogos[0]),
            {"data", "competicao", "confronto"},
        )


if __name__ == "__main__":
    unittest.main()
