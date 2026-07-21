"""Contrato, validação e cálculos das avaliações trimestrais.

O módulo recebe apenas dados brutos de Vini e Beto. Médias, saldos, cobertura,
divergências e histórico são sempre derivados em Python para que fórmulas da
planilha não se tornem fonte de verdade do aplicativo.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from hexa_config import AVALIACOES_FILE
from hexa_taticas import POSICOES_OFICIAIS

__all__ = [
    "AvaliacoesIntegrityError",
    "BaseAvaliacoes",
    "calcular_metricas_avaliacao",
    "calcular_resumo_convocados",
    "calcular_resumo_periodo",
    "carregar_avaliacoes",
    "comparar_analistas",
    "construir_rankings_periodo",
    "formatar_data_referencia",
    "formatar_numero",
    "formatar_periodo",
    "formatar_status_avaliacao",
    "historico_atleta",
    "media_disponivel",
    "periodos_disponiveis",
    "validar_integridade_avaliacoes",
]


class AvaliacoesIntegrityError(RuntimeError):
    """Erro bloqueante no contrato temporal de avaliações."""


@dataclass(frozen=True, slots=True)
class BaseAvaliacoes:
    """Base imutável, validada e indexada por período e atleta."""

    schema_version: str
    fonte: Mapping[str, Any]
    avaliacoes: tuple[Mapping[str, Any], ...]

    def periodos(self) -> tuple[str, ...]:
        return periodos_disponiveis(self)

    def do_periodo(self, periodo: str) -> dict[str, Mapping[str, Any]]:
        return {
            str(item["id_atleta"]): item
            for item in self.avaliacoes
            if item.get("periodo") == periodo
        }

    def por_nome_no_periodo(self, periodo: str) -> dict[str, Mapping[str, Any]]:
        return {
            str(item["nome"]): item
            for item in self.avaliacoes
            if item.get("periodo") == periodo
        }

    def do_atleta(self, id_atleta: str) -> list[Mapping[str, Any]]:
        return sorted(
            (
                item
                for item in self.avaliacoes
                if item.get("id_atleta") == id_atleta
            ),
            key=lambda item: (
                str(item.get("data_referencia") or ""),
                str(item.get("periodo") or ""),
            ),
        )

    def data_referencia_periodo(self, periodo: str) -> str | None:
        datas = {
            str(item["data_referencia"])
            for item in self.avaliacoes
            if item.get("periodo") == periodo
        }
        if not datas:
            return None
        if len(datas) != 1:
            raise AvaliacoesIntegrityError(
                f"O período {periodo} possui mais de uma data de referência."
            )
        return next(iter(datas))


def _numero_ou_none(valor: Any) -> float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero


def media_disponivel(valores: Iterable[Any]) -> float | None:
    """Calcula média apenas com valores numéricos presentes; zero é válido."""
    numeros = [
        numero
        for valor in valores
        if (numero := _numero_ou_none(valor)) is not None
    ]
    return sum(numeros) / len(numeros) if numeros else None


def _par_analista(registro: Mapping[str, Any], analista: str) -> tuple[float | None, float | None]:
    bloco = registro.get(analista)
    if not isinstance(bloco, Mapping):
        return None, None
    return (
        _numero_ou_none(bloco.get("capacidade_atual")),
        _numero_ou_none(bloco.get("potencial_2030")),
    )


def calcular_metricas_avaliacao(registro: Mapping[str, Any]) -> dict[str, Any]:
    """Deriva todas as métricas individuais sem usar colunas calculadas da planilha."""
    atual_vini, potencial_vini = _par_analista(registro, "vini")
    atual_beto, potencial_beto = _par_analista(registro, "beto")

    notas = (atual_vini, potencial_vini, atual_beto, potencial_beto)
    preenchidas = sum(valor is not None for valor in notas)
    if preenchidas == 4:
        status = "Completa"
    elif preenchidas:
        status = "Parcial"
    else:
        status = "Não avaliada"

    diferencas_pareadas: list[float] = []
    if atual_vini is not None and potencial_vini is not None:
        diferencas_pareadas.append(potencial_vini - atual_vini)
    if atual_beto is not None and potencial_beto is not None:
        diferencas_pareadas.append(potencial_beto - atual_beto)

    divergencia_atual = (
        abs(atual_vini - atual_beto)
        if atual_vini is not None and atual_beto is not None
        else None
    )
    divergencia_potencial = (
        abs(potencial_vini - potencial_beto)
        if potencial_vini is not None and potencial_beto is not None
        else None
    )

    return {
        "capacidade_atual_media": media_disponivel((atual_vini, atual_beto)),
        "potencial_2030_medio": media_disponivel(
            (potencial_vini, potencial_beto)
        ),
        "saldo_projetado": media_disponivel(diferencas_pareadas),
        "divergencia_capacidade": divergencia_atual,
        "divergencia_potencial": divergencia_potencial,
        "status": status,
        "notas_preenchidas": preenchidas,
        "avaliacao_completa": preenchidas == 4,
        "avaliacao_parcial": 0 < preenchidas < 4,
        "tem_avaliacao": preenchidas > 0,
    }


def _chave_periodo(item: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("data_referencia") or ""),
        str(item.get("periodo") or ""),
    )


def _historico_anterior(
    base: BaseAvaliacoes,
    registro: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    atual = _chave_periodo(registro)
    return [
        item
        for item in base.do_atleta(str(registro["id_atleta"]))
        if _chave_periodo(item) < atual
    ]


def historico_atleta(
    base: BaseAvaliacoes,
    id_atleta: str,
) -> list[dict[str, Any]]:
    """Monta série temporal com último trimestre e média histórica anteriores."""
    resultado: list[dict[str, Any]] = []
    anteriores: list[Mapping[str, Any]] = []

    for registro in base.do_atleta(id_atleta):
        metricas = calcular_metricas_avaliacao(registro)
        capacidade_atual = metricas["capacidade_atual_media"]

        ultimo_valido: float | None = None
        for anterior in reversed(anteriores):
            valor = calcular_metricas_avaliacao(anterior)[
                "capacidade_atual_media"
            ]
            if valor is not None:
                ultimo_valido = float(valor)
                break

        notas_historicas: list[float] = []
        for anterior in anteriores:
            for analista in ("vini", "beto"):
                capacidade, _ = _par_analista(anterior, analista)
                if capacidade is not None:
                    notas_historicas.append(capacidade)
        media_historica = media_disponivel(notas_historicas)

        linha = dict(registro)
        linha.update(metricas)
        linha["capacidade_ultimo_trimestre_avaliado"] = ultimo_valido
        linha["media_historica_anterior_capacidade"] = media_historica
        linha["variacao_vs_ultimo_trimestre"] = (
            float(capacidade_atual) - ultimo_valido
            if capacidade_atual is not None and ultimo_valido is not None
            else None
        )
        linha["variacao_vs_media_historica"] = (
            float(capacidade_atual) - float(media_historica)
            if capacidade_atual is not None and media_historica is not None
            else None
        )
        resultado.append(linha)
        anteriores.append(registro)

    return resultado


def calcular_resumo_periodo(
    base: BaseAvaliacoes,
    periodo: str,
    *,
    total_atletas: int | None = None,
) -> dict[str, Any]:
    """Consolida cobertura e médias do período selecionado."""
    registros = [
        item for item in base.avaliacoes if item.get("periodo") == periodo
    ]
    total_base = total_atletas if total_atletas is not None else len(registros)
    metricas = [calcular_metricas_avaliacao(item) for item in registros]

    completas = sum(bool(item["avaliacao_completa"]) for item in metricas)
    parciais = sum(bool(item["avaliacao_parcial"]) for item in metricas)
    com_alguma = sum(bool(item["tem_avaliacao"]) for item in metricas)
    notas = sum(int(item["notas_preenchidas"]) for item in metricas)

    return {
        "periodo": periodo,
        "data_referencia": base.data_referencia_periodo(periodo),
        "atletas_na_base": total_base,
        "registros_no_periodo": len(registros),
        "com_alguma_avaliacao": com_alguma,
        "avaliacoes_completas": completas,
        "avaliacoes_parciais": parciais,
        "nao_avaliados": max(total_base - com_alguma, 0),
        "notas_preenchidas": notas,
        "cobertura_completa": (
            completas / total_base if total_base else 0.0
        ),
        "cobertura_com_alguma": (
            com_alguma / total_base if total_base else 0.0
        ),
        "capacidade_atual_media": media_disponivel(
            item["capacidade_atual_media"] for item in metricas
        ),
        "potencial_2030_medio": media_disponivel(
            item["potencial_2030_medio"] for item in metricas
        ),
        "saldo_projetado_medio": media_disponivel(
            item["saldo_projetado"] for item in metricas
        ),
    }


def calcular_resumo_convocados(
    nomes: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Resume o período para uma seleção de atletas sem converter ausências em zero."""
    metricas: list[dict[str, Any]] = []
    for nome in nomes:
        if nome not in jogadores:
            continue
        registro = avaliacoes_por_nome.get(nome)
        if registro is None:
            metricas.append(
                {
                    "capacidade_atual_media": None,
                    "potencial_2030_medio": None,
                    "saldo_projetado": None,
                    "tem_avaliacao": False,
                    "avaliacao_completa": False,
                }
            )
        else:
            metricas.append(calcular_metricas_avaliacao(registro))

    return {
        "selecionados": len(metricas),
        "com_avaliacao": sum(bool(item["tem_avaliacao"]) for item in metricas),
        "completos": sum(
            bool(item["avaliacao_completa"]) for item in metricas
        ),
        "capacidade_atual_media": media_disponivel(
            item["capacidade_atual_media"] for item in metricas
        ),
        "potencial_2030_medio": media_disponivel(
            item["potencial_2030_medio"] for item in metricas
        ),
        "saldo_projetado_medio": media_disponivel(
            item["saldo_projetado"] for item in metricas
        ),
    }


