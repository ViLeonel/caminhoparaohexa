from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hexa_audit import AcaoAuditoria, EventoAuditoria
from hexa_persistencia_servidor import (
    ConfiguracaoPersistencia,
    configuracao_persistencia,
    criar_repositorio,
    migrar_json_para_sqlite,
)
from hexa_repository import ConflitoConcorrenciaError, JsonJogadoresRepository
from hexa_repository_sqlite import (
    SqliteAuditoriaRepository,
    SqliteJogadoresRepository,
)


class Phase7PersistenceTests(unittest.TestCase):
    def test_version_phase7(self) -> None:
        from hexa_config import VERSAO_APLICACAO
        self.assertEqual(VERSAO_APLICACAO, "3.0.0-admin-workflow-phase12")

    def test_json_is_safe_default(self) -> None:
        config = configuracao_persistencia(secrets={})
        self.assertEqual(config.backend, "json")
        self.assertFalse(config.duravel)

    def test_sqlite_config_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = configuracao_persistencia(
                secrets={
                    "persistencia": {
                        "backend": "sqlite",
                        "sqlite_path": str(Path(temp) / "hexa.db"),
                    }
                }
            )
            self.assertEqual(config.backend, "sqlite")
            self.assertTrue(config.duravel)
            self.assertIsInstance(criar_repositorio(config), SqliteJogadoresRepository)

    def test_sqlite_versions_and_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = SqliteJogadoresRepository(Path(temp) / "hexa.db")
            primeira = repo.salvar(
                {"A": {"nome": "A"}},
                versao_esperada="ausente",
                origem="teste",
            )
            segunda = repo.salvar(
                {"A": {"nome": "A", "clube": "B"}},
                versao_esperada=primeira.versao,
                origem="teste",
            )
            self.assertEqual(repo.carregar().versao, segunda.versao)
            self.assertEqual(len(repo.listar_revisoes()), 2)
            with self.assertRaises(ConflitoConcorrenciaError):
                repo.salvar(
                    {"A": {"nome": "A"}},
                    versao_esperada=primeira.versao,
                )

    def test_rollback_creates_new_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = SqliteJogadoresRepository(Path(temp) / "hexa.db")
            primeira = repo.salvar(
                {"A": {"nome": "A", "clube": "Um"}},
                versao_esperada="ausente",
            )
            segunda = repo.salvar(
                {"A": {"nome": "A", "clube": "Dois"}},
                versao_esperada=primeira.versao,
            )
            rollback = repo.rollback(
                primeira.versao,
                versao_esperada=segunda.versao,
                ator_email="admin@example.com",
            )
            self.assertEqual(
                repo.carregar().jogadores["A"]["clube"],
                "Um",
            )
            self.assertEqual(len(repo.listar_revisoes()), 3)
            self.assertNotEqual(rollback.versao, segunda.versao)

    def test_sqlite_audit_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            audit = SqliteAuditoriaRepository(Path(temp) / "hexa.db")
            evento = EventoAuditoria(
                id_evento="evt-1",
                ocorrido_em="2026-07-21T00:00:00+00:00",
                jogador="A",
                campo="clube",
                acao=AcaoAuditoria.ALTERACAO,
                valor_anterior="Um",
                valor_novo="Dois",
                origem="teste",
                versao_anterior="v1",
                versao_nova="v2",
                ator_email="admin@example.com",
            )
            audit.registrar([evento])
            itens = audit.listar(jogador="A")
            self.assertEqual(len(itens), 1)
            self.assertEqual(itens[0].ator_email, "admin@example.com")
            with self.assertRaises(Exception):
                audit.registrar([evento])

    def test_json_migration_does_not_modify_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            origem_path = Path(temp) / "jogadores.json"
            dados = {"A": {"nome": "A"}}
            origem_path.write_text(
                json.dumps(dados, ensure_ascii=False),
                encoding="utf-8",
            )
            original = origem_path.read_bytes()
            destino = SqliteJogadoresRepository(Path(temp) / "hexa.db")
            migrar_json_para_sqlite(
                origem=JsonJogadoresRepository(origem_path),
                destino=destino,
            )
            self.assertEqual(origem_path.read_bytes(), original)
            self.assertEqual(destino.carregar().jogadores, dados)


if __name__ == "__main__":
    unittest.main()
