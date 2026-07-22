"""Contratos de compatibilidade, responsividade e acessibilidade da Fase 6."""

from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from hexa_config import (
    MENU_ANALISE,
    MENU_CAMPO,
    MENU_PERFIS,
    MENU_ROSTER,
    VERSAO_APLICACAO,
)
from hexa_style_phase6 import PHASE6_CSS
from hexa_styles import aplicar_estilos


ROOT = Path(__file__).resolve().parents[1]


class Phase6StyleTests(unittest.TestCase):
    def test_versao_fase6(self) -> None:
        self.assertTrue(
            VERSAO_APLICACAO.startswith(("1.7.0-", "1.8.0-", "1.9.0-", "2.0.0-", "2.1.0-", "2.2.0-", "3.0.0-"))
        )

    def test_css_cobre_preferencias_e_breakpoints(self) -> None:
        obrigatorios = (
            "prefers-reduced-motion",
            "forced-colors",
            "pointer: coarse",
            "max-width: 1024px",
            "max-width: 768px",
            "max-width: 480px",
            "-webkit-text-size-adjust",
            "focus-visible",
            "100dvh",
            "@media print",
        )
        for trecho in obrigatorios:
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, PHASE6_CSS)

    def test_design_system_exporta_fase6(self) -> None:
        self.assertTrue(callable(aplicar_estilos))
        conteudo = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")
        self.assertIn("PHASE6_CSS", conteudo)
        self.assertIn("st.markdown(PHASE6_CSS", conteudo)

    def test_script_browser_e_dependencia_presentes(self) -> None:
        self.assertTrue((ROOT / "scripts/browser_smoke_phase6.py").is_file())
        requisitos = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("playwright==", requisitos)


class Phase6AppTests(unittest.TestCase):
    def test_quatro_paginas_abrem_sem_excecao(self) -> None:
        app = AppTest.from_file(str(ROOT / "caminho_hexa_2030.py"))
        app.run(timeout=30)
        self.assertEqual(len(app.exception), 0)

        for menu in (MENU_CAMPO, MENU_PERFIS, MENU_ROSTER, MENU_ANALISE):
            with self.subTest(menu=menu):
                radio = app.sidebar.radio[0]
                radio.set_value(menu)
                app.run(timeout=30)
                self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
