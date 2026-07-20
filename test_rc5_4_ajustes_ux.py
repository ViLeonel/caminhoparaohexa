"""Regressões da RC5.4 — ajustes de campo, ficha e análise."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hexa_avaliacoes import formatar_status_avaliacao
from hexa_taticas import TATICAS


class TestAjustesUxRC54(unittest.TestCase):
    def test_centroavante_433_classico_fica_em_faixa_segura(self) -> None:
        slot = TATICAS["4-3-3 Clássico"]["Centroavante (CA)"]
        self.assertEqual(slot.left, "50%")
        self.assertLessEqual(float(slot.bottom.removesuffix("%")), 76.0)

    def test_todas_as_taticas_mantem_onze_titulares(self) -> None:
        self.assertTrue(TATICAS)
        for nome, layout in TATICAS.items():
            with self.subTest(tatica=nome):
                self.assertEqual(len(layout), 11)

    def test_rotulos_publicos_de_situacao(self) -> None:
        self.assertEqual(
            formatar_status_avaliacao("Completa"),
            "Avaliação Completa",
        )
        self.assertEqual(
            formatar_status_avaliacao("Parcial"),
            "Avaliação Parcial",
        )
        self.assertEqual(
            formatar_status_avaliacao("Não avaliada"),
            "Sem Avaliação",
        )
        self.assertEqual(formatar_status_avaliacao(None), "Sem Avaliação")

    def test_campo_nao_oferece_visualizacao_em_lista(self) -> None:
        fonte = (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertIn("Monte a sua convocação", fonte)
        self.assertNotIn("Visualização tática:", fonte)
        self.assertNotIn("render_lista_tatica", fonte)
        self.assertNotIn("construir_visualizacao_tatica_lista", fonte)

    def test_analise_nao_exibe_comparacao_entre_analistas(self) -> None:
        fonte = (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertNotIn("Consensos e divergências", fonte)
        self.assertNotIn("_render_comparacao_analistas", fonte)
        self.assertNotIn("comparar_analistas", fonte)

    def test_card_de_perfil_remove_id_e_idade_antiga(self) -> None:
        fonte = (ROOT / "hexa_components.py").read_text(encoding="utf-8")
        self.assertIn("Capacidade atual", fonte)
        self.assertIn("Potencial em 2030", fonte)
        self.assertIn("Idade em 2030", fonte)
        self.assertIn("Clube atual", fonte)
        self.assertNotIn("Idade em 2026:", fonte)
        self.assertNotIn("<strong>ID:</strong>", fonte)

    def test_resumo_de_avaliacao_tem_layout_responsivo(self) -> None:
        estilos = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")
        paginas = (ROOT / "hexa_pages.py").read_text(encoding="utf-8")
        self.assertIn(".evaluation-meta-card--status", estilos)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", estilos)
        self.assertIn(".evaluation-meta-value--numeric", estilos)
        self.assertIn(".evaluation-meta-value--date", estilos)
        self.assertIn("evaluation-meta-card--status", paginas)

    def test_altura_do_campo_evitar_colapso_em_telas_baixas(self) -> None:
        estilos = (ROOT / "hexa_styles.py").read_text(encoding="utf-8")
        self.assertIn(
            "height: clamp(520px, 72vh, 620px);",
            estilos,
        )


if __name__ == "__main__":
    unittest.main()
