"""Componente lateral de feedback do projeto."""

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

__all__ = ['render_feedback_sidebar']


def render_feedback_sidebar() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Radar do projeto")
    with st.sidebar.form("form_sugestao", clear_on_submit=True):
        tipo_sugestao = st.selectbox(
            "Tipo de sugestão:",
            TIPOS_SUGESTAO,
        )
        detalhes = st.text_area(
            "Mensagem:",
            placeholder=(
                "Descreva sua sugestão com o máximo de contexto possível."
            ),
        )
        enviar = st.form_submit_button("Preparar e-mail")

    if not enviar:
        return
    if not detalhes.strip():
        st.sidebar.warning(FEEDBACK_MENSAGEM_OBRIGATORIA)
        return

    assunto = urllib.parse.quote(
        f"{ASSUNTO_FEEDBACK_PREFIXO}: {tipo_sugestao}"
    )
    corpo = urllib.parse.quote(
        f"{SAUDACAO_FEEDBACK}\n\n{detalhes.strip()}"
    )
    mailto = (
        f"mailto:{EMAIL_FEEDBACK}?subject={assunto}&body={corpo}"
    )
    st.sidebar.markdown(
        f'<a href="{mailto}" class="feedback-link">Abrir e-mail</a>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(FEEDBACK_PREPARADO)
