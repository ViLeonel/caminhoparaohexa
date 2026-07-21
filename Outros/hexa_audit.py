"""Eventos imutáveis de auditoria fora do JSON canônico dos jogadores."""

from __future__ import annotations

import copy
import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping, Protocol, Sequence, runtime_checkable

__all__ = [
    "AcaoAuditoria",
    "AuditoriaError",
    "AuditoriaRepository",
    "EventoAuditoria",
    "JsonlAuditoriaRepository",
    "gerar_eventos_alteracao",
]


class AuditoriaError(RuntimeError):
    """Falha ao persistir ou ler o histórico de auditoria."""


class AcaoAuditoria(str, Enum):
    CRIACAO = "criacao"
    ALTERACAO = "alteracao"
    REMOCAO = "remocao"


@dataclass(frozen=True, slots=True)
class EventoAuditoria:
    """Registro imutável de uma alteração em jogador."""

    id_evento: str
    ocorrido_em: str
    jogador: str
    campo: str
    acao: AcaoAuditoria
    valor_anterior: Any
    valor_novo: Any
    origem: str
    versao_anterior: str
    versao_nova: str
    ator_email: str = ""
    ator_nome: str = ""
    ator_id: str = ""

    def para_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        dados["acao"] = self.acao.value
        return dados


@runtime_checkable
class AuditoriaRepository(Protocol):
    def registrar(self, eventos: Sequence[EventoAuditoria]) -> None:
        ...

    def listar(
        self,
        *,
        jogador: str | None = None,
        limite: int | None = None,
    ) -> list[EventoAuditoria]:
        ...


def _copia_json(valor: Any) -> Any:
    """Produz cópia segura e serializável para preservar o instante do evento."""
    return json.loads(json.dumps(valor, ensure_ascii=False, default=str))


def _novo_evento(
    *,
    jogador: str,
    campo: str,
    acao: AcaoAuditoria,
    valor_anterior: Any,
    valor_novo: Any,
    origem: str,
    versao_anterior: str,
    versao_nova: str,
    ocorrido_em: str,
    ator_email: str = "",
    ator_nome: str = "",
    ator_id: str = "",
) -> EventoAuditoria:
    return EventoAuditoria(
        id_evento=str(uuid.uuid4()),
        ocorrido_em=ocorrido_em,
        jogador=jogador,
        campo=campo,
        acao=acao,
        valor_anterior=_copia_json(valor_anterior),
        valor_novo=_copia_json(valor_novo),
        origem=str(origem or "aplicacao"),
        versao_anterior=str(versao_anterior),
        versao_nova=str(versao_nova),
        ator_email=str(ator_email),
        ator_nome=str(ator_nome),
        ator_id=str(ator_id),
    )


def gerar_eventos_alteracao(
    antes: Mapping[str, Mapping[str, Any]],
    depois: Mapping[str, Mapping[str, Any]],
    *,
    origem: str,
    versao_anterior: str,
    versao_nova: str,
    ocorrido_em: str | None = None,
    ator_email: str = "",
    ator_nome: str = "",
    ator_id: str = "",
) -> list[EventoAuditoria]:
    """Calcula diferenças campo a campo sem gerar eventos redundantes."""
    timestamp = ocorrido_em or datetime.now(timezone.utc).isoformat()
    eventos: list[EventoAuditoria] = []

    nomes = sorted(set(antes) | set(depois), key=str.casefold)
    for nome in nomes:
        anterior = antes.get(nome)
        novo = depois.get(nome)

        if anterior is None and novo is not None:
            for campo in sorted(novo):
                eventos.append(
                    _novo_evento(
                        jogador=nome,
                        campo=campo,
                        acao=AcaoAuditoria.CRIACAO,
                        valor_anterior=None,
                        valor_novo=novo[campo],
                        origem=origem,
                        versao_anterior=versao_anterior,
                        versao_nova=versao_nova,
                        ocorrido_em=timestamp,
                        ator_email=ator_email,
                        ator_nome=ator_nome,
                        ator_id=ator_id,
                    )
                )
            continue

        if anterior is not None and novo is None:
            for campo in sorted(anterior):
                eventos.append(
                    _novo_evento(
                        jogador=nome,
                        campo=campo,
                        acao=AcaoAuditoria.REMOCAO,
                        valor_anterior=anterior[campo],
                        valor_novo=None,
                        origem=origem,
                        versao_anterior=versao_anterior,
                        versao_nova=versao_nova,
                        ocorrido_em=timestamp,
                        ator_email=ator_email,
                        ator_nome=ator_nome,
                        ator_id=ator_id,
                    )
                )
            continue

        if anterior is None or novo is None:
            raise AuditoriaError(
                "Estado inconsistente ao calcular alteração de auditoria."
            )
        campos = sorted(set(anterior) | set(novo))
        for campo in campos:
            valor_anterior = anterior.get(campo)
            valor_novo = novo.get(campo)
            if valor_anterior == valor_novo:
                continue
            eventos.append(
                _novo_evento(
                    jogador=nome,
                    campo=campo,
                    acao=AcaoAuditoria.ALTERACAO,
                    valor_anterior=valor_anterior,
                    valor_novo=valor_novo,
                    origem=origem,
                    versao_anterior=versao_anterior,
                    versao_nova=versao_nova,
                    ocorrido_em=timestamp,
                    ator_email=ator_email,
                    ator_nome=ator_nome,
                    ator_id=ator_id,
                )
            )

    return eventos


