"""Contexto imutável compartilhado entre o entrypoint e as telas públicas."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from hexa_avaliacoes import BaseAvaliacoes

__all__ = ["AppContext"]


@dataclass(frozen=True, slots=True)
class AppContext:
    """Dependências necessárias para renderizar uma tela pública."""

    menu: str
    jogadores: Mapping[str, Mapping[str, Any]]
    base_avaliacoes: BaseAvaliacoes
    periodo: str
