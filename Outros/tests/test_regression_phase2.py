"""Regressões históricas e contratos de navegação da Fase 2."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from hexa_avaliacoes import media_disponivel
from hexa_data import (
    _aplicar_enriquecimentos,
    extrair_altura_metros,
    extrair_valor_milhoes,
)
from hexa_repository import DataIntegrityError, JsonJogadoresRepository
from hexa_selectors import construir_registros_roster
from hexa_session import (
    chave_reserva_livre,
    chave_reserva_posicional,
    chave_titular,
    reconciliar_convocacao,
)
from hexa_taticas import TATICAS, obter_atletas_compativeis

ROOT = Path(__file__).resolve().parents[1]


class Phase2DataRegressionTests(unittest.TestCase):
    def test_idade_2030_e_derivada_do_ano_base(self) -> None:
        jogadores = {
            "Atleta": {
                "nome": "Atleta",
                "idade": 20,
                "posicao": "Centroavante",
                "posicoes_multiplas": ["Centroavante"],
                "clube": "Clube",
                "grupo": "Observação",
            }
        }
        linha = construir_registros_roster(
            jogadores,
            ano_base=2026,
            ano_copa=2030,
        )[0]
        self.assertEqual(linha["Idade 2026"], 20)
        self.assertEqual(linha["Idade 2030"], 24)

    def test_ausencia_de_nota_nao_vira_zero(self) -> None:
        self.assertIsNone(media_disponivel([None, "", None]))
        self.assertEqual(media_disponivel([0, None]), 0.0)

    def test_normalizacao_numerica_conhecida(self) -> None:
        casos = {
            "40,00 M. €": 40.0,
            "175 mil €": 0.175,
            "1,50 M. €": 1.5,
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertAlmostEqual(
                    extrair_valor_milhoes(texto),
                    esperado,
                )
        self.assertAlmostEqual(extrair_altura_metros("1,93 m"), 1.93)

    def test_enriquecimento_nao_sobrescreve_campos_editoriais(self) -> None:
        jogadores = {
            "Atleta": {
                "posicao": "Volante",
                "posicoes_multiplas": ["Volante"],
                "grupo": "Titulares",
                "tipo": "Certeza Atual",
                "nota_vini": 8.0,
                "nota_roberto": 8.5,
                "pontos_fortes": "Editorial",
                "pontos_fracos": "Editorial",
                "historico": "Editorial",
                "tm_valor_mercado": "10,00 M. €",
                "tm_ultima_atualizacao": "01/01/2026",
            }
        }
        externos = {
            "Atleta": {
                "posicao": "Centroavante",
                "posicoes_multiplas": ["Centroavante"],
                "grupo": "Observação",
                "nota_vini": 1.0,
                "pontos_fortes": "Externo",
                "tm_valor_mercado": "20,00 M. €",
                "tm_ultima_atualizacao": "02/01/2026",
            }
        }
        _aplicar_enriquecimentos(jogadores, externos)
        atleta = jogadores["Atleta"]
        self.assertEqual(atleta["posicao"], "Volante")
        self.assertEqual(atleta["posicoes_multiplas"], ["Volante"])
        self.assertEqual(atleta["grupo"], "Titulares")
        self.assertEqual(atleta["nota_vini"], 8.0)
        self.assertEqual(atleta["pontos_fortes"], "Editorial")
        self.assertEqual(atleta["tm_valor_mercado"], "20,00 M. €")

    def test_json_irrecuperavel_nao_e_sobrescrito(self) -> None:
        conteudo = b'{"Atleta": {"nome": "Atleta", ???'
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogadores.json"
            caminho.write_bytes(conteudo)
            repositorio = JsonJogadoresRepository(caminho)
            with self.assertRaises(DataIntegrityError):
                repositorio.carregar()
            self.assertEqual(caminho.read_bytes(), conteudo)


class Phase2TacticalRegressionTests(unittest.TestCase):
    def test_reconciliacao_remove_duplicidades(self) -> None:
        nome_tatica, layout = next(iter(TATICAS.items()))
        jogadores = json.loads(
            (ROOT / "jogadores_hexa_2030.json").read_text(
                encoding="utf-8-sig"
            )
        )
        primeiro_slot = next(iter(layout.values()))
        compativel = next(
            nome
            for nome, dados in jogadores.items()
            if any(
                posicao in (dados.get("posicoes_multiplas") or [])
                for posicao in primeiro_slot.posicoes
            )
        )
        estado = {
            chave_titular(nome_tatica, 0): compativel,
            chave_reserva_posicional(nome_tatica, 0): compativel,
            chave_reserva_livre(nome_tatica, 0): compativel,
        }
        relatorio = reconciliar_convocacao(
            estado,
            nome_tatica,
            layout,
            jogadores,
        )
        self.assertEqual(estado[chave_titular(nome_tatica, 0)], compativel)
        self.assertIsNone(
            estado[chave_reserva_posicional(nome_tatica, 0)]
        )
        self.assertIsNone(estado[chave_reserva_livre(nome_tatica, 0)])
        self.assertEqual(len(relatorio["chaves_limpas"]), 2)

    def test_todas_formacoes_mantem_centroavante_quando_exigido(self) -> None:
        jogadores = json.loads(
            (ROOT / "jogadores_hexa_2030.json").read_text(
                encoding="utf-8-sig"
            )
        )
        centroavantes = {
            nome
            for nome, dados in jogadores.items()
            if "Centroavante" in (dados.get("posicoes_multiplas") or [])
        }
        self.assertTrue(centroavantes)
        for nome_tatica, layout in TATICAS.items():
            for slot, configuracao in layout.items():
                if "Centroavante" not in configuracao.posicoes:
                    continue
                with self.subTest(tatica=nome_tatica, slot=slot):
                    compativeis = obter_atletas_compativeis(
                        jogadores,
                        configuracao.posicoes,
                    )
                    self.assertTrue(
                        centroavantes.intersection(compativeis)
                    )


class Phase2InterfaceRegressionTests(unittest.TestCase):
    def test_quatro_paginas_abrem_sem_excecao(self) -> None:
        menus = (
            "🏟️ Escalação",
            "🔎 Scout",
            "📋 Jogadores",
            "📊 Indicadores",
        )
        for menu in menus:
            with self.subTest(menu=menu):
                app = AppTest.from_file(
                    str(ROOT / "caminho_hexa_2030.py")
                )
                app.run(timeout=30)
                app.sidebar.radio[0].set_value(menu).run(timeout=30)
                self.assertEqual(len(app.exception), 0)

    def test_area_administrativa_fica_depois_do_radar(self) -> None:
        app = AppTest.from_file(str(ROOT / "caminho_hexa_2030.py"))
        app.run(timeout=30)
        elementos = list(app._tree[1].children.values())
        textos = [
            str(getattr(elemento, "value", "") or "")
            for elemento in elementos
        ]
        radar = next(
            indice
            for indice, texto in enumerate(textos)
            if "Radar do projeto" in texto
        )
        admin = next(
            indice
            for indice, texto in enumerate(textos)
            if "Área administrativa em construção" in texto
        )
        self.assertGreater(admin, radar)

    def test_detalhe_de_secrets_nao_aparece_na_interface(self) -> None:
        app = AppTest.from_file(str(ROOT / "caminho_hexa_2030.py"))
        app.run(timeout=30)
        textos = " ".join(
            str(elemento.value)
            for colecao in (
                app.warning,
                app.error,
                app.info,
                app.sidebar.warning,
                app.sidebar.error,
                app.sidebar.info,
                app.sidebar.markdown,
            )
            for elemento in colecao
        )
        self.assertNotIn("[administradores]", textos)
        self.assertNotIn("Secrets do Streamlit", textos)


if __name__ == "__main__":
    unittest.main()
