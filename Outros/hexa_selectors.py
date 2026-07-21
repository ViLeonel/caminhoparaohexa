"""Seletores e transformações puras para as telas do aplicativo."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from hexa_avaliacoes import calcular_metricas_avaliacao
from hexa_config import ANO_BASE_DADOS, ANO_COPA, LIMITE_DESTAQUES_ANALISE
from hexa_data import (
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_taticas import SlotTatico, indice_adaptabilidade

__all__ = [
    "LINHAS_TATICAS",
    "calcular_medias_titulares",
    "construir_avaliacoes",
    "construir_registros_mercado",
    "construir_registros_roster",
    "construir_visualizacao_tatica_lista",
    "filtrar_jogadores",
    "formatar_texto_editorial",
    "linha_tatica_do_slot",
    "ordenar_consensos",
    "ordenar_divergencias",
]


NAO_INFORMADO_FONTE = "Não informado pela fonte"


def _texto_apresentacao(valor: Any) -> str:
    if valor in (None, "", [], "N/A"):
        return NAO_INFORMADO_FONTE
    return str(valor)


_SUBSTITUICOES_ANALISTAS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bVini Leoneo\b", flags=re.IGNORECASE), "Vini Leonel"),
    (
        re.compile(r"\b" + "Vinicius" + r" Leonel\b", flags=re.IGNORECASE),
        "Vini Leonel",
    ),
    (
        re.compile(r"\b" + "Roberto" + r" Muñoz\b", flags=re.IGNORECASE),
        "Beto Muñoz",
    ),
    (re.compile(r"\b" + "Roberto" + r"\b", flags=re.IGNORECASE), "Beto"),
)


def formatar_texto_editorial(valor: Any) -> str:
    """Normaliza apenas nomes de apresentação, sem alterar a fonte canônica."""
    texto = _texto_apresentacao(valor)
    for padrao, substituicao in _SUBSTITUICOES_ANALISTAS:
        texto = padrao.sub(substituicao, texto)
    return texto


def filtrar_jogadores(
    jogadores: Mapping[str, Mapping[str, Any]],
    busca: str = "",
    posicao: str | None = None,
    grupo: str | None = None,
) -> list[tuple[str, Mapping[str, Any]]]:
    """Filtra atletas por texto, posição oficial e grupo cadastral legado."""
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
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]] | None = None,
    busca: str = "",
    posicao: str | None = None,
    grupo: str | None = None,
    ano_base: int = ANO_BASE_DADOS,
    ano_copa: int = ANO_COPA,
) -> list[dict[str, Any]]:
    """Monta a lista cadastral usando exclusivamente a avaliação temporal."""
    diferenca_anos = ano_copa - ano_base
    avaliacoes = avaliacoes_por_nome or {}
    registros: list[dict[str, Any]] = []

    for nome, dados in filtrar_jogadores(jogadores, busca, posicao, grupo):
        try:
            idade = int(dados.get("idade") or 0)
        except (TypeError, ValueError):
            idade = 0

        registro_avaliacao = avaliacoes.get(nome)
        metricas = (
            calcular_metricas_avaliacao(registro_avaliacao)
            if registro_avaliacao is not None
            else {
                "capacidade_atual_media": None,
                "potencial_2030_medio": None,
                "saldo_projetado": None,
                "status": "Não avaliada",
            }
        )
        atual = valor_mercado_atual(dados)
        maximo = valor_mercado_maximo(dados)
        registros.append(
            {
                "Nome": nome,
                "Posição": _texto_apresentacao(dados.get("posicao")),
                "Clube atual": _texto_apresentacao(dados.get("clube")),
                f"Idade {ano_base}": idade if idade > 0 else None,
                f"Idade {ano_copa}": (
                    idade + diferenca_anos if idade > 0 else None
                ),
                "Capacidade atual": metricas["capacidade_atual_media"],
                "Potencial 2030": metricas["potencial_2030_medio"],
                "Saldo projetado": metricas["saldo_projetado"],
                "Situação": metricas["status"],
                "Valor atual": formatar_valor_milhoes(atual),
                "Pico de mercado": formatar_valor_milhoes(maximo),
                "% do pico de mercado": (
                    round(percentual_do_pico(dados) or 0.0, 1)
                    if atual > 0
                    else None
                ),
            }
        )
    return registros


def construir_avaliacoes(
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Cria linhas analíticas apenas com avaliações trimestrais completas."""
    resultado: list[dict[str, Any]] = []
    for nome, registro in avaliacoes_por_nome.items():
        metricas = calcular_metricas_avaliacao(registro)
        if not metricas["avaliacao_completa"]:
            continue
        resultado.append(
            {
                "Nome": nome,
                "Posição": _texto_apresentacao(
                    registro.get("posicao_snapshot")
                ),
                "Capacidade atual": metricas["capacidade_atual_media"],
                "Potencial 2030": metricas["potencial_2030_medio"],
                "Saldo projetado": metricas["saldo_projetado"],
                "Situação": metricas["status"],
            }
        )
    return resultado


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
                "Pico de mercado (M€)": maximo,
                "% do pico de mercado": percentual_do_pico(dados) or 0.0,
                "Diferença para o pico de mercado (M€)": max(maximo - atual, 0.0),
                "Atualização do mercado": _texto_apresentacao(
                    dados.get("tm_ultima_atualizacao")
                ),
            }
        )
    return mercado


