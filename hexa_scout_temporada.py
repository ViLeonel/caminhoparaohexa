"""Seções sazonais da ficha individual: agenda e estatísticas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any

import streamlit as st

from hexa_components import (
    ColunaTabelaExecutiva,
    render_cabecalho_secao,
    render_tabela_executiva,
)
from hexa_dados_esportivos import (
    DocumentoEsportivoError,
    carregar_documento_anual,
    carregar_proximos_jogos,
    carregar_totais_atleta,
    listar_anos_disponiveis,
)

__all__ = ["render_dados_sazonais_atleta"]


_CATEGORIAS: tuple[
    tuple[str, tuple[tuple[str, str, str], ...]],
    ...,
] = (
    (
        "Participação",
        (
            ("jogos", "Jogos", "inteiro"),
            ("minutos", "Minutos", "inteiro"),
            ("titular", "Titular", "inteiro"),
        ),
    ),
    (
        "Ataque",
        (
            ("gols", "Gols", "inteiro"),
            ("assistencias", "Assistências", "inteiro"),
            ("chutes", "Chutes", "inteiro"),
            ("chutes_no_alvo", "Chutes no alvo", "inteiro"),
        ),
    ),
    (
        "Passe",
        (
            ("passes", "Passes", "inteiro"),
            ("passes_certos_percentual", "Passes certos", "percentual_1"),
            ("passes_chave", "Passes-chave", "inteiro"),
        ),
    ),
    (
        "Drible",
        (("dribles", "Dribles", "inteiro"),),
    ),
    (
        "Defesa",
        (
            ("desarmes", "Desarmes", "inteiro"),
            ("interceptacoes", "Interceptações", "inteiro"),
            ("cabeceios_ganhos", "Cabeceios ganhos", "inteiro"),
            ("erros", "Erros", "inteiro"),
            ("erros_geraram_gol", "Erros que geraram gol", "inteiro"),
        ),
    ),
    (
        "Disciplina",
        (
            ("cartoes_amarelos", "Cartões amarelos", "inteiro"),
            ("cartoes_vermelhos", "Cartões vermelhos", "inteiro"),
        ),
    ),
)

_ROTULOS_AMBITO: dict[str, str] = {
    "clube": "Clube",
    "selecao": "Seleção",
    "combinado": "Clube + Seleção",
}


def _formatar_data_iso(valor: Any) -> str:
    texto = str(valor or "").strip()[:10]
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return texto or "Data não informada"


def _formatar_carimbo(valor: Any) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return "Não informada"
    try:
        normalizado = texto.replace("Z", "+00:00")
        return datetime.fromisoformat(normalizado).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return texto


def _render_proximos_jogos(
    *,
    jogador: Mapping[str, Any],
    calendarios_dir: Path,
    hoje: date | None = None,
) -> None:
    render_cabecalho_secao(
        "Próximos jogos",
        (
            "Três próximas partidas oficiais em que o atleta pode atuar, "
            "conforme os calendários cadastrados."
        ),
    )
    try:
        jogos = carregar_proximos_jogos(
            jogador=jogador,
            diretorio=calendarios_dir,
            hoje=hoje,
            limite=3,
        )
    except DocumentoEsportivoError as erro:
        st.warning(str(erro))
        return

    if not jogos:
        st.info(
            "Ainda não há jogos futuros cadastrados para o clube atual ou "
            "para a Seleção Brasileira."
        )
        return

    registros = [
        {
            "Data": _formatar_data_iso(jogo.get("data")),
            "Competição": str(jogo.get("competicao") or "Não informada"),
            "Confronto": str(jogo.get("confronto") or "Não informado"),
        }
        for jogo in jogos
    ]
    render_tabela_executiva(
        registros,
        (
            ColunaTabelaExecutiva(
                "Data",
                "Data",
                formato="texto",
                fixada="left",
                largura=128,
            ),
            ColunaTabelaExecutiva(
                "Competição",
                "Competição",
                formato="texto",
                min_largura=180,
            ),
            ColunaTabelaExecutiva(
                "Confronto",
                "Confronto",
                formato="texto",
                min_largura=260,
            ),
        ),
        rotulo_aria="Próximos jogos possíveis do atleta",
        chave="scout_proximos_jogos",
        interativa=False,
        mostrar_barra=False,
        altura_maxima=260,
    )


def _registros_por_ambito(
    totais: Mapping[str, Mapping[str, Any]],
    campos: Sequence[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    registros: list[dict[str, Any]] = []
    for ambito in ("clube", "selecao", "combinado"):
        total = totais.get(ambito)
        if total is None:
            continue
        linha: dict[str, Any] = {"ambito": _ROTULOS_AMBITO[ambito]}
        for chave, _, _ in campos:
            linha[chave] = total.get(chave)
        registros.append(linha)
    return registros


def _render_categoria(
    *,
    temporada: int,
    nome_categoria: str,
    campos: Sequence[tuple[str, str, str]],
    totais: Mapping[str, Mapping[str, Any]],
) -> None:
    registros = _registros_por_ambito(totais, campos)
    if not registros:
        st.info(
            f"Não há indicadores de {nome_categoria.casefold()} para "
            f"a temporada {temporada}."
        )
        return

    colunas = [
        ColunaTabelaExecutiva(
            "ambito",
            "Origem",
            formato="texto",
            fixada="left",
            min_largura=150,
        )
    ]
    for chave, rotulo, formato in campos:
        colunas.append(
            ColunaTabelaExecutiva(
                chave,
                rotulo,
                formato=formato,
                alinhamento="direita",
                min_largura=128,
            )
        )

    render_tabela_executiva(
        registros,
        tuple(colunas),
        rotulo_aria=(
            f"Estatísticas de {nome_categoria} na temporada {temporada}"
        ),
        chave=f"scout_estatisticas_{temporada}_{nome_categoria.casefold()}",
        interativa=False,
        mostrar_barra=False,
        altura_maxima=260,
    )


def _render_estatisticas(
    *,
    jogador: Mapping[str, Any],
    temporadas_dir: Path,
) -> None:
    render_cabecalho_secao(
        "Estatísticas por temporada",
        (
            "Dados objetivos de clube, Seleção e total combinado. "
            "Selecione uma temporada para consultar os indicadores essenciais."
        ),
    )
    anos = listar_anos_disponiveis(temporadas_dir, "temporada")
    if not anos:
        st.info(
            "Ainda não há temporadas estatísticas publicadas para consulta."
        )
        return

    temporada = st.selectbox(
        "Temporada",
        anos,
        index=0,
        key="scout_temporada_estatistica",
        help="As temporadas anteriores permanecem disponíveis no histórico.",
    )
    id_atleta = str(jogador.get("id_atleta") or "").strip()
    if not id_atleta:
        st.info(
            "Este atleta ainda não possui identificador estável para "
            "associação estatística."
        )
        return

    try:
        totais = carregar_totais_atleta(
            diretorio=temporadas_dir,
            temporada=int(temporada),
            id_atleta=id_atleta,
        )
        documento = carregar_documento_anual(
            temporadas_dir,
            "temporada",
            int(temporada),
        )
    except DocumentoEsportivoError as erro:
        st.warning(str(erro))
        return

    if not totais:
        st.info(
            f"Não há estatísticas cadastradas para este atleta em {temporada}."
        )
        return

    if documento:
        st.caption(
            "Fonte: "
            f"{documento.get('fonte_atual') or 'Não informada'} · "
            "Atualização: "
            f"{_formatar_carimbo(documento.get('atualizado_em_utc'))}"
        )

    abas = st.tabs([nome for nome, _ in _CATEGORIAS])
    for aba, (nome, campos) in zip(abas, _CATEGORIAS):
        with aba:
            _render_categoria(
                temporada=int(temporada),
                nome_categoria=nome,
                campos=campos,
                totais=totais,
            )


def render_dados_sazonais_atleta(
    *,
    jogador: Mapping[str, Any],
    temporadas_dir: Path,
    calendarios_dir: Path,
    hoje: date | None = None,
) -> None:
    """Renderiza somente dados sazonais disponíveis, sem alterar fontes."""
    _render_proximos_jogos(
        jogador=jogador,
        calendarios_dir=calendarios_dir,
        hoje=hoje,
    )
    _render_estatisticas(
        jogador=jogador,
        temporadas_dir=temporadas_dir,
    )
