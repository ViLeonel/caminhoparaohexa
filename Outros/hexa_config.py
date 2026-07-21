"""Configurações centrais do projeto O Caminho para o Hexa 2030."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "ANO_BASE_DADOS",
    "ANO_COPA",
    "AUDIT_FILE",
    "AVALIACOES_FILE",
    "ASSUNTO_FEEDBACK_PREFIXO",
    "BASE_DIR",
    "DATA_FILE",
    "EMAIL_FEEDBACK",
    "ENRICHMENTS_FILE",
    "GRUPOS_EDITORIAIS",
    "GRUPO_OBSERVACAO",
    "GRUPO_RESERVAS",
    "GRUPO_TITULARES",
    "ICONE_APLICACAO",
    "IDADE_MAXIMA_CADASTRO",
    "IDADE_MINIMA_CADASTRO",
    "IDADE_PADRAO",
    "LEGACY_EVALUATIONS_ARCHIVE",
    "LIMITE_DESTAQUES_ANALISE",
    "MENUS",
    "MENU_ADMIN",
    "MENU_ANALISE",
    "MENU_CAMPO",
    "MENU_PERFIS",
    "MENU_ROSTER",
    "NOME_ANALISTA_BETO",
    "NOME_ANALISTA_VINI",
    "NOME_APLICACAO",
    "NOME_CURTO_ANALISTA_BETO",
    "NOME_CURTO_ANALISTA_VINI",
    "PAGE_CONFIG",
    "ROTULO_NAVEGACAO",
    "SAUDACAO_FEEDBACK",
    "TIPOS_SUGESTAO",
    "TITULO_PROJETO",
    "TITULO_SIDEBAR",
    "VERSAO_APLICACAO",
]


BASE_DIR = Path(__file__).resolve().parent

# Identidade e navegação
NOME_APLICACAO = "O Caminho para o Hexa 2030"
TITULO_PROJETO = "O Caminho para o Hexa"
ICONE_APLICACAO = "🏆"
VERSAO_APLICACAO = "1.3.0-regression-phase2"
TITULO_SIDEBAR = "CONSELHO TÁTICO"
ROTULO_NAVEGACAO = "Navegação do Painel:"

NOME_ANALISTA_VINI = "Vini Leonel"
NOME_CURTO_ANALISTA_VINI = "Vini"
NOME_ANALISTA_BETO = "Beto Muñoz"
NOME_CURTO_ANALISTA_BETO = "Beto"

MENU_CAMPO = "🏟️ Escalação"
MENU_PERFIS = "🔎 Scout"
MENU_ROSTER = "📋 Jogadores"
MENU_ANALISE = "📊 Indicadores"
MENU_ADMIN = "🔐 Área administrativa em construção"
MENUS: tuple[str, ...] = (
    MENU_CAMPO,
    MENU_PERFIS,
    MENU_ROSTER,
    MENU_ANALISE,
)

# Referências temporais
ANO_BASE_DADOS = 2026
ANO_COPA = 2030

# Vocabulário editorial legado. Mantido apenas para compatibilidade cadastral.
GRUPO_TITULARES = "Titulares"
GRUPO_RESERVAS = "Reservas"
GRUPO_OBSERVACAO = "Observação"
GRUPOS_EDITORIAIS: tuple[str, ...] = (
    GRUPO_TITULARES,
    GRUPO_RESERVAS,
    GRUPO_OBSERVACAO,
)

# Valores padrão e limites de entrada
IDADE_PADRAO = 22
IDADE_MINIMA_CADASTRO = 15
IDADE_MAXIMA_CADASTRO = 45
LIMITE_DESTAQUES_ANALISE = 8

# Feedback
EMAIL_FEEDBACK = "viniciusbl87@gmail.com"
TIPOS_SUGESTAO: tuple[str, ...] = (
    "Sugerir jogador",
    "Sugerir melhoria",
)
ASSUNTO_FEEDBACK_PREFIXO = "Caminho para o Hexa"
SAUDACAO_FEEDBACK = (
    f"Olá, {NOME_CURTO_ANALISTA_VINI} e {NOME_CURTO_ANALISTA_BETO}!"
)

# Persistência
NOME_ARQUIVO_JOGADORES = "jogadores_hexa_2030.json"
NOME_ARQUIVO_ENRIQUECIMENTOS = "enriquecimentos_tm.json"
NOME_ARQUIVO_AUDITORIA = "auditoria_jogadores.jsonl"
NOME_ARQUIVO_AVALIACOES = "avaliacoes_trimestrais_hexa_2030.json"

DATA_FILE = BASE_DIR / NOME_ARQUIVO_JOGADORES
ENRICHMENTS_FILE = BASE_DIR / NOME_ARQUIVO_ENRIQUECIMENTOS
AUDIT_FILE = BASE_DIR / NOME_ARQUIVO_AUDITORIA
AVALIACOES_FILE = BASE_DIR / NOME_ARQUIVO_AVALIACOES
LEGACY_EVALUATIONS_ARCHIVE = (
    BASE_DIR / "arquivo" / "avaliacoes_editoriais_legado_pre_t2_2026.json"
)

# Configuração da página Streamlit.
PAGE_CONFIG = {
    "page_title": NOME_APLICACAO,
    "page_icon": ICONE_APLICACAO,
    "layout": "wide",
    "initial_sidebar_state": "auto",
}
