"""Testes arquiteturais da Fase 3."""

from __future__ import annotations

import unittest
from pathlib import Path

from hexa_avaliacoes import carregar_avaliacoes
from hexa_config import MENU_ANALISE, MENU_CAMPO, MENU_PERFIS, MENU_ROSTER
from hexa_context import AppContext
from hexa_data import carregar_jogadores
from hexa_pages import PAGE_RENDERERS, render_tela

ROOT = Path(__file__).resolve().parents[1]


class Phase3ArchitectureTests(unittest.TestCase):
    def test_contexto_eh_imutavel_e_tipado(self) -> None:
        jogadores = carregar_jogadores()
        avaliacoes = carregar_avaliacoes(jogadores=jogadores)
        periodo = avaliacoes.periodos()[-1]
        contexto = AppContext(
            menu=MENU_CAMPO,
            jogadores=jogadores,
            base_avaliacoes=avaliacoes,
            periodo=periodo,
        )
        self.assertEqual(contexto.menu, MENU_CAMPO)
        with self.assertRaises(Exception):
            contexto.menu = MENU_ANALISE  # type: ignore[misc]

    def test_roteador_declara_quatro_paginas_publicas(self) -> None:
        self.assertEqual(
            set(PAGE_RENDERERS),
            {MENU_CAMPO, MENU_PERFIS, MENU_ROSTER, MENU_ANALISE},
        )

    def test_modulos_de_pagina_foram_separados(self) -> None:
        esperados = (
            "hexa_page_campo.py",
            "hexa_page_scout.py",
            "hexa_page_roster.py",
            "hexa_page_indicadores.py",
            "hexa_feedback.py",
            "hexa_style_base.py",
            "hexa_style_accessibility.py",
            "hexa_style_extensions.py",
        )
        for nome in esperados:
            self.assertTrue((ROOT / nome).is_file(), nome)

    def test_hexa_pages_permanece_pequeno(self) -> None:
        total = len((ROOT / "hexa_pages.py").read_text(encoding="utf-8").splitlines())
        self.assertLess(total, 120)

    def test_hexa_styles_permanece_pequeno(self) -> None:
        total = len((ROOT / "hexa_styles.py").read_text(encoding="utf-8").splitlines())
        self.assertLess(total, 60)

    def test_assinatura_legada_exige_contrato_completo(self) -> None:
        with self.assertRaises(TypeError):
            render_tela(menu=MENU_CAMPO)


if __name__ == "__main__":
    unittest.main()
