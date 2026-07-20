"""Testes das regras de convocação, compatibilidade e fábricas táticas."""

from __future__ import annotations

import hashlib
import json
import unittest

from hexa_taticas import (
    FABRICAS_TATICAS,
    LIMITE_CONVOCADOS,
    LIMITE_RESERVAS,
    LIMITE_TITULARES,
    POSICOES_OFICIAIS,
    TATICAS,
    construir_taticas,
    indice_adaptabilidade,
    obter_atletas_compativeis,
    validar_taticas,
)

ASSINATURAS_REGRESSAO = {
    "4-3-3 Diamante": "c68f22e3c06d0c6068fc38a2d1b03e6697594f8531baf2c0f96d52ddaecc8205",
    "4-3-3 Clássico": "f7150c7e61f8179866583b6f6e5c6525067507fa4c0ebb105ed7a6cbadb796f9",
    "4-4-2 Diamante": "a96d3110e9df62a4132a4038486c67a20c1b60b59d1d6c57420fe3e3e41d5afc",
    "4-4-2 Clássico": "25dad254ced956d1a1050ec60adc5244579e2f8286df04549b2a1c52e3404b1c",
    "4-2-3-1": "7db803d7d8e42b6dbfdb8903c9f3f81410020fb96a977ea001e0bacf41da693e",
    "4-3-2-1 Árvore de Natal": "4bead1fd2d6f6d2e7332750b11821692610000571dc92ffab22541503842b43c",
}


def _assinatura_formacao(formacao: dict) -> str:
    estrutura = [
        (nome, slot.posicoes, slot.left, slot.bottom, slot.tag)
        for nome, slot in formacao.items()
    ]
    payload = json.dumps(estrutura, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TestConvocacao(unittest.TestCase):
    def setUp(self) -> None:
        self.jogadores = {
            "Goleiro A": {
                "nome": "Goleiro A",
                "posicao": "Goleiro",
                "posicoes_multiplas": ["Goleiro"],
            },
            "Curinga": {
                "nome": "Curinga",
                "posicao": "Volante",
                "posicoes_multiplas": ["Volante", "Mezzala direito", "Meia-direita"],
            },
            "Atacante": {
                "nome": "Atacante",
                "posicao": "Centroavante",
                "posicoes_multiplas": ["Centroavante"],
            },
        }

    def test_limites_oficiais(self) -> None:
        self.assertEqual(LIMITE_TITULARES, 11)
        self.assertEqual(LIMITE_RESERVAS, 15)
        self.assertEqual(LIMITE_CONVOCADOS, 26)

    def test_todas_as_formacoes_tem_onze_slots(self) -> None:
        for nome, formacao in TATICAS.items():
            with self.subTest(formacao=nome):
                self.assertEqual(len(formacao), LIMITE_TITULARES)

    def test_formacoes_sao_validas(self) -> None:
        self.assertEqual(validar_taticas(self.jogadores), [])

    def test_compatibilidade_filtra_posicao(self) -> None:
        goleiros = obter_atletas_compativeis(self.jogadores, ("Goleiro",))
        self.assertEqual(goleiros, ["Goleiro A"])

    def test_indice_de_adaptabilidade(self) -> None:
        curinga = self.jogadores["Curinga"]
        self.assertEqual(indice_adaptabilidade(curinga, ("Volante",)), 0)
        self.assertEqual(indice_adaptabilidade(curinga, ("Mezzala direito",)), 1)
        self.assertEqual(indice_adaptabilidade(curinga, ("Meia-direita",)), 2)
        self.assertEqual(indice_adaptabilidade(curinga, ("Centroavante",)), -1)

    def test_exemplo_de_convocacao_sem_duplicidade(self) -> None:
        titulares = ["Goleiro A", "Curinga"]
        reservas = ["Atacante"]
        convocados = titulares + reservas

        self.assertEqual(len(convocados), len(set(convocados)))
        self.assertLessEqual(len(titulares), LIMITE_TITULARES)
        self.assertLessEqual(len(reservas), LIMITE_RESERVAS)
        self.assertLessEqual(len(convocados), LIMITE_CONVOCADOS)


class TestFabricasTaticas(unittest.TestCase):
    def test_registro_preserva_ordem_e_nomes_oficiais(self) -> None:
        self.assertEqual(tuple(FABRICAS_TATICAS), tuple(ASSINATURAS_REGRESSAO))
        self.assertEqual(tuple(TATICAS), tuple(ASSINATURAS_REGRESSAO))

    def test_fabricas_geram_estruturas_independentes(self) -> None:
        primeira = construir_taticas()
        segunda = construir_taticas()

        self.assertIsNot(primeira, segunda)
        for nome in primeira:
            with self.subTest(formacao=nome):
                self.assertIsNot(primeira[nome], segunda[nome])
                self.assertEqual(primeira[nome], segunda[nome])

    def test_regressao_integral_das_seis_formacoes(self) -> None:
        for nome, hash_esperado in ASSINATURAS_REGRESSAO.items():
            with self.subTest(formacao=nome):
                self.assertEqual(_assinatura_formacao(TATICAS[nome]), hash_esperado)

    def test_slots_usam_coordenadas_percentuais_validas(self) -> None:
        for nome_tatica, formacao in TATICAS.items():
            for nome_slot, slot in formacao.items():
                with self.subTest(formacao=nome_tatica, slot=nome_slot):
                    self.assertTrue(slot.left.endswith("%"))
                    self.assertTrue(slot.bottom.endswith("%"))
                    self.assertGreaterEqual(float(slot.left.removesuffix("%")), 0)
                    self.assertLessEqual(float(slot.left.removesuffix("%")), 100)
                    self.assertGreaterEqual(float(slot.bottom.removesuffix("%")), 0)
                    self.assertLessEqual(float(slot.bottom.removesuffix("%")), 100)

    def test_tags_e_posicoes_sao_validas(self) -> None:
        tags_validas = {"GOL", "LD", "LE", "ZAG", "VOL", "MCE", "MCD", "ME", "MD", "MEI", "PE", "PD", "SA", "CA"}
        for nome_tatica, formacao in TATICAS.items():
            for nome_slot, slot in formacao.items():
                with self.subTest(formacao=nome_tatica, slot=nome_slot):
                    self.assertIn(slot.tag, tags_validas)
                    self.assertTrue(slot.posicoes)
                    self.assertTrue(all(posicao in POSICOES_OFICIAIS for posicao in slot.posicoes))


if __name__ == "__main__":
    unittest.main()
