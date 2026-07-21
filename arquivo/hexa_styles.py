"""Agregador estável do design system compartilhado."""

from __future__ import annotations

import streamlit as st

from hexa_style_accessibility import HIGH_CONTRAST_CSS
from hexa_style_base import CSS
from hexa_style_extensions import RC5_CSS

__all__ = [
    "CSS",
    "HIGH_CONTRAST_CSS",
    "RC5_CSS",
    "aplicar_estilos",
]


def aplicar_estilos(*, alto_contraste: bool = False) -> None:
    """Aplica os blocos do design system em ordem determinística."""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(RC5_CSS, unsafe_allow_html=True)
    if alto_contraste:
        st.markdown(HIGH_CONTRAST_CSS, unsafe_allow_html=True)
