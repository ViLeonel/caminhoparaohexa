"""Testes do design system e da ausência de estilos inline."""

from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class TestDesignSystem(unittest.TestCase):
    def test_modulos_visuais_nao_usam_style_inline(self) -> None:
        for nome in ("caminho_hexa_2030.py", "hexa_pages.py", "hexa_components.py"):
            conteudo = (BASE_DIR / nome).read_text(encoding="utf-8")
            self.assertNotIn("style=", conteudo, nome)

    def test_cores_hexadecimais_ficam_no_design_system(self) -> None:
        for nome in ("caminho_hexa_2030.py", "hexa_pages.py", "hexa_components.py"):
            conteudo = (BASE_DIR / nome).read_text(encoding="utf-8")
            self.assertNotRegex(conteudo, r"#[0-9A-Fa-f]{6}", nome)

    def test_classes_semanticas_essenciais_existem(self) -> None:
        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")
        classes = (
            ".adapt-primary",
            ".adapt-secondary",
            ".adapt-tertiary",
            ".legend-primary",
            ".feedback-link",
            ":focus-visible",
            ".stat-positive",
            ".market-card-info",
            ".tactical-list",
            ".tactical-list-item",
        )
        for classe in classes:
            self.assertIn(classe, css)

    def test_todas_as_posicoes_do_campo_tem_classe_css(self) -> None:
        from hexa_taticas import TATICAS

        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")
        for formacao in TATICAS.values():
            for slot in formacao.values():
                left = slot.left.replace("%", "").replace(".", "-")
                bottom = slot.bottom.replace("%", "").replace(".", "-")
                self.assertIn(f".pitch-pos-l{left}-b{bottom}", css)

    def test_classes_de_progresso_cobrem_zero_a_cem(self) -> None:
        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")
        for percentual in range(101):
            self.assertIn(f".progress-pct-{percentual}", css)


    def test_pagina_oferece_alternancia_campo_lista(self) -> None:
        pagina = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertIn('("Campo", "Lista")', pagina)
        self.assertIn("render_lista_tatica", pagina)

if __name__ == "__main__":
    unittest.main()
