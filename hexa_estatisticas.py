"""Contratos e cálculos das estatísticas sazonais dos atletas.

Os arquivos de temporada mantêm somente dados objetivos. Totais combinados,
índices derivados e rankings são sempre reconstruídos pelo aplicativo.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "AMBITOS_ESTATISTICOS",
    "CAMPOS_ESTATISTICOS",
    "CAMPOS_INTEIROS",
    "CAMPOS_PERCENTUAIS",
    "EstatisticasIntegrityError",
    "ResultadoTemporada",
    "agrupar_estatisticas",
    "atualizar_temporada",
    "calcular_indices",
    "construir_rankings",
    "normalizar_registro_estatistico",
    "validar_documento_temporada",
]

AMBITOS_ESTATISTICOS: tuple[str, ...] = ("clube", "selecao")
CAMPOS_INTEIROS: tuple[str, ...] = (
    "jogos",
    "minutos",
    "titular",
    "gols",
    "assistencias",
    "chutes",
    "chutes_no_alvo",
    "passes",
    "passes_chave",
    "dribles",
    "desarmes",
    "interceptacoes",
    "cabeceios_ganhos",
    "erros",
    "erros_geraram_gol",
    "cartoes_amarelos",
    "cartoes_vermelhos",
)
CAMPOS_PERCENTUAIS: tuple[str, ...] = ("passes_certos_percentual",)
CAMPOS_ESTATISTICOS: tuple[str, ...] = (
    *CAMPOS_INTEIROS,
    *CAMPOS_PERCENTUAIS,
)

_CAMPOS_RANKING: tuple[str, ...] = (
    "jogos",
    "minutos",
    "gols",
    "assistencias",
    "chutes_no_alvo",
    "passes_chave",
    "dribles",
    "desarmes",
    "interceptacoes",
    "cabeceios_ganhos",
)


class EstatisticasIntegrityError(ValueError):
    """Indica que um documento estatístico não pode ser atualizado com segurança."""


@dataclass(frozen=True, slots=True)
class ResultadoTemporada:
    documento: dict[str, Any]
    recebidos: int
    atualizados: int
    nao_encontrados: tuple[str, ...]
    duplicados: tuple[str, ...]


def _inteiro_nao_negativo(valor: Any, *, campo: str) -> int:
    if valor in (None, ""):
        return 0
    if isinstance(valor, bool):
        raise EstatisticasIntegrityError(f"{campo} não aceita valor booleano.")
    try:
        numero = float(str(valor).replace(",", "."))
    except (TypeError, ValueError) as erro:
        raise EstatisticasIntegrityError(f"{campo} precisa ser numérico.") from erro
    if numero < 0 or not numero.is_integer():
        raise EstatisticasIntegrityError(
            f"{campo} precisa ser um inteiro maior ou igual a zero."
        )
    return int(numero)


def _percentual(valor: Any, *, campo: str) -> float | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, bool):
        raise EstatisticasIntegrityError(f"{campo} não aceita valor booleano.")
    texto = str(valor).strip().replace("%", "").replace(",", ".")
    try:
        numero = float(texto)
    except ValueError as erro:
        raise EstatisticasIntegrityError(f"{campo} precisa ser numérico.") from erro
    if not 0 <= numero <= 100:
        raise EstatisticasIntegrityError(f"{campo} precisa estar entre 0 e 100.")
    return round(numero, 2)


def normalizar_registro_estatistico(
    registro: Mapping[str, Any],
    *,
    temporada: int,
) -> dict[str, Any]:
    """Normaliza uma linha de clube ou Seleção sem inventar dados ausentes."""
    id_atleta = str(registro.get("id_atleta") or "").strip()
    nome = str(registro.get("nome") or "").strip()
    ambito = str(registro.get("ambito") or "").strip().casefold()
    if not id_atleta and not nome:
        raise EstatisticasIntegrityError(
            "Cada linha precisa informar id_atleta ou nome."
        )
    if ambito not in AMBITOS_ESTATISTICOS:
        raise EstatisticasIntegrityError(
            "O campo ambito precisa ser 'clube' ou 'selecao'."
        )

    equipe = str(registro.get("equipe") or "").strip()
    competicao = str(registro.get("competicao") or "").strip()
    normalizado: dict[str, Any] = {
        "id_atleta": id_atleta,
        "nome": nome,
        "temporada": int(temporada),
        "ambito": ambito,
        "equipe": equipe,
        "competicao": competicao,
    }
    for campo in CAMPOS_INTEIROS:
        normalizado[campo] = _inteiro_nao_negativo(
            registro.get(campo),
            campo=campo,
        )
    for campo in CAMPOS_PERCENTUAIS:
        normalizado[campo] = _percentual(registro.get(campo), campo=campo)
    return normalizado


def _chave_linha(registro: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(registro.get("id_atleta") or ""),
        str(registro.get("ambito") or ""),
        str(registro.get("equipe") or "").casefold(),
        str(registro.get("competicao") or "").casefold(),
    )


def _somar_linhas(
    linhas: Sequence[Mapping[str, Any]],
    *,
    ambito: str,
) -> dict[str, Any]:
    resultado: dict[str, Any] = {
        "ambito": ambito,
        "equipe": "Todos" if ambito == "combinado" else "",
        "competicao": "Todas",
    }
    for campo in CAMPOS_INTEIROS:
        resultado[campo] = sum(int(linha.get(campo) or 0) for linha in linhas)

    total_passes = sum(int(linha.get("passes") or 0) for linha in linhas)
    passes_certos_estimados = sum(
        int(linha.get("passes") or 0)
        * float(linha.get("passes_certos_percentual") or 0)
        / 100
        for linha in linhas
    )
    resultado["passes_certos_percentual"] = (
        round(passes_certos_estimados / total_passes * 100, 2)
        if total_passes
        else None
    )
    return resultado


def calcular_indices(registro: Mapping[str, Any]) -> dict[str, float | None]:
    """Calcula apenas índices transparentes; não cria uma nota esportiva."""
    jogos = int(registro.get("jogos") or 0)
    minutos = int(registro.get("minutos") or 0)
    titular = int(registro.get("titular") or 0)
    chutes = int(registro.get("chutes") or 0)

    def por_90(campo: str) -> float | None:
        if minutos <= 0:
            return None
        return round(float(registro.get(campo) or 0) * 90 / minutos, 3)

    return {
        "minutos_por_jogo": round(minutos / jogos, 2) if jogos else None,
        "titular_percentual": round(titular / jogos * 100, 2) if jogos else None,
        "gols_por_90": por_90("gols"),
        "assistencias_por_90": por_90("assistencias"),
        "participacoes_gol_por_90": (
            round(
                (
                    float(registro.get("gols") or 0)
                    + float(registro.get("assistencias") or 0)
                )
                * 90
                / minutos,
                3,
            )
            if minutos
            else None
        ),
        "chutes_no_alvo_percentual": (
            round(float(registro.get("chutes_no_alvo") or 0) / chutes * 100, 2)
            if chutes
            else None
        ),
    }


def agrupar_estatisticas(
    linhas: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Gera totais de clube, Seleção e combinado para cada atleta."""
    por_atleta: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for linha in linhas:
        por_atleta[str(linha["id_atleta"])].append(linha)

    totais: list[dict[str, Any]] = []
    for id_atleta, registros in sorted(por_atleta.items()):
        nome = str(registros[0].get("nome") or "")
        for ambito in (*AMBITOS_ESTATISTICOS, "combinado"):
            selecionadas = (
                registros
                if ambito == "combinado"
                else [item for item in registros if item.get("ambito") == ambito]
            )
            if not selecionadas:
                continue
            total = _somar_linhas(selecionadas, ambito=ambito)
            total.update(
                {
                    "id_atleta": id_atleta,
                    "nome": nome,
                    "temporada": registros[0]["temporada"],
                    "indices": calcular_indices(total),
                }
            )
            totais.append(total)
    return totais


