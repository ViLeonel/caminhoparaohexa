"""Contratos para calendários oficiais de clubes e Seleção."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

__all__ = [
    "CATEGORIAS_COMPETICAO",
    "CalendarioIntegrityError",
    "ResultadoCalendario",
    "atualizar_calendario",
    "normalizar_jogo",
    "proximos_jogos_do_atleta",
    "validar_documento_calendario",
]

CATEGORIAS_COMPETICAO: tuple[str, ...] = (
    "estadual",
    "regional",
    "nacional_liga",
    "nacional_copa",
    "continental_libertadores",
    "continental_sulamericana",
    "continental_outros",
    "internacional_clubes",
    "selecao",
    "amistoso_oficial",
    "outro_oficial",
)


class CalendarioIntegrityError(ValueError):
    """Indica calendário incompatível com o contrato oficial."""


@dataclass(frozen=True, slots=True)
class ResultadoCalendario:
    documento: dict[str, Any]
    recebidos: int
    atualizados: int
    duplicados: tuple[str, ...]


def _data_iso(valor: Any) -> str:
    texto = str(valor or "").strip()[:10]
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError as erro:
        raise CalendarioIntegrityError(
            "A data do jogo precisa usar AAAA-MM-DD."
        ) from erro


def normalizar_jogo(registro: Mapping[str, Any], *, ano: int) -> dict[str, Any]:
    competicao = str(registro.get("competicao") or "").strip()
    categoria = str(registro.get("categoria_competicao") or "").strip().casefold()
    mandante = str(registro.get("mandante") or "").strip()
    visitante = str(registro.get("visitante") or "").strip()
    if not competicao:
        raise CalendarioIntegrityError("competicao é obrigatória.")
    if categoria not in CATEGORIAS_COMPETICAO:
        raise CalendarioIntegrityError(
            "categoria_competicao não pertence ao vocabulário oficial."
        )
    if not mandante or not visitante:
        raise CalendarioIntegrityError("mandante e visitante são obrigatórios.")
    data_jogo = _data_iso(registro.get("data"))
    if int(data_jogo[:4]) != int(ano):
        raise CalendarioIntegrityError(
            "A data do jogo precisa pertencer ao ano do calendário."
        )
    return {
        "id_jogo": str(registro.get("id_jogo") or "").strip(),
        "ano": int(ano),
        "data": data_jogo,
        "hora": str(registro.get("hora") or "").strip(),
        "fuso_horario": str(registro.get("fuso_horario") or "").strip(),
        "competicao": competicao,
        "categoria_competicao": categoria,
        "fase": str(registro.get("fase") or "").strip(),
        "rodada": str(registro.get("rodada") or "").strip(),
        "mandante": mandante,
        "visitante": visitante,
        "estadio": str(registro.get("estadio") or "").strip(),
        "status": str(registro.get("status") or "agendado").strip().casefold(),
        "fonte_url": str(registro.get("fonte_url") or "").strip(),
    }


def _chave_jogo(jogo: Mapping[str, Any]) -> tuple[str, str, str, str]:
    id_jogo = str(jogo.get("id_jogo") or "")
    if id_jogo:
        return ("id", id_jogo, "", "")
    return (
        str(jogo.get("data") or ""),
        str(jogo.get("competicao") or "").casefold(),
        str(jogo.get("mandante") or "").casefold(),
        str(jogo.get("visitante") or "").casefold(),
    )


def atualizar_calendario(
    *,
    ano: int,
    jogos: Iterable[Mapping[str, Any]],
    documento_anterior: Mapping[str, Any] | None = None,
    fonte: str,
    atualizado_por: str = "",
    agora: datetime | None = None,
) -> ResultadoCalendario:
    if not 2000 <= int(ano) <= 2100:
        raise CalendarioIntegrityError("Ano fora do intervalo permitido.")

    normalizados: list[dict[str, Any]] = []
    duplicados: list[str] = []
    vistos: set[tuple[str, str, str, str]] = set()
    recebidos = 0
    for bruto in jogos:
        recebidos += 1
        jogo = normalizar_jogo(bruto, ano=int(ano))
        chave = _chave_jogo(jogo)
        if chave in vistos:
            duplicados.append(
                f"{jogo['data']}:{jogo['mandante']} x {jogo['visitante']}"
            )
            continue
        vistos.add(chave)
        normalizados.append(jogo)

    anterior = dict(documento_anterior or {})
    jogos_anteriores = [
        dict(item)
        for item in (anterior.get("jogos") or [])
        if isinstance(item, Mapping)
        and int(item.get("ano") or ano) == int(ano)
    ]
    por_chave = {
        _chave_jogo(item): item
        for item in jogos_anteriores
    }
    for item in normalizados:
        por_chave[_chave_jogo(item)] = item
    jogos_finais = sorted(
        por_chave.values(),
        key=lambda item: (
            str(item.get("data") or ""),
            str(item.get("hora") or ""),
            str(item.get("competicao") or "").casefold(),
            str(item.get("mandante") or "").casefold(),
        ),
    )
    historico = list(anterior.get("historico_atualizacoes") or [])
    instante = (agora or datetime.now(timezone.utc)).astimezone(timezone.utc)
    carimbo = instante.isoformat().replace("+00:00", "Z")
    historico.append(
        {
            "atualizado_em_utc": carimbo,
            "fonte": str(fonte).strip() or "Não informada",
            "atualizado_por": str(atualizado_por).strip(),
            "jogos_recebidos": recebidos,
            "jogos_atualizados": len(normalizados),
            "duplicados_descartados": len(duplicados),
        }
    )
    documento = {
        "schema_version": "1.0",
        "ano": int(ano),
        "atualizado_em_utc": carimbo,
        "fonte_atual": str(fonte).strip() or "Não informada",
        "categorias_competicao": list(CATEGORIAS_COMPETICAO),
        "historico_atualizacoes": historico,
        "jogos": jogos_finais,
    }
    validar_documento_calendario(documento)
    return ResultadoCalendario(
        documento=documento,
        recebidos=recebidos,
        atualizados=len(normalizados),
        duplicados=tuple(sorted(set(duplicados))),
    )


def validar_documento_calendario(documento: Mapping[str, Any]) -> list[str]:
    problemas: list[str] = []
    if documento.get("schema_version") != "1.0":
        problemas.append("schema_version precisa ser 1.0.")
    jogos = documento.get("jogos")
    if not isinstance(jogos, list):
        problemas.append("jogos precisa ser uma lista.")
    if problemas:
        raise CalendarioIntegrityError(" ".join(problemas))
    return problemas


def proximos_jogos_do_atleta(
    *,
    jogador: Mapping[str, Any],
    calendario: Mapping[str, Any],
    hoje: date | None = None,
    limite: int = 3,
    nome_selecao: str = "Brasil",
) -> list[dict[str, Any]]:
    """Retorna somente data, competição e confronto dos próximos jogos possíveis."""
    clube = str(jogador.get("clube") or "").strip().casefold()
    selecao = nome_selecao.strip().casefold()
    referencia = hoje or date.today()
    candidatos: list[dict[str, Any]] = []
    for jogo in calendario.get("jogos") or []:
        if not isinstance(jogo, Mapping):
            continue
        try:
            data_jogo = date.fromisoformat(str(jogo.get("data") or ""))
        except ValueError:
            continue
        if data_jogo < referencia:
            continue
        mandante = str(jogo.get("mandante") or "").strip().casefold()
        visitante = str(jogo.get("visitante") or "").strip().casefold()
        if clube not in {mandante, visitante} and selecao not in {mandante, visitante}:
            continue
        candidatos.append(
            {
                "data": data_jogo.isoformat(),
                "competicao": str(jogo.get("competicao") or ""),
                "confronto": (
                    f"{jogo.get('mandante', '')} x {jogo.get('visitante', '')}"
                ),
            }
        )
    return sorted(candidatos, key=lambda item: item["data"])[: max(0, int(limite))]