def comparar_analistas(
    base: BaseAvaliacoes,
    periodo: str,
    dimensao: str,
) -> list[dict[str, Any]]:
    """Retorna somente registros com as duas notas da dimensão escolhida."""
    campo = {
        "capacidade": "capacidade_atual",
        "potencial": "potencial_2030",
    }.get(dimensao)
    if campo is None:
        raise ValueError("dimensao deve ser 'capacidade' ou 'potencial'.")

    resultado: list[dict[str, Any]] = []
    for registro in base.avaliacoes:
        if registro.get("periodo") != periodo:
            continue
        vini = _numero_ou_none(
            (registro.get("vini") or {}).get(campo)  # type: ignore[union-attr]
        )
        beto = _numero_ou_none(
            (registro.get("beto") or {}).get(campo)  # type: ignore[union-attr]
        )
        if vini is None or beto is None:
            continue
        resultado.append(
            {
                "Nome": registro["nome"],
                "Posição": registro["posicao_snapshot"],
                "Vini": vini,
                "Beto": beto,
                "Média": (vini + beto) / 2,
                "Diferença": abs(vini - beto),
            }
        )
    return resultado


def construir_rankings_periodo(
    base: BaseAvaliacoes,
    periodo: str,
    *,
    limite: int = 8,
) -> dict[str, list[dict[str, Any]]]:
    """Gera rankings principais apenas com avaliações completas."""
    completos: list[dict[str, Any]] = []
    parciais: list[dict[str, Any]] = []
    nao_avaliados: list[dict[str, Any]] = []

    for registro in base.avaliacoes:
        if registro.get("periodo") != periodo:
            continue
        linha = dict(registro)
        linha.update(calcular_metricas_avaliacao(registro))
        if linha["avaliacao_completa"]:
            completos.append(linha)
        elif linha["avaliacao_parcial"]:
            parciais.append(linha)
        else:
            nao_avaliados.append(linha)

    def topo(campo: str, reverso: bool = True) -> list[dict[str, Any]]:
        validos = [item for item in completos if item.get(campo) is not None]
        return sorted(
            validos,
            key=lambda item: (
                -float(item[campo]) if reverso else float(item[campo]),
                str(item["nome"]).casefold(),
            ),
        )[:limite]

    return {
        "maior_capacidade": topo("capacidade_atual_media"),
        "maior_potencial": topo("potencial_2030_medio"),
        "maior_evolucao": topo("saldo_projetado"),
        "maior_regressao": topo("saldo_projetado", reverso=False),
        "parciais": sorted(parciais, key=lambda item: str(item["nome"]).casefold()),
        "nao_avaliados": sorted(
            nao_avaliados,
            key=lambda item: str(item["nome"]).casefold(),
        ),
    }


