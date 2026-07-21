"""Página administrativa protegida, ainda sem formulários de edição."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    identidade_atual,
    Permissao,
    usuario_tem_permissao,
)
from hexa_components import KPI, render_cabecalho, render_kpis
from hexa_config import VERSAO_APLICACAO

__all__ = ["render_area_administrativa"]


def render_area_administrativa(
    jogadores: Mapping[str, Mapping[str, Any]],
    *,
    identidade: IdentidadeUsuario | None = None,
) -> None:
    """Renderiza uma área privada sem permitir edição nesta entrega."""
    identidade_ativa = identidade or identidade_atual()

    render_cabecalho(
        "🔐 Administração",
        "Área privada em preparação. Nenhuma edição está habilitada nesta versão.",
    )

    if not identidade_ativa.autenticado:
        st.warning("Faça login pela barra lateral para acessar esta área.")
        return

    try:
        autorizado = usuario_tem_permissao(
            Permissao.VISUALIZAR_ADMIN,
            identidade=identidade_ativa,
        )
    except AuthConfigError as erro:
        st.error(str(erro))
        return

    if not autorizado:
        st.error(
            "A conta autenticada não está autorizada a acessar a administração."
        )
        return

    st.success("Acesso administrativo autorizado.")
    st.info(
        "Esta primeira entrega valida autenticação, autorização e identidade "
        "do editor. Formulários de edição serão adicionados somente após "
        "a confirmação do fluxo no Streamlit Community Cloud."
    )

    render_kpis(
        (
            KPI("Atletas carregados", len(jogadores), "Base canônica disponível"),
            KPI("Perfil", "Administrador", "Acesso privado autorizado", "positivo"),
            KPI("Versão", VERSAO_APLICACAO, "Build em execução", "informativo"),
        ),
        titulo="Resumo da área",
        rotulo_aria="Resumo da área administrativa",
    )

    with st.expander("Identidade disponível para auditoria"):
        st.write(
            {
                "nome": identidade_ativa.nome or "Não informado",
                "email": identidade_ativa.email or "Não informado",
                "subject": identidade_ativa.subject or "Não informado",
                "origem_auditoria": identidade_ativa.origem_auditoria,
            }
        )

    with st.expander("Próximos módulos administrativos"):
        st.markdown(
            """
            - edição editorial controlada;
            - atualização cadastral;
            - consulta do histórico de auditoria;
            - relatório de integridade;
            - exportação para versionamento no GitHub.
            """
        )