def calcular_medias_titulares(
    titulares: Sequence[Mapping[str, Any]],
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, float | int | None]:
    """Compatibilidade pública: resume titulares com o contrato temporal."""
    avaliacoes = avaliacoes_por_nome or {}
    metricas: list[dict[str, Any]] = []
    for dados in titulares:
        nome = str(dados.get("nome") or "")
        registro = avaliacoes.get(nome)
        if registro is None:
            continue
        metricas.append(calcular_metricas_avaliacao(registro))

    def media(campo: str) -> float | None:
        valores = [
            float(item[campo])
            for item in metricas
            if item.get(campo) is not None
        ]
        return sum(valores) / len(valores) if valores else None

    return {
        "capacidade_atual": media("capacidade_atual_media"),
        "potencial_2030": media("potencial_2030_medio"),
        "saldo_projetado": media("saldo_projetado"),
        "com_avaliacao": sum(bool(item["tem_avaliacao"]) for item in metricas),
        "completos": sum(
            bool(item["avaliacao_completa"]) for item in metricas
        ),
    }


def ordenar_consensos(
    avaliacoes: Sequence[Mapping[str, Any]],
    limite: int = LIMITE_DESTAQUES_ANALISE,
) -> list[Mapping[str, Any]]:
    return sorted(
        avaliacoes,
        key=lambda item: (
            float(item["Diferença"]),
            -float(item["Média"]),
            str(item["Nome"]).casefold(),
        ),
    )[:limite]


def ordenar_divergencias(
    avaliacoes: Sequence[Mapping[str, Any]],
    limite: int = LIMITE_DESTAQUES_ANALISE,
) -> list[Mapping[str, Any]]:
    return sorted(
        avaliacoes,
        key=lambda item: (
            -float(item["Diferença"]),
            -float(item["Média"]),
            str(item["Nome"]).casefold(),
        ),
    )[:limite]


LINHAS_TATICAS: tuple[str, ...] = (
    "Goleiro",
    "Defesa",
    "Meio-campo",
    "Ataque",
)

_POSICOES_POR_LINHA: dict[str, frozenset[str]] = {
    "Goleiro": frozenset({"Goleiro"}),
    "Defesa": frozenset(
        {"Lateral-direito", "Lateral-esquerdo", "Zagueiro"}
    ),
    "Meio-campo": frozenset(
        {
            "Volante",
            "Mezzala esquerdo",
            "Mezzala direito",
            "Meia-esquerda",
            "Meia-direita",
            "Meia-armador",
        }
    ),
    "Ataque": frozenset(
        {
            "Ponta-esquerda",
            "Ponta-direita",
            "Segundo atacante",
            "Centroavante",
        }
    ),
}


def linha_tatica_do_slot(configuracao: SlotTatico) -> str:
    for posicao in configuracao.posicoes:
        for linha in LINHAS_TATICAS:
            if posicao in _POSICOES_POR_LINHA[linha]:
                return linha
    return "Meio-campo"


def construir_visualizacao_tatica_lista(
    layout: Mapping[str, SlotTatico],
    escalados: Mapping[str, str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Cria lista acessível com capacidade, potencial e situação do período."""
    avaliacoes = avaliacoes_por_nome or {}
    linhas: dict[str, list[dict[str, Any]]] = {
        linha: [] for linha in LINHAS_TATICAS
    }

    for slot, configuracao in layout.items():
        nome = escalados.get(slot)
        dados = jogadores.get(nome, {}) if nome else {}
        indice = (
            indice_adaptabilidade(dados, configuracao.posicoes)
            if dados
            else -1
        )
        registro = avaliacoes.get(nome or "")
        metricas = (
            calcular_metricas_avaliacao(registro)
            if registro is not None
            else {
                "capacidade_atual_media": None,
                "potencial_2030_medio": None,
                "status": "Não avaliada",
            }
        )

        linhas[linha_tatica_do_slot(configuracao)].append(
            {
                "slot": slot,
                "tag": configuracao.tag,
                "nome": nome or "",
                "preenchido": bool(nome and dados),
                "indice_adaptabilidade": indice,
                "capacidade_atual": metricas["capacidade_atual_media"],
                "potencial_2030": metricas["potencial_2030_medio"],
                "situacao_avaliacao": metricas["status"],
            }
        )

    return linhas
