"""Testes de regressão do refinamento visual RC5.3."""

from __future__ import annotations

import ast
import importlib.util
import sys
import tomllib
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SUPPORT_ROOT = ROOT.parent
for caminho in (str(SUPPORT_ROOT), str(ROOT)):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)


def _carregar_componentes_isolado():
    """Carrega o módulo alterado sem depender dos arquivos ausentes no sandbox."""
    stub_avaliacoes = types.ModuleType("hexa_avaliacoes")
    stub_avaliacoes.calcular_metricas_avaliacao = lambda registro: {}
    stub_avaliacoes.formatar_numero = lambda valor, **_: str(valor)

    stub_data = types.ModuleType("hexa_data")
    stub_data.extrair_altura_metros = lambda *_args, **_kwargs: 0.0
    stub_data.formatar_valor_milhoes = lambda valor: str(valor)
    stub_data.percentual_do_pico = lambda *_args, **_kwargs: None
    stub_data.valor_mercado_atual = lambda *_args, **_kwargs: 0.0
    stub_data.valor_mercado_maximo = lambda *_args, **_kwargs: 0.0

    anteriores = {
        nome: sys.modules.get(nome)
        for nome in ("hexa_avaliacoes", "hexa_data")
    }
    sys.modules["hexa_avaliacoes"] = stub_avaliacoes
    sys.modules["hexa_data"] = stub_data
    try:
        nome_modulo = "hexa_components_refinamento_visual_test"
        spec = importlib.util.spec_from_file_location(
            nome_modulo,
            ROOT / "hexa_components.py",
        )
        if spec is None or spec.loader is None:
            raise AssertionError("Não foi possível carregar hexa_components.py.")
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[nome_modulo] = modulo
        spec.loader.exec_module(modulo)
        return modulo
    finally:
        for nome, anterior in anteriores.items():
            if anterior is None:
                sys.modules.pop(nome, None)
            else:
                sys.modules[nome] = anterior


class RefinamentoVisualTests(unittest.TestCase):
    def test_tema_define_fonte_e_escala_nativas(self) -> None:
        caminho = ROOT / ".streamlit" / "config.toml"
        tema = tomllib.loads(caminho.read_text(encoding="utf-8"))["theme"]
        self.assertEqual(tema["font"], "sans-serif")
        self.assertEqual(tema["headingFont"], "sans-serif")
        self.assertEqual(tema["baseFontSize"], 16)
        self.assertEqual(tema["baseFontWeight"], 400)
        self.assertEqual(
            tema["headingFontWeights"],
            [700, 600, 600, 600, 600, 600],
        )
        self.assertEqual(len(tema["headingFontSizes"]), 6)

    def test_css_centraliza_escala_e_remove_peso_800(self) -> None:
        fonte = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")
        for token in (
            "--type-display",
            "--type-h1",
            "--type-h2",
            "--type-h3",
            "--type-body",
            "--type-label",
        ):
            self.assertIn(token, fonte)
        self.assertNotIn("font-weight: 800", fonte)
        self.assertNotIn("font-family: Inter", fonte)
        self.assertIn(".kpi-grid", fonte)
        self.assertIn(".contract-details", fonte)

    def test_metricas_nativas_gigantes_foram_removidas(self) -> None:
        for nome in ("hexa_pages.py", "hexa_admin.py"):
            fonte = (ROOT / nome).read_text(encoding="utf-8")
            self.assertNotIn(".metric(", fonte)
        componentes = (ROOT / "hexa_components.py").read_text(encoding="utf-8")
        self.assertIn("def render_kpis(", componentes)
        self.assertIn("class KPI:", componentes)

    def test_titulo_redundante_da_analise_foi_removido(self) -> None:
        fonte = (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertNotIn(
            'st.markdown("## Compilado de avaliações para o Ciclo 2030")',
            fonte,
        )
        self.assertIn(
            '"Visão consolidada das avaliações esportivas e dos dados de mercado',
            fonte,
        )
        self.assertIn("mostrar_estatisticas=False", fonte)
        self.assertIn('st.markdown("## Definir reservas")', fonte)
        componentes = (ROOT / "hexa_components.py").read_text(encoding="utf-8")
        self.assertIn("## Banco selecionado", componentes)

    def test_imports_visuais_referenciam_nomes_existentes(self) -> None:
        componentes = ast.parse(
            (ROOT / "hexa_components.py").read_text(encoding="utf-8")
        )
        definidos = {
            no.name
            for no in componentes.body
            if isinstance(no, (ast.FunctionDef, ast.ClassDef))
        }
        paginas = ast.parse(
            (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        )
        importados: set[str] = set()
        for no in paginas.body:
            if isinstance(no, ast.ImportFrom) and no.module == "hexa_components":
                importados.update(alias.name for alias in no.names)
        self.assertTrue(
            {"KPI", "render_cabecalho", "render_cabecalho_secao", "render_kpis"}
            <= importados
        )
        self.assertTrue(importados <= definidos)

    def test_dados_contratuais_usam_lista_de_definicoes(self) -> None:
        modulo = _carregar_componentes_isolado()
        dados = {
            "nome": "Atleta",
            "nome_completo": "Atleta de Teste",
            "tm_nascimento": "01/01/2000",
            "tm_nacionalidades": ["Brasil"],
            "tm_posicao_site": "Médio Centro",
            "tm_posicoes_secundarias_site": ["Médio Defensivo"],
            "tm_ultima_renovacao": None,
        }
        with patch.object(modulo.st, "markdown") as markdown, patch.object(
            modulo.st,
            "info",
        ):
            modulo.render_dados_transfermarkt(dados)

        html = markdown.call_args.args[0]
        self.assertIn("<dl", html)
        self.assertIn("<dt", html)
        self.assertIn("<dd", html)
        self.assertIn("Médio Centro", html)
        self.assertIn("Médio Defensivo", html)
        self.assertNotIn("Nacionalidades", html)
        self.assertNotIn("['", html)
        self.assertNotIn("Não informado", html)
        self.assertNotIn("Última renovação", html)

    def test_kpis_sao_compactos_semanticos_e_escapados(self) -> None:
        modulo = _carregar_componentes_isolado()
        itens = (
            modulo.KPI("Cobertura", "70,5%", "43 completas", "positivo"),
            modulo.KPI("<Rótulo>", "<valor>", None, "tom-invalido"),
        )
        with patch.object(modulo.st, "markdown") as markdown:
            modulo.render_kpis(
                itens,
                titulo="Resumo",
                rotulo_aria="Indicadores de teste",
            )

        html = markdown.call_args.args[0]
        self.assertIn('role="list"', html)
        self.assertIn('role="listitem"', html)
        self.assertIn("kpi-positivo", html)
        self.assertIn("kpi-neutro", html)
        self.assertIn("&lt;Rótulo&gt;", html)
        self.assertIn("&lt;valor&gt;", html)


if __name__ == "__main__":
    unittest.main()
