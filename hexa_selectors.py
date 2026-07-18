"""Seletores e transformações puras para as telas do aplicativo."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from hexa_config import ANO_BASE_DADOS, ANO_COPA, LIMITE_DESTAQUES_ANALISE
from hexa_messages import NAO_INFORMADO_FONTE
from hexa_taticas import SlotTatico, indice_adaptabilidade
from hexa_data import (
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)



def _texto_apresentacao(valor: Any) -> str:
    """Converte valores ausentes ou sentinelas legadas em texto claro para a interface."""
    if valor in (None, "", [], "N/A"):
        return NAO_INFORMADO_FONTE
    return str(valor)


def _numero_positivo(valor: Any) -> float | None:
    """Converte uma nota em número positivo ou retorna ``None``."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


def filtrar_jogadores(
    jogadores: Mapping[str, Mapping[str, Any]],
    busca: str = "",
    posicao: str | None = None,
    grupo: str | None = None,
) -> list[tuple[str, Mapping[str, Any]]]:
    """Filtra atletas por texto, posição oficial e grupo editorial."""
    termo = busca.strip().casefold()
    resultado: list[tuple[str, Mapping[str, Any]]] = []

    for nome, dados in jogadores.items():
        texto_busca = " ".join(
            str(valor or "")
            for valor in (
                nome,
                dados.get("nome_completo"),
                dados.get("clube"),
                dados.get("posicao"),
            )
        ).casefold()
        if termo and termo not in texto_busca:
            continue

        posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
        if posicao and posicao not in posicoes:
            continue
        if grupo and dados.get("grupo") != grupo:
            continue
        resultado.append((nome, dados))

    return sorted(resultado, key=lambda item: item[0].casefold())


def construir_registros_roster(
    jogadores: Mapping[str, Mapping[str, Any]],
    busca: str = "",
    posicao: str | None = None,
    grupo: str | None = None,
    ano_base: int = ANO_BASE_DADOS,
    ano_copa: int = ANO_COPA,
) -> list[dict[str, Any]]:
    """Monta linhas de exibição do roster sem depender de pandas ou Streamlit."""
    diferenca_anos = ano_copa - ano_base
    registros: list[dict[str, Any]] = []

    for nome, dados in filtrar_jogadores(jogadores, busca, posicao, grupo):
        try:
            idade = int(dados.get("idade") or 0)
        except (TypeError, ValueError):
            idade = 0

        atual = valor_mercado_atual(dados)
        maximo = valor_mercado_maximo(dados)
        registros.append(
            {
                "Nome": nome,
                "Posição": _texto_apresentacao(dados.get("posicao")),
                "Grupo": _texto_apresentacao(dados.get("grupo")),
                "Clube": _texto_apresentacao(dados.get("clube")),
                f"Idade {ano_base}": idade,
                f"Idade {ano_copa}": idade + diferenca_anos if idade > 0 else 0,
                "Vini": float(dados.get("nota_vini") or 0.0),
                "Roberto": float(dados.get("nota_roberto") or 0.0),
                "Valor atual": formatar_valor_milhoes(atual),
                "Pico": formatar_valor_milhoes(maximo),
                "% do pico": round(percentual_do_pico(dados) or 0.0, 1),
            }
        )
    return registros


