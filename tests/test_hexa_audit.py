"""Testes dos eventos imutáveis e do repositório JSONL de auditoria."""

from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path

from hexa_audit import (
    AcaoAuditoria,
    EventoAuditoria,
    JsonlAuditoriaRepository,
    gerar_eventos_alteracao,
)


class TestGeracaoEventos(unittest.TestCase):
    def test_nao_registra_campos_sem_alteracao(self) -> None:
        antes = {"A": {"nome": "A", "clube": "X"}}
        depois = {"A": {"nome": "A", "clube": "X"}}

        eventos = gerar_eventos_alteracao(
            antes,
            depois,
            origem="teste",
            versao_anterior="v1",
            versao_nova="v2",
        )

        self.assertEqual(eventos, [])

    def test_registra_apenas_campo_modificado(self) -> None:
        antes = {"A": {"nome": "A", "clube": "X", "idade": 20}}
        depois = {"A": {"nome": "A", "clube": "Y", "idade": 20}}

        eventos = gerar_eventos_alteracao(
            antes,
            depois,
            origem="teste",
            versao_anterior="v1",
            versao_nova="v2",
            ocorrido_em="2026-07-18T00:00:00+00:00",
        )

        self.assertEqual(len(eventos), 1)
        evento = eventos[0]
        self.assertEqual(evento.jogador, "A")
        self.assertEqual(evento.campo, "clube")
        self.assertEqual(evento.valor_anterior, "X")
        self.assertEqual(evento.valor_novo, "Y")
        self.assertEqual(evento.acao, AcaoAuditoria.ALTERACAO)
        self.assertEqual(evento.versao_anterior, "v1")
        self.assertEqual(evento.versao_nova, "v2")

    def test_criacao_gera_eventos_por_campo(self) -> None:
        eventos = gerar_eventos_alteracao(
            {},
            {"Novo": {"nome": "Novo", "posicao": "Volante"}},
            origem="cadastro",
            versao_anterior="v1",
            versao_nova="v2",
        )

        self.assertEqual({evento.campo for evento in eventos}, {"nome", "posicao"})
        self.assertTrue(
            all(evento.acao is AcaoAuditoria.CRIACAO for evento in eventos)
        )

    def test_evento_e_imutavel(self) -> None:
        evento = gerar_eventos_alteracao(
            {},
            {"A": {"nome": "A"}},
            origem="teste",
            versao_anterior="v1",
            versao_nova="v2",
        )[0]

        with self.assertRaises(dataclasses.FrozenInstanceError):
            evento.campo = "outro"  # type: ignore[misc]


class TestJsonlAuditoriaRepository(unittest.TestCase):
    def test_registra_lista_e_filtra(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "auditoria.jsonl"
            repositorio = JsonlAuditoriaRepository(caminho)
            eventos = gerar_eventos_alteracao(
                {},
                {
                    "A": {"nome": "A"},
                    "B": {"nome": "B"},
                },
                origem="teste",
                versao_anterior="v1",
                versao_nova="v2",
                ocorrido_em="2026-07-18T00:00:00+00:00",
            )

            repositorio.registrar(eventos)

            self.assertEqual(len(repositorio.listar()), 2)
            self.assertEqual(len(repositorio.listar(jogador="A")), 1)
            self.assertEqual(repositorio.listar(limite=1)[0].jogador, "B")

            linhas = caminho.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(linhas), 2)
            for linha in linhas:
                dados = json.loads(linha)
                self.assertIn("id_evento", dados)
                self.assertIn("versao_nova", dados)

    def test_mesmo_evento_nao_e_duplicado(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "auditoria.jsonl"
            repositorio = JsonlAuditoriaRepository(caminho)
            evento = gerar_eventos_alteracao(
                {},
                {"A": {"nome": "A"}},
                origem="teste",
                versao_anterior="v1",
                versao_nova="v2",
            )[0]

            repositorio.registrar([evento])
            repositorio.registrar([evento])

            self.assertEqual(len(repositorio.listar()), 1)

    def test_registra_identidade_do_ator(self) -> None:
        eventos = gerar_eventos_alteracao(
            {},
            {"A": {"nome": "A"}},
            origem="admin_interface",
            versao_anterior="v1",
            versao_nova="v2",
            ator_email="admin@exemplo.com",
            ator_nome="Administrador",
            ator_id="sub-123",
        )
        evento = eventos[0]
        self.assertEqual(evento.ator_email, "admin@exemplo.com")
        self.assertEqual(evento.ator_nome, "Administrador")
        self.assertEqual(evento.ator_id, "sub-123")



if __name__ == "__main__":
    unittest.main()
