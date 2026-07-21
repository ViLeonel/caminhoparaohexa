"""Gerenciamento testável do estado da convocação."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

from hexa_taticas import LIMITE_RESERVAS, SlotTatico, obter_atletas_compativeis

__all__ = [
    "chave_reserva_livre",
    "chave_reserva_posicional",
    "chave_reservas",
    "chave_titular",
    "chaves_convocacao",
    "ler_convocacao",
    "limpar_convocacao",
    "limpar_todas_convocacoes",
    "migrar_reservas_legadas",
    "normalizar_escolha_reserva",
    "normalizar_escolha_titular",
    "normalizar_reservas",
    "ocupados_convocacao",
    "opcoes_reserva_livre",
    "opcoes_reserva_posicional",
    "opcoes_reservas",
    "opcoes_titular",
    "prioridade_posicoes_tatica",
    "quantidade_vagas_livres",
    "reconciliar_convocacao",
    "reservas_da_sessao",
]


def chave_titular(tatica: str, indice: int) -> str:
    return f"titular::{tatica}::{indice}"


def chave_reservas(tatica: str) -> str:
    """Chave legada do antigo multiselect de reservas."""
    return f"reservas::{tatica}"


def chave_reserva_posicional(tatica: str, indice: int) -> str:
    return f"reserva::{tatica}::posicional::{indice}"


def chave_reserva_livre(tatica: str, indice: int) -> str:
    return f"reserva::{tatica}::livre::{indice}"


def quantidade_vagas_livres(total_slots_taticos: int) -> int:
    """Mantém o banco em até 15 vagas, completando a tática com vagas livres."""
    return max(0, LIMITE_RESERVAS - max(0, int(total_slots_taticos)))


def chaves_convocacao(tatica: str, total_slots: int) -> tuple[str, ...]:
    """Retorna todas as chaves atuais e a chave legada de uma formação."""
    return (
        *(
            chave_titular(tatica, indice)
            for indice in range(total_slots)
        ),
        *(
            chave_reserva_posicional(tatica, indice)
            for indice in range(total_slots)
        ),
        *(
            chave_reserva_livre(tatica, indice)
            for indice in range(quantidade_vagas_livres(total_slots))
        ),
        chave_reservas(tatica),
    )


def limpar_convocacao(
    estado: MutableMapping[str, Any],
    tatica: str,
    total_slots: int,
) -> None:
    """Remove titulares e reservas de uma formação sem afetar outras telas."""
    for chave in chaves_convocacao(tatica, total_slots):
        estado.pop(chave, None)


def limpar_todas_convocacoes(
    estado: MutableMapping[str, Any],
    taticas: Mapping[str, Mapping[str, SlotTatico]],
) -> None:
    """Remove todas as formações salvas sem tocar em outros estados da interface."""
    for tatica, layout in taticas.items():
        limpar_convocacao(estado, tatica, len(layout))


def opcoes_titular(
    jogadores: Mapping[str, Mapping[str, Any]],
    posicoes_slot: Sequence[str],
    indisponiveis: set[str],
) -> list[str]:
    """Retorna atletas compatíveis que não ocupam outra vaga da convocação."""
    validos = obter_atletas_compativeis(jogadores, posicoes_slot)
    return [nome for nome in validos if nome not in indisponiveis]


def normalizar_escolha_titular(
    estado: MutableMapping[str, Any],
    chave: str,
    opcoes_disponiveis: Sequence[str],
) -> str | None:
    """Descarta uma escolha que deixou de ser válida antes de criar o widget."""
    valor = estado.get(chave)
    if valor not in opcoes_disponiveis:
        estado[chave] = None
        return None
    return str(valor)


def normalizar_escolha_reserva(
    estado: MutableMapping[str, Any],
    chave: str,
    opcoes_disponiveis: Sequence[str],
) -> str | None:
    """Aplica às reservas a mesma reconciliação segura dos titulares."""
    return normalizar_escolha_titular(estado, chave, opcoes_disponiveis)


def opcoes_reserva_posicional(
    jogadores: Mapping[str, Mapping[str, Any]],
    posicoes_slot: Sequence[str],
    indisponiveis: set[str],
) -> list[str]:
    """Filtra a vaga reserva pelas mesmas posições editoriais do slot titular."""
    validos = obter_atletas_compativeis(jogadores, posicoes_slot)
    return [nome for nome in validos if nome not in indisponiveis]


def prioridade_posicoes_tatica(
    layout: Mapping[str, SlotTatico],
) -> tuple[str, ...]:
    """Extrai a ordem de posições da formação, sem duplicidades."""
    prioridade: list[str] = []
    for configuracao in layout.values():
        for posicao in configuracao.posicoes:
            if posicao not in prioridade:
                prioridade.append(posicao)
    return tuple(prioridade)


def _posicoes_editoriais(dados: Mapping[str, Any]) -> tuple[str, ...]:
    """Lê apenas posições definidas pelos analistas, nunca posições externas."""
    brutas = dados.get("posicoes_multiplas") or [dados.get("posicao")]
    resultado: list[str] = []
    for posicao in brutas:
        texto = str(posicao or "").strip()
        if texto and texto not in resultado:
            resultado.append(texto)
    return tuple(resultado)


def _chave_ordenacao_tatica(
    nome: str,
    dados: Mapping[str, Any],
    prioridade: Sequence[str],
) -> tuple[int, int, str, str]:
    posicoes = _posicoes_editoriais(dados)
    indice_por_posicao = {
        posicao: indice for indice, posicao in enumerate(prioridade)
    }
    final = len(prioridade)
    melhor_indice = min(
        (indice_por_posicao.get(posicao, final) for posicao in posicoes),
        default=final,
    )
    posicao_principal = str(dados.get("posicao") or "")
    indice_principal = indice_por_posicao.get(posicao_principal, final)
    return (
        melhor_indice,
        indice_principal,
        posicao_principal.casefold(),
        nome.casefold(),
    )


def opcoes_reserva_livre(
    jogadores: Mapping[str, Mapping[str, Any]],
    prioridade_posicoes: Sequence[str],
    indisponiveis: set[str],
) -> list[str]:
    """Ordena qualquer atleta pela sequência posicional da formação ativa."""
    candidatos = [
        nome
        for nome in jogadores
        if nome not in indisponiveis
    ]
    return sorted(
        candidatos,
        key=lambda nome: _chave_ordenacao_tatica(
            nome,
            jogadores[nome],
            prioridade_posicoes,
        ),
    )


def opcoes_reservas(
    jogadores: Mapping[str, Mapping[str, Any]],
    titulares: set[str],
) -> list[str]:
    """Compatibilidade com o seletor legado: todos os não titulares."""
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
    """Normaliza a lista legada sem duplicados ou excedentes."""
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


def _valor_compativel(
    valor: Any,
    jogadores: Mapping[str, Mapping[str, Any]],
    posicoes: Sequence[str] | None,
) -> str | None:
    if not isinstance(valor, str) or valor not in jogadores:
        return None
    if posicoes is None:
        return valor
    compativeis = obter_atletas_compativeis(jogadores, posicoes)
    return valor if valor in compativeis else None


def reconciliar_convocacao(
    estado: MutableMapping[str, Any],
    tatica: str,
    layout: Mapping[str, SlotTatico],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Corrige a convocação inteira antes da criação dos widgets.

    A ordem canônica de prioridade é: titulares, reservas posicionais e vagas
    livres. Em um estado antigo com atleta repetido, a primeira ocorrência
    válida é preservada e as posteriores são limpas.
    """
    usados: set[str] = set()
    titulares: dict[str, str] = {}
    reservas: list[str] = []
    chaves_limpas: list[str] = []

    for indice, (slot, configuracao) in enumerate(layout.items()):
        chave = chave_titular(tatica, indice)
        nome = _valor_compativel(
            estado.get(chave),
            jogadores,
            configuracao.posicoes,
        )
        if nome is None or nome in usados:
            valor_original = estado.get(chave)
            if valor_original not in (None, ""):
                chaves_limpas.append(chave)
                estado[chave] = None
            continue
        titulares[slot] = nome
        usados.add(nome)

    for indice, (_, configuracao) in enumerate(layout.items()):
        chave = chave_reserva_posicional(tatica, indice)
        nome = _valor_compativel(
            estado.get(chave),
            jogadores,
            configuracao.posicoes,
        )
        if nome is None or nome in usados:
            valor_original = estado.get(chave)
            if valor_original not in (None, ""):
                chaves_limpas.append(chave)
                estado[chave] = None
            continue
        reservas.append(nome)
        usados.add(nome)

    for indice in range(quantidade_vagas_livres(len(layout))):
        chave = chave_reserva_livre(tatica, indice)
        nome = _valor_compativel(estado.get(chave), jogadores, None)
        if nome is None or nome in usados:
            valor_original = estado.get(chave)
            if valor_original not in (None, ""):
                chaves_limpas.append(chave)
                estado[chave] = None
            continue
        reservas.append(nome)
        usados.add(nome)

    estado.pop(chave_reservas(tatica), None)
    return {
        "titulares": titulares,
        "reservas": reservas[:LIMITE_RESERVAS],
        "ocupados": usados,
        "chaves_limpas": tuple(chaves_limpas),
    }


