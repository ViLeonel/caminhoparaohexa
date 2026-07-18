"""Componentes visuais reutilizáveis do aplicativo."""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from typing import Any

import streamlit as st

from hexa_config import (
    ANO_BASE_DADOS,
    ANO_COPA,
    GRUPO_OBSERVACAO,
    GRUPO_RESERVAS,
    GRUPO_TITULARES,
    IDADE_PADRAO,
)
from hexa_messages import (
    DADOS_EXTERNOS_AUSENTES,
    DOSSIE_CAMPO_AUSENTE,
    MERCADO_ATLETA_AUSENTE,
    NAO_INFORMADO_FONTE,
    SEM_BASE_CALCULO,
    SEM_REGISTRO_EDITORIAL,
)
from hexa_data import (
    extrair_altura_metros,
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_taticas import ABREVIACOES, LIMITE_CONVOCADOS, LIMITE_RESERVAS, LIMITE_TITULARES, SlotTatico, indice_adaptabilidade


def _esc(valor: Any, padrao: str = NAO_INFORMADO_FONTE) -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


def _nota_texto(valor: Any) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return SEM_REGISTRO_EDITORIAL
    return f"{numero:.1f}".replace(".", ",") if numero > 0 else SEM_REGISTRO_EDITORIAL


def _classe_posicao(configuracao: SlotTatico) -> str:
    left = str(configuracao.left).replace("%", "").replace(".", "-")
    bottom = str(configuracao.bottom).replace("%", "").replace(".", "-")
    return f"pitch-pos-l{left}-b{bottom}"


def _classe_adaptabilidade(indice: int) -> tuple[str, str]:
    if indice == 0:
        return "adapt-primary", "Função primária"
    if indice == 1:
        return "adapt-secondary", "Função secundária"
    if indice >= 2:
        return "adapt-tertiary", "Função alternativa"
    return "adapt-incompatible", "Fora da função"


def _classe_progresso(percentual: float) -> str:
    valor = int(round(max(0.0, min(percentual, 100.0))))
    return f"progress-pct-{valor}"


def render_cabecalho(titulo: str, subtitulo: str) -> None:
    st.markdown(f'<h1 class="app-title">{_esc(titulo)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="project-subtitle">{_esc(subtitulo)}</p>', unsafe_allow_html=True)


def render_campo(
    layout: Mapping[str, SlotTatico],
    escalados: Mapping[str, str],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    cards: list[str] = []
    for slot, configuracao in layout.items():
        nome = escalados.get(slot)
        if not nome or nome not in jogadores:
            cards.append(
                f'<div class="player-node {_classe_posicao(configuracao)}">'
                '<div class="player-card-pitch player-card-empty">'
                f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
                '<div class="player-name-tag">Selecionar atleta</div>'
                '<div class="player-empty-tag">Vaga aberta</div>'
                '</div></div>'
            )
            continue

        dados = jogadores[nome]
        indice = indice_adaptabilidade(dados, configuracao.posicoes)
        classe_adaptabilidade, rotulo_adaptabilidade = _classe_adaptabilidade(indice)
        nota_vini = float(dados.get("nota_vini") or 0.0)
        nota_roberto = float(dados.get("nota_roberto") or 0.0)

        cards.append(
            f'<div class="player-node {_classe_posicao(configuracao)}">'
            f'<div class="player-card-pitch {classe_adaptabilidade}">'
            f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
            f'<div class="player-name-tag" title="{_esc(dados.get("nome", nome))}">{_esc(dados.get("nome", nome))}</div>'
            f'<div class="player-rating-tag">★ {nota_vini:.1f} / {nota_roberto:.1f}</div>'\
            f'<div class="player-adaptability-tag">{_esc(rotulo_adaptabilidade)}</div>'
            '</div></div>'
        )

    campo = (
        '<div class="pitch-container">'
        '<div class="pitch-line-center"></div>'
        '<div class="pitch-circle"></div>'
        '<div class="pitch-penalty-top"></div>'
        '<div class="pitch-penalty-bottom"></div>'
        f'{"".join(cards)}'
        '</div>'
    )
    st.markdown(campo, unsafe_allow_html=True)


def render_legenda_adaptabilidade() -> None:
    st.markdown(
        """
        <div class="legend-box">
            <div class="legend-item"><span class="legend-dot legend-primary"></span><b>Primária:</b> posição principal</div>
            <div class="legend-item"><span class="legend-dot legend-secondary"></span><b>Secundária:</b> segunda função</div>
            <div class="legend-item"><span class="legend-dot legend-tertiary"></span><b>Alternativa:</b> terceira função ou posterior</div>
            <div class="legend-item"><span class="legend-dot legend-empty"></span><b>Vaga aberta:</b> atleta não selecionado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_lista_tatica(
    linhas: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    """Renderiza a formação em lista compacta e acessível."""
    secoes: list[str] = []
    for linha, itens in linhas.items():
        cards: list[str] = []
        for item in itens:
            preenchido = bool(item.get("preenchido"))
            indice = int(item.get("indice_adaptabilidade", -1))
            classe_adaptabilidade, rotulo_adaptabilidade = _classe_adaptabilidade(indice)
            nome = item.get("nome") if preenchido else "Selecionar atleta"
            estado = rotulo_adaptabilidade if preenchido else "Vaga aberta"
            classe_estado = classe_adaptabilidade if preenchido else "adapt-empty"

            nota_vini = item.get("nota_vini")
            nota_roberto = item.get("nota_roberto")
            notas = ""
            if preenchido:
                try:
                    notas = (
                        '<span class="tactical-list-ratings">'
                        f'Vini {float(nota_vini or 0):.1f} · Roberto {float(nota_roberto or 0):.1f}'
                        '</span>'
                    )
                except (TypeError, ValueError):
                    notas = ""

            cards.append(
                f'<li class="tactical-list-item {classe_estado}">'
                '<div class="tactical-list-main">'
                f'<span class="tactical-list-tag">{_esc(item.get("tag"))}</span>'
                '<div class="tactical-list-copy">'
                f'<span class="tactical-list-slot">{_esc(item.get("slot"))}</span>'
                f'<strong class="tactical-list-name">{_esc(nome)}</strong>'
                '</div>'
                '</div>'
                '<div class="tactical-list-meta">'
                f'{notas}'
                f'<span class="tactical-list-status">{_esc(estado)}</span>'
                '</div>'
                '</li>'
            )

        secoes.append(
            '<section class="tactical-list-section">'
            f'<h3 class="tactical-list-heading">{_esc(linha)}</h3>'
            f'<ul class="tactical-list-grid">{"".join(cards)}</ul>'
            '</section>'
        )

    st.markdown(
        '<div class="tactical-list" aria-label="Formação tática em lista">'
        + "".join(secoes)
        + '</div>',
        unsafe_allow_html=True,
    )

def render_banco_reservas(
    reservas: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    st.markdown(f"### Banco de reservas ({len(reservas)}/{LIMITE_RESERVAS})")
    if not reservas:
        st.info("Banco vazio. Selecione até 15 reservas; isso não impede continuar montando os titulares.")
        return

    cards: list[str] = []
    for nome in reservas:
        dados = jogadores.get(nome, {})
        posicao = str(dados.get("posicao") or NAO_INFORMADO_FONTE)
        sigla = ABREVIACOES.get(posicao, "OBS")
        cards.append(
            '<div class="bench-card">'
            f'<div class="bench-number">{_esc(sigla)}</div>'
            f'<div class="bench-name">{_esc(nome)}</div>'
            f'<div class="bench-club">{_esc(dados.get("clube"))}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="bench-box"><div class="bench-grid">'
        + ''.join(cards)
        + '</div></div>',
        unsafe_allow_html=True,
    )


def calcular_resumo_elenco(elenco: Sequence[Mapping[str, Any]]) -> dict[str, float | int]:
    idades = [int(j.get("idade", 0)) for j in elenco if j.get("idade")]
    alturas = [extrair_altura_metros(j.get("tm_altura"), 0.0) for j in elenco]
    alturas_validas = [valor for valor in alturas if valor > 0]
    valores_atuais = [valor_mercado_atual(j) for j in elenco]
    valores_atuais_validos = [valor for valor in valores_atuais if valor > 0]
    valores_maximos = [valor_mercado_maximo(j) for j in elenco]
    valores_maximos_validos = [valor for valor in valores_maximos if valor > 0]

    return {
        "idade_copa": (sum(idades) / len(idades) + (ANO_COPA - ANO_BASE_DADOS)) if idades else 0.0,
        "altura_media": sum(alturas_validas) / len(alturas_validas) if alturas_validas else 0.0,
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
        st.info("O raio-X aparecerá após a seleção de pelo menos um atleta. Titulares e reservas podem ser preenchidos gradualmente.")
        return

    resumo = calcular_resumo_elenco(elenco)
    atual = float(resumo["valor_atual"])
    maximo = float(resumo["valor_maximo"])
    percentual = (atual / maximo * 100.0) if maximo > 0 else 0.0

    st.markdown(
        f"""
        <div class="summary-box">
            <div class="summary-grid">
                <div><div class="summary-label">{_esc(GRUPO_TITULARES)}</div><div class="summary-value">{len(titulares)}/{LIMITE_TITULARES}</div></div>
                <div><div class="summary-label">{_esc(GRUPO_RESERVAS)}</div><div class="summary-value">{len(reservas)}/{LIMITE_RESERVAS}</div></div>
                <div><div class="summary-label">Convocados</div><div class="summary-value summary-highlight">{len(elenco)}/{LIMITE_CONVOCADOS}</div></div>
                <div><div class="summary-label">Idade média em {ANO_COPA}</div><div class="summary-value">{resumo['idade_copa']:.1f}</div></div>
                <div><div class="summary-label">Valor atual</div><div class="summary-value summary-positive">{formatar_valor_milhoes(atual)}</div></div>
                <div><div class="summary-label">Atual / pico</div><div class="summary-value">{percentual:.0f}%</div></div>
            </div>
            <div class="summary-footnote">
                Cobertura dos {len(elenco)} selecionados: mercado de {int(resumo['cobertura_mercado'])}; altura de {int(resumo['cobertura_altura'])}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cartao_perfil(nome: str, dados: Mapping[str, Any]) -> None:
    posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
    siglas: list[str] = []
    for posicao in posicoes:
        sigla = ABREVIACOES.get(str(posicao), "OBS")
        if sigla not in siglas:
            siglas.append(sigla)

    st.markdown(
        f"""
        <div class="profile-card">
            <h2>{_esc(dados.get('nome', nome))}</h2>
            <div class="profile-details">
                <b>Posições do projeto:</b> {_esc(' / '.join(siglas))}<br>
                <b>Nome completo:</b> {_esc(dados.get('nome_completo', dados.get('nome', nome)))}<br>
                <b>Clube atual:</b> {_esc(dados.get('clube'))}<br>
                <b>Grupo:</b> {_esc(dados.get('grupo'))}<br>
                <b>Idade em {ANO_BASE_DADOS}:</b> {int(dados.get('idade', IDADE_PADRAO))} anos<br>
                <b>Idade em {ANO_COPA}:</b> <span class="profile-highlight">{int(dados.get('idade', IDADE_PADRAO)) + (ANO_COPA - ANO_BASE_DADOS)} anos</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_avaliacao_leitura(dados: Mapping[str, Any]) -> None:
    nota_vini = float(dados.get("nota_vini") or 0.0)
    nota_roberto = float(dados.get("nota_roberto") or 0.0)
    notas_validas = [nota for nota in (nota_vini, nota_roberto) if nota > 0]
    media = sum(notas_validas) / len(notas_validas) if notas_validas else 0.0

    st.markdown(
        f"""
        <div class="rating-box">
            <div class="rating-grid">
                <div class="rating-card"><div class="rating-label">Vini</div><div class="rating-value">{_nota_texto(nota_vini)}</div></div>
                <div class="rating-card"><div class="rating-label">Roberto</div><div class="rating-value">{_nota_texto(nota_roberto)}</div></div>
                <div class="rating-card"><div class="rating-label">Média</div><div class="rating-value rating-gold">{_nota_texto(media)}</div></div>
            </div>
            <div class="rating-note">Registro editorial somente para leitura.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dados_transfermarkt(dados: Mapping[str, Any]) -> None:
    if not any(chave.startswith("tm_") for chave in dados):
        st.info(DADOS_EXTERNOS_AUSENTES)
        return

    nacionalidades = dados.get("tm_nacionalidades") or []
    if isinstance(nacionalidades, str):
        nacionalidades = [nacionalidades]
    posicoes_site = dados.get("tm_posicoes_secundarias_site") or []
    if isinstance(posicoes_site, str):
        posicoes_site = [posicoes_site]

    linhas = [
        f"<b>Nome completo:</b> {_esc(dados.get('nome_completo', dados.get('nome')))}",
        f"<b>Clube atual:</b> {_esc(dados.get('clube'))}",
        f"<b>Nascimento:</b> {_esc(dados.get('tm_nascimento'))} &nbsp; | &nbsp; <b>Naturalidade:</b> {_esc(dados.get('tm_naturalidade'))}",
        f"<b>Altura:</b> {_esc(dados.get('tm_altura'))} &nbsp; | &nbsp; <b>Pé:</b> {_esc(dados.get('tm_pe'))}",
        f"<b>Nacionalidades:</b> {_esc(', '.join(nacionalidades) if nacionalidades else NAO_INFORMADO_FONTE)}",
        f"<b>Agente:</b> {_esc(dados.get('tm_empresario'))}",
        f"<b>No clube desde:</b> {_esc(dados.get('tm_clube_desde'))} &nbsp; | &nbsp; <b>Contrato:</b> {_esc(dados.get('tm_contrato'))}",
    ]
    if dados.get("tm_opcao_contrato"):
        linhas.append(f"<b>Opção contratual:</b> {_esc(dados.get('tm_opcao_contrato'))}")
    if dados.get("tm_ultima_renovacao"):
        linhas.append(f"<b>Última renovação:</b> {_esc(dados.get('tm_ultima_renovacao'))}")
    if dados.get("tm_observacao_transferencia"):
        linhas.append(
            f"<b>Observação de transferência:</b> {_esc(dados.get('tm_observacao_transferencia'))}"
        )
    if dados.get("tm_clube_imagem"):
        linhas.append(
            f"<b>Clube exibido na imagem:</b> {_esc(dados.get('tm_clube_imagem'))}"
            f" &nbsp; | &nbsp; <b>Contrato exibido:</b> {_esc(dados.get('tm_contrato_imagem'))}"
        )
    if dados.get("tm_equipador"):
        linhas.append(f"<b>Equipador:</b> {_esc(dados.get('tm_equipador'))}")
    linhas.append(
        f"<b>Posição no site externo:</b> {_esc(dados.get('tm_posicao_site'))}"
        + (f" ({_esc(', '.join(posicoes_site))})" if posicoes_site else "")
    )
    if dados.get("tm_altura_metros"):
        linhas.append(f"<b>Altura normalizada:</b> {_esc(f'{float(dados["tm_altura_metros"]):.2f} m'.replace('.', ','))}")
    if dados.get("tm_fonte") or dados.get("tm_extraido_em"):
        linhas.append(
            f"<b>Origem do registro:</b> {_esc(dados.get('tm_fonte'))}"
            f" &nbsp; | &nbsp; <b>Extraído em:</b> {_esc(dados.get('tm_extraido_em'))}"
        )

    st.markdown(
        '<div class="market-card market-card-info">'
        + '<div class="market-details">'
        + '<br>'.join(linhas)
        + '</div></div>',
        unsafe_allow_html=True,
    )


def render_comparativo_mercado(dados: Mapping[str, Any]) -> None:
    atual = valor_mercado_atual(dados)
    maximo = valor_mercado_maximo(dados)
    percentual = percentual_do_pico(dados)
    diferenca = maximo - atual if maximo > 0 and atual > 0 else None

    if atual <= 0 and maximo <= 0:
        st.info(MERCADO_ATLETA_AUSENTE)
        return

    percentual_exibido = percentual or 0.0
    st.markdown(
        f"""
        <div class="market-card">
            <div class="market-grid">
                <div><div class="market-label">Valor atual</div><div class="market-value green">{formatar_valor_milhoes(atual)}</div></div>
                <div><div class="market-label">Maior valor da carreira</div><div class="market-value gold">{formatar_valor_milhoes(maximo)}</div></div>
                <div><div class="market-label">Distância do pico</div><div class="market-value">{formatar_valor_milhoes(diferenca) if diferenca is not None else SEM_BASE_CALCULO}</div></div>
            </div>
            <div class="market-label">Valor atual equivale a {percentual_exibido:.0f}% do pico de carreira</div>
            <div class="progress-track" role="progressbar" aria-label="Percentual do pico de mercado" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{max(0, min(percentual_exibido, 100)):.0f}"><div class="progress-fill {_classe_progresso(percentual_exibido)}"></div></div>
            <div class="market-dates">
                <span>Pico registrado em {_esc(dados.get('tm_data_valor_maximo'))}</span>
                <span>Última atualização: {_esc(dados.get('tm_ultima_atualizacao'))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dossie(dados: Mapping[str, Any]) -> None:
    blocos = (
        ("Pontos fortes", dados.get("pontos_fortes"), "stat-positive"),
        ("Desafios e pontos fracos", dados.get("pontos_fracos"), "stat-negative"),
        ("Histórico das discussões", dados.get("historico"), "stat-info"),
    )
    for titulo, conteudo, classe in blocos:
        texto = conteudo or DOSSIE_CAMPO_AUSENTE
        st.markdown(
            f'<div class="stat-box {classe}"><strong>{_esc(titulo)}:</strong><br>{_esc(texto)}</div>',
            unsafe_allow_html=True,
        )