def periodos_disponiveis(base: BaseAvaliacoes) -> tuple[str, ...]:
    unicos = {
        (
            str(item.get("data_referencia") or ""),
            str(item.get("periodo") or ""),
        )
        for item in base.avaliacoes
    }
    return tuple(periodo for _, periodo in sorted(unicos))


def formatar_periodo(periodo: str) -> str:
    """Converte ``2026-T2`` em ``T2 2026``."""
    partes = periodo.split("-", maxsplit=1)
    if len(partes) == 2:
        return f"{partes[1]} {partes[0]}"
    return periodo


def formatar_data_referencia(valor: str | None) -> str:
    if not valor:
        return "Não informada"
    try:
        data = date.fromisoformat(valor)
    except ValueError:
        return valor
    return data.strftime("%d/%m/%Y")


def formatar_numero(valor: Any, *, sinal: bool = False) -> str:
    numero = _numero_ou_none(valor)
    if numero is None:
        return "Sem base"
    formato = f"{numero:+.2f}" if sinal else f"{numero:.2f}"
    return formato.replace(".", ",")


_STATUS_APRESENTACAO: dict[str, str] = {
    "Completa": "Avaliação Completa",
    "Parcial": "Avaliação Parcial",
    "Não avaliada": "Sem Avaliação",
    "Avaliação Completa": "Avaliação Completa",
    "Avaliação Parcial": "Avaliação Parcial",
    "Sem Avaliação": "Sem Avaliação",
}


