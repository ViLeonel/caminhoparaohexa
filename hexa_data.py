"""Persistência, migrações e tratamento de dados do projeto.

O JSON é a fonte canônica do elenco. Este módulo mantém somente migrações e
enriquecimentos incrementais, evitando uma segunda cópia completa da base.
Campos editoriais e táticos do projeto nunca são sobrescritos por dados externos.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from hexa_taticas import POSICOES_OFICIAIS, normalizar_lista_posicoes, normalizar_posicao

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "jogadores_hexa_2030.json"
ENRICHMENTS_FILE = BASE_DIR / "enriquecimentos_tm.json"

CAMPOS_EDITORIAIS_PROTEGIDOS = {
    "nota_vini",
    "nota_roberto",
    "pontos_fortes",
    "pontos_fracos",
    "historico",
}

CAMPOS_TATICOS_PROTEGIDOS = {
    "posicao",
    "posicoes_multiplas",
    "grupo",
    "tipo",
}

CAMPOS_MINIMOS: dict[str, Any] = {
    "nome": "",
    "posicao": "Centroavante",
    "posicoes_multiplas": [],
    "clube": "N/A",
    "idade": 22,
    "grupo": "Observação",
    "tipo": "Observação",
    "nota_vini": 0.0,
    "nota_roberto": 0.0,
    "pontos_fortes": "",
    "pontos_fracos": "",
    "historico": "",
}

ALIASES_JOGADORES = {
    "Vini Jr.": "Vinicius Junior",
    "Wesley": "Wesley França",
}

# Enriquecimentos externos são mantidos em JSON separado para auditoria e atualização segura.

class DataIntegrityError(RuntimeError):
    """Indica que o JSON não pôde ser lido sem risco de perda de dados."""


def extrair_numero(valor_texto: Any, padrao: float = 0.0) -> float:
    """Extrai o primeiro número de um texto, aceitando vírgula ou ponto decimal."""
    if valor_texto is None:
        return padrao
    if isinstance(valor_texto, (int, float)):
        return float(valor_texto)
    texto = str(valor_texto).strip().lower()
    if not texto or texto == "n/a":
        return padrao
    numeros = re.findall(r"[0-9]+(?:[.,][0-9]+)?", texto)
    if not numeros:
        return padrao
    try:
        return float(numeros[0].replace(",", "."))
    except ValueError:
        return padrao


def extrair_valor_milhoes(valor_texto: Any, padrao: float = 0.0) -> float:
    """Converte valores como '175 mil €' e '40,00 M. €' para milhões de euros."""
    if valor_texto is None:
        return padrao
    if isinstance(valor_texto, (int, float)):
        return float(valor_texto)

    texto = str(valor_texto).strip().lower().replace("\u00a0", " ")
    valor = extrair_numero(texto, padrao)
    if valor == padrao and not re.search(r"\d", texto):
        return padrao

    if re.search(r"\b(mil|k)\b", texto):
        return valor / 1000.0
    if re.search(r"\b(bi|bilh(?:ão|oes|ões)?)\b", texto):
        return valor * 1000.0
    return valor


def extrair_altura_metros(valor_texto: Any, padrao: float = 0.0) -> float:
    valor = extrair_numero(valor_texto, padrao)
    if valor > 3:
        return valor / 100.0
    return valor


def formatar_valor_milhoes(valor: float | int | None) -> str:
    if valor is None:
        return "N/A"
    numero = float(valor)
    if numero <= 0:
        return "N/A"
    if numero < 1:
        return f"€ {numero * 1000:.0f} mil"
    return f"€ {numero:.2f} mi".replace(".", ",")


def percentual_do_pico(dados: Mapping[str, Any]) -> float | None:
    atual = valor_mercado_atual(dados)
    maximo = valor_mercado_maximo(dados)
    if atual <= 0 or maximo <= 0:
        return None
    return min((atual / maximo) * 100.0, 100.0)


def valor_mercado_atual(dados: Mapping[str, Any]) -> float:
    numerico = dados.get("tm_valor_mercado_milhoes")
    if isinstance(numerico, (int, float)):
        return float(numerico)
    return extrair_valor_milhoes(dados.get("tm_valor_mercado"), 0.0)


def valor_mercado_maximo(dados: Mapping[str, Any]) -> float:
    numerico = dados.get("tm_valor_maximo_milhoes")
    if isinstance(numerico, (int, float)):
        return float(numerico)
    return extrair_valor_milhoes(dados.get("tm_valor_maximo"), 0.0)


def _reparar_json_simples(texto: str) -> dict[str, Any] | None:
    """Tenta reparar somente separadores ausentes entre objetos de primeiro nível."""
    reparado = re.sub(r"}\s*(\"[^\"]+\"\s*:\s*{)", r"},\n    \1", texto)
    try:
        resultado = json.loads(reparado)
    except json.JSONDecodeError:
        return None
    return resultado if isinstance(resultado, dict) else None


def _ler_json() -> tuple[dict[str, Any], bool]:
    if not DATA_FILE.exists():
        raise DataIntegrityError(
            f"Arquivo de dados não encontrado: {DATA_FILE.name}. "
            "Inclua o JSON na raiz do repositório."
        )

    texto = DATA_FILE.read_text(encoding="utf-8-sig")
    try:
        dados = json.loads(texto)
        if not isinstance(dados, dict):
            raise DataIntegrityError("O JSON precisa conter um objeto de jogadores no nível principal.")
        return dados, False
    except json.JSONDecodeError as erro_original:
        reparado = _reparar_json_simples(texto)
        if reparado is None:
            raise DataIntegrityError(
                f"O arquivo {DATA_FILE.name} está inválido e não foi sobrescrito. "
                f"Erro: {erro_original}"
            ) from erro_original

        carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DATA_FILE.with_name(f"{DATA_FILE.stem}.corrompido-{carimbo}.json")
        backup.write_text(texto, encoding="utf-8")
        return reparado, True


def _normalizar_registro(nome_chave: str, registro: Mapping[str, Any]) -> dict[str, Any]:
    dados = dict(registro)
    dados["nome"] = str(dados.get("nome") or nome_chave).strip()

    # Remove campos transitórios de uma negociação cancelada do Éderson.
    if dados["nome"] == "Éderson":
        for campo_obsoleto in (
            "tm_clube_imagem",
            "tm_clube_desde_imagem",
            "tm_contrato_imagem",
            "tm_ultima_renovacao_imagem",
            "tm_observacao_transferencia",
        ):
            dados.pop(campo_obsoleto, None)

    posicao = normalizar_posicao(dados.get("posicao"))
    posicoes = normalizar_lista_posicoes(dados.get("posicoes_multiplas"))
    if not posicao and posicoes:
        posicao = posicoes[0]
    if not posicao:
        posicao = "Centroavante"
    if posicao not in posicoes:
        posicoes.insert(0, posicao)

    dados["posicao"] = posicao
    dados["posicoes_multiplas"] = posicoes

    for campo, valor_padrao in CAMPOS_MINIMOS.items():
        if campo not in dados or dados[campo] is None:
            dados[campo] = copy.deepcopy(valor_padrao)

    try:
        dados["idade"] = int(dados.get("idade", 22))
    except (TypeError, ValueError):
        dados["idade"] = 22

    for campo in ("nota_vini", "nota_roberto"):
        try:
            dados[campo] = float(dados.get(campo, 0.0))
        except (TypeError, ValueError):
            dados[campo] = 0.0

    # Garante campos externos normalizados, preservando também os textos originais.
    if dados.get("tm_valor_mercado") and not isinstance(dados.get("tm_valor_mercado_milhoes"), (int, float)):
        dados["tm_valor_mercado_milhoes"] = extrair_valor_milhoes(dados["tm_valor_mercado"])
    if dados.get("tm_valor_maximo") and not isinstance(dados.get("tm_valor_maximo_milhoes"), (int, float)):
        dados["tm_valor_maximo_milhoes"] = extrair_valor_milhoes(dados["tm_valor_maximo"])
    if dados.get("tm_altura") and not isinstance(dados.get("tm_altura_metros"), (int, float)):
        dados["tm_altura_metros"] = extrair_altura_metros(dados["tm_altura"])

    for campo_lista in ("tm_nacionalidades", "tm_posicoes_secundarias_site"):
        valor_lista = dados.get(campo_lista)
        if isinstance(valor_lista, str):
            dados[campo_lista] = [valor_lista]
        elif valor_lista is None:
            dados[campo_lista] = []

    return dados


def _mesclar_aliases(dados: dict[str, Any]) -> bool:
    alterado = False
    for antigo, novo in ALIASES_JOGADORES.items():
        if antigo not in dados:
            continue
        registro_antigo = dict(dados.pop(antigo))
        if novo not in dados:
            dados[novo] = registro_antigo
        else:
            for campo, valor in registro_antigo.items():
                if campo not in dados[novo] or dados[novo][campo] in (None, "", []):
                    dados[novo][campo] = valor
        dados[novo]["nome"] = novo
        alterado = True
    return alterado


def _ler_enriquecimentos() -> dict[str, dict[str, Any]]:
    """Lê enriquecimentos externos separados da lógica da aplicação."""
    if not ENRICHMENTS_FILE.exists():
        return {}

    try:
        conteudo = json.loads(ENRICHMENTS_FILE.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as erro:
        raise DataIntegrityError(
            f"O arquivo {ENRICHMENTS_FILE.name} está inválido e não foi aplicado. Erro: {erro}"
        ) from erro

    if not isinstance(conteudo, dict):
        raise DataIntegrityError(
            f"O arquivo {ENRICHMENTS_FILE.name} precisa conter um objeto no nível principal."
        )

    enriquecimentos: dict[str, dict[str, Any]] = {}
    for nome, registro in conteudo.items():
        if not isinstance(registro, Mapping):
            raise DataIntegrityError(
                f"Enriquecimento inválido para '{nome}': o registro precisa ser um objeto."
            )
        enriquecimentos[str(nome)] = dict(registro)
    return enriquecimentos


def _data_externa(valor: Any) -> datetime | None:
    """Converte datas externas conhecidas sem reinterpretar valores inválidos."""
    if not valor:
        return None
    texto = str(valor).strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def _fonte_externa_eh_mais_recente(
    registro: Mapping[str, Any],
    enriquecimento: Mapping[str, Any],
) -> bool:
    atual = _data_externa(registro.get("tm_ultima_atualizacao"))
    nova = _data_externa(enriquecimento.get("tm_ultima_atualizacao"))
    if nova is None:
        return False
    return atual is None or nova >= atual


def _aplicar_enriquecimentos(
    dados: dict[str, Any],
    enriquecimentos: Mapping[str, Mapping[str, Any]],
) -> bool:
    """Mescla dados externos sem reverter conteúdo editorial ou informação mais recente."""
    alterado = False
    campos_protegidos = CAMPOS_EDITORIAIS_PROTEGIDOS | CAMPOS_TATICOS_PROTEGIDOS

    for nome, enriquecimento in enriquecimentos.items():
        if nome not in dados:
            dados[nome] = copy.deepcopy(dict(enriquecimento))
            alterado = True
            continue

        registro = dados[nome]
        fonte_mais_recente = _fonte_externa_eh_mais_recente(registro, enriquecimento)

        for campo, valor in enriquecimento.items():
            ausente = campo not in registro or registro[campo] in (None, "", [])

            if campo in campos_protegidos:
                if ausente:
                    registro[campo] = copy.deepcopy(valor)
                    alterado = True
                continue

            if campo.startswith("tm_"):
                if ausente or (fonte_mais_recente and registro.get(campo) != valor):
                    registro[campo] = copy.deepcopy(valor)
                    alterado = True
                continue

            # Campos cadastrais externos apenas completam lacunas. O JSON canônico prevalece.
            if ausente:
                registro[campo] = copy.deepcopy(valor)
                alterado = True

    return alterado


def salvar_jogadores(dados: Mapping[str, Any]) -> None:
    """Grava JSON de forma atômica e mantém um backup da versão anterior."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporario = DATA_FILE.with_suffix(".json.tmp")
    backup = DATA_FILE.with_suffix(".json.bak")

    conteudo = json.dumps(dados, indent=4, ensure_ascii=False, sort_keys=False)
    temporario.write_text(conteudo + "\n", encoding="utf-8")

    # Valida o arquivo temporário antes de substituir a base.
    json.loads(temporario.read_text(encoding="utf-8"))

    if DATA_FILE.exists():
        shutil.copy2(DATA_FILE, backup)
    temporario.replace(DATA_FILE)


