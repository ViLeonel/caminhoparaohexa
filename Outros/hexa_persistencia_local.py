"""Persistência local e privada da convocação no navegador.

A seleção é serializada por ID estável do atleta e por formação. O módulo não
grava arquivos no servidor, não mistura usuários e não persiste dados sensíveis.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

import streamlit as st

from hexa_session import (
    chave_reserva_livre,
    chave_reserva_posicional,
    chave_titular,
    limpar_todas_convocacoes,
    quantidade_vagas_livres,
    reconciliar_convocacao,
)
from hexa_taticas import SlotTatico

__all__ = [
    "CHAVE_AVISO_RESTAURACAO",
    "CHAVE_LIMPEZA_SOLICITADA",
    "CHAVE_RESTAURACAO_CONCLUIDA",
    "LOCAL_STORAGE_KEY",
    "PersistenciaLocalResultado",
    "apagar_convocacoes_locais",
    "restaurar_convocacoes",
    "serializar_convocacoes",
    "sincronizar_persistencia_local",
]


SCHEMA_VERSION = 1
LOCAL_STORAGE_KEY = "caminho_hexa_2030_convocacoes_v1"
CHAVE_RESTAURACAO_CONCLUIDA = "_hexa_local_storage_restaurado"
CHAVE_LIMPEZA_SOLICITADA = "_hexa_local_storage_limpar"
CHAVE_DISPONIBILIDADE = "_hexa_local_storage_disponivel"
CHAVE_AVISO_RESTAURACAO = "_hexa_local_storage_aviso_restauracao"

_COMPONENT_HTML = """
<div id="hexa-local-storage-status" aria-hidden="true"></div>
"""

_COMPONENT_CSS = """
#hexa-local-storage-status {
    display: none;
    width: 0;
    height: 0;
    overflow: hidden;
}
"""

_COMPONENT_JS = """
export default function({ data, setStateValue }) {
  const storageKey = data?.storage_key;
  const action = data?.action ?? "sync";

  if (!storageKey) {
    return;
  }

  try {
    if (action === "load") {
      let payload = null;
      const raw = window.localStorage.getItem(storageKey);
      if (raw) {
        try {
          payload = JSON.parse(raw);
        } catch {
          window.localStorage.removeItem(storageKey);
        }
      }
      setStateValue("snapshot", {
        loaded: true,
        available: true,
        payload: payload,
      });
      return;
    }

    if (action === "clear") {
      window.localStorage.removeItem(storageKey);
      return;
    }

    if (action === "sync" && data?.payload) {
      const serialized = JSON.stringify(data.payload);
      if (window.localStorage.getItem(storageKey) !== serialized) {
        window.localStorage.setItem(storageKey, serialized);
      }
    }
  } catch {
    if (action === "load") {
      setStateValue("snapshot", {
        loaded: true,
        available: false,
        payload: null,
      });
    }
  }
}
"""


try:
    _storage_component = st.components.v2.component(
        name="hexa_local_storage_convocacao",
        html=_COMPONENT_HTML,
        css=_COMPONENT_CSS,
        js=_COMPONENT_JS,
        isolate_styles=True,
    )
except (AttributeError, TypeError):
    _storage_component = None


@dataclass(frozen=True, slots=True)
class PersistenciaLocalResultado:
    pronta: bool
    disponivel: bool
    restaurados: int = 0
    descartados: int = 0


def _mapas_ids(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    nome_para_id: dict[str, str] = {}
    id_para_nome: dict[str, str] = {}
    for nome, dados in jogadores.items():
        id_atleta = str(dados.get("id_atleta") or "").strip()
        if not id_atleta:
            continue
        nome_para_id[str(nome)] = id_atleta
        id_para_nome[id_atleta] = str(nome)
    return nome_para_id, id_para_nome


def _id_do_estado(
    estado: Mapping[str, Any],
    chave: str,
    nome_para_id: Mapping[str, str],
) -> str | None:
    valor = estado.get(chave)
    if not isinstance(valor, str):
        return None
    return nome_para_id.get(valor)


def serializar_convocacoes(
    estado: MutableMapping[str, Any],
    taticas: Mapping[str, Mapping[str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Produz um documento JSON estável, usando IDs e slots alinhados."""
    nome_para_id, _ = _mapas_ids(jogadores)
    convocacoes: dict[str, Any] = {}

    for tatica, layout in taticas.items():
        reconciliar_convocacao(
            estado,
            tatica,
            layout,
            jogadores,
        )
        titulares = [
            _id_do_estado(
                estado,
                chave_titular(tatica, indice),
                nome_para_id,
            )
            for indice in range(len(layout))
        ]
        posicionais = [
            _id_do_estado(
                estado,
                chave_reserva_posicional(tatica, indice),
                nome_para_id,
            )
            for indice in range(len(layout))
        ]
        livres = [
            _id_do_estado(
                estado,
                chave_reserva_livre(tatica, indice),
                nome_para_id,
            )
            for indice in range(quantidade_vagas_livres(len(layout)))
        ]
        if any(titulares) or any(posicionais) or any(livres):
            convocacoes[tatica] = {
                "titulares": titulares,
                "reservas_posicionais": posicionais,
                "reservas_livres": livres,
            }

    tatica_ativa = estado.get("tactical_selector")
    if tatica_ativa not in taticas:
        tatica_ativa = next(iter(taticas), None)

    return {
        "schema_version": SCHEMA_VERSION,
        "tatica_ativa": tatica_ativa,
        "convocacoes": convocacoes,
    }


