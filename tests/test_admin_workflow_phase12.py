"""Testes da Fase 12: workflow editorial e persistência avançada."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hexa_auth import IdentidadeUsuario, Permissao, usuario_tem_permissao
from hexa_repository import ConflitoConcorrenciaError
from hexa_repository_sqlite import (
    SqliteAuditoriaRepository,
    SqliteJogadoresRepository,
)
from hexa_workflow_editorial import (
    StatusRascunho,
    WorkflowEditorialError,
    WorkflowEditorialRepository,
)


ROOT = Path(__file__).resolve().parents[1]


class WorkflowEditorialPhase12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "hexa.sqlite3"
        self.repo = SqliteJogadoresRepository(self.db)
        jogadores = json.loads(
            (ROOT / "jogadores_hexa_2030.json").read_text(encoding="utf-8-sig")
        )
        self.inicial = self.repo.salvar(
            jogadores,
            versao_esperada="ausente",
            origem="teste_inicial",
        )
        self.workflow = WorkflowEditorialRepository(self.db)
        self.jogadores = jogadores

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _criar(self, *, ator_id: str = "autor") -> str:
        rascunho = self.workflow.criar(
            jogador="Alisson",
            versao_base=self.repo.versao_atual(),
            estado_atual=self.jogadores["Alisson"],
            alteracoes={"pontos_fortes": "Liderança e posicionamento de elite."},
            justificativa="Atualização editorial trimestral.",
            ator_email=f"{ator_id}@example.com",
            ator_nome=ator_id,
            ator_id=ator_id,
        )
        return rascunho.id_rascunho

    def test_fluxo_completo_publica_nova_revisao_e_auditoria(self) -> None:
        identificador = self._criar()
        self.workflow.enviar_revisao(
            identificador,
            ator_email="autor@example.com",
            ator_nome="Autor",
            ator_id="autor",
        )
        self.workflow.aprovar(
            identificador,
            comentario="Revisado e aprovado.",
            ator_email="revisor@example.com",
            ator_nome="Revisor",
            ator_id="revisor",
        )
        versao = self.workflow.publicar(
            identificador,
            repositorio=self.repo,
            ator_email="publicador@example.com",
            ator_nome="Publicador",
            ator_id="publicador",
        )
        publicado = self.workflow.obter(identificador)
        self.assertEqual(publicado.status, StatusRascunho.PUBLICADO)
        self.assertEqual(publicado.versao_publicada, versao)
        self.assertEqual(
            self.repo.carregar().jogadores["Alisson"]["pontos_fortes"],
            "Liderança e posicionamento de elite.",
        )
        eventos = SqliteAuditoriaRepository(self.db).listar(jogador="Alisson")
        self.assertTrue(any(item.campo == "pontos_fortes" for item in eventos))
        self.assertTrue(any(item.ator_id == "publicador" for item in eventos))

    def test_autor_nao_aprova_proprio_rascunho(self) -> None:
        identificador = self._criar()
        self.workflow.enviar_revisao(
            identificador,
            ator_email="autor@example.com",
            ator_nome="Autor",
            ator_id="autor",
        )
        with self.assertRaises(WorkflowEditorialError):
            self.workflow.aprovar(
                identificador,
                ator_email="autor@example.com",
                ator_nome="Autor",
                ator_id="autor",
            )

    def test_concorrencia_bloqueia_publicacao(self) -> None:
        identificador = self._criar()
        self.workflow.enviar_revisao(
            identificador,
            ator_email="autor@example.com",
            ator_nome="Autor",
            ator_id="autor",
        )
        self.workflow.aprovar(
            identificador,
            ator_email="revisor@example.com",
            ator_nome="Revisor",
            ator_id="revisor",
        )
        estado = self.repo.carregar()
        alterado = dict(estado.jogadores)
        alterado["Alisson"] = dict(alterado["Alisson"])
        alterado["Alisson"]["clube"] = "Outro clube"
        self.repo.salvar(
            alterado,
            versao_esperada=estado.versao,
            origem="concorrencia",
        )
        with self.assertRaises(ConflitoConcorrenciaError):
            self.workflow.publicar(
                identificador,
                repositorio=self.repo,
                ator_id="publicador",
            )

    def test_campos_externos_nao_sao_editaveis(self) -> None:
        with self.assertRaises(WorkflowEditorialError):
            self.workflow.criar(
                jogador="Alisson",
                versao_base=self.repo.versao_atual(),
                estado_atual=self.jogadores["Alisson"],
                alteracoes={"tm_valor_mercado": "999 M. €"},
                justificativa="Tentativa inválida.",
                ator_id="autor",
            )

    def test_rejeicao_exige_comentario(self) -> None:
        identificador = self._criar()
        self.workflow.enviar_revisao(
            identificador,
            ator_id="autor",
            ator_email="",
            ator_nome="",
        )
        with self.assertRaises(WorkflowEditorialError):
            self.workflow.rejeitar(
                identificador,
                comentario="não",
                ator_id="revisor",
                ator_email="",
                ator_nome="",
            )

    def test_rollback_cria_nova_revisao_sem_apagar_historico(self) -> None:
        antes = self.repo.versao_atual()
        estado = self.repo.carregar()
        alterado = dict(estado.jogadores)
        alterado["Alisson"] = dict(alterado["Alisson"])
        alterado["Alisson"]["clube"] = "Clube temporário"
        segunda = self.repo.salvar(
            alterado,
            versao_esperada=estado.versao,
            origem="alteracao_temporaria",
        )
        nova = self.workflow.rollback(
            repositorio=self.repo,
            versao_alvo=antes,
            versao_esperada=segunda.versao,
            ator_id="publicador",
        )
        self.assertNotIn(nova, {antes, segunda.versao})
        self.assertEqual(
            self.repo.carregar().jogadores["Alisson"]["clube"],
            self.jogadores["Alisson"]["clube"],
        )
        self.assertGreaterEqual(len(self.repo.listar_revisoes()), 3)


class PermissoesPhase12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.secrets = {
            "administradores": {
                "emails": ["admin@example.com"],
                "subjects": ["admin-sub"],
            },
            "seguranca": {
                "exigir_email_verificado": False,
                "tolerancia_relogio_segundos": 60,
            },
            "perfis": {
                "editores": ["editor@example.com"],
                "revisores": ["reviewer-sub"],
                "publicadores": ["publisher@example.com"],
                "auditores": ["auditor@example.com"],
            },
        }

    def test_editor_cria_mas_nao_publica(self) -> None:
        identidade = IdentidadeUsuario(
            autenticado=True,
            email="editor@example.com",
            subject="editor-sub",
        )
        self.assertTrue(
            usuario_tem_permissao(
                Permissao.CRIAR_RASCUNHO,
                identidade=identidade,
                secrets=self.secrets,
            )
        )
        self.assertFalse(
            usuario_tem_permissao(
                Permissao.PUBLICAR_RASCUNHO,
                identidade=identidade,
                secrets=self.secrets,
            )
        )

    def test_revisor_por_subject(self) -> None:
        identidade = IdentidadeUsuario(
            autenticado=True,
            email="other@example.com",
            subject="reviewer-sub",
        )
        self.assertTrue(
            usuario_tem_permissao(
                Permissao.REVISAR_RASCUNHO,
                identidade=identidade,
                secrets=self.secrets,
            )
        )

    def test_administrador_tem_todas_as_permissoes(self) -> None:
        identidade = IdentidadeUsuario(
            autenticado=True,
            email="admin@example.com",
            subject="admin-sub",
        )
        for permissao in Permissao:
            self.assertTrue(
                usuario_tem_permissao(
                    permissao,
                    identidade=identidade,
                    secrets=self.secrets,
                )
            )


class VersionPhase12Tests(unittest.TestCase):
    def test_versao_phase12(self) -> None:
        from hexa_config import VERSAO_APLICACAO

        self.assertEqual(VERSAO_APLICACAO, "3.0.0-admin-workflow-phase12")


if __name__ == "__main__":
    unittest.main()
