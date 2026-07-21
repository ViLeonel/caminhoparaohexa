"""Tela de escalação e composição tática."""

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

__all__ = ['render_tela_campo']


def _esc(valor: Any, padrao: str = "") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


def _render_cabecalho_projeto() -> None:
    descricao = (
        f"Plataforma editorial e tática de {NOME_ANALISTA_VINI} e "
        f"{NOME_ANALISTA_BETO} para acompanhar jogadores brasileiros no "
        "ciclo da Copa de 2030. Escolha uma formação, monte 11 titulares e "
        "até 15 reservas e consulte scout, avaliações trimestrais, lista "
        "monitorada e dados de mercado."
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
        "</svg></div>"
        '<div class="project-hero-copy">'
        f'<h1 id="titulo-projeto" class="project-hero-title">{_esc(TITULO_PROJETO)}</h1>'
        f'<p class="project-hero-subtitle">{_esc(descricao)}</p>'
        "</div></section>"
    )
    st.markdown(cabecalho, unsafe_allow_html=True)


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


def _render_linha_seletores_posicionais(
    itens: Sequence[tuple[int, str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    ocupados: set[str],
) -> None:
    """Renderiza reservas posicionais sem oferecer atletas já ocupados."""
    colunas = st.columns(len(itens))
    for coluna, (indice, slot, configuracao) in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_posicional(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
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
            st.selectbox(
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


def _render_linha_seletores_livres(
    itens: Sequence[int],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    prioridade_posicoes: Sequence[str],
    ocupados: set[str],
) -> None:
    """Renderiza vagas livres sem repetir titulares ou outras reservas."""
    colunas = st.columns(len(itens))
    for coluna, indice in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_livre(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
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
            st.selectbox(
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
    reconciliacao = reconciliar_convocacao(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
    )
    ocupados = set(reconciliacao["ocupados"])

    st.markdown("---")
    st.markdown("## Definir reservas")
    st.caption(
        "As primeiras 11 vagas espelham a formação escolhida. "
        "As quatro vagas finais aceitam qualquer posição oficial."
    )

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
            ocupados,
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
            ocupados,
        )

    reconciliacao_final = reconciliar_convocacao(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
    )
    return list(reconciliacao_final["reservas"])


def _render_metricas_convocacao(
    nomes_titulares: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_periodo: Mapping[str, Mapping[str, Any]],
) -> None:
    if not nomes_titulares:
        return
    resumo = calcular_resumo_convocados(
        nomes_titulares,
        jogadores,
        avaliacoes_periodo,
    )
    render_kpis(
        (
            KPI(
                "Capacidade atual",
                formatar_numero(resumo["capacidade_atual_media"]),
                "Média dos titulares avaliados",
                "destaque",
            ),
            KPI(
                "Potencial 2030",
                formatar_numero(resumo["potencial_2030_medio"]),
                "Média dos titulares avaliados",
            ),
            KPI(
                "Saldo projetado",
                formatar_numero(
                    resumo["saldo_projetado_medio"],
                    sinal=True,
                ),
                "Potencial menos capacidade",
                "positivo",
            ),
            KPI(
                "Cobertura",
                f'{resumo["com_avaliacao"]}/{resumo["selecionados"]}',
                (
                    f'{resumo["completos"]} com avaliação completa '
                    "de Vini e Beto"
                ),
                "informativo",
            ),
        ),
        titulo="Indicadores dos titulares",
        rotulo_aria="Indicadores esportivos dos titulares",
    )


def render_tela_campo(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    _render_cabecalho_projeto()
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    persistencia = sincronizar_persistencia_local(
        st.session_state,
        TATICAS,
        jogadores,
    )
    if not persistencia.pronta:
        st.caption("Restaurando a última convocação salva neste navegador…")
        return
    if st.session_state.pop(CHAVE_AVISO_RESTAURACAO, False):
        st.toast("Escalação restaurada deste navegador.")
    if not persistencia.disponivel:
        st.warning(
            "O navegador bloqueou o armazenamento local. A convocação será "
            "mantida somente enquanto esta sessão permanecer aberta."
        )

    col_config, col_campo = st.columns([1, 2], gap="large")

    with col_config:
        st.markdown(
            '<h2 class="convocation-builder-title">Monte a sua convocação</h2>',
            unsafe_allow_html=True,
        )
        tatica_ativa = st.selectbox(
            "Esquema tático:",
            list(TATICAS.keys()),
            key="tactical_selector",
        )
        layout_ativo = TATICAS[tatica_ativa]

        reconciliacao = reconciliar_convocacao(
            st.session_state,
            tatica_ativa,
            layout_ativo,
            jogadores,
        )
        ocupados = set(reconciliacao["ocupados"])

        if st.button("Limpar titulares e reservas", width="stretch"):
            limpar_convocacao(
                st.session_state,
                tatica_ativa,
                len(layout_ativo),
            )
            st.rerun()

        with st.expander("Persistência da escalação", expanded=False):
            st.caption(
                "Suas escolhas ficam salvas apenas neste navegador e "
                "dispositivo. Cada esquema tático mantém sua própria seleção."
            )
            if st.button(
                "Apagar escalações salvas neste navegador",
                width="stretch",
                key="apagar_convocacoes_locais",
            ):
                apagar_convocacoes_locais(
                    st.session_state,
                    TATICAS,
                )
                st.rerun()

        st.caption(
            "Cada campo começa vazio e aceita somente atletas compatíveis "
            "com as posições oficiais do projeto."
        )
        escalados: dict[str, str] = {}

        for indice, (slot, configuracao) in enumerate(layout_ativo.items()):
            chave = chave_titular(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
            disponiveis = opcoes_titular(
                jogadores,
                configuracao.posicoes,
                indisponiveis,
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

    with col_campo:
        st.session_state.pop("tactical_view_mode", None)
        render_campo(
            layout_ativo,
            escalados,
            jogadores,
            avaliacoes_periodo,
        )
        render_legenda_adaptabilidade()

    titulares = set(escalados.values())
    reservas = _render_selecao_reservas(
        jogadores,
        tatica_ativa,
        layout_ativo,
        titulares,
    )

    resumo_texto = resumo_convocacao(len(escalados), len(reservas))
    st.markdown(
        f'<div class="sr-only" role="status" aria-live="polite" '
        f'aria-atomic="true">{_esc(resumo_texto)}</div>',
        unsafe_allow_html=True,
    )
    if convocacao_completa(len(escalados)):
        st.success(resumo_texto)
    else:
        st.info(resumo_texto)

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
    _render_metricas_convocacao(
        list(escalados.values()),
        jogadores,
        avaliacoes_periodo,
    )
