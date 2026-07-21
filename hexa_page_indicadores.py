"""Tela de indicadores editoriais e de mercado."""

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

__all__ = ['render_tela_analise']


def _esc(valor: Any, padrao: str = "") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


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
