"""Composição das quatro telas principais do aplicativo."""

from __future__ import annotations

import html
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import streamlit as st

from hexa_config import (
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
from hexa_components import (
    render_banco_reservas,
    render_campo,
    render_cartao_perfil,
    render_comparativo_mercado,
    render_dados_transfermarkt,
    render_legenda_adaptabilidade,
    render_resumo_elenco,
)
from hexa_data import formatar_valor_milhoes
from hexa_messages import (
    ANALISE_SEM_AVALIACOES,
    FEEDBACK_MENSAGEM_OBRIGATORIA,
    FEEDBACK_PREPARADO,
    MERCADO_SEM_DADOS,
    ROSTER_SEM_RESULTADOS,
    convocacao_completa,
    resumo_convocacao,
)
from hexa_selectors import (
    calcular_medias_titulares,
    construir_avaliacoes,
    construir_registros_mercado,
    construir_registros_roster,
    construir_visualizacao_tatica_lista,
    formatar_texto_editorial,
    ordenar_consensos,
    ordenar_divergencias,
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
)
from hexa_taticas import (
    LIMITE_RESERVAS,
    POSICOES_OFICIAIS,
    TATICAS,
    SlotTatico,
    formatar_jogador_com_posicao,
)

__all__ = [
    "render_feedback_sidebar",
    "render_tela",
    "render_tela_analise",
    "render_tela_campo",
    "render_tela_perfis",
    "render_tela_roster",
]


def _esc(valor: Any, padrao: str = "") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


def _nota_texto(valor: Any) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "Sem nota"
    if numero <= 0:
        return "Sem nota"
    return f"{numero:.1f}".replace(".", ",")


def _texto_com_quebras(valor: Any, *, editorial: bool = False) -> str:
    texto = formatar_texto_editorial(valor) if editorial else str(valor or "").strip()
    if not texto:
        texto = "Conteúdo editorial ainda não registrado."
    return _esc(texto).replace("\n", "<br>")


def _render_cabecalho_pagina(
    titulo: str,
    subtitulo: str | None = None,
) -> None:
    st.markdown(
        f'<h1 class="app-title">{_esc(titulo)}</h1>',
        unsafe_allow_html=True,
    )
    if subtitulo:
        st.markdown(
            f'<p class="project-subtitle">{_esc(subtitulo)}</p>',
            unsafe_allow_html=True,
        )


def _render_cabecalho_projeto() -> None:
    descricao = (
        f"Plataforma editorial e tática de {NOME_ANALISTA_VINI} e "
        f"{NOME_ANALISTA_BETO} para acompanhar jogadores brasileiros no ciclo "
        "da Copa de 2030. Escolha uma formação, monte 11 titulares e até 15 "
        "reservas e consulte scout, avaliações, lista monitorada e dados de mercado."
    )
    cabecalho = (
        '<section class="project-hero" aria-labelledby="titulo-projeto">'
        '<div class="project-trophy" aria-hidden="true">'
        '<svg class="world-cup-trophy" viewBox="0 0 96 128" '
        'focusable="false" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M48 5C29 5 18 17 19 33c1 13 10 24 21 31 '
        '4 3 5 8 2 13L31 96h34L54 77c-3-5-2-10 2-13 '
        '11-7 20-18 21-31C78 17 67 5 48 5Z"/>'
        '<path d="M22 30c-9 5-13 14-10 23 3 10 12 16 23 18 '
        'l4-8c-8-2-14-6-16-12-2-5 0-10 5-13l-6-8Zm52 0 '
        'c9 5 13 14 10 23-3 10-12 16-23 18l-4-8c8-2 '
        '14-6 16-12 2-5 0-10-5-13l6-8Z"/>'
        '<path d="M29 99h38l6 13H23l6-13Zm-10 17h58v8H19v-8Z"/>'
        '<path class="trophy-detail" d="M35 18c7-5 18-6 27-1 '
        'M28 34c8 8 21 12 38 7 M38 57c7 2 14 2 21-1"/>'
        '</svg>'
        '</div>'
        '<div class="project-hero-copy">'
        f'<h1 id="titulo-projeto" class="project-hero-title">{_esc(TITULO_PROJETO)}</h1>'
        f'<p class="project-hero-subtitle">{_esc(descricao)}</p>'
        '</div>'
        '</section>'
    )
    st.markdown(cabecalho, unsafe_allow_html=True)


def _classe_adaptabilidade(indice: int, preenchido: bool) -> tuple[str, str]:
    if not preenchido:
        return "adapt-empty", "Vaga aberta"
    if indice == 0:
        return "adapt-primary", "Função primária"
    if indice == 1:
        return "adapt-secondary", "Função secundária"
    if indice >= 2:
        return "adapt-tertiary", "Função alternativa"
    return "adapt-incompatible", "Compatibilidade não confirmada"


def _render_lista_tatica(
    linhas: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    secoes: list[str] = []
    for linha, itens in linhas.items():
        cards: list[str] = []
        for item in itens:
            preenchido = bool(item.get("preenchido"))
            indice = int(item.get("indice_adaptabilidade", -1))
            classe, status = _classe_adaptabilidade(indice, preenchido)
            nome = str(item.get("nome") or "Selecionar atleta")
            if preenchido:
                notas = (
                    f"{NOME_CURTO_ANALISTA_VINI} "
                    f"{_nota_texto(item.get('nota_vini'))} · "
                    f"{NOME_CURTO_ANALISTA_BETO} "
                    f"{_nota_texto(item.get('nota_roberto'))}"
                )
            else:
                notas = "Sem atleta selecionado"

            cards.append(
                f'<li class="tactical-list-item {classe}">'
                '<div class="tactical-list-main">'
                f'<span class="tactical-list-tag">{_esc(item.get("tag"))}</span>'
                '<span class="tactical-list-copy">'
                f'<strong class="tactical-list-name">{_esc(nome)}</strong>'
                f'<span class="tactical-list-slot">{_esc(item.get("slot"))}</span>'
                '</span>'
                '</div>'
                '<span class="tactical-list-meta">'
                f'<span class="tactical-list-status">{_esc(status)}</span>'
                f'<span class="tactical-list-ratings">{_esc(notas)}</span>'
                '</span>'
                '</li>'
            )

        secoes.append(
            '<section class="tactical-list-section">'
            f'<h2 class="tactical-list-heading">{_esc(linha)}</h2>'
            f'<ul class="tactical-list-grid">{"".join(cards)}</ul>'
            '</section>'
        )

    st.markdown(
        '<div class="tactical-list" role="region" '
        'aria-label="Escalação em lista">'
        f'{"".join(secoes)}</div>',
        unsafe_allow_html=True,
    )


def _render_avaliacao_analistas(atleta: Mapping[str, Any]) -> None:
    nota_vini = _nota_texto(atleta.get("nota_vini"))
    nota_beto = _nota_texto(atleta.get("nota_roberto"))

    valores_validos: list[float] = []
    for campo in ("nota_vini", "nota_roberto"):
        try:
            numero = float(atleta.get(campo) or 0)
        except (TypeError, ValueError):
            continue
        if numero > 0:
            valores_validos.append(numero)

    media = (
        f"{sum(valores_validos) / len(valores_validos):.1f}".replace(".", ",")
        if valores_validos
        else "Sem base"
    )
    st.markdown(
        '<div class="rating-box" role="group" '
        'aria-label="Avaliações editoriais dos analistas">'
        '<div class="rating-grid">'
        '<div class="rating-card">'
        f'<div class="rating-label">{_esc(NOME_CURTO_ANALISTA_VINI)}</div>'
        f'<div class="rating-value">{_esc(nota_vini)}</div>'
        '</div>'
        '<div class="rating-card">'
        f'<div class="rating-label">{_esc(NOME_CURTO_ANALISTA_BETO)}</div>'
        f'<div class="rating-value">{_esc(nota_beto)}</div>'
        '</div>'
        '<div class="rating-card">'
        '<div class="rating-label">Média</div>'
        f'<div class="rating-value rating-gold">{_esc(media)}</div>'
        '</div>'
        '</div>'
        '<p class="rating-note">Notas editoriais em escala de 0 a 10, '
        'exibidas somente para leitura.</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_dossie_projeto(atleta: Mapping[str, Any]) -> None:
    historico = _texto_com_quebras(atleta.get("historico"), editorial=True)
    st.markdown(
        '<section class="stat-box stat-positive">'
        '<strong>Pontos fortes</strong><br>'
        f'{_texto_com_quebras(atleta.get("pontos_fortes"))}'
        '</section>'
        '<section class="stat-box stat-negative">'
        '<strong>Pontos de atenção</strong><br>'
        f'{_texto_com_quebras(atleta.get("pontos_fracos"))}'
        '</section>'
        '<section class="stat-box stat-info">'
        f'<strong>Histórico das discussões — '
        f'{_esc(NOME_CURTO_ANALISTA_VINI)} & '
        f'{_esc(NOME_CURTO_ANALISTA_BETO)}</strong><br>'
        f'{historico}'
        '</section>',
        unsafe_allow_html=True,
    )


def _render_linha_seletores_posicionais(
    itens: Sequence[tuple[int, str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    indisponiveis_base: set[str],
    selecionados_reservas: set[str],
) -> None:
    colunas = st.columns(len(itens))
    for coluna, (indice, slot, configuracao) in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_posicional(tatica_ativa, indice)
            indisponiveis = indisponiveis_base | selecionados_reservas
            disponiveis = opcoes_reserva_posicional(
                jogadores,
                configuracao.posicoes,
                indisponiveis,
            )
            normalizar_escolha_reserva(
                st.session_state,
                chave,
                disponiveis,
            )
            escolha = st.selectbox(
                f"Reserva — {slot}:",
                disponiveis,
                index=None,
                placeholder="Buscar atleta compatível",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
                help=(
                    "Aceita as mesmas posições editoriais permitidas para "
                    "o respectivo slot titular."
                ),
            )
            if escolha:
                selecionados_reservas.add(escolha)


def _render_linha_seletores_livres(
    itens: Sequence[int],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    prioridade_posicoes: Sequence[str],
    indisponiveis_base: set[str],
    selecionados_reservas: set[str],
) -> None:
    colunas = st.columns(len(itens))
    for coluna, indice in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_livre(tatica_ativa, indice)
            indisponiveis = indisponiveis_base | selecionados_reservas
            disponiveis = opcoes_reserva_livre(
                jogadores,
                prioridade_posicoes,
                indisponiveis,
            )
            normalizar_escolha_reserva(
                st.session_state,
                chave,
                disponiveis,
            )
            escolha = st.selectbox(
                f"Vaga livre {indice + 1}:",
                disponiveis,
                index=None,
                placeholder="Buscar em qualquer posição",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
                help=(
                    "Aceita qualquer posição oficial. As opções seguem a "
                    "ordem posicional da formação ativa."
                ),
            )
            if escolha:
                selecionados_reservas.add(escolha)


def _render_selecao_reservas(
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    layout_ativo: Mapping[str, SlotTatico],
    titulares: set[str],
) -> list[str]:
    migrar_reservas_legadas(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
        titulares,
    )

    st.markdown("---")
    st.markdown("## Banco de reservas")
    st.caption(
        "As primeiras 11 vagas espelham a formação escolhida. "
        "As quatro vagas finais aceitam qualquer posição oficial."
    )

    selecionados_reservas: set[str] = set()
    itens_layout = [
        (indice, slot, configuracao)
        for indice, (slot, configuracao) in enumerate(layout_ativo.items())
    ]

    st.markdown("### Reservas por posição — 11 vagas")
    for inicio in range(0, len(itens_layout), 3):
        _render_linha_seletores_posicionais(
            itens_layout[inicio:inicio + 3],
            jogadores,
            tatica_ativa,
            titulares,
            selecionados_reservas,
        )

    prioridade = prioridade_posicoes_tatica(layout_ativo)
    tags: list[str] = []
    for configuracao in layout_ativo.values():
        if configuracao.tag not in tags:
            tags.append(configuracao.tag)

    st.markdown("### Vagas livres — 4 vagas")
    st.caption(
        "Ordem das opções: "
        + " → ".join(tags)
        + ". O desempate é feito pelo nome do atleta."
    )
    total_livres = quantidade_vagas_livres(len(layout_ativo))
    indices_livres = list(range(total_livres))
    for inicio in range(0, total_livres, 2):
        _render_linha_seletores_livres(
            indices_livres[inicio:inicio + 2],
            jogadores,
            tatica_ativa,
            prioridade,
            titulares,
            selecionados_reservas,
        )

    return [
        nome
        for nome in (
            st.session_state.get(
                chave_reserva_posicional(tatica_ativa, indice)
            )
            for indice in range(len(layout_ativo))
        )
        if isinstance(nome, str) and nome
    ] + [
        nome
        for nome in (
            st.session_state.get(chave_reserva_livre(tatica_ativa, indice))
            for indice in range(total_livres)
        )
        if isinstance(nome, str) and nome
    ]


def render_tela_campo(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    _render_cabecalho_projeto()

    col_config, col_campo = st.columns([1, 2], gap="large")

    with col_config:
        st.markdown("## Montar convocação")
        tatica_ativa = st.selectbox(
            "Esquema tático:",
            list(TATICAS.keys()),
            key="tactical_selector",
        )
        layout_ativo = TATICAS[tatica_ativa]

        if st.button("Limpar titulares e reservas", width="stretch"):
            limpar_convocacao(
                st.session_state,
                tatica_ativa,
                len(layout_ativo),
            )
            st.rerun()

        st.caption(
            "Cada campo começa vazio e aceita somente atletas compatíveis "
            "com as posições oficiais do projeto."
        )
        escalados: dict[str, str] = {}
        selecionados: set[str] = set()

        for indice, (slot, configuracao) in enumerate(layout_ativo.items()):
            chave = chave_titular(tatica_ativa, indice)
            disponiveis = opcoes_titular(
                jogadores,
                configuracao.posicoes,
                selecionados,
            )
            normalizar_escolha_titular(
                st.session_state,
                chave,
                disponiveis,
            )

            escolha = st.selectbox(
                f"{slot}:",
                disponiveis,
                index=None,
                placeholder="Digite para buscar um atleta",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
            )
            if escolha:
                escalados[slot] = escolha
                selecionados.add(escolha)

    with col_campo:
        modo_visualizacao = st.radio(
            "Visualização tática:",
            ("Campo", "Lista"),
            horizontal=True,
            key="tactical_view_mode",
            help=(
                "A visualização em lista é mais compacta e acessível "
                "em telas pequenas."
            ),
        )

        if modo_visualizacao == "Lista":
            linhas_taticas = construir_visualizacao_tatica_lista(
                layout_ativo,
                escalados,
                jogadores,
            )
            _render_lista_tatica(linhas_taticas)
        else:
            render_campo(layout_ativo, escalados, jogadores)

        render_legenda_adaptabilidade()

    reservas = _render_selecao_reservas(
        jogadores,
        tatica_ativa,
        layout_ativo,
        selecionados,
    )
    # A reconciliação dos widgets elimina duplicidades; a filtragem final
    # protege também estados antigos ou manipulados externamente.
    reservas_unicas: list[str] = []
    for nome in reservas:
        if (
            nome not in selecionados
            and nome not in reservas_unicas
            and nome in jogadores
        ):
            reservas_unicas.append(nome)
    reservas = reservas_unicas[:LIMITE_RESERVAS]

    resumo = resumo_convocacao(len(escalados), len(reservas))
    st.markdown(
        f'<div class="sr-only" role="status" aria-live="polite" '
        f'aria-atomic="true">{_esc(resumo)}</div>',
        unsafe_allow_html=True,
    )
    if convocacao_completa(len(escalados)):
        st.success(resumo)
    else:
        st.info(resumo)

    render_banco_reservas(reservas, jogadores)

    titulares_dados = [
        jogadores[nome]
        for slot, nome in escalados.items()
        if slot in layout_ativo and nome in jogadores
    ]
    reservas_dados = [
        jogadores[nome] for nome in reservas if nome in jogadores
    ]
    render_resumo_elenco(titulares_dados, reservas_dados)

    if titulares_dados:
        medias = calcular_medias_titulares(titulares_dados)
        c1, c2, c3 = st.columns(3)
        c1.metric(
            f"Média {NOME_CURTO_ANALISTA_VINI}",
            f"{medias['vini']:.2f}"
            if medias["vini"] is not None
            else "Sem base",
        )
        c2.metric(
            f"Média {NOME_CURTO_ANALISTA_BETO}",
            f"{medias['roberto']:.2f}"
            if medias["roberto"] is not None
            else "Sem base",
        )
        c3.metric(
            "Média coletiva",
            f"{medias['coletiva']:.2f}"
            if medias["coletiva"] is not None
            else "Sem base",
        )


def render_tela_perfis(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    _render_cabecalho_pagina(
        "Jogadores, Scout e Avaliações",
        (
            "Pesquise um atleta para consultar avaliação editorial, "
            "contrato e valor de mercado."
        ),
    )

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
    st.markdown("---")
    col_perfil, col_dados = st.columns([1, 2], gap="large")

    with col_perfil:
        render_cartao_perfil(selected_name, atleta)
        st.markdown("## Avaliação dos analistas")
        _render_avaliacao_analistas(atleta)

    with col_dados:
        st.markdown("## Valor de mercado")
        render_comparativo_mercado(atleta)

        with st.expander("Dados externos e contratuais", expanded=True):
            render_dados_transfermarkt(atleta)

        st.markdown("## Dossiê do projeto")
        _render_dossie_projeto(atleta)


def render_tela_roster(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    _render_cabecalho_pagina("Lista de Jogadores")

    filtro_1, filtro_2, filtro_3 = st.columns([2, 1, 1])
    busca = filtro_1.text_input(
        "Buscar por nome ou clube",
        placeholder="Ex.: Palmeiras",
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
    grupo_filtro = filtro_3.selectbox("Grupo", ["Todos", *grupos])

    registros = construir_registros_roster(
        jogadores,
        busca=busca,
        posicao=None if posicao_filtro == "Todas" else posicao_filtro,
        grupo=None if grupo_filtro == "Todos" else grupo_filtro,
    )

    df_roster = pd.DataFrame(registros)
    st.caption(
        f"{len(df_roster)} atleta(s) exibido(s) de "
        f"{len(jogadores)} cadastrados."
    )
    if df_roster.empty:
        st.info(ROSTER_SEM_RESULTADOS)
    else:
        st.caption(
            "Tabela com nome, posição, grupo, idade, clube, notas e "
            "dados de mercado dos atletas filtrados."
        )
        st.dataframe(df_roster, width="stretch", hide_index=True)


def render_tela_analise(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    _render_cabecalho_pagina("Análises & Mercado")
    st.markdown("## Compilado de avaliações para o Ciclo 2030")

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
            st.markdown("## Maiores consensos")
            consenso = pd.DataFrame(ordenar_consensos(avaliados))
            st.dataframe(
                consenso[
                    [
                        "Nome",
                        "Posição",
                        NOME_CURTO_ANALISTA_VINI,
                        NOME_CURTO_ANALISTA_BETO,
                        "Média",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

        with col_divergencia:
            st.markdown("## Maiores divergências")
            divergencias = pd.DataFrame(ordenar_divergencias(avaliados))
            st.dataframe(
                divergencias[
                    [
                        "Nome",
                        "Posição",
                        NOME_CURTO_ANALISTA_VINI,
                        NOME_CURTO_ANALISTA_BETO,
                        "Diferença",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("## Leitura de mercado")
    if df_mercado.empty:
        st.info(MERCADO_SEM_DADOS)
        return

    total_atual = df_mercado["Atual (M€)"].sum()
    total_pico = df_mercado["Pico (M€)"].sum()
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Atletas com valor", len(df_mercado))
    col_m2.metric(
        "Valor atual somado",
        formatar_valor_milhoes(total_atual),
    )
    col_m3.metric("Pico somado", formatar_valor_milhoes(total_pico))

    mercado_ordenado = df_mercado.sort_values(
        "Atual (M€)",
        ascending=False,
    )
    st.caption(
        "Tabela textual dos valores atuais, picos e percentuais "
        "do pico de mercado."
    )
    st.dataframe(
        mercado_ordenado,
        width="stretch",
        hide_index=True,
        column_config={
            "Atual (M€)": st.column_config.NumberColumn(format="€ %.2f mi"),
            "Pico (M€)": st.column_config.NumberColumn(format="€ %.2f mi"),
            "% do pico": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "Diferença para o pico (M€)": (
                st.column_config.NumberColumn(format="€ %.2f mi")
            ),
        },
    )


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


def render_tela(
    menu: str,
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    roteador = {
        MENU_CAMPO: render_tela_campo,
        MENU_PERFIS: render_tela_perfis,
        MENU_ROSTER: render_tela_roster,
        MENU_ANALISE: render_tela_analise,
    }
    tela = roteador.get(menu, render_tela_campo)
    tela(jogadores)
