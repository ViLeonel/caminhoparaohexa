"""Regressões do hotfix do card de perfil."""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from hexa_components import render_cartao_perfil


class TestHotfixCardPerfil(TestCase):
    jogador = {
        "clube": "SE Palmeiras",
        "idade": 22,
        "posicao": "Ponta-direita",
        "posicoes_multiplas": [
            "Ponta-direita",
            "Meia-armador",
            "Mezzala direito",
        ],
    }

    def _renderizar(self, avaliacao):
        with patch("hexa_components.st.markdown") as markdown:
            render_cartao_perfil("Allan", self.jogador, avaliacao)
        return markdown.call_args.args[0]

    def test_card_renderiza_idade_e_posicoes_sem_nameerror(self) -> None:
        avaliacao = {
            "vini": {
                "capacidade_atual": 5.5,
                "potencial_2030": 7.5,
            },
            "beto": {
                "capacidade_atual": 6.5,
                "potencial_2030": 8.0,
            },
        }

        html = self._renderizar(avaliacao)

        self.assertIn("Ciclo 2030", html)
        self.assertIn("Avaliação Completa", html)
        self.assertIn("PD - MEI - MCD", html)
        self.assertIn("26", html)
        self.assertNotIn("Seleção Brasileira", html)
        self.assertNotIn("profile-position-full", html)

    def test_card_exibe_avaliacao_parcial(self) -> None:
        avaliacao = {
            "vini": {
                "capacidade_atual": 5.5,
                "potencial_2030": None,
            },
            "beto": {
                "capacidade_atual": None,
                "potencial_2030": None,
            },
        }

        html = self._renderizar(avaliacao)

        self.assertIn("Avaliação Parcial", html)

    def test_card_exibe_sem_avaliacao(self) -> None:
        html = self._renderizar(None)

        self.assertIn("Sem Avaliação", html)
