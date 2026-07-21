"""Contrato público da RC5 e prevenção de regressão ao modelo legado."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODULOS_PUBLICOS = (
    "hexa_pages.py",
    "hexa_components.py",
    "hexa_selectors.py",
)
CAMPOS_LEGADOS_PROIBIDOS = (
    "nota_vini",
    "nota_roberto",
    "pontos_fortes",
    "pontos_fracos",
)


class TestRC5ContratoPublico(unittest.TestCase):
    def test_interface_nao_le_campos_de_avaliacao_legados(self) -> None:
        for nome_arquivo in MODULOS_PUBLICOS:
            texto = (BASE_DIR / nome_arquivo).read_text(encoding="utf-8")
            for campo in CAMPOS_LEGADOS_PROIBIDOS:
                self.assertNotIn(
                    campo,
                    texto,
                    msg=f"{nome_arquivo} voltou a referenciar {campo}.",
                )

    def test_todos_os_python_sao_sintaticamente_validos(self) -> None:
        for caminho in BASE_DIR.rglob("*.py"):
            if "__pycache__" in caminho.parts:
                continue
            ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))

    def test_rotulos_publicos_dos_analistas(self) -> None:
        config = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn('NOME_ANALISTA_VINI = "Vini Leonel"', config)
        self.assertIn('NOME_CURTO_ANALISTA_VINI = "Vini"', config)
        self.assertIn('NOME_ANALISTA_BETO = "Beto Muñoz"', config)
        self.assertIn('NOME_CURTO_ANALISTA_BETO = "Beto"', config)

    def test_titulos_rc4_permanecem(self) -> None:
        config = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn("Jogadores, Scout e Avaliações", config)
        self.assertIn("Lista de Jogadores", config)
        self.assertIn("Análises & Mercado", config)

    def test_data_de_referencia_e_contexto_estao_na_interface(self) -> None:
        pages = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertIn("Data de referência", pages)
        self.assertIn("avaliações esportivas", pages.lower())
        self.assertIn("valores de mercado", pages.lower())

    def test_versao_rc5(self) -> None:
        config = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn("1.1.0-rc5-avaliacoes-trimestrais", config)


if __name__ == "__main__":
    unittest.main()
