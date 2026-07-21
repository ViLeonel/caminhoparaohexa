"""Smoke test do projeto sem iniciar o servidor Streamlit."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULOS_PUROS = (
    "hexa_config",
    "hexa_taticas",
    "hexa_models",
    "hexa_repository",
    "hexa_audit",
    "hexa_data",
    "hexa_avaliacoes",
    "hexa_messages",
    "hexa_selectors",
    "hexa_session",
)

IMPORTS_CRITICOS_PUROS = {
    "hexa_data": (
        "DataIntegrityError",
        "carregar_jogadores",
        "validar_integridade_jogadores",
        "validar_posicoes",
    ),
    "hexa_avaliacoes": (
        "carregar_avaliacoes",
        "validar_integridade_avaliacoes",
    ),
    "hexa_taticas": (
        "TATICAS",
        "validar_taticas",
    ),
}

IMPORTS_CRITICOS_UI = {
    "hexa_pages": ("render_feedback_sidebar", "render_tela"),
    "hexa_styles": ("aplicar_estilos",),
    "hexa_components": ("render_campo", "render_lista_tatica"),
    "hexa_persistencia_local": ("sincronizar_persistencia_local",),
}

ARQUIVOS_JSON = (
    "jogadores_hexa_2030.json",
    "avaliacoes_trimestrais_hexa_2030.json",
    "enriquecimentos_tm.json",
)


def verificar_imports(contratos: dict[str, tuple[str, ...]]) -> None:
    for modulo_nome, simbolos in contratos.items():
        modulo = importlib.import_module(modulo_nome)
        ausentes = [simbolo for simbolo in simbolos if not hasattr(modulo, simbolo)]
        if ausentes:
            raise RuntimeError(
                f"{modulo_nome} não exporta os símbolos esperados: {ausentes}"
            )


def carregar_json(nome: str) -> object:
    caminho = ROOT / nome
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {nome}")
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def main() -> None:
    for nome in MODULOS_PUROS:
        importlib.import_module(nome)

    verificar_imports(IMPORTS_CRITICOS_PUROS)

    if importlib.util.find_spec("streamlit") is not None:
        verificar_imports(IMPORTS_CRITICOS_UI)
        modo_ui = "incluída"
    else:
        modo_ui = "não executada (Streamlit ausente)"

    for arquivo in ARQUIVOS_JSON:
        carregar_json(arquivo)

    print(f"Smoke test: OK; camada visual {modo_ui}")


if __name__ == "__main__":
    main()
