from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import hexa_components
from hexa_components import (
    render_comparativo_mercado,
    render_dados_transfermarkt,
)


BASE_DIR = Path(__file__).resolve().parents[1]


class TestRC55DadosJogadorMercado(unittest.TestCase):
    def test_dados_do_jogador_agrupados_e_sem_campos_vazios(self) -> None:
        dados = {
            "nome": "Alexsandro",
            "nome_completo": "Alexsandro Victor de Souza Ribeiro",
            "tm_nascimento": "09/08/1999",
            "tm_naturalidade": "Rio de Janeiro, Brasil",
            "tm_altura": "1,91 m",
            "tm_pe": "Ambos",
            "tm_empresario": "Roc Nation Sports",
            "tm_clube_desde": "01/07/2022",
            "tm_contrato": "30/06/2028",
            "tm_ultima_renovacao": "15/01/2024",
            "tm_equipador": "",
            "tm_posicao_site": "Defesa Central",
            "tm_posicoes_secundarias_site": [],
        }

        with patch.object(hexa_components.st, "markdown") as markdown:
            render_dados_transfermarkt(dados)

        html = markdown.call_args.args[0]
        self.assertIn('aria-label="Dados do jogador"', html)
        self.assertIn("Identificação", html)
        self.assertIn("Vínculo profissional", html)
        self.assertIn("Referência cadastral externa", html)
        self.assertIn("Alexsandro Victor de Souza Ribeiro", html)
        self.assertIn("Defesa Central", html)
        self.assertNotIn("Equipador</dt>", html)
        self.assertNotIn("[", html)

    def test_lista_de_posicoes_externas_eh_formatada(self) -> None:
        dados = {
            "nome": "Jogador",
            "tm_posicao_site": "Médio Centro",
            "tm_posicoes_secundarias_site": [
                "Médio Defensivo",
                "Médio Ofensivo",
            ],
        }
        with patch.object(hexa_components.st, "markdown") as markdown:
            render_dados_transfermarkt(dados)

        html = markdown.call_args.args[0]
        self.assertIn("Médio Defensivo, Médio Ofensivo", html)
        self.assertNotIn("['Médio Defensivo'", html)

    def test_valor_de_mercado_tem_quatro_metricas_e_observacao(self) -> None:
        dados = {
            "tm_valor_mercado_milhoes": 15.0,
            "tm_valor_maximo_milhoes": 20.0,
            "tm_data_valor_maximo": "02/06/2025",
            "tm_ultima_atualizacao": "31/05/2026",
        }

        with patch.object(hexa_components.st, "markdown") as markdown:
            render_comparativo_mercado(dados)

        html = markdown.call_args.args[0]
        self.assertEqual(html.count('class="market-metric'), 4)
        self.assertIn('class="market-dates"', html)
        self.assertIn("<em>", html)
        self.assertIn(
            "Valor de mercado é uma referência externa e não equivale",
            html,
        )

    def test_nome_do_expander_e_tipo_compacto(self) -> None:
        fonte = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertIn(
            'st.expander("Dados do jogador", expanded=True, type="compact")',
            fonte,
        )
        self.assertNotIn(
            'st.expander("Dados externos e contratuais"',
            fonte,
        )

    def test_css_responsivo_e_hierarquia_da_observacao(self) -> None:
        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")
        self.assertIn(".player-data-groups", css)
        self.assertIn(".player-data-group--wide", css)
        self.assertIn(".market-metric", css)
        self.assertIn(".market-card-info", css)
        self.assertIn("font-style: italic;", css)
        self.assertIn("font-size: .78rem;", css)
        self.assertIn("grid-template-columns: repeat(4", css)

    def test_versao_da_aplicacao(self) -> None:
        fonte = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn(
            'VERSAO_APLICACAO = "1.1.7-rc5.5-dados-jogador-mercado"',
            fonte,
        )


if __name__ == "__main__":
    unittest.main()
