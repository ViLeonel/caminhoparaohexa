"""Composição das quatro telas principais do aplicativo."""

from __future__ import annotations

import html
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import streamlit as st

from hexa_avaliacoes import (
    BaseAvaliacoes,
    calcular_metricas_avaliacao,
    calcular_resumo_convocados,
    calcular_resumo_periodo,
    construir_rankings_periodo,
    formatar_data_referencia,
    formatar_numero,
    formatar_periodo,
    formatar_status_avaliacao,
    historico_atleta,
)
from hexa_components import (
    ColunaTabelaExecutiva,
    KPI,
    render_banco_reservas,
    render_cabecalho,
    render_cabecalho_secao,
    render_campo,
    render_cartao_perfil,
    render_comparativo_mercado,
    render_dados_transfermarkt,
    render_kpis,
    render_legenda_adaptabilidade,
    render_quadro_avaliacao_executivo,
    render_resumo_elenco,
    render_tabela_executiva,
)
from hexa_config import (
    ANO_BASE_DADOS,
    ANO_COPA,
    ASSUNTO_FEEDBACK_PREFIXO,
    EMAIL_FEEDBACK,
    GRUPO_OBSERVACAO,
    MENU_ANALISE,
    MENU_CAMPO,
    MENU_PERFIS,
    MENU_ROSTER,
    NOME_ANALISTA_BETO,
    NOME_ANALISTA_VINI,
    NOME_CURTO_ANALISTA_BETO,
    NOME_CURTO_ANALISTA_VINI,
    SAUDACAO_FEEDBACK,
    TIPOS_SUGESTAO,
    TITULO_PROJETO,
)
from hexa_data import (
    formatar_valor_milhoes,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_persistencia_local import (
    CHAVE_AVISO_RESTAURACAO,
    apagar_convocacoes_locais,
    sincronizar_persistencia_local,
)
from hexa_messages import (
    FEEDBACK_MENSAGEM_OBRIGATORIA,
    FEEDBACK_PREPARADO,
    MERCADO_SEM_DADOS,
    ROSTER_SEM_RESULTADOS,
    convocacao_completa,
    resumo_convocacao,
)
from hexa_selectors import (
    construir_registros_mercado,
    construir_registros_roster,
)
from hexa_session import (
    chave_reserva_livre,
    chave_reserva_posicional,
    chave_titular,
    limpar_convocacao,
    migrar_reservas_legadas,
    normalizar_escolha_reserva,
    normalizar_escolha_titular,
    opcoes_reserva_livre,
    opcoes_reserva_posicional,
    opcoes_titular,
    prioridade_posicoes_tatica,
    quantidade_vagas_livres,
    reconciliar_convocacao,
)
from hexa_taticas import (
    POSICOES_OFICIAIS,
    TATICAS,
    SlotTatico,
    formatar_jogador_com_posicao,
)

__all__ = [
    "render_feedback_sidebar",
    "render_tela",
    "render_tela_analise",
    "render_tela_campo",
    "render_tela_perfis",
    "render_tela_roster",
]


def _esc(valor: Any, padrao: str = "") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


def _render_cabecalho_projeto() -> None:
    descricao = (
        f"Plataforma editorial e tática de {NOME_ANALISTA_VINI} e "
        f"{NOME_ANALISTA_BETO} para acompanhar jogadores brasileiros no "
        "ciclo da Copa de 2030. Escolha uma formação, monte 11 titulares e "
        "até 15 reservas e consulte scout, avaliações trimestrais, lista "
        "monitorada e dados de mercado."
    )
    cabecalho = (
        '<section class="project-hero" aria-labelledby="titulo-projeto">'
        '<div class="project-trophy" aria-hidden="true">'
        '<svg class="world-cup-trophy" viewBox="0 0 96 128" '
        'focusable="false" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M48 5C29 5 18 17 19 33c1 13 10 24 21 31 '
        '4 3 5 8 2 13L31 96h34L54 77c-3-5-2-10 2-13 '
        '11-7 20-18 21-31C78 17 67 5 48 5Z"/>'
        '<path d="M22 30c-9 5-13 14-10 23 3 10 12 16 23 18 '
        'l4-8c-8-2-14-6-16-12-2-5 0-10 5-13l-6-8Zm52 0 '
        'c9 5 13 14 10 23-3 10-12 16-23 18l-4-8c8-2 '
        '14-6 16-12 2-5 0-10-5-13l6-8Z"/>'
        '<path d="M29 99h38l6 13H23l6-13Zm-10 17h58v8H19v-8Z"/>'
        '<path class="trophy-detail" d="M35 18c7-5 18-6 27-1 '
        'M28 34c8 8 21 12 38 7 M38 57c7 2 14 2 21-1"/>'
        "</svg></div>"
        '<div class="project-hero-copy">'
        f'<h1 id="titulo-projeto" class="project-hero-title">{_esc(TITULO_PROJETO)}</h1>'
        f'<p class="project-hero-subtitle">{_esc(descricao)}</p>'
        "</div></section>"
    )
    st.markdown(cabecalho, unsafe_allow_html=True)


def _avaliacoes_por_nome(
    base: BaseAvaliacoes,
    periodo: str,
) -> dict[str, Mapping[str, Any]]:
    return base.por_nome_no_periodo(periodo)


def _adicionar_empresarios_mercado(
    registros: Sequence[Mapping[str, Any]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Acrescenta a representação disponível sem alterar a fonte canônica."""
    enriquecidos: list[dict[str, Any]] = []
    for registro in registros:
        linha = dict(registro)
        nome = str(linha.get("Nome") or "")
        dados = jogadores.get(nome, {})
        empresario = str(dados.get("tm_empresario") or "").strip()
        linha["Empresário"] = empresario or "Não informado"
        enriquecidos.append(linha)
    return enriquecidos


def _render_contexto_periodo(
    base: BaseAvaliacoes,
    periodo: str,
    *,
    total_atletas: int,
    mostrar_estatisticas: bool = True,
) -> None:
    resumo = calcular_resumo_periodo(
        base,
        periodo,
        total_atletas=total_atletas,
    )
    data_texto = formatar_data_referencia(resumo["data_referencia"])
    estatisticas_html = ""
    if mostrar_estatisticas:
        estatisticas_html = (
            '<div class="evaluation-context-stats">'
            f'<span>{resumo["com_alguma_avaliacao"]} com alguma avaliação</span>'
            f'<span>{resumo["avaliacoes_completas"]} completas</span>'
            f'<span>Cobertura completa: {resumo["cobertura_completa"]:.1%}</span>'
            "</div>"
        )
    st.markdown(
        '<section class="evaluation-context" role="note">'
        '<div class="evaluation-context-main">'
        f'<strong>Avaliações referentes ao {_esc(formatar_periodo(periodo))}</strong>'
        f'<span>Data de referência: {_esc(data_texto)}</span>'
        "</div>"
        f"{estatisticas_html}</section>",
        unsafe_allow_html=True,
    )


def _render_linha_seletores_posicionais(
    itens: Sequence[tuple[int, str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    ocupados: set[str],
) -> None:
    """Renderiza reservas posicionais sem oferecer atletas já ocupados."""
    colunas = st.columns(len(itens))
    for coluna, (indice, slot, configuracao) in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_posicional(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
            disponiveis = opcoes_reserva_posicional(
                jogadores,
                configuracao.posicoes,
                indisponiveis,
            )
            normalizar_escolha_reserva(
                st.session_state,
                chave,
                disponiveis,
            )
            st.selectbox(
                f"Reserva — {slot}:",
                disponiveis,
                index=None,
                placeholder="Buscar atleta compatível",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
                help=(
                    "Aceita as mesmas posições editoriais permitidas para "
                    "o respectivo slot titular."
                ),
            )


def _render_linha_seletores_livres(
    itens: Sequence[int],
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    prioridade_posicoes: Sequence[str],
    ocupados: set[str],
) -> None:
    """Renderiza vagas livres sem repetir titulares ou outras reservas."""
    colunas = st.columns(len(itens))
    for coluna, indice in zip(colunas, itens):
        with coluna:
            chave = chave_reserva_livre(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
            disponiveis = opcoes_reserva_livre(
                jogadores,
                prioridade_posicoes,
                indisponiveis,
            )
            normalizar_escolha_reserva(
                st.session_state,
                chave,
                disponiveis,
            )
            st.selectbox(
                f"Vaga livre {indice + 1}:",
                disponiveis,
                index=None,
                placeholder="Buscar em qualquer posição",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
                help=(
                    "Aceita qualquer posição oficial. As opções seguem a "
                    "ordem posicional da formação ativa."
                ),
            )


def _render_selecao_reservas(
    jogadores: Mapping[str, Mapping[str, Any]],
    tatica_ativa: str,
    layout_ativo: Mapping[str, SlotTatico],
    titulares: set[str],
) -> list[str]:
    migrar_reservas_legadas(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
        titulares,
    )
    reconciliacao = reconciliar_convocacao(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
    )
    ocupados = set(reconciliacao["ocupados"])

    st.markdown("---")
    st.markdown("## Definir reservas")
    st.caption(
        "As primeiras 11 vagas espelham a formação escolhida. "
        "As quatro vagas finais aceitam qualquer posição oficial."
    )

    itens_layout = [
        (indice, slot, configuracao)
        for indice, (slot, configuracao) in enumerate(layout_ativo.items())
    ]

    st.markdown("### Reservas por posição — 11 vagas")
    for inicio in range(0, len(itens_layout), 3):
        _render_linha_seletores_posicionais(
            itens_layout[inicio:inicio + 3],
            jogadores,
            tatica_ativa,
            ocupados,
        )

    prioridade = prioridade_posicoes_tatica(layout_ativo)
    tags: list[str] = []
    for configuracao in layout_ativo.values():
        if configuracao.tag not in tags:
            tags.append(configuracao.tag)

    st.markdown("### Vagas livres — 4 vagas")
    st.caption(
        "Ordem das opções: "
        + " → ".join(tags)
        + ". O desempate é feito pelo nome do atleta."
    )
    total_livres = quantidade_vagas_livres(len(layout_ativo))
    indices_livres = list(range(total_livres))
    for inicio in range(0, total_livres, 2):
        _render_linha_seletores_livres(
            indices_livres[inicio:inicio + 2],
            jogadores,
            tatica_ativa,
            prioridade,
            ocupados,
        )

    reconciliacao_final = reconciliar_convocacao(
        st.session_state,
        tatica_ativa,
        layout_ativo,
        jogadores,
    )
    return list(reconciliacao_final["reservas"])


def _render_metricas_convocacao(
    nomes_titulares: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_periodo: Mapping[str, Mapping[str, Any]],
) -> None:
    if not nomes_titulares:
        return
    resumo = calcular_resumo_convocados(
        nomes_titulares,
        jogadores,
        avaliacoes_periodo,
    )
    render_kpis(
        (
            KPI(
                "Capacidade atual",
                formatar_numero(resumo["capacidade_atual_media"]),
                "Média dos titulares avaliados",
                "destaque",
            ),
            KPI(
                "Potencial 2030",
                formatar_numero(resumo["potencial_2030_medio"]),
                "Média dos titulares avaliados",
            ),
            KPI(
                "Saldo projetado",
                formatar_numero(
                    resumo["saldo_projetado_medio"],
                    sinal=True,
                ),
                "Potencial menos capacidade",
                "positivo",
            ),
            KPI(
                "Cobertura",
                f'{resumo["com_avaliacao"]}/{resumo["selecionados"]}',
                (
                    f'{resumo["completos"]} com avaliação completa '
                    "de Vini e Beto"
                ),
                "informativo",
            ),
        ),
        titulo="Indicadores dos titulares",
        rotulo_aria="Indicadores esportivos dos titulares",
    )


def render_tela_campo(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    _render_cabecalho_projeto()
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    persistencia = sincronizar_persistencia_local(
        st.session_state,
        TATICAS,
        jogadores,
    )
    if not persistencia.pronta:
        st.caption("Restaurando a última convocação salva neste navegador…")
        return
    if st.session_state.pop(CHAVE_AVISO_RESTAURACAO, False):
        st.toast("Escalação restaurada deste navegador.")
    if not persistencia.disponivel:
        st.warning(
            "O navegador bloqueou o armazenamento local. A convocação será "
            "mantida somente enquanto esta sessão permanecer aberta."
        )

    col_config, col_campo = st.columns([1, 2], gap="large")

    with col_config:
        st.markdown(
            '<h2 class="convocation-builder-title">Monte a sua convocação</h2>',
            unsafe_allow_html=True,
        )
        tatica_ativa = st.selectbox(
            "Esquema tático:",
            list(TATICAS.keys()),
            key="tactical_selector",
        )
        layout_ativo = TATICAS[tatica_ativa]

        reconciliacao = reconciliar_convocacao(
            st.session_state,
            tatica_ativa,
            layout_ativo,
            jogadores,
        )
        ocupados = set(reconciliacao["ocupados"])

        if st.button("Limpar titulares e reservas", width="stretch"):
            limpar_convocacao(
                st.session_state,
                tatica_ativa,
                len(layout_ativo),
            )
            st.rerun()

        with st.expander("Persistência da escalação", expanded=False):
            st.caption(
                "Suas escolhas ficam salvas apenas neste navegador e "
                "dispositivo. Cada esquema tático mantém sua própria seleção."
            )
            if st.button(
                "Apagar escalações salvas neste navegador",
                width="stretch",
                key="apagar_convocacoes_locais",
            ):
                apagar_convocacoes_locais(
                    st.session_state,
                    TATICAS,
                )
                st.rerun()

        st.caption(
            "Cada campo começa vazio e aceita somente atletas compatíveis "
            "com as posições oficiais do projeto."
        )
        escalados: dict[str, str] = {}

        for indice, (slot, configuracao) in enumerate(layout_ativo.items()):
            chave = chave_titular(tatica_ativa, indice)
            valor_atual = st.session_state.get(chave)
            atual = valor_atual if isinstance(valor_atual, str) else None
            indisponiveis = ocupados - ({atual} if atual else set())
            disponiveis = opcoes_titular(
                jogadores,
                configuracao.posicoes,
                indisponiveis,
            )
            normalizar_escolha_titular(
                st.session_state,
                chave,
                disponiveis,
            )

            escolha = st.selectbox(
                f"{slot}:",
                disponiveis,
                index=None,
                placeholder="Digite para buscar um atleta",
                format_func=lambda nome, base=jogadores: (
                    formatar_jogador_com_posicao(nome, base)
                ),
                key=chave,
            )
            if escolha:
                escalados[slot] = escolha

    with col_campo:
        st.session_state.pop("tactical_view_mode", None)
        render_campo(
            layout_ativo,
            escalados,
            jogadores,
            avaliacoes_periodo,
        )
        render_legenda_adaptabilidade()

    titulares = set(escalados.values())
    reservas = _render_selecao_reservas(
        jogadores,
        tatica_ativa,
        layout_ativo,
        titulares,
    )

    resumo_texto = resumo_convocacao(len(escalados), len(reservas))
    st.markdown(
        f'<div class="sr-only" role="status" aria-live="polite" '
        f'aria-atomic="true">{_esc(resumo_texto)}</div>',
        unsafe_allow_html=True,
    )
    if convocacao_completa(len(escalados)):
        st.success(resumo_texto)
    else:
        st.info(resumo_texto)

    render_banco_reservas(reservas, jogadores)

    titulares_dados = [
        jogadores[nome]
        for slot, nome in escalados.items()
        if slot in layout_ativo and nome in jogadores
    ]
    reservas_dados = [
        jogadores[nome] for nome in reservas if nome in jogadores
    ]
    render_resumo_elenco(titulares_dados, reservas_dados)
    _render_metricas_convocacao(
        list(escalados.values()),
        jogadores,
        avaliacoes_periodo,
    )


def _valor_analista(
    registro: Mapping[str, Any],
    analista: str,
    campo: str,
) -> float | None:
    bloco = registro.get(analista)
    if not isinstance(bloco, Mapping):
        return None
    valor = bloco.get(campo)
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _render_resumo_avaliacao(
    metricas: Mapping[str, Any],
    registro: Mapping[str, Any],
) -> None:
    """Exibe situação, saldo e data sem truncamento em colunas estreitas."""
    situacao = formatar_status_avaliacao(metricas["status"])
    saldo = formatar_numero(metricas["saldo_projetado"], sinal=True)
    data_referencia = formatar_data_referencia(
        str(registro["data_referencia"])
    )
    st.markdown(
        '<section class="evaluation-meta-grid" '
        'aria-label="Resumo da avaliação trimestral">'
        '<article class="evaluation-meta-card evaluation-meta-card--status">'
        '<div class="evaluation-meta-label">Situação</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--status">'
        f'{_esc(situacao)}</div>'
        '</article>'
        '<article class="evaluation-meta-card" '
        'title="Média de potencial menos capacidade atual, calculada apenas '
        'para cada analista que preencheu o par completo.">'
        '<div class="evaluation-meta-label">Saldo projetado</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--numeric '
        f'evaluation-meta-emphasis">{_esc(saldo)}</div>'
        '</article>'
        '<article class="evaluation-meta-card">'
        '<div class="evaluation-meta-label">Data de referência</div>'
        f'<div class="evaluation-meta-value evaluation-meta-value--date">'
        f'{_esc(data_referencia)}</div>'
        '</article>'
        '</section>'
        '<div class="sr-only">'
        f'Situação da avaliação: {_esc(situacao)}. '
        f'Saldo projetado: {_esc(saldo)}. '
        f'Data de referência: {_esc(data_referencia)}.'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_avaliacao_trimestral(
    registro: Mapping[str, Any] | None,
    *,
    periodo: str,
) -> None:
    render_cabecalho_secao(
        formatar_periodo(periodo),
        rotulo="Avaliação trimestral",
    )
    if registro is None:
        st.info(
            "Não há avaliação registrada para este atleta no período "
            "selecionado."
        )
        return

    metricas = calcular_metricas_avaliacao(registro)
    if metricas["status"] == "Parcial":
        st.warning(
            "Avaliação parcial: pelo menos uma das quatro notas ainda não "
            "foi registrada neste período."
        )
    elif metricas["status"] == "Não avaliada":
        st.info(
            "O atleta está na base, mas ainda não recebeu notas neste período."
        )

    render_quadro_avaliacao_executivo(
        registro,
        rotulo_vini=NOME_CURTO_ANALISTA_VINI,
        rotulo_beto=NOME_CURTO_ANALISTA_BETO,
    )

    _render_resumo_avaliacao(metricas, registro)

    st.caption(
        "Posição no período: "
        f'{registro.get("posicao_snapshot", "Não informada")} · '
        "Clube no período: "
        f'{registro.get("clube_snapshot", "Não informado")}.'
    )

    observacao_vini = str(
        (registro.get("vini") or {}).get("observacao") or ""
    ).strip()
    observacao_beto = str(
        (registro.get("beto") or {}).get("observacao") or ""
    ).strip()
    st.markdown("### Observações do trimestre")
    col_vini, col_beto = st.columns(2, gap="large")
    with col_vini:
        st.markdown(f"**{NOME_ANALISTA_VINI}**")
        if observacao_vini:
            st.write(observacao_vini)
        else:
            st.caption("Nenhuma observação registrada por Vini.")
    with col_beto:
        st.markdown(f"**{NOME_ANALISTA_BETO}**")
        if observacao_beto:
            st.write(observacao_beto)
        else:
            st.caption("Nenhuma observação registrada por Beto.")


def _render_historico_atleta(
    base: BaseAvaliacoes,
    id_atleta: str,
) -> None:
    serie = historico_atleta(base, id_atleta)
    if len(serie) <= 1:
        st.caption(
            "O gráfico histórico será exibido quando existir mais de um "
            "trimestre avaliado para o atleta."
        )
        return

    df = pd.DataFrame(
        [
            {
                "Período": formatar_periodo(str(item["periodo"])),
                "Capacidade atual": item["capacidade_atual_media"],
                "Potencial 2030": item["potencial_2030_medio"],
            }
            for item in serie
        ]
    ).set_index("Período")
    render_cabecalho_secao("Histórico de avaliações")
    st.line_chart(df)


def render_tela_perfis(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    render_cabecalho(
        "Scout",
        (
            "Pesquise um atleta para consultar avaliação trimestral, "
            "contrato e valor de mercado."
        ),
    )
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    nomes = sorted(jogadores.keys(), key=str.casefold)
    selected_name = st.selectbox(
        "Buscar atleta por nome:",
        nomes,
        index=None,
        placeholder="Digite ou selecione o nome do atleta",
        format_func=lambda nome, base=jogadores: (
            formatar_jogador_com_posicao(nome, base)
        ),
        key="busca_perfil_atleta",
    )

    if selected_name is None:
        st.info(
            "Busque por nome e selecione um atleta para abrir a ficha individual."
        )
        return

    atleta = jogadores[selected_name]
    registro = avaliacoes_periodo.get(selected_name)
    st.markdown("---")
    col_perfil, col_dados = st.columns([1, 2], gap="large")

    with col_perfil:
        render_cartao_perfil(selected_name, atleta, registro)
        _render_avaliacao_trimestral(registro, periodo=periodo)

    with col_dados:
        with st.expander("Dados do jogador", expanded=True, type="compact"):
            render_dados_transfermarkt(atleta)

        render_cabecalho_secao("Valor de mercado")
        render_comparativo_mercado(atleta)

        _render_historico_atleta(
            base_avaliacoes,
            str(atleta.get("id_atleta") or ""),
        )



def _tipar_valores_mercado_roster(
    registros: Sequence[Mapping[str, Any]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Substitui rótulos monetários por números para ordenar e filtrar corretamente."""
    tipados: list[dict[str, Any]] = []
    for registro in registros:
        item = dict(registro)
        nome = str(item.get("Nome") or "").strip()
        atleta = jogadores.get(nome)

        if isinstance(atleta, Mapping):
            valor_atual = valor_mercado_atual(atleta)
            valor_pico = valor_mercado_maximo(atleta)
            item["Valor atual"] = valor_atual if valor_atual > 0 else None
            item["Pico de mercado"] = valor_pico if valor_pico > 0 else None
        else:
            item["Valor atual"] = None
            item["Pico de mercado"] = None

        tipados.append(item)
    return tipados


def render_tela_roster(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    render_cabecalho("Jogadores")
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    avaliacoes_periodo = _avaliacoes_por_nome(base_avaliacoes, periodo)

    filtro_1, filtro_2, filtro_3 = st.columns([2, 1, 1])
    busca = filtro_1.text_input(
        "Buscar por nome ou clube",
        placeholder="Ex.: Real Madrid ou Vini Jr",
    )
    posicao_filtro = filtro_2.selectbox(
        "Posição",
        ["Todas", *POSICOES_OFICIAIS],
    )
    grupos = sorted(
        {
            str(dados.get("grupo", GRUPO_OBSERVACAO))
            for dados in jogadores.values()
        }
    )
    grupo_filtro = filtro_3.selectbox("Grupo cadastral", ["Todos", *grupos])

    registros = construir_registros_roster(
        jogadores,
        avaliacoes_periodo,
        busca=busca,
        posicao=None if posicao_filtro == "Todas" else posicao_filtro,
        grupo=None if grupo_filtro == "Todos" else grupo_filtro,
    )
    registros = _tipar_valores_mercado_roster(registros, jogadores)

    st.caption(
        f"{len(registros)} atleta(s) exibido(s) de "
        f"{len(jogadores)} cadastrados."
    )
    if not registros:
        st.info(ROSTER_SEM_RESULTADOS)
        return

    render_tabela_executiva(
        registros,
        (
            ColunaTabelaExecutiva(
                "Nome",
                "Nome",
                largura="15%",
                fixada="left",
            ),
            ColunaTabelaExecutiva("Posição", "Posição"),
            ColunaTabelaExecutiva("Clube atual", "Clube atual"),
            ColunaTabelaExecutiva(
                f"Idade {ANO_BASE_DADOS}",
                f"Idade {ANO_BASE_DADOS}",
                formato="inteiro",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                f"Idade {ANO_COPA}",
                f"Idade {ANO_COPA}",
                formato="inteiro",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Capacidade atual",
                "Capacidade atual",
                formato="decimal_2",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Potencial 2030",
                "Potencial 2030",
                formato="decimal_2",
                alinhamento="centro",
                destaque=True,
            ),
            ColunaTabelaExecutiva(
                "Saldo projetado",
                "Saldo projetado",
                formato="sinal_2",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Situação",
                "Situação",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "Valor atual",
                "Valor atual",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "Pico de mercado",
                "Pico de mercado",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "% do pico de mercado",
                "% do pico",
                formato="percentual_1",
                alinhamento="direita",
                progresso=True,
            ),
        ),
        rotulo_aria="Tabela de jogadores monitorados",
        legenda="Jogadores, posições, avaliações e dados de mercado",
        chave=f"grade_roster_{periodo}",
        mostrar_barra=True,
        altura_maxima=600,
    )


def _tabela_ranking(
    itens: Sequence[Mapping[str, Any]],
    campo: str,
    rotulo: str,
    *,
    chave: str,
) -> None:
    if not itens:
        st.info("Sem avaliações completas para este recorte.")
        return

    registros = [
        {
            "Nome": item["nome"],
            "Posição": item["posicao_snapshot"],
            rotulo: item[campo],
        }
        for item in itens
    ]
    render_tabela_executiva(
        registros,
        (
            ColunaTabelaExecutiva(
                "Nome",
                "Nome",
                largura="46%",
                fixada="left",
            ),
            ColunaTabelaExecutiva("Posição", "Posição"),
            ColunaTabelaExecutiva(
                rotulo,
                rotulo,
                formato=(
                    "sinal_2"
                    if campo == "saldo_projetado"
                    else "decimal_2"
                ),
                alinhamento="centro",
                destaque=True,
            ),
        ),
        rotulo_aria=f"Ranking: {rotulo}",
        legenda=f"Ranking de atletas por {rotulo.casefold()}",
        chave=chave,
        mostrar_barra=False,
        altura_maxima=430,
    )


def render_tela_analise(
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    render_cabecalho(
        "Indicadores",
        "Visão consolidada das avaliações esportivas e dos dados de mercado do ciclo 2030.",
    )
    _render_contexto_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
        mostrar_estatisticas=False,
    )

    resumo = calcular_resumo_periodo(
        base_avaliacoes,
        periodo,
        total_atletas=len(jogadores),
    )
    render_kpis(
        (
            KPI("Atletas cadastrados", resumo["atletas_na_base"]),
            KPI(
                "Com alguma avaliação",
                resumo["com_alguma_avaliacao"],
                "Ao menos uma nota registrada",
                "informativo",
            ),
            KPI(
                "Avaliações completas",
                resumo["avaliacoes_completas"],
                "Quatro notas preenchidas",
                "destaque",
            ),
            KPI(
                "Cobertura completa",
                f'{resumo["cobertura_completa"]:.1%}',
                "Sobre todos os atletas cadastrados",
                "positivo",
            ),
        ),
        titulo="Cobertura das avaliações",
        rotulo_aria="Cobertura das avaliações no período",
    )
    render_kpis(
        (
            KPI(
                "Capacidade atual média",
                formatar_numero(resumo["capacidade_atual_media"]),
                "Escala de 0 a 10",
                "destaque",
            ),
            KPI(
                "Potencial médio 2030",
                formatar_numero(resumo["potencial_2030_medio"]),
                "Escala de 0 a 10",
            ),
            KPI(
                "Saldo projetado médio",
                formatar_numero(
                    resumo["saldo_projetado_medio"],
                    sinal=True,
                ),
                "Potencial menos capacidade atual",
                "positivo",
            ),
        ),
        titulo="Indicadores esportivos",
        rotulo_aria="Médias esportivas do período",
    )

    rankings = construir_rankings_periodo(
        base_avaliacoes,
        periodo,
    )
    render_cabecalho_secao(
        "Destaques com avaliação completa",
        "Rankings calculados somente com as quatro notas do período preenchidas.",
    )
    col_atual, col_potencial = st.columns(2, gap="large")
    with col_atual:
        st.markdown("### Maior capacidade atual")
        _tabela_ranking(
            rankings["maior_capacidade"],
            "capacidade_atual_media",
            "Capacidade atual",
            chave=f"grade_capacidade_atual_{periodo}",
        )
    with col_potencial:
        st.markdown("### Maior potencial 2030")
        _tabela_ranking(
            rankings["maior_potencial"],
            "potencial_2030_medio",
            "Potencial 2030",
            chave=f"grade_potencial_2030_{periodo}",
        )

    col_evolucao, col_regressao = st.columns(2, gap="large")
    with col_evolucao:
        st.markdown("### Maior evolução projetada")
        _tabela_ranking(
            rankings["maior_evolucao"],
            "saldo_projetado",
            "Saldo projetado",
            chave=f"grade_evolucao_{periodo}",
        )
    with col_regressao:
        st.markdown("### Maior regressão projetada")
        regressao = [
            item
            for item in rankings["maior_regressao"]
            if item.get("saldo_projetado") is not None
            and float(item["saldo_projetado"]) < 0
        ]
        _tabela_ranking(
            regressao,
            "saldo_projetado",
            "Saldo projetado",
            chave=f"grade_regressao_{periodo}",
        )

    with st.expander(
        f'Avaliações parciais ({len(rankings["parciais"])})',
        expanded=False,
    ):
        if rankings["parciais"]:
            render_tabela_executiva(
                [
                    {
                        "Nome": item["nome"],
                        "Posição": item["posicao_snapshot"],
                        "Situação": formatar_status_avaliacao(
                            item["status"]
                        ),
                    }
                    for item in rankings["parciais"]
                ],
                (
                    ColunaTabelaExecutiva(
                        "Nome",
                        "Nome",
                        largura="46%",
                        fixada="left",
                    ),
                    ColunaTabelaExecutiva("Posição", "Posição"),
                    ColunaTabelaExecutiva(
                        "Situação",
                        "Situação",
                        alinhamento="centro",
                        destaque=True,
                    ),
                ),
                rotulo_aria="Avaliações parciais do período",
                legenda="Atletas com avaliação trimestral parcial",
                chave=f"grade_avaliacoes_parciais_{periodo}",
                mostrar_barra=False,
                altura_maxima=360,
            )
        else:
            st.caption("Nenhuma avaliação parcial neste período.")

    with st.expander(
        f'Atletas ainda não avaliados ({len(rankings["nao_avaliados"])})',
        expanded=False,
    ):
        if rankings["nao_avaliados"]:
            st.write(
                ", ".join(
                    str(item["nome"])
                    for item in rankings["nao_avaliados"]
                )
            )
        else:
            st.caption("Todos os atletas possuem alguma avaliação.")

    st.markdown("---")
    render_cabecalho_secao(
        "Leitura de mercado",
        "Referência externa, separada da avaliação esportiva editorial.",
    )
    st.info(
        "As avaliações esportivas usam a data de referência "
        f'{formatar_data_referencia(resumo["data_referencia"])}. '
        "Os valores de mercado possuem datas próprias de atualização e "
        "não equivalem a avaliação de desempenho."
    )
    mercado = _adicionar_empresarios_mercado(
        construir_registros_mercado(jogadores),
        jogadores,
    )
    if not mercado:
        st.info(MERCADO_SEM_DADOS)
        return

    total_atual = sum(float(item["Atual (M€)"]) for item in mercado)
    total_pico = sum(
        float(item["Pico de mercado (M€)"])
        for item in mercado
    )
    render_kpis(
        (
            KPI(
                "Atletas com valor",
                len(mercado),
                "Cobertura disponível na fonte externa",
                "informativo",
            ),
            KPI(
                "Valor atual somado",
                formatar_valor_milhoes(total_atual),
                "Não equivale à avaliação esportiva",
                "destaque",
            ),
            KPI(
                "Pico de mercado somado",
                formatar_valor_milhoes(total_pico),
                "Maior valor registrado na carreira",
            ),
        ),
        titulo="Resumo de mercado",
        rotulo_aria="Resumo dos dados de mercado",
    )

    mercado_ordenado = sorted(
        mercado,
        key=lambda item: float(item["Atual (M€)"]),
        reverse=True,
    )
    render_tabela_executiva(
        mercado_ordenado,
        (
            ColunaTabelaExecutiva(
                "Nome",
                "Nome",
                largura="18%",
                fixada="left",
            ),
            ColunaTabelaExecutiva("Posição", "Posição"),
            ColunaTabelaExecutiva(
                "Empresário",
                "Empresário",
                largura="18%",
                min_largura=180,
            ),
            ColunaTabelaExecutiva(
                "Atual (M€)",
                "Valor atual",
                formato="moeda_milhoes",
                alinhamento="direita",
                destaque=True,
            ),
            ColunaTabelaExecutiva(
                "Pico de mercado (M€)",
                "Pico de mercado",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "% do pico de mercado",
                "% do pico",
                formato="percentual_1",
                alinhamento="direita",
                progresso=True,
            ),
            ColunaTabelaExecutiva(
                "Diferença para o pico de mercado (M€)",
                "Diferença para o pico",
                formato="moeda_milhoes",
                alinhamento="direita",
            ),
            ColunaTabelaExecutiva(
                "Atualização do mercado",
                "Atualização",
                formato="data",
                alinhamento="centro",
            ),
        ),
        rotulo_aria="Tabela consolidada de valor de mercado",
        legenda=(
            "Valores atuais, picos de carreira, empresários e datas de "
            "atualização dos atletas monitorados"
        ),
        chave="grade_mercado",
        mostrar_barra=True,
        altura_maxima=620,
    )


def render_feedback_sidebar() -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Radar do projeto")
    with st.sidebar.form("form_sugestao", clear_on_submit=True):
        tipo_sugestao = st.selectbox(
            "Tipo de sugestão:",
            TIPOS_SUGESTAO,
        )
        detalhes = st.text_area(
            "Mensagem:",
            placeholder=(
                "Descreva sua sugestão com o máximo de contexto possível."
            ),
        )
        enviar = st.form_submit_button("Preparar e-mail")

    if not enviar:
        return
    if not detalhes.strip():
        st.sidebar.warning(FEEDBACK_MENSAGEM_OBRIGATORIA)
        return

    assunto = urllib.parse.quote(
        f"{ASSUNTO_FEEDBACK_PREFIXO}: {tipo_sugestao}"
    )
    corpo = urllib.parse.quote(
        f"{SAUDACAO_FEEDBACK}\n\n{detalhes.strip()}"
    )
    mailto = (
        f"mailto:{EMAIL_FEEDBACK}?subject={assunto}&body={corpo}"
    )
    st.sidebar.markdown(
        f'<a href="{mailto}" class="feedback-link">Abrir e-mail</a>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(FEEDBACK_PREPARADO)


def render_tela(
    menu: str,
    jogadores: Mapping[str, Mapping[str, Any]],
    base_avaliacoes: BaseAvaliacoes,
    periodo: str,
) -> None:
    roteador = {
        MENU_CAMPO: render_tela_campo,
        MENU_PERFIS: render_tela_perfis,
        MENU_ROSTER: render_tela_roster,
        MENU_ANALISE: render_tela_analise,
    }
    tela = roteador.get(menu, render_tela_campo)
    tela(jogadores, base_avaliacoes, periodo)
