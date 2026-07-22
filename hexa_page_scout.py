"""Tela de scout e ficha individual."""

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
    CALENDARIOS_DIR,
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
    TEMPORADAS_DIR,
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
from hexa_scout_temporada import render_dados_sazonais_atleta
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

__all__ = ['render_tela_perfis']


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


def _valor_analista(
    registro: Mapping[str, Any],
    analista: str,
    campo: str,
) -> float | None:
    bloco = registro.get(analista)
    if not isinstance(bloco, Mapping):
        return None
    valor = bloco.get(campo)
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _render_resumo_avaliacao(
    metricas: Mapping[str, Any],
    registro: Mapping[str, Any],
) -> None:
    """Exibe situação, saldo e data sem truncamento em colunas estreitas."""
    situacao = formatar_status_avaliacao(metricas["status"])
    saldo = formatar_numero(metricas["saldo_projetado"], sinal=True)
    data_referencia = formatar_data_referencia(
        str(registro["data_referencia"])
    )
    st.markdown(
        '<section class="evaluation-meta-grid" '
        'aria-label="Resumo da avaliação trimestral">'
        '<article class="evaluation-meta-card evaluation-meta-card--status">'
        '<div class="evaluation-meta-label">Situação</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--status">'
        f'{_esc(situacao)}</div>'
        '</article>'
        '<article class="evaluation-meta-card" '
        'title="Média de potencial menos capacidade atual, calculada apenas '
        'para cada analista que preencheu o par completo.">'
        '<div class="evaluation-meta-label">Saldo projetado</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--numeric '
        f'evaluation-meta-emphasis">{_esc(saldo)}</div>'
        '</article>'
        '<article class="evaluation-meta-card">'
        '<div class="evaluation-meta-label">Data de referência</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--date">'
        f'{_esc(data_referencia)}</div>'
        '</article>'
        '</section>'
        '<div class="sr-only">'
        f'Situação da avaliação: {_esc(situacao)}. '
        f'Saldo projetado: {_esc(saldo)}. '
        f'Data de referência: {_esc(data_referencia)}.'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_avaliacao_trimestral(
    registro: Mapping[str, Any] | None,
    *,
    periodo: str,
) -> None:
    render_cabecalho_secao(
        formatar_periodo(periodo),
        rotulo="Avaliação trimestral",
    )
    if registro is None:
        st.info(
            "Não há avaliação registrada para este atleta no período "
            "selecionado."
        )
        return

    metricas = calcular_metricas_avaliacao(registro)
    if metricas["status"] == "Parcial":
        st.warning(
            "Avaliação parcial: pelo menos uma das quatro notas ainda não "
            "foi registrada neste período."
        )
    elif metricas["status"] == "Não avaliada":
        st.info(
            "O atleta está na base, mas ainda não recebeu notas neste período."
        )

    render_quadro_avaliacao_executivo(
        registro,
        rotulo_vini=NOME_CURTO_ANALISTA_VINI,
        rotulo_beto=NOME_CURTO_ANALISTA_BETO,
    )

    _render_resumo_avaliacao(metricas, registro)

    st.caption(
        "Posição no período: "
        f'{registro.get("posicao_snapshot", "Não informada")} · '
        "Clube no período: "
        f'{registro.get("clube_snapshot", "Não informado")}.'
    )

    observacao_vini = str(
        (registro.get("vini") or {}).get("observacao") or ""
    ).strip()
    observacao_beto = str(
        (registro.get("beto") or {}).get("observacao") or ""
    ).strip()
    st.markdown("### Observações do trimestre")
    col_vini, col_beto = st.columns(2, gap="large")
    with col_vini:
        st.markdown(f"**{NOME_ANALISTA_VINI}**")
        if observacao_vini:
            st.write(observacao_vini)
        else:
            st.caption("Nenhuma observação registrada por Vini.")
    with col_beto:
        st.markdown(f"**{NOME_ANALISTA_BETO}**")
        if observacao_beto:
            st.write(observacao_beto)
        else:
            st.caption("Nenhuma observação registrada por Beto.")


def _render_historico_atleta(
    base: BaseAvaliacoes,
    id_atleta: str,
) -> None:
    serie = historico_atleta(base, id_atleta)
    if len(serie) <= 1:
        st.caption(
            "O gráfico histórico será exibido quando existir mais de um "
            "trimestre avaliado para o atleta."
        )
        return

    df = pd.DataFrame(
        [
            {
                "Período": formatar_periodo(str(item["periodo"])),
                "Capacidade atual": item["capacidade_atual_media"],
                "Potencial 2030": item["potencial_2030_medio"],
            }
            for item in serie
        ]
    ).set_index("Período")
    render_cabecalho_secao("Histórico de avaliações")
    st.line_chart(df)


def render_tela_perfis(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    render_cabecalho(
        "Scout",
        (
            "Pesquise um atleta para consultar avaliação trimestral, "
            "contrato e valor de mercado."
        ),
    )
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    nomes = sorted(jogadores.keys(), key=str.casefold)
    selected_name = st.selectbox(
        "Buscar atleta por nome:",
        nomes,
        index=None,
        placeholder="Digite ou selecione o nome do atleta",
        format_func=lambda nome, base=jogadores: (
            formatar_jogador_com_posicao(nome, base)
        ),
        key="busca_perfil_atleta",
    )

    if selected_name is None:
        st.info(
            "Busque por nome e selecione um atleta para abrir a ficha individual."
        )
        return

    atleta = jogadores[selected_name]
    registro = avaliacoes_periodo.get(selected_name)
    st.markdown("---")
    col_perfil, col_dados = st.columns([1, 2], gap="large")

    with col_perfil:
        render_cartao_perfil(selected_name, atleta, registro)
        _render_avaliacao_trimestral(registro, periodo=periodo)

    with col_dados:
        with st.expander("Dados do jogador", expanded=True, type="compact"):
            render_dados_transfermarkt(atleta)

        render_cabecalho_secao("Valor de mercado")
        render_comparativo_mercado(atleta)

        _render_historico_atleta(
            base_avaliacoes,
            str(atleta.get("id_atleta") or ""),
        )

        render_dados_sazonais_atleta(
            jogador=atleta,
            temporadas_dir=TEMPORADAS_DIR,
            calendarios_dir=CALENDARIOS_DIR,
        )
