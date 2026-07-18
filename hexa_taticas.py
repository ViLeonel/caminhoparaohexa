"""Vocabulário oficial, fábricas de formações e regras de compatibilidade tática."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

POSICOES_OFICIAIS: tuple[str, ...] = (
    "Goleiro",
    "Lateral-direito",
    "Lateral-esquerdo",
    "Zagueiro",
    "Volante",
    "Mezzala esquerdo",
    "Mezzala direito",
    "Meia-esquerda",
    "Meia-direita",
    "Meia-armador",
    "Ponta-esquerda",
    "Ponta-direita",
    "Segundo atacante",
    "Centroavante",
)

ABREVIACOES: dict[str, str] = {
    "Goleiro": "GOL",
    "Lateral-direito": "LD",
    "Lateral-esquerdo": "LE",
    "Zagueiro": "ZAG",
    "Volante": "VOL",
    "Mezzala esquerdo": "MCE",
    "Mezzala direito": "MCD",
    "Meia-esquerda": "ME",
    "Meia-direita": "MD",
    "Meia-armador": "MEI",
    "Ponta-esquerda": "PE",
    "Ponta-direita": "PD",
    "Segundo atacante": "SA",
    "Centroavante": "CA",
}

# Migração de grafias antigas e equivalências de fontes externas.
# Esses aliases servem somente para normalização; a lista oficial acima prevalece.
ALIASES_POSICAO: dict[str, str] = {
    "Guarda-redes": "Goleiro",
    "Guarda-Redes": "Goleiro",
    "Lateral Direito": "Lateral-direito",
    "Lateral Esquerdo": "Lateral-esquerdo",
    "Zagueiro Direito": "Zagueiro",
    "Zagueiro Esquerdo": "Zagueiro",
    "Defesa central": "Zagueiro",
    "Defesa Central": "Zagueiro",
    "Médio Defensivo": "Volante",
    "Meio-Campo (Defensivo)": "Volante",
    "Médio Centro": "Mezzala direito",
    "Meio-Campo (Apoio)": "Mezzala esquerdo",
    "Meio-Campo (Criativo)": "Meia-armador",
    "Médio Ofensivo": "Meia-armador",
    "Médio Direito": "Meia-direita",
    "Médio Esquerdo": "Meia-esquerda",
    "Meia Direita": "Meia-direita",
    "Meia Esquerda": "Meia-esquerda",
    "Ponta Direita": "Ponta-direita",
    "Ponta Esquerda": "Ponta-esquerda",
    "Ponta-direito": "Ponta-direita",
    "Ponta-esquerdo": "Ponta-esquerda",
    "Extremo Direito": "Ponta-direita",
    "Extremo Esquerdo": "Ponta-esquerda",
    "Segundo Avançado": "Segundo atacante",
    "Ponta de Lança": "Centroavante",
}

LIMITE_TITULARES = 11
LIMITE_RESERVAS = 15
LIMITE_CONVOCADOS = LIMITE_TITULARES + LIMITE_RESERVAS


@dataclass(frozen=True, slots=True)
class SlotTatico:
    """Configuração visual e posicional de um lugar no campo."""

    posicoes: tuple[str, ...]
    left: str
    bottom: str
    tag: str


TipoEntradaSlot = tuple[str, SlotTatico]
FabricaTatica = Callable[[], dict[str, SlotTatico]]


def _slot(
    nome: str,
    posicoes: Sequence[str],
    left: int,
    bottom: int,
    tag: str,
) -> TipoEntradaSlot:
    """Cria uma entrada de slot com coordenadas percentuais padronizadas."""
    if not nome.strip():
        raise ValueError("O nome do slot tático não pode ser vazio.")
    if not posicoes:
        raise ValueError(f"{nome}: informe ao menos uma posição compatível.")
    if not 0 <= left <= 100 or not 0 <= bottom <= 100:
        raise ValueError(f"{nome}: coordenadas devem ficar entre 0 e 100.")
    return nome, SlotTatico(tuple(posicoes), f"{left}%", f"{bottom}%", tag)


def _combinar_linhas(*linhas: Sequence[TipoEntradaSlot]) -> dict[str, SlotTatico]:
    """Combina linhas preservando ordem e rejeitando nomes de slots duplicados."""
    formacao: dict[str, SlotTatico] = {}
    for linha in linhas:
        for nome, configuracao in linha:
            if nome in formacao:
                raise ValueError(f"Slot tático duplicado: {nome}.")
            formacao[nome] = configuracao
    return formacao


def _linha_goleiro() -> tuple[TipoEntradaSlot, ...]:
    return (_slot("Goleiro (GOL)", ("Goleiro",), 50, 8, "GOL"),)


def _linha_defensiva_quatro() -> tuple[TipoEntradaSlot, ...]:
    return (
        _slot("Lateral-esquerdo (LE)", ("Lateral-esquerdo",), 15, 28, "LE"),
        _slot("Zagueiro Esquerdo (ZAG)", ("Zagueiro",), 37, 22, "ZAG"),
        _slot("Zagueiro Direito (ZAG)", ("Zagueiro",), 63, 22, "ZAG"),
        _slot("Lateral-direito (LD)", ("Lateral-direito",), 85, 28, "LD"),
    )


def _formacao_433_diamante() -> dict[str, SlotTatico]:
    meio = (
        _slot("Mezzala Esquerdo (MCE)", ("Mezzala esquerdo", "Meia-esquerda", "Volante"), 30, 52, "MCE"),
        _slot("Volante (VOL)", ("Volante",), 50, 40, "VOL"),
        _slot("Mezzala Direito (MCD)", ("Mezzala direito", "Meia-direita", "Volante"), 70, 52, "MCD"),
    )
    ataque = (
        _slot("Ponta-esquerda (PE)", ("Ponta-esquerda", "Segundo atacante"), 20, 72, "PE"),
        _slot("Centroavante (CA)", ("Centroavante",), 50, 82, "CA"),
        _slot("Ponta-direita (PD)", ("Ponta-direita", "Meia-armador"), 80, 72, "PD"),
    )
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


def _formacao_433_classico() -> dict[str, SlotTatico]:
    meio = (
        _slot("Volante (VOL)", ("Volante",), 38, 45, "VOL"),
        _slot("Volante Apoio (VOL)", ("Volante", "Mezzala esquerdo", "Mezzala direito"), 62, 45, "VOL"),
        _slot("Meia-Armador (MEI)", ("Meia-armador",), 50, 60, "MEI"),
    )
    ataque = (
        _slot("Ponta-esquerda (PE)", ("Ponta-esquerda",), 20, 72, "PE"),
        _slot("Centroavante (CA)", ("Centroavante",), 50, 82, "CA"),
        _slot("Ponta-direita (PD)", ("Ponta-direita",), 80, 72, "PD"),
    )
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


def _formacao_442_diamante() -> dict[str, SlotTatico]:
    meio = (
        _slot("Volante (VOL)", ("Volante",), 50, 40, "VOL"),
        _slot("Mezzala Esquerdo (MCE)", ("Mezzala esquerdo",), 30, 52, "MCE"),
        _slot("Mezzala Direito (MCD)", ("Mezzala direito", "Mezzala esquerdo", "Meia-armador"), 70, 52, "MCD"),
        _slot("Meia-Armador (MEI)", ("Meia-armador",), 50, 65, "MEI"),
    )
    ataque = (
        _slot("Segundo Atacante (SA)", ("Segundo atacante", "Ponta-esquerda", "Ponta-direita", "Centroavante"), 38, 78, "SA"),
        _slot("Centroavante (CA)", ("Centroavante",), 62, 78, "CA"),
    )
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


def _formacao_442_classico() -> dict[str, SlotTatico]:
    meio = (
        _slot("Meia-esquerda (ME)", ("Meia-esquerda", "Mezzala esquerdo", "Ponta-esquerda"), 20, 55, "ME"),
        _slot("Volante Esquerdo (VOL)", ("Volante",), 40, 45, "VOL"),
        _slot("Volante Direito (VOL)", ("Volante",), 60, 45, "VOL"),
        _slot("Meia-direita (MD)", ("Meia-direita", "Mezzala direito", "Ponta-direita"), 80, 55, "MD"),
    )
    ataque = (
        _slot("Segundo Atacante (SA)", ("Segundo atacante", "Meia-armador", "Ponta-esquerda"), 38, 78, "SA"),
        _slot("Centroavante (CA)", ("Centroavante", "Segundo atacante"), 62, 78, "CA"),
    )
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


def _formacao_4231() -> dict[str, SlotTatico]:
    meio = (
        _slot("Volante Esquerdo (VOL)", ("Volante", "Mezzala esquerdo"), 38, 42, "VOL"),
        _slot("Volante Direito (VOL)", ("Volante", "Mezzala direito"), 62, 42, "VOL"),
        _slot("Ponta-esquerda (PE)", ("Ponta-esquerda", "Meia-esquerda"), 20, 65, "PE"),
        _slot("Meia-Armador (MEI)", ("Meia-armador", "Segundo atacante"), 50, 62, "MEI"),
        _slot("Ponta-direita (PD)", ("Ponta-direita", "Meia-direita"), 80, 65, "PD"),
    )
    ataque = (_slot("Centroavante (CA)", ("Centroavante",), 50, 82, "CA"),)
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


def _formacao_4321_arvore_natal() -> dict[str, SlotTatico]:
    meio = (
        _slot("Mezzala Esquerdo (MCE)", ("Mezzala esquerdo", "Volante"), 25, 45, "MCE"),
        _slot("Volante (VOL)", ("Volante",), 50, 42, "VOL"),
        _slot("Mezzala Direito (MCD)", ("Mezzala direito", "Volante"), 75, 45, "MCD"),
        _slot("Meia-Armador Esq (MEI)", ("Meia-armador", "Segundo atacante", "Ponta-esquerda"), 35, 65, "MEI"),
        _slot("Meia-Armador Dir (MEI)", ("Meia-armador", "Segundo atacante", "Ponta-direita"), 65, 65, "MEI"),
    )
    ataque = (_slot("Centroavante (CA)", ("Centroavante",), 50, 82, "CA"),)
    return _combinar_linhas(_linha_goleiro(), _linha_defensiva_quatro(), meio, ataque)


FABRICAS_TATICAS: dict[str, FabricaTatica] = {
    "4-3-3 Diamante": _formacao_433_diamante,
    "4-3-3 Clássico": _formacao_433_classico,
    "4-4-2 Diamante": _formacao_442_diamante,
    "4-4-2 Clássico": _formacao_442_classico,
    "4-2-3-1": _formacao_4231,
    "4-3-2-1 Árvore de Natal": _formacao_4321_arvore_natal,
}


def construir_taticas(
    fabricas: Mapping[str, FabricaTatica] | None = None,
) -> dict[str, dict[str, SlotTatico]]:
    """Materializa as formações registradas em dicionários independentes."""
    registro = fabricas or FABRICAS_TATICAS
    taticas: dict[str, dict[str, SlotTatico]] = {}
    for nome, fabrica in registro.items():
        formacao = fabrica()
        if nome in taticas:
            raise ValueError(f"Formação duplicada: {nome}.")
        taticas[nome] = formacao
    return taticas


# Não existem atletas padrão. Cada formação começa vazia e é preenchida pelo usuário.
TATICAS: dict[str, dict[str, SlotTatico]] = construir_taticas()

def normalizar_posicao(posicao: Any) -> str | None:
    """Converte grafias antigas/externas para uma posição oficial."""
    if posicao is None:
        return None
    valor = str(posicao).strip()
    if not valor:
        return None
    if valor in POSICOES_OFICIAIS:
        return valor
    return ALIASES_POSICAO.get(valor)


def normalizar_lista_posicoes(posicoes: Iterable[Any] | None) -> list[str]:
    """Normaliza, elimina duplicidades e descarta posições não reconhecidas."""
    resultado: list[str] = []
    for item in posicoes or []:
        normalizada = normalizar_posicao(item)
        if normalizada and normalizada not in resultado:
            resultado.append(normalizada)
    return resultado


def obter_atletas_compativeis(
    jogadores: Mapping[str, Mapping[str, Any]],
    posicoes_permitidas: Iterable[str],
) -> list[str]:
    permitidas = set(posicoes_permitidas)
    nomes: list[str] = []
    for nome, dados in jogadores.items():
        posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
        if any(posicao in permitidas for posicao in posicoes):
            nomes.append(nome)
    return sorted(nomes, key=str.casefold)


def formatar_jogador_com_posicao(nome: str, jogadores: Mapping[str, Mapping[str, Any]]) -> str:
    dados = jogadores.get(nome)
    if not dados:
        return nome
    posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
    siglas: list[str] = []
    for posicao in posicoes:
        sigla = ABREVIACOES.get(str(posicao), "OBS")
        if sigla not in siglas:
            siglas.append(sigla)
    clube = str(dados.get("clube") or "N/A")
    return f"{nome} — {clube} — {'/'.join(siglas)}"


def indice_adaptabilidade(dados_jogador: Mapping[str, Any], posicoes_permitidas: Iterable[str]) -> int:
    """Retorna 0 para posição primária, 1 para secundária, 2+ para terciária e -1 se incompatível."""
    permitidas = set(posicoes_permitidas)
    posicoes = dados_jogador.get("posicoes_multiplas") or [dados_jogador.get("posicao")]
    for indice, posicao in enumerate(posicoes):
        if posicao in permitidas:
            return indice
    return -1


def validar_taticas(_jogadores: Mapping[str, Mapping[str, Any]] | None = None) -> list[str]:
    """Valida quantidade de slots e uso exclusivo das posições oficiais."""
    erros: list[str] = []
    for nome_tatica, slots in TATICAS.items():
        if len(slots) != LIMITE_TITULARES:
            erros.append(f"{nome_tatica}: possui {len(slots)} slots, não {LIMITE_TITULARES}.")
        for slot, configuracao in slots.items():
            invalidas = [p for p in configuracao.posicoes if p not in POSICOES_OFICIAIS]
            if invalidas:
                erros.append(f"{nome_tatica} / {slot}: posições inválidas {invalidas}.")
    return erros
