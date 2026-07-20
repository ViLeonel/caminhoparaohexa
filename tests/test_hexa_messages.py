"""Testes das mensagens operacionais e estados vazios."""

from __future__ import annotations

import unittest
from pathlib import Path

from hexa_messages import (
    ANALISE_SEM_AVALIACOES,
    AVISO_PERSISTENCIA,
    MERCADO_SEM_DADOS,
    NAO_INFORMADO_FONTE,
    PERFIL_VAZIO,
    ROSTER_SEM_RESULTADOS,
    convocacao_completa,
    resumo_convocacao,
)
from hexa_selectors import construir_registros_roster
from hexa_taticas import LIMITE_RESERVAS, LIMITE_TITULARES


class TestMensagensOperacionais(unittest.TestCase):
    def test_resumo_convocacao_informa_vagas(self) -> None:
        resumo = resumo_convocacao(8, 4)
        self.assertIn(f"Titulares: 8/{LIMITE_TITULARES}", resumo)
        self.assertIn(f"Reservas: 4/{LIMITE_RESERVAS}", resumo)
        self.assertIn("Faltam 3 titular(es)", resumo)
        self.assertIn("Banco disponível: 11 vaga(s)", resumo)

    def test_convocacao_completa(self) -> None:
        self.assertFalse(convocacao_completa(LIMITE_TITULARES - 1))
        self.assertTrue(convocacao_completa(LIMITE_TITULARES))

    def test_mensagens_explicam_o_estado(self) -> None:
        self.assertIn("pesquisa começa vazia", PERFIL_VAZIO)
        self.assertIn("filtros", ROSTER_SEM_RESULTADOS)
        self.assertIn("duas notas", ANALISE_SEM_AVALIACOES)
        self.assertIn("não valor igual a zero", MERCADO_SEM_DADOS)

    def test_aviso_de_persistencia_menciona_cloud_e_github(self) -> None:
        self.assertIn("Streamlit Community Cloud", AVISO_PERSISTENCIA)
        self.assertIn("GitHub", AVISO_PERSISTENCIA)

    def test_roster_converte_sentinela_legada(self) -> None:
        jogadores = {
            "Teste": {
                "nome": "Teste",
                "posicao": "Centroavante",
                "grupo": "Observação",
                "clube": "N/A",
                "idade": 22,
                "nota_vini": 0,
                "nota_roberto": 0,
                "posicoes_multiplas": ["Centroavante"],
            }
        }
        registros = construir_registros_roster(jogadores)
        self.assertEqual(registros[0]["Clube"], NAO_INFORMADO_FONTE)


class TestUsoDasMensagens(unittest.TestCase):
    def test_paginas_nao_usam_estados_vazios_genericos(self) -> None:
        raiz = Path(__file__).resolve().parents[1]
        paginas = (raiz / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertNotIn('st.info("Ainda não', paginas)
        self.assertNotIn('st.info("Nenhum', paginas)
        self.assertIn("AVISO_PERSISTENCIA", paginas)


if __name__ == "__main__":
    unittest.main()
