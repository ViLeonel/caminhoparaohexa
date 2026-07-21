"""Contratos e implementação de persistência dos jogadores.

O domínio usa um repositório para desacoplar regras de normalização e interface
da tecnologia de armazenamento. A implementação padrão continua sendo JSON,
com controle otimista de concorrência, backup e escrita atômica.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Protocol, runtime_checkable

__all__ = [
    "ConflitoConcorrenciaError",
    "DataIntegrityError",
    "JogadoresRepository",
    "JsonJogadoresRepository",
    "RegistroVersao",
    "RepositorioOcupadoError",
    "ResultadoLeitura",
    "VERSAO_AUSENTE",
]



class DataIntegrityError(RuntimeError):
    """Indica que a fonte de dados não pôde ser lida sem risco de perda."""


class ConflitoConcorrenciaError(RuntimeError):
    """Indica que a fonte mudou desde a leitura realizada pela sessão."""

    def __init__(self, versao_esperada: str, versao_atual: str) -> None:
        self.versao_esperada = versao_esperada
        self.versao_atual = versao_atual
        super().__init__(
            "A base de jogadores foi alterada por outra sessão desde o carregamento. "
            "Recarregue a aplicação antes de tentar salvar novamente."
        )


class RepositorioOcupadoError(RuntimeError):
    """Indica que outra gravação está em andamento no repositório."""


VERSAO_AUSENTE = "ausente"


@dataclass(frozen=True, slots=True)
class ResultadoLeitura:
    """Resultado bruto de uma leitura, incluindo versão e eventual reparo."""

    jogadores: dict[str, Any]
    reparado: bool = False
    versao: str = VERSAO_AUSENTE


@dataclass(frozen=True, slots=True)
class RegistroVersao:
    """Metadados auditáveis da última gravação concluída."""

    versao: str
    atualizado_em: str
    origem: str


@runtime_checkable
class JogadoresRepository(Protocol):
    """Contrato mínimo para fontes persistentes de jogadores."""

    def carregar(self) -> ResultadoLeitura:
        """Carrega a estrutura bruta e a versão atual da fonte canônica."""

    def salvar(
        self,
        jogadores: Mapping[str, Any],
        *,
        versao_esperada: str | None = None,
        origem: str = "aplicacao",
    ) -> RegistroVersao:
        """Persiste a base, opcionalmente condicionada à versão esperada."""


class JsonJogadoresRepository:
    """Repositório JSON com bloqueio otimista, backup e escrita atômica."""

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
    def caminho_metadados(self) -> Path:
        return self.caminho.with_suffix(".meta.json")

    @property
    def caminho_bloqueio(self) -> Path:
        return self.caminho.with_suffix(".json.lock")

    @staticmethod
    def _hash_bytes(conteudo: bytes) -> str:
        return hashlib.sha256(conteudo).hexdigest()

    def versao_atual(self) -> str:
        if not self.caminho.exists():
            return VERSAO_AUSENTE
        return self._hash_bytes(self.caminho.read_bytes())

    @staticmethod
    def _reparar_json_simples(texto: str) -> dict[str, Any] | None:
        """Tenta corrigir apenas vírgulas ausentes entre objetos de primeiro nível."""
        reparado = re.sub(r"}\s*(\"[^\"]+\"\s*:\s*{)", r"},\n    \1", texto)
        try:
            resultado = json.loads(reparado)
        except json.JSONDecodeError:
            return None
        return resultado if isinstance(resultado, dict) else None

    def carregar(self) -> ResultadoLeitura:
        if not self.caminho.exists():
            raise DataIntegrityError(
                f"Arquivo de dados não encontrado: {self.caminho.name}. "
                "Inclua o JSON na raiz do repositório."
            )

        conteudo = self.caminho.read_bytes()
        versao = self._hash_bytes(conteudo)
        texto = conteudo.decode("utf-8-sig")
        try:
            dados = json.loads(texto)
        except json.JSONDecodeError as erro_original:
            reparado = self._reparar_json_simples(texto)
            if reparado is None:
                raise DataIntegrityError(
                    f"O arquivo {self.caminho.name} está inválido e não foi sobrescrito. "
                    f"Erro: {erro_original}"
                ) from erro_original

            carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = self.caminho.with_name(
                f"{self.caminho.stem}.corrompido-{carimbo}.json"
            )
            backup.write_bytes(conteudo)
            return ResultadoLeitura(reparado, reparado=True, versao=versao)

        if not isinstance(dados, dict):
            raise DataIntegrityError(
                "O JSON precisa conter um objeto de jogadores no nível principal."
            )
        return ResultadoLeitura(dados, versao=versao)

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
                    raise RepositorioOcupadoError(
                        "Outra gravação da base está em andamento. Tente novamente."
                    )
                time.sleep(0.05)

        try:
            yield
        finally:
            self.caminho_bloqueio.unlink(missing_ok=True)

    def _salvar_metadados(self, registro: RegistroVersao) -> None:
        temporario = self.caminho_metadados.with_suffix(".meta.json.tmp")
        conteudo = json.dumps(
            {
                "versao": registro.versao,
                "atualizado_em": registro.atualizado_em,
                "origem": registro.origem,
            },
            indent=4,
            ensure_ascii=False,
        )
        temporario.write_text(conteudo + "\n", encoding="utf-8")
        json.loads(temporario.read_text(encoding="utf-8"))
        temporario.replace(self.caminho_metadados)

    def salvar(
        self,
        jogadores: Mapping[str, Any],
        *,
        versao_esperada: str | None = None,
        origem: str = "aplicacao",
    ) -> RegistroVersao:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".json.tmp")
        backup = self.caminho.with_suffix(".json.bak")

        conteudo = json.dumps(
            jogadores,
            indent=4,
            ensure_ascii=False,
            sort_keys=False,
        ) + "\n"
        bytes_novos = conteudo.encode("utf-8")
        temporario.write_bytes(bytes_novos)

        # Nunca substitui a fonte antes de validar o arquivo temporário.
        json.loads(temporario.read_text(encoding="utf-8"))

        with self._bloqueio_exclusivo():
            versao_atual = self.versao_atual()
            if (
                versao_esperada is not None
                and versao_esperada != versao_atual
            ):
                temporario.unlink(missing_ok=True)
                raise ConflitoConcorrenciaError(
                    versao_esperada=versao_esperada,
                    versao_atual=versao_atual,
                )

            if self.caminho.exists():
                shutil.copy2(self.caminho, backup)
            temporario.replace(self.caminho)

            versao_nova = self._hash_bytes(bytes_novos)
            registro = RegistroVersao(
                versao=versao_nova,
                atualizado_em=datetime.now(timezone.utc).isoformat(),
                origem=str(origem or "aplicacao"),
            )
            self._salvar_metadados(registro)
            return registro
