"""Entrada principal do aplicativo O Caminho para o Hexa 2030."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
base_dir_texto = str(BASE_DIR)
if base_dir_texto in sys.path:
    sys.path.remove(base_dir_texto)
sys.path.insert(0, base_dir_texto)

from hexa_admin import render_area_administrativa
LOGGER = logging.getLogger(__name__)

from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    identidade_atual,
    registrar_erro_configuracao_auth,
    render_controle_login,
    Permissao,
    usuario_tem_permissao,
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
from hexa_context import AppContext
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


def render_preferencias_acessibilidade() -> None:
    st.sidebar.markdown("---")
    with st.sidebar.expander("Acessibilidade", expanded=False):
        st.toggle(
            "Modo de alto contraste",
            key="modo_alto_contraste",
            help="Aumenta o contraste de textos, bordas, foco e superfícies.",
        )
        st.selectbox(
            "Densidade das tabelas",
            ("Compacta", "Confortável"),
            key="densidade_tabelas",
            help=(
                "Compacta exibe mais linhas. Confortável aumenta a altura "
                "das linhas sem alterar os dados."
            ),
        )


def carregar_identidade_segura() -> IdentidadeUsuario:
    """Obtém a identidade sem revelar falhas de configuração ao visitante."""
    try:
        return identidade_atual()
    except AuthConfigError as erro:
        registrar_erro_configuracao_auth(erro)
        return identidade_atual(validar_politica=False)


def render_navegacao(
    identidade: IdentidadeUsuario,
) -> str:
    """Renderiza a navegação; o acesso administrativo fica após o Radar."""
    st.sidebar.markdown(
        f"<h2 class='sidebar-title'>{TITULO_SIDEBAR}</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    menus_disponiveis = list(MENUS)
    try:
        if usuario_tem_permissao(
            Permissao.VISUALIZAR_ADMIN,
            identidade=identidade,
        ):
            menus_disponiveis.append(MENU_ADMIN)
    except AuthConfigError as erro:
        registrar_erro_configuracao_auth(erro)

    return st.sidebar.radio(
        ROTULO_NAVEGACAO,
        menus_disponiveis,
    )

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
    alto_contraste = bool(
        st.session_state.get("modo_alto_contraste", False)
    )
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

    identidade = carregar_identidade_segura()
    menu = render_navegacao(identidade)
    periodo = render_seletor_periodo(base_avaliacoes)

    # A ordem das chamadas define a ordem visual na barra lateral.
    render_feedback_sidebar()
    render_controle_login(identidade)
    render_preferencias_acessibilidade()

    if menu == MENU_ADMIN:
        render_area_administrativa(
            jogadores,
            identidade=identidade,
        )
    else:
        render_tela(
            AppContext(
                menu=menu,
                jogadores=jogadores,
                base_avaliacoes=base_avaliacoes,
                periodo=periodo,
            )
        )


if __name__ == "__main__":
    main()
