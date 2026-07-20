from __future__ import annotations

import re
import unittest
from pathlib import Path

from hexa_accessibility import atende_aa, razao_contraste

ROOT = Path(__file__).resolve().parents[1]


class TestContrasteWCAG(unittest.TestCase):
    def test_combinacoes_normais_atendem_aa(self) -> None:
        pares = (
            ("#F8FAFC", "#0F172A"),
            ("#94A3B8", "#0F172A"),
            ("#EAB308", "#0F172A"),
            ("#22C55E", "#0F172A"),
            ("#F97316", "#0F172A"),
            ("#EF4444", "#0F172A"),
            ("#3B82F6", "#0F172A"),
            ("#020617", "#EAB308"),
        )
        for texto, fundo in pares:
            with self.subTest(texto=texto, fundo=fundo):
                self.assertTrue(atende_aa(texto, fundo), razao_contraste(texto, fundo))

    def test_alto_contraste_atende_aa(self) -> None:
        for texto, fundo in (("#FFFFFF", "#000000"), ("#FFF200", "#000000"),
                              ("#7CFF6B", "#000000"), ("#00E5FF", "#000000")):
            self.assertTrue(atende_aa(texto, fundo))

    def test_cor_invalida_falha(self) -> None:
        with self.assertRaises(ValueError):
            razao_contraste("red", "#000000")


class TestEstruturaAcessivel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.components = (ROOT / "hexa_components.py").read_text(encoding="utf-8")
        cls.pages = (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        cls.main = (ROOT / "caminho_hexa_2030.py").read_text(encoding="utf-8")
        cls.styles = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")

    def test_regioes_personalizadas_tem_rotulos(self) -> None:
        for trecho in ("role=\"img\"", "aria-label=\"Campo tático",
                       "aria-label=\"Formação tática em lista",
                       "aria-label=\"Banco de reservas"):
            self.assertIn(trecho, self.components)

    def test_mensagens_dinamicas_possuem_live_region(self) -> None:
        self.assertIn('aria-live="polite"', self.components)
        self.assertIn('aria-live="polite"', self.pages)

    def test_skip_link_e_main(self) -> None:
        self.assertIn("skip-link", self.main)
        self.assertIn('id="conteudo-principal"', self.main)

    def test_foco_e_alvos_de_toque(self) -> None:
        self.assertIn(":focus-visible", self.styles)
        self.assertIn("min-height: 44px", self.styles)

    def test_alto_contraste_disponivel(self) -> None:
        self.assertIn("HIGH_CONTRAST_CSS", self.styles)
        self.assertIn("Modo de alto contraste", self.main)

    def test_sem_titulos_h3_como_primeiro_nivel_das_paginas(self) -> None:
        self.assertNotIn('st.markdown("### ', self.pages)


if __name__ == "__main__":
    unittest.main()