def formatar_status_avaliacao(valor: Any) -> str:
    """Converte o estado interno da avaliação para um rótulo público claro."""
    status = str(valor or "").strip()
    if not status:
        return "Sem Avaliação"
    return _STATUS_APRESENTACAO.get(status, status)


def _validar_nota(valor: Any, contexto: str, erros: list[str]) -> None:
    if valor is None:
        return
    numero = _numero_ou_none(valor)
    if numero is None:
        erros.append(f"{contexto}: nota não numérica.")
        return
    if numero < 0 or numero > 10:
        erros.append(f"{contexto}: nota fora da escala de 0 a 10.")
        return
    if abs(numero * 2 - round(numero * 2)) > 1e-9:
        erros.append(f"{contexto}: nota deve usar passos de 0,5.")


def validar_integridade_avaliacoes(
    documento: Mapping[str, Any],
    jogadores: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """Retorna todos os erros bloqueantes sem modificar a fonte."""
    erros: list[str] = []
    if str(documento.get("schema_version")) != "1.0":
        erros.append("schema_version de avaliações deve ser '1.0'.")

    fonte = documento.get("fonte")
    if not isinstance(fonte, Mapping):
        erros.append("A fonte das avaliações não foi informada.")
    elif len(str(fonte.get("sha256") or "")) != 64:
        erros.append("O hash SHA-256 da planilha é inválido.")

    avaliacoes = documento.get("avaliacoes")
    if not isinstance(avaliacoes, list):
        return [*erros, "O campo 'avaliacoes' precisa ser uma lista."]

    ids_jogadores: dict[str, str] = {}
    if jogadores is not None:
        for nome, dados in jogadores.items():
            identificador = str(dados.get("id_atleta") or "").strip()
            if not identificador:
                erros.append(f"{nome}: id_atleta ausente no cadastro.")
                continue
            if identificador in ids_jogadores:
                erros.append(
                    f"id_atleta duplicado no cadastro: {identificador}."
                )
            ids_jogadores[identificador] = nome

    chaves: set[tuple[str, str]] = set()
    datas_por_periodo: dict[str, set[str]] = defaultdict(set)
    posicoes = set(POSICOES_OFICIAIS)

    for indice, item in enumerate(avaliacoes, start=1):
        contexto = f"Avaliação {indice}"
        if not isinstance(item, Mapping):
            erros.append(f"{contexto}: registro precisa ser um objeto.")
            continue

        id_atleta = str(item.get("id_atleta") or "").strip()
        nome = str(item.get("nome") or "").strip()
        periodo = str(item.get("periodo") or "").strip()
        data_referencia = str(item.get("data_referencia") or "").strip()
        chave = (id_atleta, periodo)

        if not id_atleta or not nome:
            erros.append(f"{contexto}: atleta sem ID ou nome.")
        if chave in chaves:
            erros.append(
                f"{contexto}: duplicidade para {id_atleta} em {periodo}."
            )
        chaves.add(chave)

        try:
            ano = int(item.get("ano"))
        except (TypeError, ValueError):
            ano = 0
            erros.append(f"{contexto}: ano inválido.")
        trimestre = str(item.get("trimestre") or "")
        if trimestre not in {"T1", "T2", "T3", "T4"}:
            erros.append(f"{contexto}: trimestre inválido ({trimestre}).")
        if periodo != f"{ano}-{trimestre}":
            erros.append(f"{contexto}: período incompatível com ano/trimestre.")
        if ano == 2026 and trimestre == "T1":
            erros.append("T1 2026 foi excluído por decisão editorial.")

        try:
            referencia = date.fromisoformat(data_referencia)
        except ValueError:
            referencia = None
            erros.append(f"{contexto}: data de referência inválida.")
        esperadas = {
            "T1": (3, 31),
            "T2": (6, 30),
            "T3": (9, 30),
            "T4": (12, 31),
        }
        if referencia is not None:
            mes_dia = esperadas.get(trimestre)
            if (
                referencia.year != ano
                or mes_dia is None
                or (referencia.month, referencia.day) != mes_dia
            ):
                erros.append(
                    f"{contexto}: data não corresponde ao fechamento de {trimestre}."
                )
            datas_por_periodo[periodo].add(data_referencia)

        posicao = str(item.get("posicao_snapshot") or "")
        if posicao not in posicoes:
            erros.append(f"{contexto}: posição oficial inválida ({posicao}).")

        for analista in ("vini", "beto"):
            bloco = item.get(analista)
            if not isinstance(bloco, Mapping):
                erros.append(f"{contexto}: bloco '{analista}' inválido.")
                continue
            _validar_nota(
                bloco.get("capacidade_atual"),
                f"{contexto}/{analista}/capacidade",
                erros,
            )
            _validar_nota(
                bloco.get("potencial_2030"),
                f"{contexto}/{analista}/potencial",
                erros,
            )
            observacao = bloco.get("observacao")
            if observacao is not None and not isinstance(observacao, str):
                erros.append(
                    f"{contexto}/{analista}: observação precisa ser texto."
                )

        if jogadores is not None and id_atleta:
            nome_cadastrado = ids_jogadores.get(id_atleta)
            if nome_cadastrado is None:
                erros.append(
                    f"{contexto}: ID {id_atleta} não existe no cadastro."
                )
            elif nome_cadastrado != nome:
                erros.append(
                    f"{contexto}: nome '{nome}' não corresponde ao ID "
                    f"{id_atleta} ('{nome_cadastrado}')."
                )

    for periodo, datas in datas_por_periodo.items():
        if len(datas) != 1:
            erros.append(
                f"O período {periodo} possui datas de referência divergentes."
            )
    return erros


def carregar_avaliacoes(
    caminho: Path | str = AVALIACOES_FILE,
    *,
    jogadores: Mapping[str, Mapping[str, Any]] | None = None,
) -> BaseAvaliacoes:
    """Lê e valida o JSON temporal; nunca tenta repará-lo automaticamente."""
    arquivo = Path(caminho)
    if not arquivo.exists():
        raise AvaliacoesIntegrityError(
            f"O arquivo {arquivo.name} não foi encontrado."
        )
    try:
        documento = json.loads(arquivo.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as erro:
        raise AvaliacoesIntegrityError(
            f"O arquivo {arquivo.name} está inválido: {erro}"
        ) from erro
    if not isinstance(documento, Mapping):
        raise AvaliacoesIntegrityError(
            "O JSON de avaliações precisa conter um objeto no nível principal."
        )

    erros = validar_integridade_avaliacoes(documento, jogadores)
    if erros:
        raise AvaliacoesIntegrityError(
            "A base de avaliações contém erros bloqueantes: "
            + " | ".join(erros)
        )

    return BaseAvaliacoes(
        schema_version=str(documento["schema_version"]),
        fonte=dict(documento["fonte"]),
        avaliacoes=tuple(
            dict(item) for item in documento.get("avaliacoes", [])
        ),
    )
