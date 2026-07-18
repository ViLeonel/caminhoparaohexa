"""Entrada principal do aplicativo O Caminho para o Hexa 2030."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from hexa_config import MENUS, PAGE_CONFIG, ROTULO_NAVEGACAO, TITULO_SIDEBAR
from hexa_data import DataIntegrityError, carregar_jogadores, validar_integridade_jogadores, validar_posicoes
from hexa_pages import render_feedback_sidebar, render_tela
from hexa_styles import aplicar_estilos
from hexa_taticas import validar_taticas


def carregar_base_segura() -> dict[str, dict]:
    try:
        return carregar_jogadores()
    except DataIntegrityError as erro:
        st.error(str(erro))
        st.info("Corrija o JSON no GitHub e reinicie o aplicativo. O arquivo inválido não foi sobrescrito.")
        st.stop()
        return {}


def render_erros_configuracao(jogadores: dict[str, dict]) -> None:
    relatorio = validar_integridade_jogadores(jogadores)
    erros = validar_posicoes(jogadores) + validar_taticas(jogadores)
    avisos = [problema.mensagem for problema in relatorio.avisos]
    if not erros and not avisos:
        return

    with st.expander("Inconsistências de configuração detectadas", expanded=True):
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


def render_navegacao() -> str:
    st.sidebar.markdown(
        f"<h2 class='sidebar-title'>{TITULO_SIDEBAR}</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    return st.sidebar.radio(ROTULO_NAVEGACAO, MENUS)


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    alto_contraste = render_preferencias_acessibilidade()
    aplicar_estilos(alto_contraste=alto_contraste)
    st.markdown('<a class="skip-link" href="#conteudo-principal">Pular para o conteúdo principal</a>', unsafe_allow_html=True)
    st.markdown('<main id="conteudo-principal" tabindex="-1"></main>', unsafe_allow_html=True)

    jogadores = carregar_base_segura()
    render_erros_configuracao(jogadores)
    menu = render_navegacao()
    render_tela(menu, jogadores)
    render_feedback_sidebar()


if __name__ == "__main__":
    main()
