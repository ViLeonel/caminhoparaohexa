"""Integração entre a RC5 e as regras de convocação preservadas da RC4."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from hexa_session import (
    opcoes_reserva_livre,
    opcoes_reserva_posicional,
    prioridade_posicoes_tatica,
    quantidade_vagas_livres,
)
from hexa_taticas import LIMITE_RESERVAS, TATICAS

BASE_DIR = Path(__file__).resolve().parents[1]


class TestRC5ConvocacaoIntegracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.jogadores = json.loads(
            (BASE_DIR / "jogadores_hexa_2030.json").read_text(encoding="utf-8")
        )

    def test_formacoes_mantem_onze_slots_e_quatro_vagas_livres(self) -> None:
        self.assertGreaterEqual(len(TATICAS), 1)
        for nome, layout in TATICAS.items():
            with self.subTest(tatica=nome):
                self.assertEqual(len(layout), 11)
                self.assertEqual(
                    quantidade_vagas_livres(len(layout)),
                    LIMITE_RESERVAS - 11,
                )

    def test_reserva_posicional_respeita_compatibilidade_e_indisponiveis(self) -> None:
        layout = next(iter(TATICAS.values()))
        primeiro_slot = next(iter(layout.values()))
        opcoes = opcoes_reserva_posicional(
            self.jogadores,
            primeiro_slot.posicoes,
            set(),
        )
        self.assertTrue(opcoes)
        escolhido = opcoes[0]
        sem_repeticao = opcoes_reserva_posicional(
            self.jogadores,
            primeiro_slot.posicoes,
            {escolhido},
        )
        self.assertNotIn(escolhido, sem_repeticao)

    def test_vagas_livres_seguem_prioridade_tatica_sem_duplicidade(self) -> None:
        layout = next(iter(TATICAS.values()))
        prioridade = prioridade_posicoes_tatica(layout)
        opcoes = opcoes_reserva_livre(
            self.jogadores,
            prioridade,
            set(),
        )
        self.assertEqual(len(opcoes), len(set(opcoes)))
        escolhido = opcoes[0]
        restantes = opcoes_reserva_livre(
            self.jogadores,
            prioridade,
            {escolhido},
        )
        self.assertNotIn(escolhido, restantes)


if __name__ == "__main__":
    unittest.main()
