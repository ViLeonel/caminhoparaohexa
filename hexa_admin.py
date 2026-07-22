"""Área administrativa completa, protegida e auditável."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from hexa_admin_atualizacao import render_central_atualizacao
from hexa_admin_editorial import render_workflow_editorial
from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    Permissao,
    identidade_atual,
    usuario_tem_permissao,
)
from hexa_components import KPI, render_cabecalho, render_kpis
from hexa_config import VERSAO_APLICACAO
from hexa_persistencia_servidor import configuracao_persistencia, criar_repositorio
from hexa_repository_sqlite import SqliteJogadoresRepository

__all__ = ["render_area_administrativa"]


def render_area_administrativa(
    jogadores: Mapping[str, Mapping[str, Any]],
    *,
    identidade: IdentidadeUsuario | None = None,
) -> None:
    """Renderiza administração, workflow editorial e Central de Atualização."""
    identidade_ativa = identidade or identidade_atual()

    render_cabecalho(
        "🔐 Administração",
        "Edição versionada, revisão editorial, publicação, auditoria e recuperação.",
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

    config_persistencia = configuracao_persistencia()
    repositorio = criar_repositorio(config_persistencia)
    revisoes = (
        len(repositorio.listar_revisoes(limite=500))
        if isinstance(repositorio, SqliteJogadoresRepository)
        else 0
    )

    render_kpis(
        (
            KPI("Atletas carregados", len(jogadores), "Base canônica disponível"),
            KPI(
                "Persistência",
                config_persistencia.backend.upper(),
                config_persistencia.descricao,
                "informativo",
            ),
            KPI(
                "Revisões",
                revisoes if config_persistencia.duravel else "—",
                "Histórico imutável"
                if config_persistencia.duravel
                else "Modo somente leitura",
            ),
            KPI("Versão", VERSAO_APLICACAO, "Build em execução", "informativo"),
        ),
        titulo="Resumo da área",
        rotulo_aria="Resumo da área administrativa",
    )

    if not config_persistencia.duravel:
        st.warning(
            "O backend JSON está ativo. A consulta e a Central de Atualização "
            "continuam disponíveis, mas edição, publicação e rollback permanecem bloqueados."
        )
    else:
        st.success(
            "Persistência durável ativa. Alterações editoriais exigem rascunho, "
            "revisão e publicação."
        )

    with st.expander("Identidade e permissões"):
        permissoes = {
            permissao.value: usuario_tem_permissao(
                permissao,
                identidade=identidade_ativa,
            )
            for permissao in Permissao
        }
        st.write(
            {
                "nome": identidade_ativa.nome or "Não informado",
                "email": identidade_ativa.email or "Não informado",
                "subject": identidade_ativa.subject or "Não informado",
                "origem_auditoria": identidade_ativa.origem_auditoria,
                "permissoes": permissoes,
            }
        )

    with st.expander("Persistência e revisões"):
        st.write(
            {
                "backend": config_persistencia.backend,
                "durável": config_persistencia.duravel,
                "descrição": config_persistencia.descricao,
                "edição_habilitada": config_persistencia.duravel,
            }
        )
        if isinstance(repositorio, SqliteJogadoresRepository):
            st.caption(
                "Publicações e rollbacks criam novas revisões; nenhuma versão histórica é apagada."
            )
            st.dataframe(
                [
                    {
                        "versão": item.versao[:12],
                        "data": item.criada_em,
                        "origem": item.origem,
                        "anterior": item.versao_anterior[:12],
                        "ator": item.ator_nome or item.ator_email or item.ator_id,
                    }
                    for item in repositorio.listar_revisoes(limite=20)
                ],
                width="stretch",
                hide_index=True,
            )

    st.divider()
    render_workflow_editorial(identidade_ativa)

    st.divider()
    render_central_atualizacao(
        jogadores,
        identidade=identidade_ativa,
    )
