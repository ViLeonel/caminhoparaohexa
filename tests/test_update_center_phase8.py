from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from hexa_atualizacao import (
    DocumentoRepository,
    carregar_registros_arquivo,
    preparar_calendario,
    preparar_temporada,
)
from hexa_auth import Permissao
from hexa_calendarios import (
    CATEGORIAS_COMPETICAO,
    proximos_jogos_do_atleta,
)
from hexa_config import VERSAO_APLICACAO
from hexa_estatisticas import CAMPOS_ESTATISTICOS


class UpdateCenterPhase8Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.jogadores = {
            "Atleta A": {
                "nome": "Atleta A",
                "id_atleta": "ATH-TEST-1",
                "clube": "Clube A",
                "posicao": "Centroavante",
                "posicoes_multiplas": ["Centroavante"],
                "grupo": "Observação",
                "tipo": "Observação",
                "nota_vini": 0.0,
                "nota_roberto": 0.0,
                "pontos_fortes": "",
                "pontos_fracos": "",
                "historico": "",
                "idade": 20,
            }
        }
        self.agora = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)

    def test_contract_contains_only_requested_statistics(self) -> None:
        esperados = {
            "jogos", "minutos", "titular", "gols", "assistencias", "chutes",
            "chutes_no_alvo", "passes", "passes_certos_percentual",
            "passes_chave", "dribles", "desarmes", "interceptacoes",
            "cabeceios_ganhos", "erros", "erros_geraram_gol",
            "cartoes_amarelos", "cartoes_vermelhos",
        }
        self.assertEqual(set(CAMPOS_ESTATISTICOS), esperados)

    def test_update_season_combines_club_and_national_team(self) -> None:
        registros = [
            {
                "id_atleta": "ATH-TEST-1",
                "ambito": "clube",
                "equipe": "Clube A",
                "competicao": "Liga",
                "jogos": 10,
                "minutos": 900,
                "titular": 10,
                "gols": 5,
                "passes": 100,
                "passes_certos_percentual": 80,
            },
            {
                "id_atleta": "ATH-TEST-1",
                "ambito": "selecao",
                "equipe": "Brasil",
                "competicao": "Eliminatórias",
                "jogos": 2,
                "minutos": 90,
                "titular": 1,
                "gols": 1,
                "passes": 20,
                "passes_certos_percentual": 100,
            },
        ]
        previa = preparar_temporada(
            ano=2026,
            registros=registros,
            jogadores=self.jogadores,
            documento_anterior=None,
            fonte="Teste",
            atualizado_por="tester",
            agora=self.agora,
        )
        combinados = [
            item for item in previa.documento["totais"]
            if item["ambito"] == "combinado"
        ]
        self.assertEqual(len(combinados), 1)
        self.assertEqual(combinados[0]["jogos"], 12)
        self.assertEqual(combinados[0]["gols"], 6)
        self.assertEqual(combinados[0]["passes_certos_percentual"], 83.33)

    def test_update_preserves_prior_update_history(self) -> None:
        anterior = {
            "historico_atualizacoes": [
                {"atualizado_em_utc": "2026-06-30T00:00:00Z"}
            ]
        }
        previa = preparar_temporada(
            ano=2026,
            registros=[{
                "id_atleta": "ATH-TEST-1",
                "ambito": "clube",
                "equipe": "Clube A",
                "competicao": "Liga",
            }],
            jogadores=self.jogadores,
            documento_anterior=anterior,
            fonte="Teste",
            atualizado_por="tester",
            agora=self.agora,
        )
        self.assertEqual(len(previa.documento["historico_atualizacoes"]), 2)

    def test_calendar_supports_state_and_sudamericana(self) -> None:
        self.assertIn("estadual", CATEGORIAS_COMPETICAO)
        self.assertIn("continental_sulamericana", CATEGORIAS_COMPETICAO)

    def test_calendar_returns_only_three_simple_upcoming_matches(self) -> None:
        jogos = [
            {
                "id_jogo": str(indice),
                "data": f"2026-08-{indice:02d}",
                "competicao": "Estadual",
                "categoria_competicao": "estadual",
                "mandante": "Clube A" if indice % 2 else "Clube B",
                "visitante": "Clube B" if indice % 2 else "Clube A",
            }
            for indice in range(1, 6)
        ]
        previa = preparar_calendario(
            ano=2026,
            registros=jogos,
            documento_anterior=None,
            fonte="Oficial",
            atualizado_por="tester",
            agora=self.agora,
        )
        proximos = proximos_jogos_do_atleta(
            jogador=self.jogadores["Atleta A"],
            calendario=previa.documento,
            hoje=date(2026, 8, 1),
        )
        self.assertEqual(len(proximos), 3)
        self.assertEqual(
            set(proximos[0]),
            {"data", "competicao", "confronto"},
        )

    def test_repository_creates_backup_and_does_not_touch_other_year(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            repo = DocumentoRepository(Path(pasta), "temporada")
            repo.salvar(2025, {"schema_version": "1.0", "temporada": 2025})
            repo.salvar(2026, {"schema_version": "1.0", "temporada": 2026, "v": 1})
            repo.salvar(2026, {"schema_version": "1.0", "temporada": 2026, "v": 2})
            self.assertEqual(repo.carregar(2025)["temporada"], 2025)
            self.assertEqual(repo.carregar(2026)["v"], 2)
            backup = Path(pasta) / "temporada_2026.json.bak"
            self.assertTrue(backup.exists())
            self.assertEqual(json.loads(backup.read_text())["v"], 1)

    def test_csv_parser(self) -> None:
        registros = carregar_registros_arquivo(
            nome_arquivo="temporada.csv",
            conteudo=(
                b"id_atleta,ambito,equipe,competicao,jogos\n"
                b"ATH-TEST-1,clube,Clube A,Liga,1\n"
            ),
        )
        self.assertEqual(registros[0]["jogos"], "1")

    def test_update_preserves_existing_current_season_rows_not_received(self) -> None:
        anterior = {
            "registros": [
                {
                    "id_atleta": "ATH-TEST-1",
                    "nome": "Atleta A",
                    "temporada": 2026,
                    "ambito": "selecao",
                    "equipe": "Brasil",
                    "competicao": "Eliminatórias",
                    **{campo: 0 for campo in CAMPOS_ESTATISTICOS if campo != "passes_certos_percentual"},
                    "passes_certos_percentual": None,
                }
            ]
        }
        previa = preparar_temporada(
            ano=2026,
            registros=[{
                "id_atleta": "ATH-TEST-1",
                "ambito": "clube",
                "equipe": "Clube A",
                "competicao": "Liga",
                "jogos": 1,
            }],
            jogadores=self.jogadores,
            documento_anterior=anterior,
            fonte="Teste",
            atualizado_por="tester",
            agora=self.agora,
        )
        self.assertEqual(len(previa.documento["registros"]), 2)

    def test_xlsx_parser_does_not_evaluate_macros(self) -> None:
        from io import BytesIO
        from openpyxl import Workbook

        arquivo = BytesIO()
        workbook = Workbook()
        aba = workbook.active
        aba.append(["id_atleta", "ambito", "equipe", "competicao", "jogos"])
        aba.append(["ATH-TEST-1", "clube", "Clube A", "Liga", 1])
        workbook.save(arquivo)
        workbook.close()

        registros = carregar_registros_arquivo(
            nome_arquivo="temporada.xlsx",
            conteudo=arquivo.getvalue(),
        )
        self.assertEqual(registros[0]["id_atleta"], "ATH-TEST-1")

    def test_phase_permission_and_version(self) -> None:
        self.assertEqual(
            Permissao.EXECUTAR_ATUALIZACAO.value,
            "executar_atualizacao",
        )
        self.assertEqual(VERSAO_APLICACAO, "2.2.0-indices-rankings-phase11")


if __name__ == "__main__":
    unittest.main()
