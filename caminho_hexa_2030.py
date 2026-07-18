"""Entrada principal do aplicativo O Caminho para o Hexa 2030."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from hexa_admin import render_area_administrativa
from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    render_controle_login,
    usuario_eh_admin,
)
from hexa_avaliacoes import (
    AvaliacoesIntegrityError,
    BaseAvaliacoes,
    carregar_avaliacoes,
    formatar_data_referencia,
    formatar_periodo,
)
from hexa_config import (
    MENU_ADMIN,
    MENUS,
    PAGE_CONFIG,
    ROTULO_NAVEGACAO,
    TITULO_SIDEBAR,
)
from hexa_data import (
    DataIntegrityError,
    carregar_jogadores,
    validar_integridade_jogadores,
    validar_posicoes,
)
from hexa_pages import render_feedback_sidebar, render_tela
from hexa_styles import aplicar_estilos
from hexa_taticas import validar_taticas


def carregar_base_segura() -> dict[str, dict[str, Any]]:
    try:
        return carregar_jogadores()
    except DataIntegrityError as erro:
        st.error(str(erro))
        st.info(
            "Corrija o JSON no GitHub e reinicie o aplicativo. "
            "O arquivo inválido não foi sobrescrito."
        )
        st.stop()
        return {}


def carregar_avaliacoes_seguras(
    jogadores: dict[str, dict[str, Any]],
) -> BaseAvaliacoes:
    try:
        return carregar_avaliacoes(jogadores=jogadores)
    except AvaliacoesIntegrityError as erro:
        st.error(str(erro))
        st.info(
            "Corrija o JSON trimestral no GitHub e reinicie o aplicativo. "
            "A fonte inválida não foi reparada nem sobrescrita."
        )
        st.stop()
        raise


def render_erros_configuracao(
    jogadores: dict[str, dict[str, Any]],
) -> None:
    relatorio = validar_integridade_jogadores(jogadores)
    erros = validar_posicoes(jogadores) + validar_taticas(jogadores)
    avisos = [problema.mensagem for problema in relatorio.avisos]
    if not erros and not avisos:
        return

    with st.expander(
        "Inconsistências de configuração detectadas",
        expanded=True,
    ):
        for mensagem in erros:
            st.error(mensagem)
        for mensagem in avisos:
            st.warning(mensagem)


def render_preferencias_acessibilidade() -> bool:
    st.sidebar.markdown("### Acessibilidade")
    return st.sidebar.toggle(
        "Modo de alto contraste",
        key="modo_alto_contraste",
        help="Aumenta o contraste de textos, bordas, foco e superfícies.",
    )


def render_navegacao() -> tuple[str, IdentidadeUsuario]:
    st.sidebar.markdown(
        f"<h2 class='sidebar-title'>{TITULO_SIDEBAR}</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    identidade = render_controle_login()
    st.sidebar.markdown("---")

    menus_disponiveis = list(MENUS)
    try:
        if usuario_eh_admin():
            menus_disponiveis.append(MENU_ADMIN)
    except AuthConfigError as erro:
        st.sidebar.warning(str(erro))

    menu = st.sidebar.radio(
        ROTULO_NAVEGACAO,
        menus_disponiveis,
    )
    return menu, identidade


def render_seletor_periodo(base: BaseAvaliacoes) -> str:
    periodos = list(base.periodos())
    if not periodos:
        raise AvaliacoesIntegrityError(
            "A base trimestral não possui períodos disponíveis."
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Período de avaliação")
    periodo = st.sidebar.selectbox(
        "Período ativo",
        periodos,
        index=len(periodos) - 1,
        format_func=formatar_periodo,
        disabled=len(periodos) == 1,
        key="periodo_avaliacao_ativo",
        help=(
            "O mesmo período é aplicado ao campo, à ficha individual, "
            "à lista e às análises."
        ),
    )
    data_referencia = base.data_referencia_periodo(periodo)
    st.sidebar.caption(
        "Data de referência: "
        f"{formatar_data_referencia(data_referencia)}"
    )
    st.sidebar.caption("Fonte editorial: avaliações trimestrais de Vini e Beto.")
    return periodo


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    alto_contraste = render_preferencias_acessibilidade()
    aplicar_estilos(alto_contraste=alto_contraste)
    st.markdown(
        '<a class="skip-link" href="#conteudo-principal">'
        "Pular para o conteúdo principal</a>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<main id="conteudo-principal" tabindex="-1"></main>',
        unsafe_allow_html=True,
    )

    jogadores = carregar_base_segura()
    base_avaliacoes = carregar_avaliacoes_seguras(jogadores)
    render_erros_configuracao(jogadores)
    menu, identidade = render_navegacao()
    periodo = render_seletor_periodo(base_avaliacoes)

    if menu == MENU_ADMIN:
        render_area_administrativa(
            jogadores,
            identidade=identidade,
        )
    else:
        render_tela(
            menu=menu,
            jogadores=jogadores,
            base_avaliacoes=base_avaliacoes,
            periodo=periodo,
        )

    render_feedback_sidebar()


if __name__ == "__main__":
    main()
