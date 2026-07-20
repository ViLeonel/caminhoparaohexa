"""Testes das transformações puras usadas pelas telas."""

from __future__ import annotations

import unittest

from hexa_taticas import SlotTatico
from hexa_selectors import (
    calcular_medias_titulares,
    construir_avaliacoes,
    construir_registros_mercado,
    construir_registros_roster,
    construir_visualizacao_tatica_lista,
    filtrar_jogadores,
    ordenar_consensos,
    ordenar_divergencias,
)


class TestSelectors(unittest.TestCase):
    def setUp(self) -> None:
        self.jogadores = {
            "A": {
                "nome": "A",
                "nome_completo": "Atleta Alpha",
                "posicao": "Volante",
                "posicoes_multiplas": ["Volante", "Mezzala direito"],
                "grupo": "Titulares",
                "clube": "Clube Azul",
                "idade": 24,
                "nota_vini": 8.0,
                "nota_roberto": 7.0,
                "tm_valor_mercado_milhoes": 20.0,
                "tm_valor_maximo_milhoes": 25.0,
            },
            "B": {
                "nome": "B",
                "nome_completo": "Atleta Beta",
                "posicao": "Centroavante",
                "posicoes_multiplas": ["Centroavante"],
                "grupo": "Reservas",
                "clube": "Clube Verde",
                "idade": 21,
                "nota_vini": 9.0,
                "nota_roberto": 9.0,
                "tm_valor_mercado_milhoes": 10.0,
                "tm_valor_maximo_milhoes": 10.0,
            },
            "C": {
                "nome": "C",
                "posicao": "Goleiro",
                "posicoes_multiplas": ["Goleiro"],
                "grupo": "Observação",
                "clube": "Clube Azul",
                "idade": "inválida",
                "nota_vini": 0.0,
                "nota_roberto": 6.0,
            },
        }

    def test_filtro_busca_nome_completo_clube_posicao_e_grupo(self) -> None:
        self.assertEqual([n for n, _ in filtrar_jogadores(self.jogadores, busca="alpha")], ["A"])
        self.assertEqual([n for n, _ in filtrar_jogadores(self.jogadores, busca="verde")], ["B"])
        self.assertEqual([n for n, _ in filtrar_jogadores(self.jogadores, posicao="Mezzala direito")], ["A"])
        self.assertEqual([n for n, _ in filtrar_jogadores(self.jogadores, grupo="Observação")], ["C"])

    def test_registros_roster_calculam_idade_projetada(self) -> None:
        registros = construir_registros_roster(self.jogadores, busca="Alpha")
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["Idade 2026"], 24)
        self.assertEqual(registros[0]["Idade 2030"], 28)
        self.assertEqual(registros[0]["% do pico"], 80.0)

    def test_avaliacoes_ignoram_notas_ausentes(self) -> None:
        avaliacoes = construir_avaliacoes(self.jogadores)
        self.assertEqual({item["Nome"] for item in avaliacoes}, {"A", "B"})

    def test_ordenacao_consensos_e_divergencias(self) -> None:
        avaliacoes = construir_avaliacoes(self.jogadores)
        self.assertEqual(ordenar_consensos(avaliacoes)[0]["Nome"], "B")
        self.assertEqual(ordenar_divergencias(avaliacoes)[0]["Nome"], "A")

    def test_mercado_ignora_ausencia_de_valor_atual(self) -> None:
        mercado = construir_registros_mercado(self.jogadores)
        self.assertEqual({item["Nome"] for item in mercado}, {"A", "B"})

    def test_medias_titulares_preservam_ausencia(self) -> None:
        medias = calcular_medias_titulares([self.jogadores["A"], self.jogadores["C"]])
        self.assertEqual(medias["vini"], 8.0)
        self.assertEqual(medias["roberto"], 6.5)
        self.assertEqual(medias["coletiva"], 7.25)
        sem_notas = calcular_medias_titulares([{"nota_vini": 0, "nota_roberto": None}])
        self.assertIsNone(sem_notas["vini"])
        self.assertIsNone(sem_notas["roberto"])
        self.assertIsNone(sem_notas["coletiva"])


    def test_visualizacao_tatica_lista_agrupa_e_preserva_vagas(self) -> None:
        layout = {
            "Goleiro": SlotTatico(("Goleiro",), "50%", "8%", "GOL"),
            "Zagueiro": SlotTatico(("Zagueiro",), "50%", "22%", "ZAG"),
            "Volante": SlotTatico(("Volante",), "50%", "45%", "VOL"),
            "Atacante": SlotTatico(("Centroavante",), "50%", "82%", "CA"),
        }
        linhas = construir_visualizacao_tatica_lista(
            layout,
            {"Goleiro": "C", "Volante": "A"},
            self.jogadores,
        )
        self.assertEqual(tuple(linhas), ("Goleiro", "Defesa", "Meio-campo", "Ataque"))
        self.assertTrue(linhas["Goleiro"][0]["preenchido"])
        self.assertEqual(linhas["Meio-campo"][0]["nome"], "A")
        self.assertFalse(linhas["Defesa"][0]["preenchido"])
        self.assertFalse(linhas["Ataque"][0]["preenchido"])

if __name__ == "__main__":
    unittest.main()
