from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def _media(valores):
    numeros = [float(valor) for valor in valores if valor is not None]
    return sum(numeros) / len(numeros) if numeros else None


def _calcular_metricas(registro):
    vini = registro.get("vini") or {}
    beto = registro.get("beto") or {}
    atual_vini = vini.get("capacidade_atual")
    atual_beto = beto.get("capacidade_atual")
    potencial_vini = vini.get("potencial_2030")
    potencial_beto = beto.get("potencial_2030")
    return {
        "capacidade_atual_media": _media((atual_vini, atual_beto)),
        "potencial_2030_medio": _media((potencial_vini, potencial_beto)),
        "saldo_projetado": None,
        "status": "Completa",
    }


def _instalar_stubs() -> None:
    streamlit = types.ModuleType("streamlit")
    streamlit.markdown = lambda *args, **kwargs: None
    streamlit.info = lambda *args, **kwargs: None
    streamlit.write = lambda *args, **kwargs: None
    sys.modules["streamlit"] = streamlit

    avaliacoes = types.ModuleType("hexa_avaliacoes")
    avaliacoes.calcular_metricas_avaliacao = _calcular_metricas
    avaliacoes.formatar_numero = lambda valor, sinal=False: (
        "Sem base"
        if valor is None
        else (
            f"{float(valor):+.2f}".replace(".", ",")
            if sinal
            else f"{float(valor):.2f}".replace(".", ",")
        )
    )
    avaliacoes.formatar_status_avaliacao = lambda valor: str(valor)
    sys.modules["hexa_avaliacoes"] = avaliacoes

    config = types.ModuleType("hexa_config")
    config.ANO_BASE_DADOS = 2026
    config.ANO_COPA = 2030
    sys.modules["hexa_config"] = config

    data = types.ModuleType("hexa_data")
    data.extrair_altura_metros = lambda dados: 0.0
    data.formatar_valor_milhoes = lambda valor: (
        f"€ {float(valor):,.2f} mi"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    data.percentual_do_pico = lambda dados: 75.0
    data.valor_mercado_atual = lambda dados: 15.0
    data.valor_mercado_maximo = lambda dados: 20.0
    sys.modules["hexa_data"] = data

    taticas = types.ModuleType("hexa_taticas")
    taticas.ABREVIACOES = {"Zagueiro": "ZAG"}
    taticas.LIMITE_CONVOCADOS = 26
    taticas.LIMITE_RESERVAS = 15
    taticas.LIMITE_TITULARES = 11
    taticas.SlotTatico = object
    taticas.indice_adaptabilidade = lambda *args, **kwargs: 0
    sys.modules["hexa_taticas"] = taticas


def _carregar_componentes():
    _instalar_stubs()
    nome_modulo = "hexa_components_rc57_teste"
    spec = importlib.util.spec_from_file_location(
        nome_modulo,
        BASE_DIR / "hexa_components.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Não foi possível carregar hexa_components.py.")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome_modulo] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class CapturaStreamlit:
    def __init__(self):
        self.markdowns = []
        self.infos = []

    def markdown(self, conteudo, **kwargs):
        self.markdowns.append(conteudo)

    def info(self, conteudo, **kwargs):
        self.infos.append(conteudo)

    def write(self, conteudo, **kwargs):
        self.markdowns.append(str(conteudo))


class TestRC57TabelasExecutivas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.componentes = _carregar_componentes()

    def setUp(self):
        self.captura = CapturaStreamlit()
        self.componentes.st = self.captura

    def test_tabela_generica_formata_e_escapa_valores(self):
        colunas = (
            self.componentes.ColunaTabelaExecutiva(
                "nome",
                "Nome",
                largura="40%",
            ),
            self.componentes.ColunaTabelaExecutiva(
                "saldo",
                "Saldo",
                formato="sinal_2",
                alinhamento="centro",
            ),
            self.componentes.ColunaTabelaExecutiva(
                "percentual",
                "% do pico",
                formato="percentual_1",
                alinhamento="direita",
                progresso=True,
                destaque=True,
            ),
        )
        self.componentes.render_tabela_executiva(
            [
                {
                    "nome": ("Atleta <teste>", "Clube & contexto"),
                    "saldo": 0.25,
                    "percentual": 75.0,
                }
            ],
            colunas,
            rotulo_aria="Tabela de teste",
            legenda="Teste semântico",
        )
        html = self.captura.markdowns[-1]

        self.assertIn("executive-table-card", html)
        self.assertIn("executive-table", html)
        self.assertIn("Atleta &lt;teste&gt;", html)
        self.assertIn("Clube &amp; contexto", html)
        self.assertIn("+0,25", html)
        self.assertIn("75,0%", html)
        self.assertIn("width:75.0%", html)
        self.assertIn("executive-table-column--accent", html)

    def test_tabela_larga_e_longa_recebe_modificadores(self):
        colunas = tuple(
            self.componentes.ColunaTabelaExecutiva(
                f"c{i}",
                f"Coluna {i}",
            )
            for i in range(6)
        )
        registros = [
            {f"c{i}": f"{linha}-{i}" for i in range(6)}
            for linha in range(13)
        ]
        self.componentes.render_tabela_executiva(
            registros,
            colunas,
            rotulo_aria="Tabela extensa",
        )
        html = self.captura.markdowns[-1]

        self.assertIn("executive-table-card--wide", html)
        self.assertIn("executive-table-card--tall", html)

    def test_quadro_de_avaliacao_usa_mesmo_componente(self):
        registro = {
            "vini": {
                "capacidade_atual": 7.0,
                "potencial_2030": 7.0,
            },
            "beto": {
                "capacidade_atual": 7.0,
                "potencial_2030": 7.5,
            },
        }
        self.componentes.render_quadro_avaliacao_executivo(registro)
        html = self.captura.markdowns[-1]

        self.assertIn("executive-table-card", html)
        self.assertIn("Capacidade atual", html)
        self.assertIn("Potencial 2030", html)
        self.assertIn("7,25", html)
        self.assertNotIn("evaluation-scorecard", html)

    def test_css_remove_folga_inferior_da_tabela(self):
        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")

        self.assertIn(".executive-table {", css)
        self.assertIn("margin: 0 !important;", css)
        self.assertIn(
            ".executive-table tbody tr:last-child > *",
            css,
        )
        self.assertIn("border-bottom: 0;", css)
        self.assertIn(".executive-table-column--accent", css)

    def test_todas_as_tabelas_publicas_usam_renderer_executivo(self):
        fonte = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")

        self.assertNotIn("st.dataframe(", fonte)
        self.assertNotIn("st.table(", fonte)
        self.assertGreaterEqual(
            fonte.count("render_tabela_executiva("),
            4,
        )
        self.assertIn("Tabela de jogadores monitorados", fonte)
        self.assertIn("Tabela consolidada de valor de mercado", fonte)
        self.assertIn("Avaliações parciais do período", fonte)

    def test_versao_rc57(self):
        fonte = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn(
            'VERSAO_APLICACAO = "1.1.10-hotfix-rc5.7-mercado"',
            fonte,
        )


if __name__ == "__main__":
    unittest.main()