def _lista_ids(valor: Any, tamanho: int) -> list[str | None]:
    if not isinstance(valor, list):
        return [None] * tamanho
    resultado: list[str | None] = []
    for item in valor[:tamanho]:
        resultado.append(str(item) if isinstance(item, str) and item else None)
    return [*resultado, *([None] * max(0, tamanho - len(resultado)))]


def restaurar_convocacoes(
    estado: MutableMapping[str, Any],
    payload: Any,
    taticas: Mapping[str, Mapping[str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> tuple[int, int]:
    """Restaura um documento local, descartando IDs e posições inválidos."""
    if not isinstance(payload, Mapping):
        return 0, 0
    if payload.get("schema_version") != SCHEMA_VERSION:
        return 0, 1

    _, id_para_nome = _mapas_ids(jogadores)
    convocacoes = payload.get("convocacoes")
    if not isinstance(convocacoes, Mapping):
        convocacoes = {}

    limpar_todas_convocacoes(estado, taticas)
    restaurados = 0
    descartados = 0

    tatica_ativa = payload.get("tatica_ativa")
    if isinstance(tatica_ativa, str) and tatica_ativa in taticas:
        estado["tactical_selector"] = tatica_ativa

    for tatica, layout in taticas.items():
        bloco = convocacoes.get(tatica)
        if not isinstance(bloco, Mapping):
            continue

        titulares = _lista_ids(bloco.get("titulares"), len(layout))
        posicionais = _lista_ids(
            bloco.get("reservas_posicionais"),
            len(layout),
        )
        livres = _lista_ids(
            bloco.get("reservas_livres"),
            quantidade_vagas_livres(len(layout)),
        )

        for indice, id_atleta in enumerate(titulares):
            if id_atleta is None:
                continue
            nome = id_para_nome.get(id_atleta)
            if nome is None:
                descartados += 1
                continue
            estado[chave_titular(tatica, indice)] = nome
            restaurados += 1

        for indice, id_atleta in enumerate(posicionais):
            if id_atleta is None:
                continue
            nome = id_para_nome.get(id_atleta)
            if nome is None:
                descartados += 1
                continue
            estado[chave_reserva_posicional(tatica, indice)] = nome
            restaurados += 1

        for indice, id_atleta in enumerate(livres):
            if id_atleta is None:
                continue
            nome = id_para_nome.get(id_atleta)
            if nome is None:
                descartados += 1
                continue
            estado[chave_reserva_livre(tatica, indice)] = nome
            restaurados += 1

        relatorio = reconciliar_convocacao(
            estado,
            tatica,
            layout,
            jogadores,
        )
        descartados += len(relatorio["chaves_limpas"])

    return restaurados, descartados


def apagar_convocacoes_locais(
    estado: MutableMapping[str, Any],
    taticas: Mapping[str, Mapping[str, SlotTatico]],
) -> None:
    """Limpa a sessão e solicita a exclusão do item no navegador."""
    limpar_todas_convocacoes(estado, taticas)
    estado[CHAVE_LIMPEZA_SOLICITADA] = True
    estado[CHAVE_RESTAURACAO_CONCLUIDA] = True
    estado[CHAVE_AVISO_RESTAURACAO] = False


def _snapshot_resultado(resultado: Any) -> Mapping[str, Any]:
    snapshot = getattr(resultado, "snapshot", None)
    return snapshot if isinstance(snapshot, Mapping) else {}


def sincronizar_persistencia_local(
    estado: MutableMapping[str, Any],
    taticas: Mapping[str, Mapping[str, SlotTatico]],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> PersistenciaLocalResultado:
    """Carrega uma vez e depois sincroniza automaticamente com o navegador."""
    if _storage_component is None:
        estado[CHAVE_RESTAURACAO_CONCLUIDA] = True
        estado[CHAVE_DISPONIBILIDADE] = False
        return PersistenciaLocalResultado(pronta=True, disponivel=False)

    limpar_solicitado = bool(estado.pop(CHAVE_LIMPEZA_SOLICITADA, False))
    restauracao_concluida = bool(
        estado.get(CHAVE_RESTAURACAO_CONCLUIDA, False)
    )

    if limpar_solicitado:
        acao = "clear"
        payload = None
    elif restauracao_concluida:
        acao = "sync"
        payload = serializar_convocacoes(
            estado,
            taticas,
            jogadores,
        )
    else:
        acao = "load"
        payload = None

    try:
        resultado = _storage_component(
            key="hexa_local_storage_convocacao",
            data={
                "action": acao,
                "storage_key": LOCAL_STORAGE_KEY,
                "payload": payload,
            },
            default={
                "snapshot": {
                    "loaded": False,
                    "available": True,
                    "payload": None,
                }
            },
            on_snapshot_change=lambda: None,
            width="content",
            height=0,
        )
    except Exception:
        # Alguns ambientes de teste, navegadores restritivos ou versões sem
        # registro de components.v2 conseguem criar o componente, mas falham
        # apenas na renderização. A persistência local é opcional e não deve
        # impedir o restante do aplicativo de funcionar.
        estado[CHAVE_RESTAURACAO_CONCLUIDA] = True
        estado[CHAVE_DISPONIBILIDADE] = False
        return PersistenciaLocalResultado(pronta=True, disponivel=False)

    if restauracao_concluida or limpar_solicitado:
        disponivel = bool(
            estado.get(CHAVE_DISPONIBILIDADE, True)
        )
        return PersistenciaLocalResultado(
            pronta=True,
            disponivel=disponivel,
        )

    snapshot = _snapshot_resultado(resultado)
    if not snapshot.get("loaded"):
        return PersistenciaLocalResultado(
            pronta=False,
            disponivel=True,
        )

    disponivel = bool(snapshot.get("available", False))
    restaurados, descartados = restaurar_convocacoes(
        estado,
        snapshot.get("payload"),
        taticas,
        jogadores,
    )
    estado[CHAVE_RESTAURACAO_CONCLUIDA] = True
    estado[CHAVE_DISPONIBILIDADE] = disponivel
    estado[CHAVE_AVISO_RESTAURACAO] = restaurados > 0

    return PersistenciaLocalResultado(
        pronta=True,
        disponivel=disponivel,
        restaurados=restaurados,
        descartados=descartados,
    )
