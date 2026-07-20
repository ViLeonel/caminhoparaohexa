from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class KPI:
    rotulo: str
    valor: object
    contexto: str | None = None
    tom: str = "neutro"


@dataclass(frozen=True)
class ColunaTabelaExecutiva:
    chave: str
    rotulo: str
    largura: str | None = None
    formato: str = "texto"
    alinhamento: str = "esquerda"
    progresso: bool = False
    destaque: bool = False


class StreamlitStub(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("streamlit")
        self.kpis_renderizados: list[tuple[KPI, ...]] = []
        self.tabelas_renderizadas: list[list[dict[str, object]]] = []
        self.sidebar = types.SimpleNamespace()

    def markdown(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None

    def write(self, *args, **kwargs):
        return None

    def columns(self, quantidade, **kwargs):
        total = quantidade if isinstance(quantidade, int) else len(quantidade)
        return [nullcontext() for _ in range(total)]

    def expander(self, *args, **kwargs):
        return nullcontext()


def _instalar_stubs() -> StreamlitStub:
    st = StreamlitStub()
    sys.modules["streamlit"] = st

    avaliacoes = types.ModuleType("hexa_avaliacoes")
    avaliacoes.BaseAvaliacoes = object
    avaliacoes.calcular_metricas_avaliacao = lambda registro: {}
    avaliacoes.calcular_resumo_convocados = lambda *args, **kwargs: {}
    avaliacoes.calcular_resumo_periodo = lambda *args, **kwargs: {
        "data_referencia": "2026-06-30",
        "atletas_na_base": 2,
        "com_alguma_avaliacao": 2,
        "avaliacoes_completas": 2,
        "cobertura_completa": 1.0,
        "capacidade_atual_media": 7.0,
        "potencial_2030_medio": 7.5,
        "saldo_projetado_medio": 0.5,
    }
    avaliacoes.construir_rankings_periodo = lambda *args, **kwargs: {
        "maior_capacidade": [],
        "maior_potencial": [],
        "maior_evolucao": [],
        "maior_regressao": [],
        "parciais": [],
        "nao_avaliados": [],
    }
    avaliacoes.formatar_data_referencia = lambda valor: "30/06/2026"
    avaliacoes.formatar_numero = lambda valor, sinal=False: (
        f"{float(valor):+.2f}" if sinal else f"{float(valor):.2f}"
    )
    avaliacoes.formatar_periodo = lambda valor: "T2 2026"
    avaliacoes.formatar_status_avaliacao = lambda valor: str(valor)
    avaliacoes.historico_atleta = lambda *args, **kwargs: []
    sys.modules["hexa_avaliacoes"] = avaliacoes

    componentes = types.ModuleType("hexa_components")
    componentes.ColunaTabelaExecutiva = ColunaTabelaExecutiva
    componentes.KPI = KPI
    componentes.render_banco_reservas = lambda *args, **kwargs: None
    componentes.render_cabecalho = lambda *args, **kwargs: None
    componentes.render_cabecalho_secao = lambda *args, **kwargs: None
    componentes.render_campo = lambda *args, **kwargs: None
    componentes.render_cartao_perfil = lambda *args, **kwargs: None
    componentes.render_comparativo_mercado = lambda *args, **kwargs: None
    componentes.render_dados_transfermarkt = lambda *args, **kwargs: None

    def render_kpis(itens, **kwargs):
        st.kpis_renderizados.append(tuple(itens))

    def render_tabela_executiva(registros, *args, **kwargs):
        st.tabelas_renderizadas.append(list(registros))

    componentes.render_kpis = render_kpis
    componentes.render_legenda_adaptabilidade = lambda *args, **kwargs: None
    componentes.render_quadro_avaliacao_executivo = lambda *args, **kwargs: None
    componentes.render_resumo_elenco = lambda *args, **kwargs: None
    componentes.render_tabela_executiva = render_tabela_executiva
    sys.modules["hexa_components"] = componentes

    config = types.ModuleType("hexa_config")
    config.ANO_BASE_DADOS = 2026
    config.ANO_COPA = 2030
    config.ASSUNTO_FEEDBACK_PREFIXO = "Caminho para o Hexa"
    config.EMAIL_FEEDBACK = "teste@example.com"
    config.GRUPO_OBSERVACAO = "Observação"
    config.MENU_ANALISE = "📊 Indicadores"
    config.MENU_CAMPO = "🏟️ Escalação"
    config.MENU_PERFIS = "🔎 Scout"
    config.MENU_ROSTER = "📋 Jogadores"
    config.NOME_ANALISTA_BETO = "Beto Muñoz"
    config.NOME_ANALISTA_VINI = "Vini Leonel"
    config.NOME_CURTO_ANALISTA_BETO = "Beto"
    config.NOME_CURTO_ANALISTA_VINI = "Vini"
    config.SAUDACAO_FEEDBACK = "Olá"
    config.TIPOS_SUGESTAO = ("Sugerir jogador", "Sugerir melhoria")
    config.TITULO_PROJETO = "O Caminho para o Hexa"
    sys.modules["hexa_config"] = config

    data = types.ModuleType("hexa_data")
    data.formatar_valor_milhoes = lambda valor: f"€ {float(valor):.2f} mi"
    sys.modules["hexa_data"] = data

    persistencia = types.ModuleType("hexa_persistencia_local")
    persistencia.CHAVE_AVISO_RESTAURACAO = "aviso"
    persistencia.apagar_convocacoes_locais = lambda *args, **kwargs: None
    persistencia.sincronizar_persistencia_local = lambda *args, **kwargs: None
    sys.modules["hexa_persistencia_local"] = persistencia

    messages = types.ModuleType("hexa_messages")
    messages.FEEDBACK_MENSAGEM_OBRIGATORIA = "Obrigatório"
    messages.FEEDBACK_PREPARADO = "Preparado"
    messages.MERCADO_SEM_DADOS = "Sem dados"
    messages.ROSTER_SEM_RESULTADOS = "Sem resultados"
    messages.convocacao_completa = lambda *args, **kwargs: False
    messages.resumo_convocacao = lambda *args, **kwargs: ""
    sys.modules["hexa_messages"] = messages

    selectors = types.ModuleType("hexa_selectors")
    selectors.construir_registros_mercado = lambda jogadores: [
        {
            "Nome": "Atleta A",
            "Posição": "Zagueiro",
            "Atual (M€)": 15.0,
            "Pico de mercado (M€)": 20.0,
            "% do pico de mercado": 75.0,
            "Diferença para o pico de mercado (M€)": 5.0,
            "Atualização do mercado": "31/05/2026",
        },
        {
            "Nome": "Atleta B",
            "Posição": "Centroavante",
            "Atual (M€)": 10.0,
            "Pico de mercado (M€)": 12.0,
            "% do pico de mercado": 83.3,
            "Diferença para o pico de mercado (M€)": 2.0,
            "Atualização do mercado": "30/05/2026",
        },
    ]
    selectors.construir_registros_roster = lambda *args, **kwargs: []
    sys.modules["hexa_selectors"] = selectors

    session = types.ModuleType("hexa_session")
    for nome in (
        "chave_reserva_livre",
        "chave_reserva_posicional",
        "chave_titular",
        "limpar_convocacao",
        "migrar_reservas_legadas",
        "normalizar_escolha_reserva",
        "normalizar_escolha_titular",
        "opcoes_reserva_livre",
        "opcoes_reserva_posicional",
        "opcoes_titular",
        "prioridade_posicoes_tatica",
        "quantidade_vagas_livres",
        "reconciliar_convocacao",
    ):
        setattr(session, nome, lambda *args, **kwargs: None)
    sys.modules["hexa_session"] = session

    taticas = types.ModuleType("hexa_taticas")
    taticas.POSICOES_OFICIAIS = ()
    taticas.TATICAS = {}
    taticas.SlotTatico = object
    taticas.formatar_jogador_com_posicao = lambda nome, base: nome
    sys.modules["hexa_taticas"] = taticas

    return st


def _carregar_paginas():
    st = _instalar_stubs()
    nome_modulo = "hexa_pages_hotfix_rc57_teste"
    spec = importlib.util.spec_from_file_location(
        nome_modulo,
        BASE_DIR / "hexa_pages.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Não foi possível carregar hexa_pages.py.")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome_modulo] = modulo
    spec.loader.exec_module(modulo)
    return modulo, st


class TestHotfixRC57Mercado(unittest.TestCase):
    def test_render_tela_analise_executa_caminho_de_mercado(self):
        paginas, st = _carregar_paginas()

        paginas.render_tela_analise(
            jogadores={
                "Atleta A": {"nome": "Atleta A"},
                "Atleta B": {"nome": "Atleta B"},
            },
            base_avaliacoes=object(),
            periodo="2026-T2",
        )

        resumo_mercado = next(
            grupo
            for grupo in st.kpis_renderizados
            if grupo and grupo[0].rotulo == "Atletas com valor"
        )
        self.assertEqual(resumo_mercado[0].valor, 2)
        self.assertEqual(len(st.tabelas_renderizadas[-1]), 2)

    def test_nome_obsoleto_nao_permanece_no_codigo(self):
        fonte = (BASE_DIR / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertNotIn("df_mercado", fonte)
        self.assertIn('len(mercado)', fonte)

    def test_versao_do_hotfix(self):
        fonte = (BASE_DIR / "hexa_config.py").read_text(encoding="utf-8")
        self.assertIn(
            'VERSAO_APLICACAO = "1.1.10-hotfix-rc5.7-mercado"',
            fonte,
        )


if __name__ == "__main__":
    unittest.main()
