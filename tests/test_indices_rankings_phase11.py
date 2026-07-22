"""Regressões da Fase 11 — índices e rankings sazonais."""

from __future__ import annotations

import unittest
from pathlib import Path
from datetime import datetime, timezone

from hexa_estatisticas import atualizar_temporada
from hexa_indices_rankings import (
    INDICADORES_RANKING,
    construir_painel_rankings,
    recalcular_indices_rankings,
    validar_painel_rankings,
)


def _total(
    id_atleta: str,
    nome: str,
    *,
    ambito: str = "combinado",
    minutos: int = 900,
    jogos: int = 10,
    gols: int = 0,
    assistencias: int = 0,
    erros: int = 0,
) -> dict:
    return {
        "id_atleta": id_atleta,
        "nome": nome,
        "temporada": 2026,
        "ambito": ambito,
        "jogos": jogos,
        "minutos": minutos,
        "titular": jogos,
        "gols": gols,
        "assistencias": assistencias,
        "chutes": 10,
        "chutes_no_alvo": 5,
        "passes": 100,
        "passes_certos_percentual": 90.0,
        "passes_chave": 3,
        "dribles": 2,
        "desarmes": 4,
        "interceptacoes": 3,
        "cabeceios_ganhos": 2,
        "erros": erros,
        "erros_geraram_gol": 0,
        "cartoes_amarelos": 1,
        "cartoes_vermelhos": 0,
        "indices": {
            "minutos_por_jogo": minutos / jogos,
            "titular_percentual": 100.0,
            "gols_por_90": gols * 90 / minutos,
            "assistencias_por_90": assistencias * 90 / minutos,
            "participacoes_gol_por_90": (gols + assistencias) * 90 / minutos,
            "chutes_no_alvo_percentual": 50.0,
        },
    }


class Phase11RankingsTests(unittest.TestCase):
    def test_painel_nao_cria_nota_composta(self) -> None:
        painel = construir_painel_rankings(
            [_total("ATH-1", "Atleta A", gols=4)],
            temporada=2026,
        )
        self.assertFalse(painel["metodologia"]["nota_composta"])
        self.assertEqual(validar_painel_rankings(painel), [])

    def test_rankings_sao_separados_por_ambito(self) -> None:
        totais = [
            _total("ATH-1", "Clube", ambito="clube", gols=5),
            _total("ATH-1", "Seleção", ambito="selecao", gols=2),
            _total("ATH-1", "Combinado", ambito="combinado", gols=7),
        ]
        painel = construir_painel_rankings(totais, temporada=2026)
        self.assertEqual(
            painel["rankings"]["clube"]["gols"][0]["valor"],
            5.0,
        )
        self.assertEqual(
            painel["rankings"]["selecao"]["gols"][0]["valor"],
            2.0,
        )
        self.assertEqual(
            painel["rankings"]["combinado"]["gols"][0]["valor"],
            7.0,
        )

    def test_indices_eficiencia_exigem_450_minutos(self) -> None:
        totais = [
            _total("ATH-1", "Poucos minutos", minutos=90, gols=3),
            _total("ATH-2", "Elegível", minutos=900, gols=5),
        ]
        painel = construir_painel_rankings(totais, temporada=2026)
        ranking = painel["rankings"]["combinado"]["gols_por_90"]
        self.assertEqual([item["nome"] for item in ranking], ["Elegível"])

    def test_menos_erros_usa_ordem_crescente(self) -> None:
        totais = [
            _total("ATH-1", "Mais erros", erros=4),
            _total("ATH-2", "Menos erros", erros=1),
        ]
        painel = construir_painel_rankings(totais, temporada=2026)
        ranking = painel["rankings"]["combinado"]["erros"]
        self.assertEqual(ranking[0]["nome"], "Menos erros")

    def test_empates_compartilham_posicao(self) -> None:
        totais = [
            _total("ATH-1", "Atleta A", gols=5),
            _total("ATH-2", "Atleta B", gols=5),
            _total("ATH-3", "Atleta C", gols=3),
        ]
        painel = construir_painel_rankings(totais, temporada=2026)
        ranking = painel["rankings"]["combinado"]["gols"]
        self.assertEqual([item["posicao"] for item in ranking[:3]], [1, 1, 3])

    def test_recalculo_substitui_apenas_derivados(self) -> None:
        documento = {
            "schema_version": "1.0",
            "temporada": 2026,
            "atualizado_em_utc": "2026-09-30T12:00:00Z",
            "registros": [{"registro_bruto": True}],
            "totais": [_total("ATH-1", "Atleta A", gols=4)],
        }
        recalculado = recalcular_indices_rankings(documento)
        self.assertEqual(recalculado["registros"], documento["registros"])
        self.assertIn("indices_rankings", recalculado)
        self.assertIn("indices", recalculado["totais"][0])

    def test_atualizacao_trimestral_recalcula_automaticamente(self) -> None:
        jogadores = {
            "Atleta A": {
                "id_atleta": "ATH-1",
                "nome": "Atleta A",
            }
        }
        registro = {
            "id_atleta": "ATH-1",
            "nome": "Atleta A",
            "ambito": "clube",
            "equipe": "Clube A",
            "competicao": "Liga",
            "jogos": 10,
            "minutos": 900,
            "titular": 10,
            "gols": 4,
            "assistencias": 2,
        }
        resultado = atualizar_temporada(
            temporada=2026,
            registros=[registro],
            jogadores=jogadores,
            fonte="Teste",
            agora=datetime(2026, 9, 30, tzinfo=timezone.utc),
        )
        self.assertIn("indices_rankings", resultado.documento)
        painel = resultado.documento["indices_rankings"]
        self.assertEqual(validar_painel_rankings(painel), [])

    def test_painel_publico_esta_integrado_aos_indicadores(self) -> None:
        fonte = (Path(__file__).resolve().parents[1] / "hexa_page_indicadores.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("render_indices_rankings_temporada", fonte)
        self.assertIn("TEMPORADAS_DIR", fonte)

    def test_versao_phase11(self) -> None:
        from hexa_config import VERSAO_APLICACAO

        self.assertEqual(VERSAO_APLICACAO, "3.0.0-admin-workflow-phase12")

    def test_contrato_mantem_apenas_indicadores_transparentes(self) -> None:
        chaves = {item.chave for item in INDICADORES_RANKING}
        self.assertNotIn("nota", chaves)
        self.assertNotIn("score", chaves)
        self.assertIn("gols_por_90", chaves)
        self.assertIn("passes_certos_percentual", chaves)


if __name__ == "__main__":
    unittest.main()
