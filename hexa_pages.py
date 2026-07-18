"""Composição das quatro telas principais do aplicativo."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st

from hexa_config import (
    ANO_BASE_DADOS,
    ASSUNTO_FEEDBACK_PREFIXO,
    EMAIL_FEEDBACK,
    GRUPO_OBSERVACAO,
    GRUPO_RESERVAS,
    GRUPOS_EDITORIAIS,
    IDADE_MAXIMA_CADASTRO,
    IDADE_MINIMA_CADASTRO,
    IDADE_PADRAO,
    MENU_ANALISE,
    MENU_CAMPO,
    MENU_PERFIS,
    MENU_ROSTER,
    SAUDACAO_FEEDBACK,
    TIPOS_SUGESTAO,
    TITULO_PROJETO,
)

from hexa_components import (
    render_avaliacao_leitura,
    render_banco_reservas,
    render_cabecalho,
    render_campo,
    render_cartao_perfil,
    render_comparativo_mercado,
    render_dados_transfermarkt,
    render_dossie,
    render_legenda_adaptabilidade,
    render_lista_tatica,
    render_resumo_elenco,
)
from hexa_data import adicionar_jogador, formatar_valor_milhoes
from hexa_messages import (
    ANALISE_SEM_AVALIACOES,
    AVISO_PERSISTENCIA,
    FEEDBACK_MENSAGEM_OBRIGATORIA,
    FEEDBACK_PREPARADO,
    MERCADO_SEM_DADOS,
    PERFIL_VAZIO,
    ROSTER_SEM_RESULTADOS,
    SUCESSO_CADASTRO,
    convocacao_completa,
    resumo_convocacao,
)
from hexa_selectors import (
    calcular_medias_titulares,
    construir_avaliacoes,
    construir_registros_mercado,
    construir_registros_roster,
    construir_visualizacao_tatica_lista,
    ordenar_consensos,
    ordenar_divergencias,
)
from hexa_session import (
    chave_reservas,
    chave_titular,
    limpar_convocacao,
    normalizar_escolha_titular,
    normalizar_reservas,
    opcoes_reservas,
    opcoes_titular,
)
from hexa_taticas import (
    LIMITE_RESERVAS,
    POSICOES_OFICIAIS,
    TATICAS,
    formatar_jogador_com_posicao,
)



def render_tela_campo(jogadores: Mapping[str, Mapping[str, Any]]) -> None:
    render_cabecalho(
        TITULO_PROJETO,
        "Monte os 11 titulares e até 15 reservas, sem atletas pré-selecionados.",
    )

    col_config, col_campo = st.columns([1, 2], gap="large")

    with col_config:
        st.markdown("### Montar convocação")
        tatica_ativa = st.selectbox(
            "Esquema tático:",
            list(TATICAS.keys()),
            key="tactical_selector",
        )
        layout_ativo = TATICAS[tatica_ativa]

        if st.button("Limpar titulares e reservas", width="stretch"):
            limpar_convocacao(st.session_state, tatica_ativa, len(layout_ativo))
            st.rerun()

        st.caption("Cada campo começa vazio e aceita somente atletas compatíveis com as posições oficiais do projeto.")
        escalados: dict[str, str] = {}
        selecionados: set[str] = set()

        for indice, (slot, configuracao) in enumerate(layout_ativo.items()):
            chave = chave_titular(tatica_ativa, indice)
            disponiveis = opcoes_titular(jogadores, configuracao.posicoes, selecionados)
            normalizar_escolha_titular(st.session_state, chave, disponiveis)

            escolha = st.selectbox(
                f"{slot}:",
                disponiveis,
                index=None,
                placeholder="Digite para buscar um atleta",
                format_func=lambda nome, base=jogadores: formatar_jogador_com_posicao(nome, base),
                key=chave,
            )
            if escolha:
                escalados[slot] = escolha
                selecionados.add(escolha)

        st.markdown(f"### {GRUPO_RESERVAS}")
        chave_reservas_ativa = chave_reservas(tatica_ativa)
        opcoes_banco = opcoes_reservas(jogadores, selecionados)
        normalizar_reservas(
            st.session_state,
            chave_reservas_ativa,
            opcoes_banco,
            LIMITE_RESERVAS,
        )

        reservas = st.multiselect(
            f"Escolha até {LIMITE_RESERVAS} jogadores elegíveis para o banco:",
            opcoes_banco,
            max_selections=LIMITE_RESERVAS,
            placeholder="Digite para buscar e selecionar reservas",
            format_func=lambda nome, base=jogadores: formatar_jogador_com_posicao(nome, base),
            key=chave_reservas_ativa,
        )
        resumo = resumo_convocacao(len(escalados), len(reservas))
        if convocacao_completa(len(escalados)):
            st.success(resumo)
        else:
            st.info(resumo)

    with col_campo:
        modo_visualizacao = st.radio(
            "Visualização tática:",
            ("Campo", "Lista"),
            horizontal=True,
            key="tactical_view_mode",
            help="A visualização em lista é mais compacta e acessível em telas pequenas.",
        )

        if modo_visualizacao == "Lista":
            linhas_taticas = construir_visualizacao_tatica_lista(
                layout_ativo,
                escalados,
                jogadores,
            )
            render_lista_tatica(linhas_taticas)
        else:
            render_campo(layout_ativo, escalados, jogadores)

        render_legenda_adaptabilidade()
        render_banco_reservas(reservas, jogadores)

        titulares_dados = [
            jogadores[nome]
            for slot, nome in escalados.items()
            if slot in layout_ativo and nome in jogadores
        ]
        reservas_dados = [jogadores[nome] for nome in reservas if nome in jogadores]
        render_resumo_elenco(titulares_dados, reservas_dados)

        if titulares_dados:
            medias = calcular_medias_titulares(titulares_dados)
            c1, c2, c3 = st.columns(3)
            c1.metric("Média Vini", f"{medias['vini']:.2f}" if medias["vini"] is not None else "Sem base")
            c2.metric(
                "Média Roberto",
                f"{medias['roberto']:.2f}" if medias["roberto"] is not None else "Sem base",
            )
            c3.metric(
                "Média coletiva",
                f"{medias['coletiva']:.2f}" if medias["coletiva"] is not None else "Sem base",
            )


def render_tela_perfis(jogadores: Mapping[str, Mapping[str, Any]]) -> None:
    render_cabecalho(
        "Ficha Individual do Atleta",
        "Pesquise um atleta para consultar avaliação editorial, contrato e valor de mercado.",
    )

    nomes = sorted(jogadores.keys(), key=str.casefold)
    selected_name = st.selectbox(
        "Buscar atleta por nome:",
        nomes,
        index=None,
        placeholder="Digite ou selecione o nome do atleta",
        format_func=lambda nome, base=jogadores: formatar_jogador_com_posicao(nome, base),
        key="busca_perfil_atleta",
    )

    if selected_name is None:
        st.info(PERFIL_VAZIO)
        return

    atleta = jogadores[selected_name]
    st.markdown("---")
    col_perfil, col_dados = st.columns([1, 2], gap="large")

    with col_perfil:
        render_cartao_perfil(selected_name, atleta)
        st.markdown("### Avaliação dos analistas")
        render_avaliacao_leitura(atleta)

    with col_dados:
        st.markdown("### Valor de mercado")
        render_comparativo_mercado(atleta)

        with st.expander("Dados externos e contratuais", expanded=True):
            render_dados_transfermarkt(atleta)

        st.markdown("### Dossiê do projeto")
        render_dossie(atleta)


def render_tela_roster(jogadores: dict[str, dict[str, Any]]) -> None:
    render_cabecalho(
        "Gestão do Roster",
        "Consulte, filtre e inclua atletas. Nenhum jogador é removido da base.",
    )

    tab_base, tab_novo = st.tabs(["Base de jogadores", "Adicionar atleta"])

    with tab_base:
        filtro_1, filtro_2, filtro_3 = st.columns([2, 1, 1])
        busca = filtro_1.text_input("Buscar por nome ou clube", placeholder="Ex.: Palmeiras")
        posicao_filtro = filtro_2.selectbox("Posição", ["Todas", *POSICOES_OFICIAIS])
        grupos = sorted({str(d.get("grupo", GRUPO_OBSERVACAO)) for d in jogadores.values()})
        grupo_filtro = filtro_3.selectbox("Grupo", ["Todos", *grupos])

        registros = construir_registros_roster(
            jogadores,
            busca=busca,
            posicao=None if posicao_filtro == "Todas" else posicao_filtro,
            grupo=None if grupo_filtro == "Todos" else grupo_filtro,
        )

        df_roster = pd.DataFrame(registros)
        st.caption(f"{len(df_roster)} atleta(s) exibido(s) de {len(jogadores)} cadastrados.")
        if df_roster.empty:
            st.info(ROSTER_SEM_RESULTADOS)
        else:
            st.dataframe(df_roster, width="stretch", hide_index=True)

    with tab_novo:
        st.warning(AVISO_PERSISTENCIA)
        with st.form("novo_jogador", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            nome_curto = col_a.text_input("Nome curto*")
            nome_completo = col_b.text_input("Nome completo")

            col_c, col_d = st.columns(2)
            posicao = col_c.selectbox("Posição principal*", POSICOES_OFICIAIS)
            clube = col_d.text_input("Clube atual")

            posicoes_secundarias = st.multiselect(
                "Posições secundárias",
                [p for p in POSICOES_OFICIAIS if p != posicao],
            )

            col_e, col_f = st.columns(2)
            idade = col_e.number_input(f"Idade em {ANO_BASE_DADOS}", min_value=IDADE_MINIMA_CADASTRO, max_value=IDADE_MAXIMA_CADASTRO, value=IDADE_PADRAO)
            grupo = col_f.selectbox("Grupo", GRUPOS_EDITORIAIS)

            pontos_fortes = st.text_area("Pontos fortes")
            pontos_fracos = st.text_area("Pontos fracos")
            historico = st.text_area("Histórico das discussões")

            cadastrar = st.form_submit_button("Cadastrar atleta", width="stretch")

        if cadastrar:
            try:
                adicionar_jogador(
                    jogadores,
                    {
                        "nome": nome_curto,
                        "nome_completo": nome_completo,
                        "posicao": posicao,
                        "posicoes_multiplas": [posicao, *posicoes_secundarias],
                        "clube": clube or "N/A",
                        "idade": int(idade),
                        "grupo": grupo,
                        "nota_vini": 0.0,
                        "nota_roberto": 0.0,
                        "pontos_fortes": pontos_fortes,
                        "pontos_fracos": pontos_fracos,
                        "historico": historico,
                    },
                )
                st.success(SUCESSO_CADASTRO.format(nome=nome_curto))
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))


def render_tela_analise(jogadores: Mapping[str, Mapping[str, Any]]) -> None:
    render_cabecalho(
        "Análise Coletiva de Scout",
        "Consensos, divergências e leitura do valor de mercado do elenco monitorado.",
    )

    avaliados = construir_avaliacoes(jogadores)
    mercado = construir_registros_mercado(jogadores)

    df_avaliados = pd.DataFrame(avaliados)
    df_mercado = pd.DataFrame(mercado)

    if df_avaliados.empty:
        st.info(ANALISE_SEM_AVALIACOES)
    else:
        media_geral = df_avaliados["Média"].mean()
        divergencia_media = df_avaliados["Diferença"].mean()
        c1, c2, c3 = st.columns(3)
        c1.metric("Atletas avaliados", len(df_avaliados))
        c2.metric("Média geral", f"{media_geral:.2f}")
        c3.metric("Divergência média", f"{divergencia_media:.2f}")

        col_consenso, col_divergencia = st.columns(2, gap="large")
        with col_consenso:
            st.markdown("### Maiores consensos")
            consenso = pd.DataFrame(ordenar_consensos(avaliados))
            st.dataframe(
                consenso[["Nome", "Posição", "Vini", "Roberto", "Média"]],
                width="stretch",
                hide_index=True,
            )

        with col_divergencia:
            st.markdown("### Maiores divergências")
            divergencias = pd.DataFrame(ordenar_divergencias(avaliados))
            st.dataframe(
                divergencias[["Nome", "Posição", "Vini", "Roberto", "Diferença"]],
                width="stretch",
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("### Leitura de mercado")
    if df_mercado.empty:
        st.info(MERCADO_SEM_DADOS)
        return

    total_atual = df_mercado["Atual (M€)"].sum()
    total_pico = df_mercado["Pico (M€)"].sum()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Atletas com valor", len(df_mercado))
    col_m2.metric("Valor atual somado", formatar_valor_milhoes(total_atual))
    col_m3.metric("Pico somado", formatar_valor_milhoes(total_pico))

    mercado_ordenado = df_mercado.sort_values("Atual (M€)", ascending=False)
    st.dataframe(
        mercado_ordenado,
        width="stretch",
        hide_index=True,
        column_config={
            "Atual (M€)": st.column_config.NumberColumn(format="€ %.2f mi"),
            "Pico (M€)": st.column_config.NumberColumn(format="€ %.2f mi"),
            "% do pico": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            "Diferença para o pico (M€)": st.column_config.NumberColumn(format="€ %.2f mi"),
        },
    )


def render_feedback_sidebar() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Radar do projeto")
    with st.sidebar.form("form_sugestao", clear_on_submit=True):
        tipo_sugestao = st.selectbox("Tipo de sugestão:", TIPOS_SUGESTAO)
        detalhes = st.text_area(
            "Mensagem:",
            placeholder="Descreva sua sugestão com o máximo de contexto possível.",
        )
        enviar = st.form_submit_button("Preparar e-mail")

    if not enviar:
        return
    if not detalhes.strip():
        st.sidebar.warning(FEEDBACK_MENSAGEM_OBRIGATORIA)
        return

    assunto = urllib.parse.quote(f"{ASSUNTO_FEEDBACK_PREFIXO}: {tipo_sugestao}")
    corpo = urllib.parse.quote(f"{SAUDACAO_FEEDBACK}\n\n{detalhes.strip()}")
    mailto = f"mailto:{EMAIL_FEEDBACK}?subject={assunto}&body={corpo}"
    st.sidebar.markdown(
        f'<a href="{mailto}" class="feedback-link">Abrir e-mail</a>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(FEEDBACK_PREPARADO)


def render_tela(menu: str, jogadores: dict[str, dict[str, Any]]) -> None:
    roteador = {
        MENU_CAMPO: render_tela_campo,
        MENU_PERFIS: render_tela_perfis,
        MENU_ROSTER: render_tela_roster,
        MENU_ANALISE: render_tela_analise,
    }
    tela = roteador.get(menu, render_tela_campo)
    tela(jogadores)
