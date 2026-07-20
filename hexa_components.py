"""Componentes visuais reutilizáveis do aplicativo."""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import streamlit as st

from hexa_avaliacoes import (
    calcular_metricas_avaliacao,
    formatar_numero,
    formatar_status_avaliacao,
)
from hexa_config import ANO_BASE_DADOS, ANO_COPA
from hexa_data import (
    extrair_altura_metros,
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_taticas import (
    ABREVIACOES,
    LIMITE_CONVOCADOS,
    LIMITE_RESERVAS,
    LIMITE_TITULARES,
    SlotTatico,
    indice_adaptabilidade,
)

__all__ = [
    "KPI",
    "calcular_resumo_elenco",
    "render_avaliacao_leitura",
    "render_banco_reservas",
    "render_cabecalho",
    "render_cabecalho_secao",
    "render_campo",
    "render_cartao_perfil",
    "render_comparativo_mercado",
    "render_dados_transfermarkt",
    "render_dossie",
    "render_kpis",
    "render_legenda_adaptabilidade",
    "render_lista_tatica",
    "render_resumo_elenco",
]


def _esc(valor: Any, padrao: str = "Não informado") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


TomKPI = Literal["neutro", "destaque", "positivo", "informativo"]


@dataclass(frozen=True, slots=True)
class KPI:
    """Indicador compacto, semântico e reutilizável."""

    rotulo: str
    valor: Any
    contexto: str | None = None
    tom: TomKPI = "neutro"


_TONS_KPI: frozenset[str] = frozenset(
    {"neutro", "destaque", "positivo", "informativo"}
)


def _adaptabilidade(indice: int) -> tuple[str, str]:
    if indice == 0:
        return "adapt-primary", "Função primária"
    if indice == 1:
        return "adapt-secondary", "Função secundária"
    if indice >= 2:
        return "adapt-tertiary", "Função alternativa"
    return "adapt-incompatible", "Compatibilidade não confirmada"


def render_cabecalho(titulo: str, subtitulo: str | None = None) -> None:
    """Renderiza o cabeçalho editorial principal de uma página."""
    subtitulo_html = (
        f'<p class="project-subtitle">{_esc(subtitulo)}</p>'
        if subtitulo
        else ""
    )
    st.markdown(
        '<header class="page-header">'
        f'<h1 class="app-title">{_esc(titulo)}</h1>'
        f"{subtitulo_html}"
        "</header>",
        unsafe_allow_html=True,
    )


def render_cabecalho_secao(
    titulo: str,
    subtitulo: str | None = None,
    *,
    rotulo: str | None = None,
    nivel: Literal[2, 3] = 2,
) -> None:
    """Cria uma hierarquia de seção consistente sem inflar títulos."""
    tag = "h2" if nivel == 2 else "h3"
    rotulo_html = (
        f'<p class="section-eyebrow">{_esc(rotulo)}</p>'
        if rotulo
        else ""
    )
    subtitulo_html = (
        f'<p class="section-subtitle">{_esc(subtitulo)}</p>'
        if subtitulo
        else ""
    )
    st.markdown(
        '<header class="section-header">'
        f"{rotulo_html}"
        f'<{tag} class="section-title section-title-{nivel}">{_esc(titulo)}</{tag}>'
        f"{subtitulo_html}"
        "</header>",
        unsafe_allow_html=True,
    )


def render_kpis(
    itens: Sequence[KPI],
    *,
    titulo: str | None = None,
    descricao: str | None = None,
    rotulo_aria: str = "Indicadores",
) -> None:
    """Renderiza KPIs compactos com leitura linear e sem dependência de ``st.metric``."""
    if not itens:
        return

    cabecalho = ""
    if titulo or descricao:
        titulo_html = (
            f'<h2 class="kpi-group-title">{_esc(titulo)}</h2>'
            if titulo
            else ""
        )
        descricao_html = (
            f'<p class="kpi-group-description">{_esc(descricao)}</p>'
            if descricao
            else ""
        )
        cabecalho = (
            '<header class="kpi-group-header">'
            f"{titulo_html}{descricao_html}"
            "</header>"
        )

    cards: list[str] = []
    for item in itens:
        tom = item.tom if item.tom in _TONS_KPI else "neutro"
        contexto_html = (
            f'<span class="kpi-context">{_esc(item.contexto)}</span>'
            if item.contexto
            else ""
        )
        cards.append(
            f'<article class="kpi-card kpi-{tom}" role="listitem">'
            f'<span class="kpi-label">{_esc(item.rotulo)}</span>'
            f'<strong class="kpi-value">{_esc(item.valor)}</strong>'
            f"{contexto_html}"
            "</article>"
        )

    st.markdown(
        '<section class="kpi-group" '
        f'aria-label="{_esc(rotulo_aria)}">'
        f"{cabecalho}"
        '<div class="kpi-grid" role="list">'
        f'{"".join(cards)}'
        "</div></section>",
        unsafe_allow_html=True,
    )


def render_campo(
    layout: Mapping[str, SlotTatico],
    escalados: Mapping[str, str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Renderiza o campo usando apenas a avaliação do período selecionado."""
    avaliacoes = avaliacoes_por_nome or {}
    cards: list[str] = []

    for slot, configuracao in layout.items():
        nome = escalados.get(slot)
        posicao_css = (
            f"left:{_esc(configuracao.left)};"
            f"bottom:{_esc(configuracao.bottom)};"
        )
        if not nome or nome not in jogadores:
            cards.append(
                f'<div class="player-node" style="{posicao_css}">'
                '<div class="player-card-pitch player-card-empty">'
                f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
                '<div class="player-name-tag">Selecionar atleta</div>'
                '<div class="player-empty-tag">Vaga aberta</div>'
                "</div></div>"
            )
            continue

        dados = jogadores[nome]
        indice = indice_adaptabilidade(dados, configuracao.posicoes)
        classe, descricao = _adaptabilidade(indice)
        avaliacao = avaliacoes.get(nome)
        metricas = (
            calcular_metricas_avaliacao(avaliacao)
            if avaliacao is not None
            else {
                "capacidade_atual_media": None,
                "potencial_2030_medio": None,
                "status": "Não avaliada",
            }
        )
        atual = formatar_numero(metricas["capacidade_atual_media"])
        potencial = formatar_numero(metricas["potencial_2030_medio"])
        situacao = formatar_status_avaliacao(metricas["status"])

        cards.append(
            f'<div class="player-node" style="{posicao_css}">'
            f'<div class="player-card-pitch {classe}">'
            f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
            f'<div class="player-name-tag" title="{_esc(nome)}">{_esc(nome)}</div>'
            f'<div class="player-rating-tag">Atual {atual} · Pot. {potencial}</div>'
            f'<span class="player-adaptability-tag">{_esc(descricao)} · '
            f'{_esc(situacao)}</span>'
            "</div></div>"
        )

    campo = (
        '<div class="pitch-container" role="region" tabindex="0" '
        'aria-label="Campo tático com titulares">'
        '<div class="pitch-line-center"></div>'
        '<div class="pitch-circle"></div>'
        '<div class="pitch-penalty-top"></div>'
        '<div class="pitch-penalty-bottom"></div>'
        f'{"".join(cards)}</div>'
    )
    st.markdown(campo, unsafe_allow_html=True)


def render_banco_reservas(
    reservas: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    st.markdown(f"## Banco selecionado ({len(reservas)}/{LIMITE_RESERVAS})")
    if not reservas:
        st.info(
            "Banco vazio. As vagas podem ser preenchidas gradualmente, "
            "sem impedir a montagem dos titulares."
        )
        return

    cards: list[str] = []
    for nome in reservas:
        dados = jogadores.get(nome, {})
        posicao = str(dados.get("posicao") or "Não informada")
        sigla = ABREVIACOES.get(posicao, "OBS")
        cards.append(
            '<div class="bench-card">'
            f'<div class="bench-number">{_esc(sigla)}</div>'
            f'<div class="bench-name">{_esc(nome)}</div>'
            f'<div class="bench-club">{_esc(dados.get("clube"))}</div>'
            "</div>"
        )

    st.markdown(
        '<div class="bench-box" tabindex="0" role="region" '
        'aria-label="Banco de reservas"><div class="bench-grid">'
        + "".join(cards)
        + "</div></div>",
        unsafe_allow_html=True,
    )


def calcular_resumo_elenco(
    elenco: Sequence[Mapping[str, Any]],
) -> dict[str, float | int]:
    idades = [
        int(jogador.get("idade", 0))
        for jogador in elenco
        if jogador.get("idade")
    ]
    alturas = [
        extrair_altura_metros(jogador.get("tm_altura"), 0.0)
        for jogador in elenco
    ]
    alturas_validas = [valor for valor in alturas if valor > 0]
    valores_atuais = [valor_mercado_atual(jogador) for jogador in elenco]
    valores_atuais_validos = [
        valor for valor in valores_atuais if valor > 0
    ]
    valores_maximos = [valor_mercado_maximo(jogador) for jogador in elenco]
    valores_maximos_validos = [
        valor for valor in valores_maximos if valor > 0
    ]

    return {
        "idade_2030": (
            sum(idades) / len(idades) + 4 if idades else 0.0
        ),
        "altura_media": (
            sum(alturas_validas) / len(alturas_validas)
            if alturas_validas
            else 0.0
        ),
        "valor_atual": sum(valores_atuais_validos),
        "valor_maximo": sum(valores_maximos_validos),
        "cobertura_mercado": len(valores_atuais_validos),
        "cobertura_altura": len(alturas_validas),
    }


def render_resumo_elenco(
    titulares: Sequence[Mapping[str, Any]],
    reservas: Sequence[Mapping[str, Any]],
) -> None:
    elenco = [*titulares, *reservas]
    if not elenco:
        st.info(
            "Preencha titulares ou reservas para gerar o raio-X cadastral "
            "e de mercado da convocação."
        )
        return

    resumo = calcular_resumo_elenco(elenco)
    atual = float(resumo["valor_atual"])
    maximo = float(resumo["valor_maximo"])
    percentual = atual / maximo * 100.0 if maximo > 0 else 0.0

    st.markdown(
        '<div class="summary-box"><div class="summary-grid">'
        '<div><div class="summary-label">Titulares</div>'
        f'<div class="summary-value">{len(titulares)}/{LIMITE_TITULARES}</div></div>'
        '<div><div class="summary-label">Reservas</div>'
        f'<div class="summary-value">{len(reservas)}/{LIMITE_RESERVAS}</div></div>'
        '<div><div class="summary-label">Convocados</div>'
        f'<div class="summary-value summary-highlight">{len(elenco)}/{LIMITE_CONVOCADOS}</div></div>'
        '<div><div class="summary-label">Idade média em 2030</div>'
        f'<div class="summary-value">{float(resumo["idade_2030"]):.1f}</div></div>'
        '<div><div class="summary-label">Valor atual</div>'
        f'<div class="summary-value summary-positive">{_esc(formatar_valor_milhoes(atual))}</div></div>'
        '<div><div class="summary-label">Atual / pico</div>'
        f'<div class="summary-value">{percentual:.0f}%</div></div>'
        "</div>"
        '<div class="summary-footnote">'
        f'Cobertura dos {len(elenco)} selecionados: mercado de '
        f'{int(resumo["cobertura_mercado"])}; altura de '
        f'{int(resumo["cobertura_altura"])}.'
        "</div></div>",
        unsafe_allow_html=True,
    )


def _idade_projetada_2030(dados: Mapping[str, Any]) -> str:
    try:
        idade_base = int(dados.get("idade") or 0)
    except (TypeError, ValueError):
        return "—"
    if idade_base <= 0:
        return "—"
    return str(idade_base + (ANO_COPA - ANO_BASE_DADOS))


def render_cartao_perfil(
    nome: str,
    dados: Mapping[str, Any],
    registro_avaliacao: Mapping[str, Any] | None = None,
) -> None:
    """Renderiza um card editorial inspirado em videogames, sem dados legados."""
    posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
    siglas: list[str] = []
    for posicao in posicoes:
        sigla = ABREVIACOES.get(str(posicao), "OBS")
        if sigla not in siglas:
            siglas.append(sigla)

    metricas = (
        calcular_metricas_avaliacao(registro_avaliacao)
        if registro_avaliacao is not None
        else {
            "capacidade_atual_media": None,
            "potencial_2030_medio": None,
            "status": "Não avaliada",
        }
    )
    capacidade = (
        "—"
        if metricas["capacidade_atual_media"] is None
        else formatar_numero(metricas["capacidade_atual_media"])
    )
    potencial = (
        "—"
        if metricas["potencial_2030_medio"] is None
        else formatar_numero(metricas["potencial_2030_medio"])
    )
    status = formatar_status_avaliacao(metricas.get("status"))
    clube = dados.get("clube") or "Não informado"
    idade_2030 = _idade_projetada_2030(dados)
    posicoes_curtas = " - ".join(siglas) if siglas else "OBS"

    st.markdown(
        '<article class="profile-card" '
        f'aria-label="Card do jogador {_esc(nome)}">'
        '<div class="profile-card-topline">'
        '<span class="profile-card-kicker">Ciclo 2030</span>'
        f'<span class="profile-evaluation-status">{_esc(status)}</span>'
        "</div>"
        '<div class="profile-card-identity">'
        f'<h2>{_esc(nome)}</h2>'
        f'<p class="profile-position-inline">{_esc(posicoes_curtas)}</p>'
        '<p class="profile-club">'
        '<span>Clube atual</span>'
        f'<strong>{_esc(clube)}</strong>'
        "</p>"
        "</div>"
        '<dl class="profile-game-stats">'
        '<div class="profile-game-stat">'
        '<dt>Capacidade atual</dt>'
        f'<dd>{_esc(capacidade)}</dd>'
        "</div>"
        '<div class="profile-game-stat">'
        '<dt>Potencial em 2030</dt>'
        f'<dd>{_esc(potencial)}</dd>'
        "</div>"
        '<div class="profile-game-stat">'
        '<dt>Idade em 2030</dt>'
        f'<dd>{_esc(idade_2030)}</dd>'
        "</div>"
        "</dl>"
        "</article>",
        unsafe_allow_html=True,
    )


def render_comparativo_mercado(dados: Mapping[str, Any]) -> None:
    """Exibe valor de mercado com hierarquia visual e metadados separados."""
    atual = valor_mercado_atual(dados)
    maximo = valor_mercado_maximo(dados)
    percentual = percentual_do_pico(dados)
    diferenca = max(maximo - atual, 0.0) if maximo > 0 else 0.0

    if atual <= 0 and maximo <= 0:
        st.info("Não há dados de mercado suficientes para este atleta.")
        return

    percentual_texto = (
        f"{percentual:.1f}%" if percentual is not None else "Sem base"
    )
    st.markdown(
        '<section class="market-card" '
        'aria-label="Resumo do valor de mercado">'
        '<dl class="market-grid">'
        '<div class="market-metric market-metric--primary">'
        '<dt class="market-label">Valor atual</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(atual))}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Pico de valor de mercado</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(maximo))}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Percentual do pico de mercado</dt>'
        f'<dd class="market-value">{_esc(percentual_texto)}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Diferença para o pico de mercado</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(diferenca))}</dd>'
        "</div>"
        "</dl>"
        '<dl class="market-dates">'
        '<div class="market-date-item">'
        '<dt>Data do pico de mercado</dt>'
        f'<dd>{_esc(dados.get("tm_data_valor_maximo"))}</dd>'
        "</div>"
        '<div class="market-date-item">'
        '<dt>Última atualização</dt>'
        f'<dd>{_esc(dados.get("tm_ultima_atualizacao"))}</dd>'
        "</div>"
        "</dl>"
        '<p class="market-card-info"><em>'
        "Valor de mercado é uma referência externa e não equivale à "
        "avaliação esportiva do projeto."
        "</em></p>"
        "</section>",
        unsafe_allow_html=True,
    )


def render_dados_transfermarkt(dados: Mapping[str, Any]) -> None:
    """Exibe os dados do jogador agrupados por contexto e omite campos vazios."""
    posicoes_externas = dados.get("tm_posicoes_secundarias_site")
    if isinstance(posicoes_externas, (list, tuple, set)):
        posicoes_externas = ", ".join(
            str(posicao).strip()
            for posicao in posicoes_externas
            if str(posicao).strip()
        )

    grupos = (
        (
            "Identificação",
            (
                ("Nome completo", dados.get("nome_completo") or dados.get("nome")),
                ("Nascimento", dados.get("tm_nascimento")),
                ("Naturalidade", dados.get("tm_naturalidade")),
                ("Altura", dados.get("tm_altura")),
                ("Pé preferencial", dados.get("tm_pe")),
            ),
            "",
        ),
        (
            "Vínculo profissional",
            (
                ("Empresário", dados.get("tm_empresario")),
                ("No clube desde", dados.get("tm_clube_desde")),
                ("Contrato até", dados.get("tm_contrato")),
                ("Opção de contrato", dados.get("tm_opcao_contrato")),
                ("Última renovação", dados.get("tm_ultima_renovacao")),
                ("Equipador", dados.get("tm_equipador")),
            ),
            "",
        ),
        (
            "Referência cadastral externa",
            (
                ("Posição na fonte externa", dados.get("tm_posicao_site")),
                ("Posições externas", posicoes_externas),
            ),
            " player-data-group--wide",
        ),
    )

    grupos_html: list[str] = []
    for titulo, campos, classe_extra in grupos:
        itens = [
            (rotulo, valor)
            for rotulo, valor in campos
            if valor not in (None, "", [], (), set())
        ]
        if not itens:
            continue

        definicoes = "".join(
            '<div class="player-data-item">'
            f'<dt class="player-data-term">{_esc(rotulo)}</dt>'
            f'<dd class="player-data-description">{_esc(valor)}</dd>'
            "</div>"
            for rotulo, valor in itens
        )
        grupos_html.append(
            f'<section class="player-data-group{classe_extra}">'
            f'<h3 class="player-data-group-title">{_esc(titulo)}</h3>'
            '<dl class="player-data-list">'
            f"{definicoes}</dl>"
            "</section>"
        )

    if not grupos_html:
        st.info("Não há dados do jogador disponíveis.")
        return

    st.markdown(
        '<section class="player-data-panel" '
        'aria-label="Dados do jogador">'
        '<div class="player-data-groups">'
        f'{"".join(grupos_html)}'
        "</div></section>",
        unsafe_allow_html=True,
    )


def render_legenda_adaptabilidade() -> None:
    st.markdown(
        '<div class="legend-box" aria-label="Legenda de adaptabilidade">'
        '<div class="legend-item"><span class="legend-dot legend-primary"></span>'
        "<strong>Função primária</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-secondary"></span>'
        "<strong>Função secundária</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-tertiary"></span>'
        "<strong>Função alternativa</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-empty"></span>'
        "<strong>Vaga aberta ou compatibilidade não confirmada</strong></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_lista_tatica(
    linhas: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    """Componente de compatibilidade para estruturas táticas já preparadas."""
    secoes: list[str] = []
    for linha, itens in linhas.items():
        cards: list[str] = []
        for item in itens:
            nome = str(item.get("nome") or "Selecionar atleta")
            preenchido = bool(item.get("preenchido"))
            indice = int(item.get("indice_adaptabilidade", -1))
            classe, status = (
                _adaptabilidade(indice)
                if preenchido
                else ("adapt-empty", "Vaga aberta")
            )
            atual = formatar_numero(item.get("capacidade_atual"))
            potencial = formatar_numero(item.get("potencial_2030"))
            situacao = formatar_status_avaliacao(
                item.get("situacao_avaliacao") or "Não avaliada"
            )
            cards.append(
                f'<li class="tactical-list-item {classe}">'
                '<div class="tactical-list-main">'
                f'<span class="tactical-list-tag">{_esc(item.get("tag"))}</span>'
                '<span class="tactical-list-copy">'
                f'<strong class="tactical-list-name">{_esc(nome)}</strong>'
                f'<span class="tactical-list-slot">{_esc(item.get("slot"))}</span>'
                "</span></div>"
                '<span class="tactical-list-meta">'
                f'<span class="tactical-list-status">{_esc(status)}</span>'
                f'<span class="tactical-list-ratings">Atual {atual} · '
                f'Pot. {potencial} · {_esc(situacao)}</span>'
                "</span></li>"
            )
        secoes.append(
            '<section class="tactical-list-section">'
            f'<h2 class="tactical-list-heading">{_esc(linha)}</h2>'
            f'<ul class="tactical-list-grid">{"".join(cards)}</ul>'
            "</section>"
        )

    st.markdown(
        '<div class="tactical-list" role="region" tabindex="0" '
        'aria-label="Escalação em lista">'
        f'{"".join(secoes)}</div>',
        unsafe_allow_html=True,
    )


def render_avaliacao_leitura(
    registro: Mapping[str, Any] | None,
) -> None:
    """Compatibilidade pública: exibe somente o contrato trimestral."""
    if registro is None:
        st.info("Não há avaliação registrada para o período selecionado.")
        return
    metricas = calcular_metricas_avaliacao(registro)
    st.write(
        {
            "capacidade_atual": metricas["capacidade_atual_media"],
            "potencial_2030": metricas["potencial_2030_medio"],
            "saldo_projetado": metricas["saldo_projetado"],
            "situacao": formatar_status_avaliacao(metricas["status"]),
        }
    )


def render_dossie(_: Mapping[str, Any]) -> None:
    """O dossiê legado foi desativado na RC5."""
    st.info(
        "O histórico editorial ativo passa a ser formado pelas observações "
        "trimestrais de Vini e Beto."
    )