def construir_rankings(
    totais: Sequence[Mapping[str, Any]],
    *,
    limite: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    """Cria rankings objetivos para o total combinado, sem nota composta."""
    combinados = [item for item in totais if item.get("ambito") == "combinado"]
    rankings: dict[str, list[dict[str, Any]]] = {}
    for campo in _CAMPOS_RANKING:
        ordenados = sorted(
            combinados,
            key=lambda item: (
                -float(item.get(campo) or 0),
                str(item.get("nome") or "").casefold(),
            ),
        )[: max(1, int(limite))]
        rankings[campo] = [
            {
                "posicao": indice,
                "id_atleta": str(item.get("id_atleta") or ""),
                "nome": str(item.get("nome") or ""),
                "valor": item.get(campo, 0),
            }
            for indice, item in enumerate(ordenados, start=1)
        ]
    return rankings


def _indice_jogadores(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    por_nome: dict[str, str] = {}
    por_id: dict[str, tuple[str, str]] = {}
    for chave, dados in jogadores.items():
        nome = str(dados.get("nome") or chave).strip()
        id_atleta = str(dados.get("id_atleta") or "").strip()
        por_nome[nome.casefold()] = id_atleta
        if id_atleta:
            por_id[id_atleta] = (nome, chave)
    return por_nome, por_id


def atualizar_temporada(
    *,
    temporada: int,
    registros: Iterable[Mapping[str, Any]],
    jogadores: Mapping[str, Mapping[str, Any]],
    documento_anterior: Mapping[str, Any] | None = None,
    fonte: str,
    atualizado_por: str = "",
    agora: datetime | None = None,
) -> ResultadoTemporada:
    """Atualiza somente a temporada informada e preserva seu histórico interno."""
    ano = int(temporada)
    if not 2000 <= ano <= 2100:
        raise EstatisticasIntegrityError("Temporada fora do intervalo permitido.")

    por_nome, por_id = _indice_jogadores(jogadores)
    normalizados: list[dict[str, Any]] = []
    nao_encontrados: list[str] = []
    vistos: set[tuple[str, str, str, str]] = set()
    duplicados: list[str] = []
    recebidos = 0

    for bruto in registros:
        recebidos += 1
        item = normalizar_registro_estatistico(bruto, temporada=ano)
        id_atleta = item["id_atleta"]
        if not id_atleta:
            id_atleta = por_nome.get(str(item["nome"]).casefold(), "")
        if id_atleta not in por_id:
            nao_encontrados.append(str(item["nome"] or id_atleta or "sem identificação"))
            continue
        nome_canonico, _ = por_id[id_atleta]
        item["id_atleta"] = id_atleta
        item["nome"] = nome_canonico
        chave = _chave_linha(item)
        if chave in vistos:
            duplicados.append(f"{nome_canonico}:{item['ambito']}:{item['competicao']}")
            continue
        vistos.add(chave)
        normalizados.append(item)

    anterior = dict(documento_anterior or {})
    historico = list(anterior.get("historico_atualizacoes") or [])
    instante = (agora or datetime.now(timezone.utc)).astimezone(timezone.utc)
    carimbo = instante.isoformat().replace("+00:00", "Z")
    historico.append(
        {
            "atualizado_em_utc": carimbo,
            "fonte": str(fonte).strip() or "Não informada",
            "atualizado_por": str(atualizado_por).strip(),
            "registros_recebidos": recebidos,
            "registros_atualizados": len(normalizados),
            "nao_encontrados": len(nao_encontrados),
            "duplicados_descartados": len(duplicados),
        }
    )

    registros_anteriores = [
        dict(item)
        for item in (anterior.get("registros") or [])
        if isinstance(item, Mapping)
        and int(item.get("temporada") or ano) == ano
    ]
    por_chave = {
        _chave_linha(item): item
        for item in registros_anteriores
    }
    for item in normalizados:
        por_chave[_chave_linha(item)] = item
    registros_finais = sorted(
        por_chave.values(),
        key=lambda item: (
            str(item.get("nome") or "").casefold(),
            str(item.get("ambito") or ""),
            str(item.get("equipe") or "").casefold(),
            str(item.get("competicao") or "").casefold(),
        ),
    )

    totais = agrupar_estatisticas(registros_finais)
    documento = {
        "schema_version": "1.0",
        "temporada": ano,
        "atualizado_em_utc": carimbo,
        "fonte_atual": str(fonte).strip() or "Não informada",
        "historico_atualizacoes": historico,
        "registros": registros_finais,
        "totais": totais,
        "rankings": construir_rankings(totais),
    }
    validar_documento_temporada(documento)
    return ResultadoTemporada(
        documento=documento,
        recebidos=recebidos,
        atualizados=len(normalizados),
        nao_encontrados=tuple(sorted(set(nao_encontrados))),
        duplicados=tuple(sorted(set(duplicados))),
    )


def validar_documento_temporada(documento: Mapping[str, Any]) -> list[str]:
    problemas: list[str] = []
    if documento.get("schema_version") != "1.0":
        problemas.append("schema_version precisa ser 1.0.")
    try:
        temporada = int(documento.get("temporada"))
    except (TypeError, ValueError):
        problemas.append("temporada inválida.")
        temporada = 0
    if not 2000 <= temporada <= 2100:
        problemas.append("temporada fora do intervalo permitido.")
    registros = documento.get("registros")
    if not isinstance(registros, list):
        problemas.append("registros precisa ser uma lista.")
    if problemas:
        raise EstatisticasIntegrityError(" ".join(problemas))
    return problemas
