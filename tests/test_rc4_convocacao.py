"""Testes de regressão da RC4 para o banco posicional."""

from __future__ import annotations

import unittest

from hexa_session import (
    chave_reserva_livre,
    chave_reserva_posicional,
    chave_reservas,
    chave_titular,
    ler_convocacao,
    limpar_convocacao,
    migrar_reservas_legadas,
    opcoes_reserva_livre,
    opcoes_reserva_posicional,
    prioridade_posicoes_tatica,
    quantidade_vagas_livres,
)
from hexa_taticas import LIMITE_RESERVAS, TATICAS


class RC4ConvocacaoTests(unittest.TestCase):
    def test_todas_as_taticas_geram_onze_posicionais_e_quatro_livres(self) -> None:
        self.assertTrue(TATICAS)
        for nome, layout in TATICAS.items():
            with self.subTest(tatica=nome):
                self.assertEqual(len(layout), 11)
                self.assertEqual(quantidade_vagas_livres(len(layout)), 4)
                self.assertEqual(
                    len(layout) + quantidade_vagas_livres(len(layout)),
                    LIMITE_RESERVAS,
                )

    def test_reserva_posicional_usa_posicoes_editoriais(self) -> None:
        layout = next(iter(TATICAS.values()))
        configuracao = next(iter(layout.values()))
        posicao = configuracao.posicoes[0]
        jogadores = {
            "Compatível": {
                "posicao": posicao,
                "posicoes_multiplas": [posicao],
            },
            "Compatível secundário": {
                "posicao": "Posição diferente",
                "posicoes_multiplas": ["Posição diferente", posicao],
            },
            "Incompatível": {
                "posicao": "Posição diferente",
                "posicoes_multiplas": ["Posição diferente"],
            },
        }
        opcoes = opcoes_reserva_posicional(
            jogadores,
            configuracao.posicoes,
            {"Compatível secundário"},
        )
        self.assertEqual(opcoes, ["Compatível"])

    def test_vagas_livres_seguem_prioridade_da_tatica(self) -> None:
        layout = next(iter(TATICAS.values()))
        prioridade = prioridade_posicoes_tatica(layout)
        self.assertGreaterEqual(len(prioridade), 3)
        jogadores = {
            "Terceiro": {
                "posicao": prioridade[2],
                "posicoes_multiplas": [prioridade[2]],
            },
            "Primeiro B": {
                "posicao": prioridade[0],
                "posicoes_multiplas": [prioridade[0]],
            },
            "Segundo": {
                "posicao": prioridade[1],
                "posicoes_multiplas": [prioridade[1]],
            },
            "Primeiro A": {
                "posicao": prioridade[0],
                "posicoes_multiplas": [prioridade[0]],
            },
        }
        self.assertEqual(
            opcoes_reserva_livre(jogadores, prioridade, set()),
            ["Primeiro A", "Primeiro B", "Segundo", "Terceiro"],
        )

    def test_migracao_legada_preserva_unicidade_e_remove_chave_antiga(self) -> None:
        tatica, layout = next(iter(TATICAS.items()))
        jogadores: dict[str, dict[str, object]] = {}
        legado: list[str] = []

        for indice, configuracao in enumerate(layout.values()):
            nome = f"Reserva {indice + 1}"
            posicao = configuracao.posicoes[0]
            jogadores[nome] = {
                "posicao": posicao,
                "posicoes_multiplas": [posicao],
            }
            legado.append(nome)

        prioridade = prioridade_posicoes_tatica(layout)
        for indice in range(4):
            nome = f"Livre {indice + 1}"
            posicao = prioridade[indice % len(prioridade)]
            jogadores[nome] = {
                "posicao": posicao,
                "posicoes_multiplas": [posicao],
            }
            legado.append(nome)

        estado: dict[str, object] = {
            chave_reservas(tatica): [*legado, legado[0]],
        }
        migradas = migrar_reservas_legadas(
            estado,
            tatica,
            layout,
            jogadores,
            set(),
        )

        self.assertNotIn(chave_reservas(tatica), estado)
        self.assertEqual(len(migradas), len(set(migradas)))
        self.assertEqual(len(migradas), LIMITE_RESERVAS)
        self.assertTrue(
            any(
                estado.get(chave_reserva_posicional(tatica, indice))
                for indice in range(len(layout))
            )
        )

    def test_leitura_descarta_repeticao_entre_titular_e_reserva(self) -> None:
        tatica, layout = next(iter(TATICAS.items()))
        primeiro_slot = next(iter(layout.values()))
        posicao = primeiro_slot.posicoes[0]
        jogadores = {
            "Atleta": {
                "posicao": posicao,
                "posicoes_multiplas": [posicao],
            }
        }
        estado = {
            chave_titular(tatica, 0): "Atleta",
            chave_reserva_posicional(tatica, 0): "Atleta",
            chave_reserva_livre(tatica, 0): "Atleta",
        }
        titulares, reservas = ler_convocacao(
            estado,
            tatica,
            layout,
            jogadores,
        )
        self.assertEqual(list(titulares.values()), ["Atleta"])
        self.assertEqual(reservas, [])

    def test_limpeza_remove_chaves_novas_e_legada(self) -> None:
        tatica, layout = next(iter(TATICAS.items()))
        estado: dict[str, object] = {
            chave_reservas(tatica): ["Legado"],
        }
        for indice in range(len(layout)):
            estado[chave_titular(tatica, indice)] = "Titular"
            estado[chave_reserva_posicional(tatica, indice)] = "Reserva"
        for indice in range(4):
            estado[chave_reserva_livre(tatica, indice)] = "Livre"

        limpar_convocacao(estado, tatica, len(layout))
        self.assertEqual(estado, {})


if __name__ == "__main__":
    unittest.main()