class JsonlAuditoriaRepository:
    """Histórico append-only lógico com substituição atômica do arquivo JSONL."""

    def __init__(
        self,
        caminho: Path,
        *,
        timeout_bloqueio: float = 2.0,
        bloqueio_obsoleto_apos: float = 30.0,
    ) -> None:
        self.caminho = Path(caminho)
        self.timeout_bloqueio = max(0.1, float(timeout_bloqueio))
        self.bloqueio_obsoleto_apos = max(1.0, float(bloqueio_obsoleto_apos))

    @property
    def caminho_bloqueio(self) -> Path:
        return self.caminho.with_suffix(self.caminho.suffix + ".lock")

    @contextmanager
    def _bloqueio_exclusivo(self) -> Iterator[None]:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        inicio = time.monotonic()

        while True:
            try:
                descritor = os.open(
                    self.caminho_bloqueio,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.write(
                    descritor,
                    (
                        f"pid={os.getpid()}\n"
                        f"criado_em={datetime.now(timezone.utc).isoformat()}\n"
                    ).encode("utf-8"),
                )
                os.close(descritor)
                break
            except FileExistsError:
                try:
                    idade = time.time() - self.caminho_bloqueio.stat().st_mtime
                    if idade > self.bloqueio_obsoleto_apos:
                        self.caminho_bloqueio.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue

                if time.monotonic() - inicio >= self.timeout_bloqueio:
                    raise AuditoriaError(
                        "O histórico de auditoria está ocupado por outra gravação."
                    )
                time.sleep(0.05)

        try:
            yield
        finally:
            self.caminho_bloqueio.unlink(missing_ok=True)

    @staticmethod
    def _evento_de_dict(dados: Mapping[str, Any]) -> EventoAuditoria:
        try:
            return EventoAuditoria(
                id_evento=str(dados["id_evento"]),
                ocorrido_em=str(dados["ocorrido_em"]),
                jogador=str(dados["jogador"]),
                campo=str(dados["campo"]),
                acao=AcaoAuditoria(str(dados["acao"])),
                valor_anterior=copy.deepcopy(dados.get("valor_anterior")),
                valor_novo=copy.deepcopy(dados.get("valor_novo")),
                origem=str(dados["origem"]),
                versao_anterior=str(dados["versao_anterior"]),
                versao_nova=str(dados["versao_nova"]),
                ator_email=str(dados.get("ator_email") or ""),
                ator_nome=str(dados.get("ator_nome") or ""),
                ator_id=str(dados.get("ator_id") or ""),
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise AuditoriaError("Evento de auditoria inválido.") from erro

    def registrar(self, eventos: Sequence[EventoAuditoria]) -> None:
        if not eventos:
            return

        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(self.caminho.suffix + ".tmp")

        with self._bloqueio_exclusivo():
            linhas_existentes = (
                self.caminho.read_text(encoding="utf-8").splitlines()
                if self.caminho.exists()
                else []
            )
            ids_existentes: set[str] = set()
            for linha in linhas_existentes:
                if not linha.strip():
                    continue
                try:
                    dados = json.loads(linha)
                    ids_existentes.add(str(dados["id_evento"]))
                except (json.JSONDecodeError, KeyError, TypeError) as erro:
                    raise AuditoriaError(
                        f"O arquivo {self.caminho.name} contém evento inválido."
                    ) from erro

            novas_linhas = list(linhas_existentes)
            for evento in eventos:
                if evento.id_evento in ids_existentes:
                    continue
                novas_linhas.append(
                    json.dumps(
                        evento.para_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
                ids_existentes.add(evento.id_evento)

            conteudo = "\n".join(novas_linhas)
            if conteudo:
                conteudo += "\n"
            temporario.write_text(conteudo, encoding="utf-8")

            for linha in temporario.read_text(encoding="utf-8").splitlines():
                if linha.strip():
                    self._evento_de_dict(json.loads(linha))

            temporario.replace(self.caminho)

    def listar(
        self,
        *,
        jogador: str | None = None,
        limite: int | None = None,
    ) -> list[EventoAuditoria]:
        if not self.caminho.exists():
            return []

        eventos: list[EventoAuditoria] = []
        for numero, linha in enumerate(
            self.caminho.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not linha.strip():
                continue
            try:
                evento = self._evento_de_dict(json.loads(linha))
            except (json.JSONDecodeError, AuditoriaError) as erro:
                raise AuditoriaError(
                    f"Evento inválido na linha {numero} de {self.caminho.name}."
                ) from erro
            if jogador is None or evento.jogador == jogador:
                eventos.append(evento)

        eventos.sort(key=lambda evento: evento.ocorrido_em)
        if limite is not None:
            return eventos[-max(0, int(limite)) :]
        return eventos
