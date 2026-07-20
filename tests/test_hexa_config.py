"""Testes das configurações centrais do projeto."""

from __future__ import annotations

import unittest

import hexa_config as config
from hexa_selectors import construir_registros_roster


class HexaConfigTests(unittest.TestCase):
    def test_referencias_temporais_sao_coerentes(self) -> None:
        self.assertGreater(config.ANO_COPA, config.ANO_BASE_DADOS)

    def test_grupos_editoriais_nao_tem_duplicidade(self) -> None:
        self.assertEqual(len(config.GRUPOS_EDITORIAIS), len(set(config.GRUPOS_EDITORIAIS)))
        self.assertIn(config.GRUPO_OBSERVACAO, config.GRUPOS_EDITORIAIS)

    def test_menus_nao_tem_duplicidade(self) -> None:
        self.assertEqual(len(config.MENUS), len(set(config.MENUS)))
        self.assertEqual(config.MENUS[0], config.MENU_CAMPO)

    def test_caminhos_apontam_para_a_raiz_do_projeto(self) -> None:
        self.assertEqual(config.DATA_FILE.parent, config.BASE_DIR)
        self.assertEqual(config.ENRICHMENTS_FILE.parent, config.BASE_DIR)

    def test_page_config_reutiliza_identidade_central(self) -> None:
        self.assertEqual(config.PAGE_CONFIG["page_title"], config.NOME_APLICACAO)
        self.assertEqual(config.PAGE_CONFIG["page_icon"], config.ICONE_APLICACAO)

    def test_projecao_do_roster_usa_anos_centrais(self) -> None:
        jogadores = {
            "Atleta": {
                "idade": 20,
                "posicao": "Volante",
                "posicoes_multiplas": ["Volante"],
                "grupo": config.GRUPO_OBSERVACAO,
                "nota_vini": 0,
                "nota_roberto": 0,
            }
        }
        registro = construir_registros_roster(jogadores)[0]
        self.assertEqual(registro[f"Idade {config.ANO_BASE_DADOS}"], 20)
        self.assertEqual(
            registro[f"Idade {config.ANO_COPA}"],
            20 + config.ANO_COPA - config.ANO_BASE_DADOS,
        )


if __name__ == "__main__":
    unittest.main()
