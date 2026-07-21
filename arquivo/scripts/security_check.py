"""Verificações locais de segurança e higiene do repositório."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ARQUIVOS_PROIBIDOS = (
    ".streamlit/secrets.toml",
    "secrets.toml",
    ".env",
)

PADROES_SUSPEITOS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
)

EXTENSOES_TEXTO = {
    ".py", ".toml", ".yml", ".yaml", ".json", ".md", ".txt", ".gitignore"
}


def main() -> None:
    problemas: list[str] = []

    for relativo in ARQUIVOS_PROIBIDOS:
        if (ROOT / relativo).exists():
            problemas.append(f"Arquivo sensível presente: {relativo}")

    for caminho in ROOT.rglob("*"):
        if not caminho.is_file():
            continue
        if any(parte in {".git", ".venv", "venv", "__pycache__"} for parte in caminho.parts):
            continue
        if caminho.suffix not in EXTENSOES_TEXTO and caminho.name != ".gitignore":
            continue
        try:
            texto = caminho.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for padrao in PADROES_SUSPEITOS:
            if padrao.search(texto):
                problemas.append(
                    f"Padrão de segredo suspeito em {caminho.relative_to(ROOT)}"
                )

    if problemas:
        raise SystemExit("\n".join(problemas))
    print("Security repository check: OK")


if __name__ == "__main__":
    main()
