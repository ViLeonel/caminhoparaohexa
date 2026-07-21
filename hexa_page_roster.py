"""Tela de jogadores e lista monitorada."""

from __future__ import annotations

import html
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import streamlit as st

from hexa_avaliacoes import (
    BaseAvaliacoes,
    calcular_metricas_avaliacao,
    calcular_resumo_convocados,
    calcular_resumo_periodo,
    construir_rankings_periodo,
    formatar_data_referencia,
    formatar_numero,
    formatar_periodo,
    formatar_status_avaliacao,
    historico_atleta,
)
from hexa_components import (
    ColunaTabelaExecutiva,
    KPI,
    render_banco_reservas,
    render_cabecalho,
    render_cabecalho_secao,
    render_campo,
    render_cartao_perfil,
    render_comparativo_mercado,
    render_dados_transfermarkt,
    render_kpis,
    render_legenda_adaptabilidade,
    render_quadro_avaliacao_executivo,
    render_resumo_elenco,
    render_tabela_executiva,
)
from hexa_config import (
    ANO_BASE_DADOS,
    ANO_COPA,
    ASSUNTO_FEEDBACK_PREFIXO,
    EMAIL_FEEDBACK,
    GRUPO_OBSERVACAO,
    MENU_ANALISE,
    MENU_CAMPO,
    MENU_PERFIS,
    MENU_ROSTER,
    NOME_ANALISTA_BETO,
    NOME_ANALISTA_VINI,
    NOME_CURTO_ANALISTA_BETO,
    NOME_CURTO_ANALISTA_VINI,
    SAUDACAO_FEEDBACK,
    TIPOS_SUGESTAO,
    TITULO_PROJETO,
)
from hexa_data import (
    formatar_valor_milhoes,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_persistencia_local import (
    CHAVE_AVISO_RESTAURACAO,
    apagar_convocacoes_locais,
    sincronizar_persistencia_local,
)
from hexa_messages import (
    FEEDBACK_MENSAGEM_OBRIGATORIA,
    FEEDBACK_PREPARADO,
    MERCADO_SEM_DADOS,
    ROSTER_SEM_RESULTADOS,
    convocacao_completa,
    resumo_convocacao,
)
from hexa_selectors import (
    construir_registros_mercado,
    construir_registros_roster,
)
from hexa_session import (
    chave_reserva_livre,
    chave_reserva_posicional,
    chave_titular,
    limpar_convocacao,
    migrar_reservas_legadas,
    normalizar_escolha_reserva,
    normalizar_escolha_titular,
    opcoes_reserva_livre,
    opcoes_reserva_posicional,
    opcoes_titular,
    prioridade_posicoes_tatica,
    quantidade_vagas_livres,
    reconciliar_convocacao,
)
from hexa_taticas import (
    POSICOES_OFICIAIS,
    TATICAS,
    SlotTatico,
    formatar_jogador_com_posicao,
)

__all__ = ['render_tela_roster']


def _esc(valor: Any, padrao: str = "") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


def _avaliacoes_por_nome(
    base: BaseAvaliacoes,
    periodo: str,
) -> dict[str, Mapping[str, Any]]:
    return base.por_nome_no_periodo(periodo)


def _render_contexto_periodo(
    base: BaseAvaliacoes,
    periodo: str,
    *,
    total_atletas: int,
    mostrar_estatisticas: bool = True,
) -> None:
    resumo = calcular_resumo_periodo(
        base,
        periodo,
        total_atletas=total_atletas,
    )
    data_texto = formatar_data_referencia(resumo["data_referencia"])
    estatisticas_html = ""
    if mostrar_estatisticas:
        estatisticas_html = (
            '<div class="evaluation-context-stats">'
            f'<span>{resumo["com_alguma_avaliacao"]} com alguma avaliação</span>'
            f'<span>{resumo["avaliacoes_completas"]} completas</span>'
            f'<span>Cobertura completa: {resumo["cobertura_completa"]:.1%}</span>'
            "</div>"
        )
    st.markdown(
        '<section class="evaluation-context" role="note">'
        '<div class="evaluation-context-main">'
        f'<strong>Avaliações referentes ao {_esc(formatar_periodo(periodo))}</strong>'
        f'<span>Data de referência: {_esc(data_texto)}</span>'
        "</div>"
        f"{estatisticas_html}</section>",
        unsafe_allow_html=True,
    )


def _tipar_valores_mercado_roster(
    registros: Sequence[Mapping[str, Any]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Substitui rótulos monetários por números para ordenar e filtrar corretamente."""
    tipados: list[dict[str, Any]] = []
    for registro in registros:
        item = dict(registro)
        nome = str(item.get("Nome") or "").strip()
        atleta = jogadores.get(nome)

        if isinstance(atleta, Mapping):
            valor_atual = valor_mercado_atual(atleta)
            valor_pico = valor_mercado_maximo(atleta)
            item["Valor atual"] = valor_atual if valor_atual > 0 else None
            item["Pico de mercado"] = valor_pico if valor_pico > 0 else None
        else:
            item["Valor atual"] = None
            item["Pico de mercado"] = None

        tipados.append(item)
    return tipados


def render_tela_roster(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    render_cabecalho("Jogadores")
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    filtro_1, filtro_2, filtro_3 = st.columns([2, 1, 1])
    busca = filtro_1.text_input(
        "Buscar por nome ou clube",
        placeholder="Ex.: Real Madrid ou Vini Jr",
    )
    posicao_filtro = filtro_2.selectbox(
        "Posição",
        ["Todas", *POSICOES_OFICIAIS],
    )
    grupos = sorted(
        {
            str(dados.get("grupo", GRUPO_OBSERVACAO))
            for dados in jogadores.values()
        }
    )
    grupo_filtro = filtro_3.selectbox("Grupo cadastral", ["Todos", *grupos])

    registros = construir_registros_roster(
        jogadores,
        avaliacoes_periodo,
        busca=busca,
        posicao=None if posicao_filtro == "Todas" else posicao_filtro,
        grupo=None if grupo_filtro == "Todos" else grupo_filtro,
    )
    registros = _tipar_valores_mercado_roster(registros, jogadores)

    st.caption(
        f"{len(registros)} atleta(s) exibido(s) de "
        f"{len(jogadores)} cadastrados."
    )
    if not registros:
        st.info(ROSTER_SEM_RESULTADOS)
        return

    render_tabela_executiva(
        registros,
        (
            ColunaTabelaExecutiva(
                "Nome",
                "Nome",
                largura="15%",
                fixada="left",
            ),
            ColunaTabelaExecutiva("Posição", "Posição"),
            ColunaTabelaExecutiva("Clube atual", "Clube atual"),
            ColunaTabelaExecutiva(
                f"Idade {ANO_BASE_DADOS}",
                f"Idade {ANO_BASE_DADOS}",
                formato="inteiro",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                f"Idade {ANO_COPA}",
                f"Idade {ANO_COPA}",
                formato="inteiro",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Capacidade atual",
                "Capacidade atual",
                formato="decimal_2",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Potencial 2030",
                "Potencial 2030",
                formato="decimal_2",
                alinhamento="centro",
                destaque=True,
            ),
            ColunaTabelaExecutiva(
                "Saldo projetado",
                "Saldo projetado",
                formato="sinal_2",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Situação",
                "Situação",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Valor atual",
                "Valor atual",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "Pico de mercado",
                "Pico de mercado",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "% do pico de mercado",
                "% do pico",
                formato="percentual_1",
                alinhamento="direita",
                progresso=True,
            ),
        ),
        rotulo_aria="Tabela de jogadores monitorados",
        legenda="Jogadores, posições, avaliações e dados de mercado",
        chave=f"grade_roster_{periodo}",
        mostrar_barra=True,
        altura_maxima=600,
    )
