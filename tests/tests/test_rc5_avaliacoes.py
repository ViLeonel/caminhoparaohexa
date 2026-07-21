"""Testes de regressão da RC5 — avaliações trimestrais."""

from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from hexa_avaliacoes import (
    BaseAvaliacoes,
    calcular_metricas_avaliacao,
    calcular_resumo_periodo,
    carregar_avaliacoes,
    historico_atleta,
    validar_integridade_avaliacoes,
)

BASE_DIR = Path(__file__).resolve().parents[1]
AVALIACOES = BASE_DIR / "avaliacoes_trimestrais_hexa_2030.json"
JOGADORES = BASE_DIR / "jogadores_hexa_2030.json"
LEGADO = (
    BASE_DIR
    / "arquivo"
    / "avaliacoes_editoriais_legado_pre_t2_2026.json"
)


class TestRC5Avaliacoes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.jogadores = json.loads(JOGADORES.read_text(encoding="utf-8"))
        cls.base = carregar_avaliacoes(AVALIACOES, jogadores=cls.jogadores)

    def test_integridade_estrutural_t2_2026(self) -> None:
        self.assertEqual(len(self.base.avaliacoes), 61)
        self.assertEqual(
            {registro["periodo"] for registro in self.base.avaliacoes},
            {"2026-T2"},
        )
        self.assertEqual(
            {registro["data_referencia"] for registro in self.base.avaliacoes},
            {"2026-06-30"},
        )
        self.assertFalse(
            any(registro["trimestre"] == "T1" for registro in self.base.avaliacoes)
        )
        self.assertEqual(
            len({registro["id_atleta"] for registro in self.base.avaliacoes}),
            61,
        )

    def test_resumo_regressao_t2_2026(self) -> None:
        resumo = calcular_resumo_periodo(
            self.base,
            "2026-T2",
            total_atletas=len(self.jogadores),
        )
        self.assertEqual(resumo["com_alguma_avaliacao"], 47)
        self.assertEqual(resumo["avaliacoes_completas"], 43)
        self.assertEqual(resumo["avaliacoes_parciais"], 4)
        self.assertEqual(resumo["nao_avaliados"], 14)
        self.assertEqual(resumo["notas_preenchidas"], 180)
        self.assertTrue(
            math.isclose(
                resumo["capacidade_atual_media"],
                7.154255319148936,
                rel_tol=0,
                abs_tol=1e-12,
            )
        )
        self.assertTrue(
            math.isclose(
                resumo["potencial_2030_medio"],
                7.920212765957447,
                rel_tol=0,
                abs_tol=1e-12,
            )
        )
        self.assertTrue(
            math.isclose(
                resumo["saldo_projetado_medio"],
                0.7659574468085106,
                rel_tol=0,
                abs_tol=1e-12,
            )
        )

    def test_quatro_avaliacoes_parciais(self) -> None:
        parciais = {
            registro["nome"]
            for registro in self.base.avaliacoes
            if calcular_metricas_avaliacao(registro)["status"] == "Parcial"
        }
        self.assertEqual(
            parciais,
            {"Arthur", "Igor Jesus", "Igor Paixão", "Pedro Morisco"},
        )

    def test_saldo_usa_apenas_pares_completos_e_aceita_regressao(self) -> None:
        registro = {
            "vini": {
                "capacidade_atual": 8.0,
                "potencial_2030": 6.5,
            },
            "beto": {
                "capacidade_atual": 7.0,
                "potencial_2030": None,
            },
        }
        metricas = calcular_metricas_avaliacao(registro)
        self.assertEqual(metricas["capacidade_atual_media"], 7.5)
        self.assertEqual(metricas["potencial_2030_medio"], 6.5)
        self.assertEqual(metricas["saldo_projetado"], -1.5)
        self.assertEqual(metricas["status"], "Parcial")

    def test_historico_procura_ultimo_periodo_avaliado(self) -> None:
        registros = [
            {
                "id_atleta": "ATH-9999",
                "nome": "Teste",
                "periodo": "2026-T2",
                "ano": 2026,
                "trimestre": "T2",
                "data_referencia": "2026-06-30",
                "posicao_snapshot": "Goleiro",
                "clube_snapshot": "Clube",
                "vini": {"capacidade_atual": 8.0, "potencial_2030": 8.0, "observacao": ""},
                "beto": {"capacidade_atual": 8.0, "potencial_2030": 8.0, "observacao": ""},
            },
            {
                "id_atleta": "ATH-9999",
                "nome": "Teste",
                "periodo": "2026-T3",
                "ano": 2026,
                "trimestre": "T3",
                "data_referencia": "2026-09-30",
                "posicao_snapshot": "Goleiro",
                "clube_snapshot": "Clube",
                "vini": {"capacidade_atual": None, "potencial_2030": None, "observacao": ""},
                "beto": {"capacidade_atual": None, "potencial_2030": None, "observacao": ""},
            },
            {
                "id_atleta": "ATH-9999",
                "nome": "Teste",
                "periodo": "2026-T4",
                "ano": 2026,
                "trimestre": "T4",
                "data_referencia": "2026-12-31",
                "posicao_snapshot": "Goleiro",
                "clube_snapshot": "Clube",
                "vini": {"capacidade_atual": 7.0, "potencial_2030": 7.5, "observacao": ""},
                "beto": {"capacidade_atual": 7.5, "potencial_2030": 8.0, "observacao": ""},
            },
        ]
        base = BaseAvaliacoes(
            schema_version="1.0",
            fonte={},
            avaliacoes=tuple(registros),
        )
        serie = historico_atleta(base, "ATH-9999")
        ultimo = serie[-1]
        self.assertEqual(ultimo["capacidade_atual_media"], 7.25)
        self.assertEqual(ultimo["variacao_vs_ultimo_trimestre"], -0.75)
        self.assertEqual(ultimo["media_historica_anterior_capacidade"], 8.0)
        self.assertEqual(ultimo["variacao_vs_media_historica"], -0.75)

    def test_json_temporal_valida_contra_cadastro(self) -> None:
        documento = json.loads(AVALIACOES.read_text(encoding="utf-8"))
        self.assertEqual(
            validar_integridade_avaliacoes(documento, jogadores=self.jogadores),
            [],
        )

    def test_ids_estaveis_foram_adicionados_sem_remover_legado(self) -> None:
        ids = {
            registro["id_atleta"]
            for registro in self.jogadores.values()
        }
        self.assertEqual(len(ids), 61)
        self.assertTrue(all(valor.startswith("ATH-") for valor in ids))
        for registro in self.jogadores.values():
            for campo in (
                "nota_vini",
                "nota_roberto",
                "pontos_fortes",
                "pontos_fracos",
                "historico",
                "posicao",
                "posicoes_multiplas",
                "grupo",
                "tipo",
            ):
                self.assertIn(campo, registro)

    def test_arquivo_legado_contem_os_61_atletas(self) -> None:
        legado = json.loads(LEGADO.read_text(encoding="utf-8"))
        self.assertEqual(len(legado["avaliacoes_legadas"]), 61)
        self.assertEqual(
            set(legado["avaliacoes_legadas"]),
            set(self.jogadores),
        )
        self.assertEqual(
            set(legado["campos_arquivados"]),
            {
                "nota_vini",
                "nota_roberto",
                "pontos_fortes",
                "pontos_fracos",
                "historico",
            },
        )


if __name__ == "__main__":
    unittest.main()
