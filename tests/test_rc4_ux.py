"""Testes de regressão de textos e nomes públicos da RC4."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

from hexa_config import (
    MENU_ANALISE,
    MENU_PERFIS,
    MENU_ROSTER,
    NOME_ANALISTA_BETO,
    NOME_ANALISTA_VINI,
    NOME_CURTO_ANALISTA_BETO,
    NOME_CURTO_ANALISTA_VINI,
    SAUDACAO_FEEDBACK,
    VERSAO_APLICACAO,
)
from hexa_selectors import (
    construir_avaliacoes,
    construir_registros_roster,
    formatar_texto_editorial,
)


class RC4UXTests(unittest.TestCase):
    def test_identidade_e_menus(self) -> None:
        self.assertEqual(NOME_ANALISTA_VINI, "Vini Leonel")
        self.assertEqual(NOME_CURTO_ANALISTA_VINI, "Vini")
        self.assertEqual(NOME_ANALISTA_BETO, "Beto Muñoz")
        self.assertEqual(NOME_CURTO_ANALISTA_BETO, "Beto")
        self.assertEqual(MENU_PERFIS, "👤 Jogadores, Scout e Avaliações")
        self.assertEqual(MENU_ROSTER, "📋 Lista de Jogadores")
        self.assertEqual(MENU_ANALISE, "📊 Análises & Mercado")
        self.assertEqual(SAUDACAO_FEEDBACK, "Olá, Vini e Beto!")
        self.assertEqual(VERSAO_APLICACAO, "1.0.0-rc4-ux-convocacao")

    def test_formatacao_editorial_nao_altera_vinicius_junior(self) -> None:
        texto = (
            "Vinicius Leonel e Roberto Muñoz avaliaram Vinicius Junior. "
            "Roberto pediu nova observação."
        )
        self.assertEqual(
            formatar_texto_editorial(texto),
            (
                "Vini Leonel e Beto Muñoz avaliaram Vinicius Junior. "
                "Beto pediu nova observação."
            ),
        )

    def test_tabelas_publicas_usam_vini_e_beto(self) -> None:
        jogadores = {
            "Atleta": {
                "posicao": "Goleiro",
                "posicoes_multiplas": ["Goleiro"],
                "grupo": "Observação",
                "clube": "Clube",
                "idade": 20,
                "nota_vini": 8,
                "nota_roberto": 7,
            }
        }
        roster = construir_registros_roster(jogadores)[0]
        avaliacao = construir_avaliacoes(jogadores)[0]
        for registro in (roster, avaliacao):
            self.assertIn("Vini", registro)
            self.assertIn("Beto", registro)
            self.assertNotIn("Roberto", registro)

    def test_frases_antigas_e_cadastro_publico_foram_removidos(self) -> None:
        raiz = Path(__file__).resolve().parents[1]
        fonte = (raiz / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "A pesquisa começa vazia para evitar escolhas acidentais.",
            fonte,
        )
        self.assertNotIn(
            "Consulte, filtre e inclua atletas. Nenhum jogador é removido da base.",
            fonte,
        )
        self.assertNotIn(
            "Consensos, divergências e leitura do valor de mercado do elenco monitorado.",
            fonte,
        )
        self.assertNotIn("Adicionar atleta", fonte)
        self.assertNotIn("adicionar_jogador", fonte)

    def test_literais_publicos_nao_usam_nome_antigo_do_analista(self) -> None:
        raiz = Path(__file__).resolve().parents[1]
        for caminho in (
            raiz / "hexa_config.py",
            raiz / "hexa_pages.py",
        ):
            arvore = ast.parse(caminho.read_text(encoding="utf-8"))
            literais = [
                no.value
                for no in ast.walk(arvore)
                if isinstance(no, ast.Constant) and isinstance(no.value, str)
            ]
            proibidos = [
                literal for literal in literais if "Roberto" in literal
            ]
            self.assertEqual(proibidos, [], caminho.name)


if __name__ == "__main__":
    unittest.main()
