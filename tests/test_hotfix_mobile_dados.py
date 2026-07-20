"""Testes de regressão do hotfix mobile e dados externos."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fonte_funcao(nome_arquivo: str, nome_funcao: str) -> str:
    caminho = ROOT / nome_arquivo
    fonte = caminho.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == nome_funcao:
            trecho = ast.get_source_segment(fonte, no)
            if trecho is None:
                break
            return trecho
    raise AssertionError(f"Função {nome_funcao!r} não encontrada em {nome_arquivo}.")


class HotfixMobileDadosTests(unittest.TestCase):
    def test_sidebar_inicia_em_modo_responsivo(self) -> None:
        fonte = (ROOT / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn('"initial_sidebar_state": "auto"', fonte)
        self.assertNotIn('"initial_sidebar_state": "expanded"', fonte)

    def test_cabecalho_nativo_nao_e_ocultado(self) -> None:
        fonte = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")
        self.assertNotIn('header[data-testid="stHeader"]', fonte)
        self.assertIn("#MainMenu", fonte)
        self.assertIn(".stDeployButton", fonte)

    def test_navegacao_aparece_antes_do_login(self) -> None:
        fonte = _fonte_funcao("caminho_hexa_2030.py", "render_navegacao")
        arvore = ast.parse(fonte)
        chamadas: list[tuple[int, str]] = []
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call):
                continue
            nome = ""
            if isinstance(no.func, ast.Name):
                nome = no.func.id
            elif isinstance(no.func, ast.Attribute):
                nome = no.func.attr
            chamadas.append((no.lineno, nome))
        chamadas.sort()
        nomes = [nome for _, nome in chamadas]
        self.assertLess(
            nomes.index("radio"),
            nomes.index("render_controle_login"),
        )

    def test_nacionalidade_nao_e_exibida_e_posicoes_usam_campos_reais(self) -> None:
        fonte = _fonte_funcao(
            "hexa_components.py",
            "render_dados_transfermarkt",
        )
        self.assertNotIn("tm_nacionalidades", fonte)
        self.assertNotIn('"Nacionalidades"', fonte)
        self.assertIn("tm_posicao_site", fonte)
        self.assertIn("tm_posicoes_secundarias_site", fonte)
        self.assertNotIn('dados.get("tm_posicao")', fonte)
        self.assertNotIn('dados.get("tm_posicoes_secundarias")', fonte)


if __name__ == "__main__":
    unittest.main()
