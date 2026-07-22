"""Interface administrativa do workflow editorial completo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from hexa_auth import IdentidadeUsuario, Permissao, usuario_tem_permissao
from hexa_persistencia_servidor import configuracao_persistencia, criar_repositorio
from hexa_repository import ConflitoConcorrenciaError
from hexa_repository_sqlite import SqliteJogadoresRepository
from hexa_taticas import POSICOES_OFICIAIS
from hexa_workflow_editorial import (
    RascunhoEditorial,
    StatusRascunho,
    WorkflowEditorialError,
    WorkflowEditorialRepository,
)

__all__ = ["render_workflow_editorial"]


def _ator(identidade: IdentidadeUsuario) -> dict[str, str]:
    return {
        "ator_email": identidade.email,
        "ator_nome": identidade.nome,
        "ator_id": identidade.subject,
    }


def _tem(permissao: Permissao, identidade: IdentidadeUsuario) -> bool:
    try:
        return usuario_tem_permissao(permissao, identidade=identidade)
    except Exception:
        return False


def _diff(rascunho: RascunhoEditorial, estado: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "Campo": campo,
            "Antes": estado.get(campo),
            "Depois": valor,
        }
        for campo, valor in rascunho.alteracoes.items()
    ]


def _render_criacao(
    repositorio: SqliteJogadoresRepository,
    workflow: WorkflowEditorialRepository,
    identidade: IdentidadeUsuario,
) -> None:
    if not _tem(Permissao.CRIAR_RASCUNHO, identidade):
        st.info("Seu perfil não possui permissão para criar rascunhos.")
        return

    leitura = repositorio.carregar()
    jogadores = leitura.jogadores
    nomes = sorted(jogadores, key=str.casefold)
    jogador = st.selectbox(
        "Jogador",
        nomes,
        index=None,
        placeholder="Selecione o atleta",
        key="phase12_editor_player",
    )
    if not jogador:
        st.caption("Selecione um atleta para iniciar uma proposta editorial.")
        return

    atual = jogadores[jogador]
    with st.form("phase12_editor_form", clear_on_submit=False):
        st.markdown("#### Dados cadastrais e táticos")
        col1, col2 = st.columns(2)
        with col1:
            clube = st.text_input("Clube", value=str(atual.get("clube") or ""))
            idade = st.number_input(
                "Idade",
                min_value=15,
                max_value=45,
                value=int(atual.get("idade") or 22),
                step=1,
            )
            grupo = st.selectbox(
                "Grupo",
                ("Titulares", "Reservas", "Observação"),
                index=("Titulares", "Reservas", "Observação").index(
                    str(atual.get("grupo") or "Observação")
                )
                if str(atual.get("grupo") or "Observação")
                in ("Titulares", "Reservas", "Observação")
                else 2,
            )
        with col2:
            posicao_atual = str(atual.get("posicao") or POSICOES_OFICIAIS[0])
            posicao = st.selectbox(
                "Posição principal",
                POSICOES_OFICIAIS,
                index=POSICOES_OFICIAIS.index(posicao_atual)
                if posicao_atual in POSICOES_OFICIAIS
                else 0,
            )
            posicoes = st.multiselect(
                "Posições múltiplas",
                POSICOES_OFICIAIS,
                default=[
                    item
                    for item in atual.get("posicoes_multiplas", [posicao])
                    if item in POSICOES_OFICIAIS
                ],
            )

        st.markdown("#### Avaliação editorial")
        nota1, nota2 = st.columns(2)
        with nota1:
            nota_vini = st.number_input(
                "Nota Vini",
                min_value=0.0,
                max_value=10.0,
                value=float(atual.get("nota_vini") or 0.0),
                step=0.5,
            )
        with nota2:
            nota_roberto = st.number_input(
                "Nota Beto",
                min_value=0.0,
                max_value=10.0,
                value=float(atual.get("nota_roberto") or 0.0),
                step=0.5,
            )
        pontos_fortes = st.text_area(
            "Pontos fortes",
            value=str(atual.get("pontos_fortes") or ""),
            height=120,
        )
        pontos_fracos = st.text_area(
            "Pontos fracos",
            value=str(atual.get("pontos_fracos") or ""),
            height=120,
        )
        historico = st.text_area(
            "Histórico",
            value=str(atual.get("historico") or ""),
            height=160,
        )
        justificativa = st.text_area(
            "Justificativa da alteração",
            placeholder="Explique por que a mudança deve ser revisada e publicada.",
            height=100,
        )
        enviar = st.form_submit_button("Criar rascunho", type="primary")

    if not enviar:
        return
    alteracoes = {
        "clube": clube,
        "idade": int(idade),
        "grupo": grupo,
        "posicao": posicao,
        "posicoes_multiplas": list(posicoes or [posicao]),
        "nota_vini": float(nota_vini),
        "nota_roberto": float(nota_roberto),
        "pontos_fortes": pontos_fortes,
        "pontos_fracos": pontos_fracos,
        "historico": historico,
    }
    try:
        criado = workflow.criar(
            jogador=jogador,
            versao_base=leitura.versao,
            estado_atual=atual,
            alteracoes=alteracoes,
            justificativa=justificativa,
            **_ator(identidade),
        )
        workflow.enviar_revisao(criado.id_rascunho, **_ator(identidade))
    except WorkflowEditorialError as erro:
        st.error(str(erro))
    else:
        st.success("Rascunho criado e enviado para revisão.")
        st.rerun()


def _rotulo(rascunho: RascunhoEditorial) -> str:
    return (
        f"{rascunho.jogador} · {rascunho.status.value.replace('_', ' ')} · "
        f"{rascunho.id_rascunho[:8]}"
    )


def _render_revisao(
    repositorio: SqliteJogadoresRepository,
    workflow: WorkflowEditorialRepository,
    identidade: IdentidadeUsuario,
) -> None:
    rascunhos = workflow.listar(limite=200)
    if not rascunhos:
        st.info("Nenhum rascunho editorial registrado.")
        return
    selecionado = st.selectbox(
        "Rascunho",
        rascunhos,
        format_func=_rotulo,
        key="phase12_review_draft",
    )
    estado = repositorio.carregar().jogadores.get(selecionado.jogador, {})
    st.caption(
        f"Criado por {selecionado.criado_por_nome or selecionado.criado_por_email or 'não informado'} "
        f"em {selecionado.criado_em}"
    )
    st.write(f"**Justificativa:** {selecionado.justificativa}")
    st.dataframe(_diff(selecionado, estado), width="stretch", hide_index=True)

    comentario = st.text_area(
        "Comentário de revisão",
        key=f"phase12_review_comment_{selecionado.id_rascunho}",
    )
    colunas = st.columns(4)
    if (
        selecionado.status is StatusRascunho.EM_REVISAO
        and _tem(Permissao.REVISAR_RASCUNHO, identidade)
    ):
        if colunas[0].button("Aprovar", type="primary", key="phase12_approve"):
            try:
                workflow.aprovar(
                    selecionado.id_rascunho,
                    comentario=comentario,
                    **_ator(identidade),
                )
            except WorkflowEditorialError as erro:
                st.error(str(erro))
            else:
                st.success("Rascunho aprovado.")
                st.rerun()
        if colunas[1].button("Rejeitar", key="phase12_reject"):
            try:
                workflow.rejeitar(
                    selecionado.id_rascunho,
                    comentario=comentario,
                    **_ator(identidade),
                )
            except WorkflowEditorialError as erro:
                st.error(str(erro))
            else:
                st.success("Rascunho rejeitado.")
                st.rerun()

    if (
        selecionado.status is StatusRascunho.APROVADO
        and _tem(Permissao.PUBLICAR_RASCUNHO, identidade)
    ):
        confirmar = st.checkbox(
            "Confirmo que revisei o diff e desejo publicar uma nova revisão.",
            key=f"phase12_publish_confirm_{selecionado.id_rascunho}",
        )
        if colunas[2].button(
            "Publicar",
            type="primary",
            disabled=not confirmar,
            key="phase12_publish",
        ):
            try:
                versao = workflow.publicar(
                    selecionado.id_rascunho,
                    repositorio=repositorio,
                    **_ator(identidade),
                )
            except (WorkflowEditorialError, ConflitoConcorrenciaError) as erro:
                st.error(str(erro))
            else:
                st.success(f"Publicação concluída. Revisão {versao[:12]}.")
                st.rerun()

    eventos = workflow.eventos(selecionado.id_rascunho)
    with st.expander("Trilha do workflow"):
        st.dataframe(eventos, width="stretch", hide_index=True)


def _render_rollback(
    repositorio: SqliteJogadoresRepository,
    workflow: WorkflowEditorialRepository,
    identidade: IdentidadeUsuario,
) -> None:
    if not _tem(Permissao.EXECUTAR_ROLLBACK, identidade):
        st.info("Seu perfil não possui permissão para rollback.")
        return
    revisoes = repositorio.listar_revisoes(limite=100)
    if len(revisoes) < 2:
        st.info("Ainda não há revisões históricas suficientes para rollback.")
        return
    atual = repositorio.versao_atual()
    alvos = [item for item in revisoes if item.versao != atual]
    alvo = st.selectbox(
        "Revisão de destino",
        alvos,
        format_func=lambda item: (
            f"{item.criada_em} · {item.origem} · {item.versao[:12]}"
        ),
    )
    st.warning(
        "O rollback não apaga o histórico. Ele cria uma nova revisão com o conteúdo selecionado."
    )
    confirmacao = st.text_input(
        "Digite ROLLBACK para confirmar",
        key="phase12_rollback_confirmation",
    )
    if st.button(
        "Executar rollback",
        type="primary",
        disabled=confirmacao != "ROLLBACK",
    ):
        try:
            nova = workflow.rollback(
                repositorio=repositorio,
                versao_alvo=alvo.versao,
                versao_esperada=atual,
                **_ator(identidade),
            )
        except (WorkflowEditorialError, ConflitoConcorrenciaError) as erro:
            st.error(str(erro))
        else:
            st.success(f"Rollback concluído como nova revisão {nova[:12]}.")
            st.rerun()


def render_workflow_editorial(
    identidade: IdentidadeUsuario,
) -> None:
    """Renderiza edição, revisão, publicação e rollback somente em SQLite."""
    config = configuracao_persistencia()
    repositorio = criar_repositorio(config)
    st.subheader("Workflow editorial")

    if not isinstance(repositorio, SqliteJogadoresRepository) or not config.duravel:
        st.warning(
            "A edição administrativa exige backend SQLite em volume durável. "
            "Com o backend JSON, a área permanece somente leitura."
        )
        return

    workflow = WorkflowEditorialRepository(repositorio.caminho)
    abas = st.tabs(("Criar rascunho", "Revisar e publicar", "Histórico e rollback"))
    with abas[0]:
        _render_criacao(repositorio, workflow, identidade)
    with abas[1]:
        _render_revisao(repositorio, workflow, identidade)
    with abas[2]:
        _render_rollback(repositorio, workflow, identidade)
