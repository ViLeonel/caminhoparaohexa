"""Testes do schema e dos relatórios de integridade dos jogadores."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any, Mapping

import hexa_data
from hexa_models import (
    SeveridadeIntegridade,
    chave_canonica_nome,
    validar_estrutura_bruta,
    validar_jogadores_normalizados,
)
from hexa_repository import DataIntegrityError, RegistroVersao, ResultadoLeitura


class RepositorioMemoria:
    def __init__(self, jogadores: Mapping[str, Any]) -> None:
        self.jogadores = copy.deepcopy(dict(jogadores))
        self.salvamentos: list[dict[str, Any]] = []

    def carregar(self) -> ResultadoLeitura:
        return ResultadoLeitura(copy.deepcopy(self.jogadores))

    def salvar(
        self,
        jogadores: Mapping[str, Any],
        *,
        versao_esperada: str | None = None,
        origem: str = "aplicacao",
    ) -> RegistroVersao:
        copia = copy.deepcopy(dict(jogadores))
        self.salvamentos.append(copia)
        self.jogadores = copia
        return RegistroVersao("memoria", "2026-07-18T00:00:00+00:00", origem)


def jogador_valido(nome: str = "Atleta") -> dict[str, Any]:
    return {
        "nome": nome,
        "posicao": "Volante",
        "posicoes_multiplas": ["Volante"],
        "clube": "Clube",
        "idade": 22,
        "grupo": "Observação",
        "tipo": "Observação",
        "nota_vini": 7.0,
        "nota_roberto": 7.5,
        "pontos_fortes": "",
        "pontos_fracos": "",
        "historico": "",
    }


class TestSchemaJogadores(unittest.TestCase):
    def test_chave_canonica_remove_acentos_caixa_e_espacos(self) -> None:
        self.assertEqual(chave_canonica_nome("  João   Gomes "), "joao gomes")

    def test_detecta_registro_nao_objeto_como_erro(self) -> None:
        relatorio = validar_estrutura_bruta({"Atleta": "conteúdo inválido"})
        self.assertTrue(relatorio.possui_erros)
        self.assertEqual(relatorio.erros[0].codigo, "registro_nao_objeto")

    def test_detecta_duplicidade_normalizada(self) -> None:
        relatorio = validar_estrutura_bruta(
            {
                "João Gomes": {"nome": "João Gomes"},
                "joao  gomes": {"nome": "joao  gomes"},
            }
        )
        self.assertTrue(any(item.codigo == "nome_duplicado" for item in relatorio.erros))

    def test_diferencia_aviso_de_erro(self) -> None:
        relatorio = validar_estrutura_bruta(
            {"Chave": {"nome": "Nome Diferente", "posicao": "Volante"}}
        )
        self.assertFalse(relatorio.possui_erros)
        self.assertEqual(relatorio.avisos[0].severidade, SeveridadeIntegridade.AVISO)

    def test_valida_notas_idade_e_posicao_principal(self) -> None:
        atleta = jogador_valido()
        atleta["idade"] = 99
        atleta["nota_vini"] = 11
        atleta["posicoes_multiplas"] = ["Meia-armador"]
        relatorio = validar_jogadores_normalizados({"Atleta": atleta})
        codigos = {item.codigo for item in relatorio.erros}
        self.assertIn("idade_invalida", codigos)
        self.assertIn("nota_invalida", codigos)
        self.assertIn("posicao_principal_ausente", codigos)

    def test_base_valida_nao_produz_problemas(self) -> None:
        relatorio = validar_jogadores_normalizados({"Atleta": jogador_valido()})
        self.assertTrue(relatorio.valido)
        self.assertEqual(relatorio.problemas, ())


class TestBloqueioDePersistencia(unittest.TestCase):
    def test_carregamento_nao_descarta_registro_estruturalmente_invalido(self) -> None:
        repositorio = RepositorioMemoria(
            {
                "Atleta": jogador_valido(),
                "Quebrado": ["não", "é", "objeto"],
            }
        )
        with self.assertRaises(DataIntegrityError):
            hexa_data.carregar_jogadores(repositorio)
        self.assertEqual(repositorio.salvamentos, [])

    def test_salvamento_invalido_e_bloqueado(self) -> None:
        atleta = jogador_valido()
        atleta["nota_roberto"] = -1
        repositorio = RepositorioMemoria({})
        with self.assertRaises(DataIntegrityError):
            hexa_data.salvar_jogadores({"Atleta": atleta}, repositorio)
        self.assertEqual(repositorio.salvamentos, [])

    def test_enriquecimento_parcial_nao_cria_posicao_inventada(self) -> None:
        base: dict[str, dict[str, Any]] = {}
        alterado = hexa_data._aplicar_enriquecimentos(
            base,
            {"Novo": {"nome": "Novo", "tm_valor_mercado": "1,00 M. €"}},
        )
        self.assertFalse(alterado)
        self.assertNotIn("Novo", base)

    def test_nao_usa_notrequired_do_python_311(self) -> None:
        codigo = Path(__file__).resolve().parents[1].joinpath("hexa_models.py").read_text(encoding="utf-8")
        self.assertNotIn("NotRequired", codigo)


if __name__ == "__main__":
    unittest.main()
