"""Roteamento estável das telas públicas.

As implementações foram separadas por domínio para reduzir acoplamento. A
assinatura legada de ``render_tela`` continua aceita durante a migração.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from hexa_avaliacoes import BaseAvaliacoes
from hexa_config import MENU_ANALISE, MENU_CAMPO, MENU_PERFIS, MENU_ROSTER
from hexa_context import AppContext
from hexa_feedback import render_feedback_sidebar
from hexa_page_campo import render_tela_campo
from hexa_page_indicadores import render_tela_analise
from hexa_page_roster import render_tela_roster
from hexa_page_scout import render_tela_perfis

__all__ = [
    "PAGE_RENDERERS",
    "render_feedback_sidebar",
    "render_tela",
    "render_tela_analise",
    "render_tela_campo",
    "render_tela_perfis",
    "render_tela_roster",
]

PageRenderer = Callable[
    [Mapping[str, Mapping[str, Any]], BaseAvaliacoes, str],
    None,
]

PAGE_RENDERERS: Mapping[str, PageRenderer] = {
    MENU_CAMPO: render_tela_campo,
    MENU_PERFIS: render_tela_perfis,
    MENU_ROSTER: render_tela_roster,
    MENU_ANALISE: render_tela_analise,
}


def render_tela(
    contexto: AppContext | None = None,
    *,
    menu: str | None = None,
    jogadores: Mapping[str, Mapping[str, Any]] | None = None,
    base_avaliacoes: BaseAvaliacoes | None = None,
    periodo: str | None = None,
) -> None:
    """Renderiza uma tela pública com contexto tipado ou argumentos legados."""
    if contexto is None:
        if (
            menu is None
            or jogadores is None
            or base_avaliacoes is None
            or periodo is None
        ):
            raise TypeError(
                "Informe AppContext ou todos os argumentos legados de render_tela."
            )
        contexto = AppContext(
            menu=menu,
            jogadores=jogadores,
            base_avaliacoes=base_avaliacoes,
            periodo=periodo,
        )

    tela = PAGE_RENDERERS.get(contexto.menu, render_tela_campo)
    tela(
        contexto.jogadores,
        contexto.base_avaliacoes,
        contexto.periodo,
    )
