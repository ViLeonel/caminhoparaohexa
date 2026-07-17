"""Composição das quatro telas principais do aplicativo."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st

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
    render_resumo_elenco,
)
from hexa_data import (
    adicionar_jogador,
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_taticas import (
    LIMITE_RESERVAS,
    POSICOES_OFICIAIS,
    TATICAS,
    formatar_jogador_com_posicao,
    obter_atletas_compativeis,
)

MENU_CAMPO = "🏟️ Campo de Jogo"
MENU_PERFIS = "👤 Perfis & Scout"
MENU_ROSTER = "📋 Gestão do Roster"
MENU_ANALISE = "📊 Análise de Opiniões"
MENUS = (MENU_CAMPO, MENU_PERFIS, MENU_ROSTER, MENU_ANALISE)


def _chave_titular(tatica: str, indice: int) -> str:
    return f"titular::{tatica}::{indice}"


def _chave_reservas(tatica: str) -> str:
    return f"reservas::{tatica}"


def _limpar_convocacao(tatica: str, total_slots: int) -> None:
    for indice in range(total_slots):
        st.session_state.pop(_chave_titular(tatica, indice), None)
    st.session_state.pop(_chave_reservas(tatica), None)


def render_tela_campo(jogadores: Mapping[str, Mapping[str, Any]]) -> None:
    render_cabecalho(
        "🏆 O Caminho para o Hexa",
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
            _limpar_convocacao(tatica_ativa, len(layout_ativo))
            st.rerun()

        st.caption("Cada campo começa vazio e aceita somente atletas compatíveis com as posições oficiais do projeto.")
        escalados: dict[str, str] = {}
        selecionados: set[str] = set()

        for indice, (slot, configuracao) in enumerate(layout_ativo.items()):
            chave = _chave_titular(tatica_ativa, indice)
            validos = obter_atletas_compativeis(jogadores, configuracao.posicoes)
            disponiveis = [nome for nome in validos if nome not in selecionados]

            valor_atual = st.session_state.get(chave)
            if valor_atual not in disponiveis:
                st.session_state[chave] = None

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

        st.markdown("### Reservas")
        chave_reservas = _chave_reservas(tatica_ativa)
        opcoes_reservas = [
            nome for nome in sorted(jogadores.keys(), key=str.casefold)
            if nome not in selecionados
        ]
        reservas_anteriores = [
            nome for nome in st.session_state.get(chave_reservas, [])
            if nome in opcoes_reservas
        ][:LIMITE_RESERVAS]
        st.session_state[chave_reservas] = reservas_anteriores

        reservas = st.multiselect(
            f"Escolha até {LIMITE_RESERVAS} jogadores elegíveis para o banco:",
            opcoes_reservas,
            max_selections=LIMITE_RESERVAS,
            placeholder="Digite para buscar e selecionar reservas",
            format_func=lambda nome, base=jogadores: formatar_jogador_com_posicao(nome, base),
            key=chave_reservas,
        )
        st.caption(f"{len(escalados)}/11 titulares e {len(reservas)}/{LIMITE_RESERVAS} reservas selecionados.")

    with col_campo:
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
            notas_vini = [
                float(j.get("nota_vini") or 0)
                for j in titulares_dados
                if float(j.get("nota_vini") or 0) > 0
            ]
            notas_roberto = [
                float(j.get("nota_roberto") or 0)
                for j in titulares_dados
                if float(j.get("nota_roberto") or 0) > 0
            ]
            media_vini = sum(notas_vini) / len(notas_vini) if notas_vini else 0.0
            media_roberto = sum(notas_roberto) / len(notas_roberto) if notas_roberto else 0.0

            c1, c2, c3 = st.columns(3)
            c1.metric("Média Vini", f"{media_vini:.2f}" if notas_vini else "N/A")
            c2.metric("Média Roberto", f"{media_roberto:.2f}" if notas_roberto else "N/A")
            coletiva = (media_vini + media_roberto) / 2 if notas_vini and notas_roberto else 0.0
            c3.metric("Média coletiva", f"{coletiva:.2f}" if coletiva else "N/A")


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
        st.info("Digite parte do nome e selecione um atleta para abrir a ficha individual.")
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
        grupos = sorted({str(d.get("grupo", "Observação")) for d in jogadores.values()})
        grupo_filtro = filtro_3.selectbox("Grupo", ["Todos", *grupos])

        registros: list[dict[str, Any]] = []
        for nome, dados in jogadores.items():
            texto_busca = f"{nome} {dados.get('clube', '')}".casefold()
            if busca and busca.casefold() not in texto_busca:
                continue
            if posicao_filtro != "Todas" and posicao_filtro not in dados.get("posicoes_multiplas", []):
                continue
            if grupo_filtro != "Todos" and dados.get("grupo") != grupo_filtro:
                continue

            atual = valor_mercado_atual(dados)
            maximo = valor_mercado_maximo(dados)
            registros.append(
                {
                    "Nome": nome,
                    "Posição": dados.get("posicao", "N/A"),
                    "Grupo": dados.get("grupo", "N/A"),
                    "Clube": dados.get("clube", "N/A"),
                    "Idade 2026": dados.get("idade", 0),
                    "Idade 2030": int(dados.get("idade", 0)) + 4,
                    "Vini": float(dados.get("nota_vini") or 0.0),
                    "Roberto": float(dados.get("nota_roberto") or 0.0),
                    "Valor atual": formatar_valor_milhoes(atual),
                    "Pico": formatar_valor_milhoes(maximo),
                    "% do pico": round(percentual_do_pico(dados) or 0.0, 1),
                }
            )

        df_roster = pd.DataFrame(registros)
        st.caption(f"{len(df_roster)} atleta(s) exibido(s) de {len(jogadores)} cadastrados.")
        st.dataframe(df_roster, width="stretch", hide_index=True)

    with tab_novo:
        st.info("O cadastro inclui um atleta no JSON sem alterar ou excluir registros existentes.")
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
            idade = col_e.number_input("Idade em 2026", min_value=15, max_value=45, value=22)
            grupo = col_f.selectbox("Grupo", ["Titulares", "Reservas", "Observação"])

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
                st.success(f"{nome_curto} foi incluído na base.")
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))


def render_tela_analise(jogadores: Mapping[str, Mapping[str, Any]]) -> None:
    render_cabecalho(
        "Análise Coletiva de Scout",
        "Consensos, divergências e leitura do valor de mercado do elenco monitorado.",
    )

    avaliados: list[dict[str, Any]] = []
    mercado: list[dict[str, Any]] = []

    for nome, dados in jogadores.items():
        nota_vini = float(dados.get("nota_vini") or 0.0)
        nota_roberto = float(dados.get("nota_roberto") or 0.0)
        if nota_vini > 0 and nota_roberto > 0:
            avaliados.append(
                {
                    "Nome": nome,
                    "Posição": dados.get("posicao", "N/A"),
                    "Vini": nota_vini,
                    "Roberto": nota_roberto,
                    "Diferença": abs(nota_vini - nota_roberto),
                    "Média": (nota_vini + nota_roberto) / 2,
                }
            )

        atual = valor_mercado_atual(dados)
        maximo = valor_mercado_maximo(dados)
        if atual > 0:
            mercado.append(
                {
                    "Nome": nome,
                    "Posição": dados.get("posicao", "N/A"),
                    "Atual (M€)": atual,
                    "Pico (M€)": maximo,
                    "% do pico": percentual_do_pico(dados) or 0.0,
                    "Diferença para o pico (M€)": max(maximo - atual, 0.0),
                }
            )

    df_avaliados = pd.DataFrame(avaliados)
    df_mercado = pd.DataFrame(mercado)

    if df_avaliados.empty:
        st.info("Ainda não existem atletas com as duas avaliações preenchidas.")
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
            consenso = df_avaliados.sort_values(["Diferença", "Média"], ascending=[True, False]).head(8)
            st.dataframe(
                consenso[["Nome", "Posição", "Vini", "Roberto", "Média"]],
                width="stretch",
                hide_index=True,
            )

        with col_divergencia:
            st.markdown("### Maiores divergências")
            divergencias = df_avaliados.sort_values(["Diferença", "Média"], ascending=[False, False]).head(8)
            st.dataframe(
                divergencias[["Nome", "Posição", "Vini", "Roberto", "Diferença"]],
                width="stretch",
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("### Leitura de mercado")
    if df_mercado.empty:
        st.info("Ainda não existem valores de mercado cadastrados.")
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
        tipo_sugestao = st.selectbox("Tipo de sugestão:", ["Sugerir jogador", "Sugerir melhoria"])
        detalhes = st.text_area(
            "Mensagem:",
            placeholder="Descreva sua sugestão com o máximo de contexto possível.",
        )
        enviar = st.form_submit_button("Preparar e-mail")

    if not enviar:
        return
    if not detalhes.strip():
        st.sidebar.warning("Digite uma mensagem antes de continuar.")
        return

    assunto = urllib.parse.quote(f"Caminho para o Hexa: {tipo_sugestao}")
    corpo = urllib.parse.quote(f"Olá, Vini e Roberto!\n\n{detalhes.strip()}")
    mailto = f"mailto:viniciusbl87@gmail.com?subject={assunto}&body={corpo}"
    st.sidebar.markdown(
        f'<a href="{mailto}" style="display:block;text-align:center;background:#EAB308;color:#020617;'
        'font-weight:800;padding:10px;border-radius:8px;text-decoration:none;">Abrir e-mail</a>',
        unsafe_allow_html=True,
    )


def render_tela(menu: str, jogadores: dict[str, dict[str, Any]]) -> None:
    roteador = {
        MENU_CAMPO: render_tela_campo,
        MENU_PERFIS: render_tela_perfis,
        MENU_ROSTER: render_tela_roster,
        MENU_ANALISE: render_tela_analise,
    }
    tela = roteador.get(menu, render_tela_campo)
    tela(jogadores)
