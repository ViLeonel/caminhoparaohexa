"""Testes do contrato e da implementação JSON do repositório."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

import hexa_data
from hexa_repository import (
    ConflitoConcorrenciaError,
    DataIntegrityError,
    JsonJogadoresRepository,
    RegistroVersao,
    ResultadoLeitura,
)


class RepositorioMemoria:
    def __init__(self, jogadores: Mapping[str, Any], reparado: bool = False) -> None:
        self._jogadores = dict(jogadores)
        self.reparado = reparado
        self.salvamentos: list[dict[str, Any]] = []

    def carregar(self) -> ResultadoLeitura:
        return ResultadoLeitura(dict(self._jogadores), self.reparado)

    def salvar(
        self,
        jogadores: Mapping[str, Any],
        *,
        versao_esperada: str | None = None,
        origem: str = "aplicacao",
    ) -> RegistroVersao:
        copia = json.loads(json.dumps(jogadores, ensure_ascii=False))
        self.salvamentos.append(copia)
        self._jogadores = copia
        return RegistroVersao("memoria", "2026-07-18T00:00:00+00:00", origem)


class TestJsonJogadoresRepository(unittest.TestCase):
    def test_leitura_e_escrita_atomica_com_backup(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            caminho.write_text('{"Antigo": {"nome": "Antigo"}}', encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)

            leitura = repositorio.carregar()
            self.assertFalse(leitura.reparado)
            self.assertIn("Antigo", leitura.jogadores)

            repositorio.salvar({"Novo": {"nome": "Novo"}})

            self.assertEqual(json.loads(caminho.read_text(encoding="utf-8")), {"Novo": {"nome": "Novo"}})
            backup = caminho.with_suffix(".json.bak")
            self.assertTrue(backup.exists())
            self.assertIn("Antigo", json.loads(backup.read_text(encoding="utf-8")))

    def test_json_irrecuperavel_nao_e_sobrescrito(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            original = '{"Atleta": '
            caminho.write_text(original, encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)

            with self.assertRaises(DataIntegrityError):
                repositorio.carregar()

            self.assertEqual(caminho.read_text(encoding="utf-8"), original)

    def test_reparo_controlado_preserva_original_em_backup(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            texto = '{"A": {"nome": "A"} "B": {"nome": "B"}}'
            caminho.write_text(texto, encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)

            leitura = repositorio.carregar()

            self.assertTrue(leitura.reparado)
            self.assertEqual(set(leitura.jogadores), {"A", "B"})
            backups = list(Path(pasta).glob("jogadores.corrompido-*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), texto)


    def test_duas_sessoes_nao_sobrescrevem_versao_mais_recente(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            caminho.write_text("{}\n", encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)

            sessao_a = repositorio.carregar()
            sessao_b = repositorio.carregar()
            self.assertEqual(sessao_a.versao, sessao_b.versao)

            primeira = repositorio.salvar(
                {"A": {"nome": "A"}},
                versao_esperada=sessao_a.versao,
                origem="sessao_a",
            )

            with self.assertRaises(ConflitoConcorrenciaError):
                repositorio.salvar(
                    {"B": {"nome": "B"}},
                    versao_esperada=sessao_b.versao,
                    origem="sessao_b",
                )

            self.assertEqual(json.loads(caminho.read_text(encoding="utf-8")), {"A": {"nome": "A"}})
            self.assertEqual(repositorio.versao_atual(), primeira.versao)

    def test_metadados_registram_versao_data_e_origem(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            caminho.write_text("{}\n", encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)
            leitura = repositorio.carregar()

            registro = repositorio.salvar(
                {"A": {"nome": "A"}},
                versao_esperada=leitura.versao,
                origem="teste_automatizado",
            )

            metadados = json.loads(
                repositorio.caminho_metadados.read_text(encoding="utf-8")
            )
            self.assertEqual(metadados["versao"], registro.versao)
            self.assertEqual(metadados["origem"], "teste_automatizado")
            self.assertTrue(metadados["atualizado_em"])



class TestIntegracaoRepositorioDados(unittest.TestCase):
    def test_carregamento_usa_repositorio_injetado(self) -> None:
        repositorio = RepositorioMemoria(
            {
                "Atleta": {
                    "nome": "Atleta",
                    "posicao": "Guarda-redes",
                    "posicoes_multiplas": ["Guarda-redes"],
                }
            }
        )

        jogadores = hexa_data.carregar_jogadores(repositorio)

        self.assertEqual(jogadores["Atleta"]["posicao"], "Goleiro")
        self.assertEqual(len(repositorio.salvamentos), 1)

    def test_adicionar_so_muta_sessao_depois_de_salvar(self) -> None:
        class RepositorioFalho(RepositorioMemoria):
            def salvar(
                self,
                jogadores: Mapping[str, Any],
                *,
                versao_esperada: str | None = None,
                origem: str = "aplicacao",
            ) -> RegistroVersao:
                raise OSError("falha simulada")

        jogadores: dict[str, dict[str, Any]] = {}
        repositorio = RepositorioFalho({})

        with self.assertRaises(OSError):
            hexa_data.adicionar_jogador(
                jogadores,
                {"nome": "Novo", "posicao": "Volante"},
                repositorio,
            )

        self.assertEqual(jogadores, {})

    def test_adicionar_persiste_e_depois_atualiza_sessao(self) -> None:
        jogadores: dict[str, dict[str, Any]] = {}
        repositorio = RepositorioMemoria({})

        nome = hexa_data.adicionar_jogador(
            jogadores,
            {"nome": "Novo", "posicao": "Volante"},
            repositorio,
        )

        self.assertEqual(nome, "Novo")
        self.assertIn("Novo", jogadores)
        self.assertEqual(len(repositorio.salvamentos), 1)


    def test_conflito_nao_muta_base_da_sessao_antiga(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            caminho.write_text("{}\n", encoding="utf-8")
            repositorio = JsonJogadoresRepository(caminho)
            leitura_a = repositorio.carregar()
            leitura_b = repositorio.carregar()

            jogadores_a = hexa_data.BaseJogadores({}, versao_fonte=leitura_a.versao)
            jogadores_b = hexa_data.BaseJogadores({}, versao_fonte=leitura_b.versao)

            hexa_data.adicionar_jogador(
                jogadores_a,
                {"nome": "Primeiro", "posicao": "Volante"},
                repositorio,
            )

            with self.assertRaises(ConflitoConcorrenciaError):
                hexa_data.adicionar_jogador(
                    jogadores_b,
                    {"nome": "Segundo", "posicao": "Volante"},
                    repositorio,
                )

            self.assertNotIn("Segundo", jogadores_b)
            self.assertEqual(set(json.loads(caminho.read_text(encoding="utf-8"))), {"Primeiro"})



class CompatibilidadePythonTest(unittest.TestCase):
    def test_repositorio_nao_depende_de_datetime_utc(self) -> None:
        codigo = Path(__file__).resolve().parents[1].joinpath("hexa_repository.py").read_text(encoding="utf-8")
        self.assertNotIn("from datetime import UTC", codigo)
        self.assertIn("timezone.utc", codigo)

    def test_falha_canonica_nao_gera_auditoria(self) -> None:
        class AuditoriaMemoria:
            def __init__(self) -> None:
                self.eventos = []

            def registrar(self, eventos) -> None:
                self.eventos.extend(eventos)

            def listar(self, *, jogador=None, limite=None):
                return list(self.eventos)

        class RepositorioFalho:
            def carregar(self):
                return ResultadoLeitura({}, versao="v1")

            def salvar(self, jogadores, *, versao_esperada=None, origem="aplicacao"):
                raise OSError("falha simulada")

        auditoria = AuditoriaMemoria()
        dados = {
            "Atleta": {
                "nome": "Atleta",
                "posicao": "Volante",
                "posicoes_multiplas": ["Volante"],
                "clube": "Clube",
                "idade": 22,
                "grupo": "Observação",
                "tipo": "Observação",
                "nota_vini": 0.0,
                "nota_roberto": 0.0,
                "pontos_fortes": "",
                "pontos_fracos": "",
                "historico": "",
            }
        }

        with self.assertRaises(OSError):
            hexa_data.salvar_jogadores(
                dados,
                RepositorioFalho(),
                versao_esperada="v1",
                estado_anterior={},
                auditoria=auditoria,
            )

        self.assertEqual(auditoria.eventos, [])



if __name__ == "__main__":
    unittest.main()