def ocupados_convocacao(
    estado: Mapping[str, Any],
    tatica: str,
    layout: Mapping[str, SlotTatico],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> set[str]:
    """Lê todas as escolhas válidas sem modificar o estado."""
    escalados, reservas = ler_convocacao(
        estado,
        tatica,
        layout,
        jogadores,
    )
    return {*escalados.values(), *reservas}


def reservas_da_sessao(
    estado: Mapping[str, Any],
    tatica: str,
    total_slots: int,
) -> list[str]:
    """Lê os 11 slots posicionais e depois as vagas livres, sem duplicidade."""
    reservas: list[str] = []

    for indice in range(total_slots):
        valor = estado.get(chave_reserva_posicional(tatica, indice))
        if isinstance(valor, str) and valor and valor not in reservas:
            reservas.append(valor)

    for indice in range(quantidade_vagas_livres(total_slots)):
        valor = estado.get(chave_reserva_livre(tatica, indice))
        if isinstance(valor, str) and valor and valor not in reservas:
            reservas.append(valor)

    return reservas[:LIMITE_RESERVAS]


def migrar_reservas_legadas(
    estado: MutableMapping[str, Any],
    tatica: str,
    layout: Mapping[str, SlotTatico],
    jogadores: Mapping[str, Mapping[str, Any]],
    titulares: set[str],
) -> list[str]:
    """Distribui o antigo multiselect nos novos slots antes de criar widgets.

    A migração só ocorre quando nenhum slot novo já possui valor. Primeiro tenta
    uma vaga posicional compatível; depois usa uma das quatro vagas livres.
    """
    total_slots = len(layout)
    chaves_novas = [
        *(
            chave_reserva_posicional(tatica, indice)
            for indice in range(total_slots)
        ),
        *(
            chave_reserva_livre(tatica, indice)
            for indice in range(quantidade_vagas_livres(total_slots))
        ),
    ]
    if any(estado.get(chave) for chave in chaves_novas):
        return reservas_da_sessao(estado, tatica, total_slots)

    legado = estado.get(chave_reservas(tatica), [])
    if not isinstance(legado, (list, tuple)):
        estado.pop(chave_reservas(tatica), None)
        return []

    usados = set(titulares)
    itens_layout = list(layout.items())

    for valor in legado[:LIMITE_RESERVAS]:
        if not isinstance(valor, str):
            continue
        nome = valor
        if nome not in jogadores or nome in usados:
            continue

        alocado = False
        for indice, (_, configuracao) in enumerate(itens_layout):
            chave = chave_reserva_posicional(tatica, indice)
            if estado.get(chave):
                continue
            compativeis = obter_atletas_compativeis(
                jogadores,
                configuracao.posicoes,
            )
            if nome in compativeis:
                estado[chave] = nome
                usados.add(nome)
                alocado = True
                break

        if alocado:
            continue

        for indice in range(quantidade_vagas_livres(total_slots)):
            chave = chave_reserva_livre(tatica, indice)
            if not estado.get(chave):
                estado[chave] = nome
                usados.add(nome)
                break

    estado.pop(chave_reservas(tatica), None)
    reconciliar_convocacao(
        estado,
        tatica,
        layout,
        jogadores,
    )
    return reservas_da_sessao(estado, tatica, total_slots)


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
            and nome in obter_atletas_compativeis(
                jogadores,
                configuracao.posicoes,
            )
        ):
            escalados[slot] = nome
            selecionados.add(nome)

    reservas: list[str] = []
    for indice, (_, configuracao) in enumerate(layout.items()):
        nome = estado.get(chave_reserva_posicional(tatica, indice))
        if (
            isinstance(nome, str)
            and nome in jogadores
            and nome not in selecionados
            and nome in obter_atletas_compativeis(
                jogadores,
                configuracao.posicoes,
            )
        ):
            reservas.append(nome)
            selecionados.add(nome)

    for indice in range(quantidade_vagas_livres(len(layout))):
        nome = estado.get(chave_reserva_livre(tatica, indice))
        if (
            isinstance(nome, str)
            and nome in jogadores
            and nome not in selecionados
        ):
            reservas.append(nome)
            selecionados.add(nome)

    if not reservas:
        reservas_brutas = estado.get(chave_reservas(tatica), [])
        if isinstance(reservas_brutas, (list, tuple)):
            for nome in reservas_brutas:
                if (
                    isinstance(nome, str)
                    and nome in jogadores
                    and nome not in selecionados
                ):
                    reservas.append(nome)
                    selecionados.add(nome)
                    if len(reservas) >= LIMITE_RESERVAS:
                        break

    return escalados, reservas[:LIMITE_RESERVAS]
