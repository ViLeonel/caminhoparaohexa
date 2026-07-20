"""Testes do gerenciamento de estado da convocação."""

from __future__ import annotations

import unittest

from hexa_session import (
    chave_reservas,
    chave_titular,
    ler_convocacao,
    limpar_convocacao,
    normalizar_escolha_titular,
    normalizar_reservas,
    opcoes_reservas,
    opcoes_titular,
)
from hexa_taticas import SlotTatico


class TestSession(unittest.TestCase):
    def setUp(self) -> None:
        self.jogadores = {
            "Goleiro": {"posicao": "Goleiro", "posicoes_multiplas": ["Goleiro"]},
            "Volante": {"posicao": "Volante", "posicoes_multiplas": ["Volante"]},
            "Atacante": {"posicao": "Centroavante", "posicoes_multiplas": ["Centroavante"]},
        }
        self.layout = {
            "GOL": SlotTatico(("Goleiro",), "50%", "10%", "GOL"),
            "VOL": SlotTatico(("Volante",), "50%", "45%", "VOL"),
        }

    def test_chaves_sao_estaveis(self) -> None:
        self.assertEqual(chave_titular("4-3-3", 2), "titular::4-3-3::2")
        self.assertEqual(chave_reservas("4-3-3"), "reservas::4-3-3")

    def test_limpeza_afeta_apenas_formacao_informada(self) -> None:
        estado = {
            chave_titular("A", 0): "Goleiro",
            chave_reservas("A"): ["Atacante"],
            chave_titular("B", 0): "Volante",
        }
        limpar_convocacao(estado, "A", 2)
        self.assertNotIn(chave_titular("A", 0), estado)
        self.assertNotIn(chave_reservas("A"), estado)
        self.assertEqual(estado[chave_titular("B", 0)], "Volante")

    def test_opcoes_titular_excluem_selecionados(self) -> None:
        self.assertEqual(
            opcoes_titular(self.jogadores, ("Volante",), {"Goleiro"}),
            ["Volante"],
        )
        self.assertEqual(
            opcoes_titular(self.jogadores, ("Volante",), {"Volante"}),
            [],
        )

    def test_escolha_invalida_e_descartada(self) -> None:
        estado = {"slot": "Atacante"}
        self.assertIsNone(normalizar_escolha_titular(estado, "slot", ["Volante"]))
        self.assertIsNone(estado["slot"])

    def test_reservas_removem_duplicados_indisponiveis_e_excedentes(self) -> None:
        estado = {"reservas": ["Atacante", "Atacante", "Inexistente", "Volante"]}
        resultado = normalizar_reservas(
            estado,
            "reservas",
            ["Atacante", "Volante"],
            limite=1,
        )
        self.assertEqual(resultado, ["Atacante"])
        self.assertEqual(estado["reservas"], ["Atacante"])

    def test_opcoes_reservas_excluem_titulares(self) -> None:
        self.assertEqual(
            opcoes_reservas(self.jogadores, {"Goleiro"}),
            ["Atacante", "Volante"],
        )

    def test_leitura_descarta_duplicidade_e_incompatibilidade(self) -> None:
        estado = {
            chave_titular("T", 0): "Goleiro",
            chave_titular("T", 1): "Goleiro",
            chave_reservas("T"): ["Goleiro", "Atacante", "Atacante"],
        }
        escalados, reservas = ler_convocacao(estado, "T", self.layout, self.jogadores)
        self.assertEqual(escalados, {"GOL": "Goleiro"})
        self.assertEqual(reservas, ["Atacante"])


if __name__ == "__main__":
    unittest.main()