def carregar_jogadores() -> dict[str, dict[str, Any]]:
    """Carrega, migra e enriquece o JSON sem apagar conteúdo editorial."""
    dados_brutos, reparado = _ler_json()
    enriquecimentos = _ler_enriquecimentos()
    alterado = reparado or _mesclar_aliases(dados_brutos)

    normalizados: dict[str, dict[str, Any]] = {}
    for nome, registro in dados_brutos.items():
        if not isinstance(registro, Mapping):
            continue
        registro_normalizado = _normalizar_registro(nome, registro)
        chave = registro_normalizado.get("nome") or nome
        normalizados[str(chave)] = registro_normalizado
        if registro_normalizado != registro or chave != nome:
            alterado = True

    if _aplicar_enriquecimentos(normalizados, enriquecimentos):
        alterado = True

    # Segunda normalização cobre os atletas recém-injetados.
    normalizados = {
        nome: _normalizar_registro(nome, registro)
        for nome, registro in normalizados.items()
    }

    if alterado:
        salvar_jogadores(normalizados)
    return normalizados


def adicionar_jogador(
    jogadores: dict[str, dict[str, Any]],
    dados_novos: Mapping[str, Any],
) -> str:
    nome = str(dados_novos.get("nome", "")).strip()
    if not nome:
        raise ValueError("O nome do jogador é obrigatório.")
    if nome in jogadores:
        raise ValueError(f"O jogador '{nome}' já está cadastrado.")

    registro = copy.deepcopy(CAMPOS_MINIMOS)
    registro.update(dict(dados_novos))
    registro["nome"] = nome
    registro = _normalizar_registro(nome, registro)
    jogadores[nome] = registro
    salvar_jogadores(jogadores)
    return nome


def validar_posicoes(jogadores: Mapping[str, Mapping[str, Any]]) -> list[str]:
    erros: list[str] = []
    for nome, dados in jogadores.items():
        posicao = dados.get("posicao")
        if posicao not in POSICOES_OFICIAIS:
            erros.append(f"{nome}: posição principal inválida ({posicao}).")
        for secundaria in dados.get("posicoes_multiplas", []):
            if secundaria not in POSICOES_OFICIAIS:
                erros.append(f"{nome}: posição secundária inválida ({secundaria}).")
    return erros
