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
    preenchidas = sum(
        valor is not None
        for valor in (
            atual_vini,
            potencial_vini,
            atual_beto,
            potencial_beto,
        )
    )
    status = (
        "Completa"
        if preenchidas == 4
        else "Parcial"
        if preenchidas
        else "Não avaliada"
    )
    return {
        "capacidade_atual_media": _media((atual_vini, atual_beto)),
        "potencial_2030_medio": _media((potencial_vini, potencial_beto)),
        "saldo_projetado": None,
        "status": status,
    }


def _instalar_stubs() -> None:
    streamlit = types.ModuleType("streamlit")
    streamlit.markdown = lambda *args, **kwargs: None
    streamlit.info = lambda *args, **kwargs: None
    streamlit.write = lambda *args, **kwargs: None
    sys.modules["streamlit"] = streamlit

    avaliacoes = types.ModuleType("hexa_avaliacoes")
    avaliacoes.calcular_metricas_avaliacao = _calcular_metricas
    avaliacoes.formatar_numero = (
        lambda valor, sinal=False: "Sem base"
        if valor is None
        else f"{float(valor):+.2f}".replace(".", ",")
        if sinal
        else f"{float(valor):.2f}".replace(".", ",")
    )
    avaliacoes.formatar_status_avaliacao = lambda valor: {
        "Completa": "Avaliação Completa",
        "Parcial": "Avaliação Parcial",
        "Não avaliada": "Sem Avaliação",
    }.get(str(valor), str(valor))
    sys.modules["hexa_avaliacoes"] = avaliacoes

    config = types.ModuleType("hexa_config")
    config.ANO_BASE_DADOS = 2026
    config.ANO_COPA = 2030
    sys.modules["hexa_config"] = config

    data = types.ModuleType("hexa_data")
    data.extrair_altura_metros = lambda dados: 0.0
    data.formatar_valor_milhoes = lambda valor: f"€ {float(valor):,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    data.percentual_do_pico = lambda dados: (
        float(dados.get("tm_valor_mercado_milhoes", 0))
        / float(dados.get("tm_valor_maximo_milhoes", 1))
        * 100
    )
    data.valor_mercado_atual = lambda dados: float(
        dados.get("tm_valor_mercado_milhoes", 0)
    )
    data.valor_mercado_maximo = lambda dados: float(
        dados.get("tm_valor_maximo_milhoes", 0)
    )
    sys.modules["hexa_data"] = data

    taticas = types.ModuleType("hexa_taticas")
    taticas.ABREVIACOES = {
        "Zagueiro": "ZAG",
        "Ponta-direita": "PD",
        "Meia-armador": "MEI",
        "Mezzala direito": "MCD",
    }
    taticas.LIMITE_CONVOCADOS = 26
    taticas.LIMITE_RESERVAS = 15
    taticas.LIMITE_TITULARES = 11
    taticas.SlotTatico = object
    taticas.indice_adaptabilidade = lambda *args, **kwargs: 0
    sys.modules["hexa_taticas"] = taticas


def _carregar_componentes():
    _instalar_stubs()
    nome_modulo = "hexa_components_rc56_teste"
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


class TestRC56RefinoExecutivo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.componentes = _carregar_componentes()

    def setUp(self):
        self.captura = CapturaStreamlit()
        self.componentes.st = self.captura

    def test_dados_jogador_remove_referencia_e_adiciona_clube(self):
        dados = {
            "nome": "Alexsandro",
            "nome_completo": "Alexsandro Victor de Souza Ribeiro",
            "clube": "LOSC Lille",
            "tm_nascimento": "09/08/1999",
            "tm_empresario": "Roc Nation Sports",
            "tm_posicao_site": "Defesa Central",
        }
        self.componentes.render_dados_transfermarkt(dados)
        html = self.captura.markdowns[-1]

        self.assertIn("Identificação", html)
        self.assertIn("Vínculo profissional", html)
        self.assertIn("Clube atual", html)
        self.assertIn("LOSC Lille", html)
        self.assertNotIn("Referência cadastral externa", html)
        self.assertNotIn("Defesa Central", html)

    def test_mercado_mantem_observacao_semantica(self):
        dados = {
            "tm_valor_mercado_milhoes": 15.0,
            "tm_valor_maximo_milhoes": 20.0,
            "tm_data_valor_maximo": "02/06/2025",
            "tm_ultima_atualizacao": "31/05/2026",
        }
        self.componentes.render_comparativo_mercado(dados)
        html = self.captura.markdowns[-1]

        self.assertIn('class="market-dates"', html)
        self.assertIn('class="market-card-info"', html)
        self.assertIn("<em>", html)
        self.assertIn("referência externa", html)

    def test_quadro_executivo_substitui_dataframe(self):
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

        self.assertIn("evaluation-scorecard", html)
        self.assertIn("Capacidade atual", html)
        self.assertIn("Potencial 2030", html)
        self.assertIn("7,00", html)
        self.assertIn("7,25", html)
        self.assertIn("Desempenho no período", html)
        self.assertIn("Projeção para o ciclo", html)

    def test_paginas_usam_novos_titulos_e_componente(self):
        fonte = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")

        self.assertIn('render_cabecalho(\n        "Scout",', fonte)
        self.assertIn('render_cabecalho("Jogadores")', fonte)
        self.assertIn('        "Indicadores",', fonte)
        self.assertIn("render_quadro_avaliacao_executivo(", fonte)

        trecho = fonte.split("def _render_avaliacao_trimestral", 1)[1]
        trecho = trecho.split("def _render_historico_atleta", 1)[0]
        self.assertNotIn("st.dataframe(", trecho)

    def test_navegacao_usa_nomes_solicitados(self):
        fonte = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")

        self.assertIn('MENU_CAMPO = "🏟️ Escalação"', fonte)
        self.assertIn('MENU_PERFIS = "🔎 Scout"', fonte)
        self.assertIn('MENU_ROSTER = "📋 Jogadores"', fonte)
        self.assertIn('MENU_ANALISE = "📊 Indicadores"', fonte)
        self.assertIn(
            'VERSAO_APLICACAO = "1.1.8-rc5.6-refino-executivo"',
            fonte,
        )

    def test_css_aplica_respiro_e_fonte_menor(self):
        css = (BASE_DIR / "hexa_styles.py").read_text(encoding="utf-8")

        self.assertIn(".evaluation-scorecard", css)
        self.assertIn(".evaluation-score-average", css)
        self.assertGreaterEqual(css.count("margin: 1.5rem 0 0;"), 2)
        self.assertGreaterEqual(css.count("font-size: .75rem;"), 2)
        self.assertIn("padding-top: .9rem;", css)
        self.assertIn("border-top: 1px dashed", css)


if __name__ == "__main__":
    unittest.main()
