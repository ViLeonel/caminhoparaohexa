"""Entrada principal do aplicativo O Caminho para o Hexa 2030."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from hexa_data import DataIntegrityError, carregar_jogadores, validar_posicoes
from hexa_pages import MENUS, render_feedback_sidebar, render_tela
from hexa_styles import PAGE_CONFIG, aplicar_estilos
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
    erros = validar_posicoes(jogadores) + validar_taticas(jogadores)
    if not erros:
        return

    with st.expander("Inconsistências de configuração detectadas", expanded=True):
        for mensagem in erros:
            st.error(mensagem)


def render_navegacao() -> str:
    st.sidebar.markdown(
        "<h2 style='text-align:center;color:#EAB308;margin-top:15px;'>CONSELHO TÁTICO</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    return st.sidebar.radio("Navegação do Painel:", MENUS)


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    aplicar_estilos()

    jogadores = carregar_base_segura()
    render_erros_configuracao(jogadores)
    menu = render_navegacao()
    render_tela(menu, jogadores)
    render_feedback_sidebar()


if __name__ == "__main__":
    main()
