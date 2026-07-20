"""Testes mínimos de integridade, normalização e mesclagem externa."""

from __future__ import annotations

import copy
import unittest

import hexa_data


class TestIntegridadeEditorial(unittest.TestCase):
    def setUp(self) -> None:
        self.registro = {
            "nome": "Atleta Teste",
            "posicao": "Volante",
            "posicoes_multiplas": ["Volante"],
            "grupo": "Titulares",
            "tipo": "Certeza Atual",
            "nota_vini": 8.0,
            "nota_roberto": 7.5,
            "pontos_fortes": "Leitura",
            "pontos_fracos": "Aceleração",
            "historico": "Debate editorial preservado.",
            "clube": "Clube Canônico",
            "tm_valor_mercado": "10,00 M. €",
            "tm_ultima_atualizacao": "10/07/2026",
        }

    def test_enriquecimento_nao_sobrescreve_campos_protegidos(self) -> None:
        base = {"Atleta Teste": copy.deepcopy(self.registro)}
        enriquecimento = {
            "Atleta Teste": {
                "posicao": "Centroavante",
                "grupo": "Observação",
                "nota_vini": 1.0,
                "nota_roberto": 1.0,
                "pontos_fortes": "Texto externo",
                "pontos_fracos": "Texto externo",
                "historico": "Texto externo",
                "tm_valor_mercado": "12,00 M. €",
                "tm_ultima_atualizacao": "11/07/2026",
            }
        }

        hexa_data._aplicar_enriquecimentos(base, enriquecimento)
        resultado = base["Atleta Teste"]

        for campo in hexa_data.CAMPOS_EDITORIAIS_PROTEGIDOS | hexa_data.CAMPOS_TATICOS_PROTEGIDOS:
            if campo in self.registro:
                self.assertEqual(resultado[campo], self.registro[campo])

        self.assertEqual(resultado["tm_valor_mercado"], "12,00 M. €")

    def test_enriquecimento_antigo_nao_reverte_dados_tm(self) -> None:
        base = {"Atleta Teste": copy.deepcopy(self.registro)}
        enriquecimento = {
            "Atleta Teste": {
                "tm_valor_mercado": "5,00 M. €",
                "tm_ultima_atualizacao": "01/07/2026",
            }
        }

        alterado = hexa_data._aplicar_enriquecimentos(base, enriquecimento)

        self.assertFalse(alterado)
        self.assertEqual(base["Atleta Teste"]["tm_valor_mercado"], "10,00 M. €")
        self.assertEqual(base["Atleta Teste"]["tm_ultima_atualizacao"], "10/07/2026")

    def test_campo_cadastral_externo_apenas_completa_lacuna(self) -> None:
        base = {"Atleta Teste": copy.deepcopy(self.registro)}
        enriquecimento = {
            "Atleta Teste": {
                "clube": "Clube Externo",
                "nome_completo": "Nome Completo",
            }
        }

        hexa_data._aplicar_enriquecimentos(base, enriquecimento)

        self.assertEqual(base["Atleta Teste"]["clube"], "Clube Canônico")
        self.assertEqual(base["Atleta Teste"]["nome_completo"], "Nome Completo")


class TestNormalizacao(unittest.TestCase):
    def test_alias_de_posicao_e_numeros_externos(self) -> None:
        normalizado = hexa_data._normalizar_registro(
            "Atleta",
            {
                "nome": "Atleta",
                "posicao": "Guarda-redes",
                "posicoes_multiplas": ["Guarda-redes"],
                "tm_valor_mercado": "175 mil €",
                "tm_altura": "1,93 m",
            },
        )

        self.assertEqual(normalizado["posicao"], "Goleiro")
        self.assertEqual(normalizado["posicoes_multiplas"], ["Goleiro"])
        self.assertAlmostEqual(normalizado["tm_valor_mercado_milhoes"], 0.175)
        self.assertAlmostEqual(normalizado["tm_altura_metros"], 1.93)

    def test_valores_em_milhoes(self) -> None:
        self.assertAlmostEqual(hexa_data.extrair_valor_milhoes("40,00 M. €"), 40.0)
        self.assertAlmostEqual(hexa_data.extrair_valor_milhoes("1,50 M. €"), 1.5)
        self.assertAlmostEqual(hexa_data.extrair_valor_milhoes("175 mil €"), 0.175)

    def test_api_publica_exporta_validar_integridade_jogadores(self) -> None:
        from hexa_data import validar_integridade_jogadores
        self.assertTrue(callable(validar_integridade_jogadores))

    def test_salvamento_registra_auditoria_apos_sucesso(self) -> None:
        import tempfile
        from pathlib import Path

        from hexa_audit import JsonlAuditoriaRepository
        from hexa_repository import JsonJogadoresRepository

        registro = {
            "nome": "Atleta",
            "posicao": "Volante",
            "posicoes_multiplas": ["Volante"],
            "clube": "Clube B",
            "idade": 22,
            "grupo": "Observação",
            "tipo": "Observação",
            "nota_vini": 0.0,
            "nota_roberto": 0.0,
            "pontos_fortes": "",
            "pontos_fracos": "",
            "historico": "",
        }
        anterior = dict(registro)
        anterior["clube"] = "Clube A"

        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            caminho = raiz / "jogadores.json"
            caminho.write_text(
                __import__("json").dumps({"Atleta": anterior}, ensure_ascii=False),
                encoding="utf-8",
            )
            repositorio = JsonJogadoresRepository(caminho)
            leitura = repositorio.carregar()
            auditoria = JsonlAuditoriaRepository(raiz / "auditoria.jsonl")

            hexa_data.salvar_jogadores(
                {"Atleta": registro},
                repositorio,
                versao_esperada=leitura.versao,
                origem="teste",
                estado_anterior=leitura.jogadores,
                auditoria=auditoria,
            )

            eventos = auditoria.listar()
            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0].campo, "clube")
            self.assertEqual(eventos[0].valor_anterior, "Clube A")
            self.assertEqual(eventos[0].valor_novo, "Clube B")



if __name__ == "__main__":
    unittest.main()
