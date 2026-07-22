"""Página administrativa protegida, ainda sem formulários de edição."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from hexa_admin_atualizacao import render_central_atualizacao
from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    identidade_atual,
    Permissao,
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
    """Renderiza uma área privada sem permitir edição nesta entrega."""
    identidade_ativa = identidade or identidade_atual()

    render_cabecalho(
        "🔐 Administração",
        "Persistência administrativa preparada; edição continua desabilitada.",
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
    config_persistencia = configuracao_persistencia()
    repositorio = criar_repositorio(config_persistencia)
    revisoes = (
        len(repositorio.listar_revisoes(limite=500))
        if isinstance(repositorio, SqliteJogadoresRepository)
        else 0
    )

    st.info(
        "A Fase 7 prepara persistência versionada, auditoria e rollback. "
        "A edição de atletas continua desabilitada até a ativação explícita "
        "de um armazenamento durável fora do filesystem efêmero."
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
                "Histórico imutável" if config_persistencia.duravel else "JSON sem banco ativo",
            ),
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

    with st.expander("Persistência e recuperação"):
        st.write(
            {
                "backend": config_persistencia.backend,
                "durável": config_persistencia.duravel,
                "descrição": config_persistencia.descricao,
                "edição_habilitada": False,
            }
        )
        if isinstance(repositorio, SqliteJogadoresRepository):
            st.caption(
                "Rollbacks criam uma nova revisão; o histórico anterior nunca é apagado."
            )
            st.dataframe(
                [
                    {
                        "versão": item.versao[:12],
                        "data": item.criada_em,
                        "origem": item.origem,
                        "anterior": item.versao_anterior[:12],
                    }
                    for item in repositorio.listar_revisoes(limite=20)
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.warning(
                "O backend JSON permanece ativo. No Streamlit Community Cloud, "
                "gravações no filesystem não são persistência durável."
            )

    st.divider()
    render_central_atualizacao(
        jogadores,
        identidade=identidade_ativa,
    )