def construir_avaliacoes(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Retorna atletas que possuem as duas notas editoriais preenchidas."""
    avaliados: list[dict[str, Any]] = []
    for nome, dados in jogadores.items():
        nota_vini = _numero_positivo(dados.get("nota_vini"))
        nota_roberto = _numero_positivo(dados.get("nota_roberto"))
        if nota_vini is None or nota_roberto is None:
            continue
        avaliados.append(
            {
                "Nome": nome,
                "Posição": _texto_apresentacao(dados.get("posicao")),
                "Vini": nota_vini,
                "Roberto": nota_roberto,
                "Diferença": abs(nota_vini - nota_roberto),
                "Média": (nota_vini + nota_roberto) / 2,
            }
        )
    return avaliados


def construir_registros_mercado(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Monta linhas comparativas de valor atual e pico de mercado."""
    mercado: list[dict[str, Any]] = []
    for nome, dados in jogadores.items():
        atual = valor_mercado_atual(dados)
        maximo = valor_mercado_maximo(dados)
        if atual <= 0:
            continue
        mercado.append(
            {
                "Nome": nome,
                "Posição": _texto_apresentacao(dados.get("posicao")),
                "Atual (M€)": atual,
                "Pico (M€)": maximo,
                "% do pico": percentual_do_pico(dados) or 0.0,
                "Diferença para o pico (M€)": max(maximo - atual, 0.0),
            }
        )
    return mercado


def calcular_medias_titulares(
    titulares: Sequence[Mapping[str, Any]],
) -> dict[str, float | None]:
    """Calcula médias independentes e coletiva apenas com notas válidas."""
    notas_vini = [
        numero
        for jogador in titulares
        if (numero := _numero_positivo(jogador.get("nota_vini"))) is not None
    ]
    notas_roberto = [
        numero
        for jogador in titulares
        if (numero := _numero_positivo(jogador.get("nota_roberto"))) is not None
    ]

    media_vini = sum(notas_vini) / len(notas_vini) if notas_vini else None
    media_roberto = sum(notas_roberto) / len(notas_roberto) if notas_roberto else None
    media_coletiva = (
        (media_vini + media_roberto) / 2
        if media_vini is not None and media_roberto is not None
        else None
    )
    return {
        "vini": media_vini,
        "roberto": media_roberto,
        "coletiva": media_coletiva,
    }


def ordenar_consensos(
    avaliacoes: Sequence[Mapping[str, Any]],
    limite: int = LIMITE_DESTAQUES_ANALISE,
) -> list[Mapping[str, Any]]:
    """Ordena por menor diferença e, em empate, maior média."""
    return sorted(
        avaliacoes,
        key=lambda item: (float(item["Diferença"]), -float(item["Média"])),
    )[:limite]


def ordenar_divergencias(
    avaliacoes: Sequence[Mapping[str, Any]],
    limite: int = LIMITE_DESTAQUES_ANALISE,
) -> list[Mapping[str, Any]]:
    """Ordena por maior diferença e, em empate, maior média."""
    return sorted(
        avaliacoes,
        key=lambda item: (-float(item["Diferença"]), -float(item["Média"])),
    )[:limite]


LINHAS_TATICAS: tuple[str, ...] = (
    "Goleiro",
    "Defesa",
    "Meio-campo",
    "Ataque",
)

_POSICOES_POR_LINHA: dict[str, frozenset[str]] = {
    "Goleiro": frozenset({"Goleiro"}),
    "Defesa": frozenset({"Lateral-direito", "Lateral-esquerdo", "Zagueiro"}),
    "Meio-campo": frozenset({
        "Volante",
        "Mezzala esquerdo",
        "Mezzala direito",
        "Meia-esquerda",
        "Meia-direita",
        "Meia-armador",
    }),
    "Ataque": frozenset({
        "Ponta-esquerda",
        "Ponta-direita",
        "Segundo atacante",
        "Centroavante",
    }),
}


def linha_tatica_do_slot(configuracao: SlotTatico) -> str:
    """Classifica um slot em uma das quatro linhas de apresentação."""
    for posicao in configuracao.posicoes:
        for linha in LINHAS_TATICAS:
            if posicao in _POSICOES_POR_LINHA[linha]:
                return linha
    return "Meio-campo"


def construir_visualizacao_tatica_lista(
    layout: Mapping[str, SlotTatico],
    escalados: Mapping[str, str],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Cria uma estrutura acessível em lista usando a mesma escalação do campo."""
    linhas: dict[str, list[dict[str, Any]]] = {linha: [] for linha in LINHAS_TATICAS}

    for slot, configuracao in layout.items():
        nome = escalados.get(slot)
        dados = jogadores.get(nome, {}) if nome else {}
        indice = indice_adaptabilidade(dados, configuracao.posicoes) if dados else -1

        linhas[linha_tatica_do_slot(configuracao)].append(
            {
                "slot": slot,
                "tag": configuracao.tag,
                "nome": nome or "",
                "preenchido": bool(nome and dados),
                "indice_adaptabilidade": indice,
                "nota_vini": dados.get("nota_vini") if dados else None,
                "nota_roberto": dados.get("nota_roberto") if dados else None,
            }
        )

    return linhas
