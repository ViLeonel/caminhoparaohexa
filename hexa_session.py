"""Gerenciamento testável do estado da convocação."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

from hexa_taticas import LIMITE_RESERVAS, SlotTatico, obter_atletas_compativeis


def chave_titular(tatica: str, indice: int) -> str:
    return f"titular::{tatica}::{indice}"


def chave_reservas(tatica: str) -> str:
    return f"reservas::{tatica}"


def limpar_convocacao(
    estado: MutableMapping[str, Any],
    tatica: str,
    total_slots: int,
) -> None:
    """Remove titulares e reservas de uma formação sem afetar outras telas."""
    for indice in range(total_slots):
        estado.pop(chave_titular(tatica, indice), None)
    estado.pop(chave_reservas(tatica), None)


def opcoes_titular(
    jogadores: Mapping[str, Mapping[str, Any]],
    posicoes_slot: Sequence[str],
    selecionados: set[str],
) -> list[str]:
    """Retorna atletas compatíveis ainda não usados na convocação titular."""
    validos = obter_atletas_compativeis(jogadores, posicoes_slot)
    return [nome for nome in validos if nome not in selecionados]


def normalizar_escolha_titular(
    estado: MutableMapping[str, Any],
    chave: str,
    opcoes_disponiveis: Sequence[str],
) -> str | None:
    """Descarta uma escolha que deixou de ser válida após mudanças anteriores."""
    valor = estado.get(chave)
    if valor not in opcoes_disponiveis:
        estado[chave] = None
        return None
    return str(valor)


def opcoes_reservas(
    jogadores: Mapping[str, Mapping[str, Any]],
    titulares: set[str],
) -> list[str]:
    """Retorna todos os atletas não utilizados entre os titulares."""
    return [
        nome
        for nome in sorted(jogadores.keys(), key=str.casefold)
        if nome not in titulares
    ]


def normalizar_reservas(
    estado: MutableMapping[str, Any],
    chave: str,
    opcoes_disponiveis: Sequence[str],
    limite: int = LIMITE_RESERVAS,
) -> list[str]:
    """Remove indisponíveis, duplicados e excedentes preservando a ordem."""
    permitidos = set(opcoes_disponiveis)
    resultado: list[str] = []
    vistos: set[str] = set()

    valor_atual = estado.get(chave, [])
    if not isinstance(valor_atual, (list, tuple)):
        valor_atual = []

    for nome in valor_atual:
        if nome not in permitidos or nome in vistos:
            continue
        resultado.append(str(nome))
        vistos.add(str(nome))
        if len(resultado) >= limite:
            break

    estado[chave] = resultado
    return resultado


def ler_convocacao(
    estado: Mapping[str, Any],
    tatica: str,
    layout: Mapping[str, SlotTatico],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str], list[str]]:
    """Reconstrói uma convocação válida a partir do estado persistido."""
    escalados: dict[str, str] = {}
    selecionados: set[str] = set()

    for indice, (slot, configuracao) in enumerate(layout.items()):
        nome = estado.get(chave_titular(tatica, indice))
        if (
            isinstance(nome, str)
            and nome in jogadores
            and nome not in selecionados
            and nome in obter_atletas_compativeis(jogadores, configuracao.posicoes)
        ):
            escalados[slot] = nome
            selecionados.add(nome)

    reservas_brutas = estado.get(chave_reservas(tatica), [])
    reservas: list[str] = []
    if isinstance(reservas_brutas, (list, tuple)):
        for nome in reservas_brutas:
            if (
                isinstance(nome, str)
                and nome in jogadores
                and nome not in selecionados
                and nome not in reservas
            ):
                reservas.append(nome)
                if len(reservas) >= LIMITE_RESERVAS:
                    break
    return escalados, reservas
