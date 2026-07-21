"""Persistência, migrações e tratamento de dados do projeto.

O JSON é a fonte canônica do elenco. Este módulo mantém somente migrações e
enriquecimentos incrementais, evitando uma segunda cópia completa da base.
Campos editoriais e táticos do projeto nunca são sobrescritos por dados externos.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from typing import Any, Mapping

from hexa_audit import (
    AuditoriaRepository,
    JsonlAuditoriaRepository,
    gerar_eventos_alteracao,
)
from hexa_config import (
    AUDIT_FILE,
    DATA_FILE,
    ENRICHMENTS_FILE,
    GRUPO_OBSERVACAO,
    IDADE_PADRAO,
)
from hexa_models import (
    RelatorioIntegridade,
    validar_estrutura_bruta,
    validar_jogadores_normalizados,
)
from hexa_repository import (
    DataIntegrityError,
    JogadoresRepository,
    JsonJogadoresRepository,
    RegistroVersao,
    VERSAO_AUSENTE,
)
from hexa_taticas import POSICOES_OFICIAIS, normalizar_lista_posicoes, normalizar_posicao


__all__ = [
    "BaseJogadores",
    "DataIntegrityError",
    "adicionar_jogador",
    "auditoria_padrao",
    "carregar_jogadores",
    "extrair_altura_metros",
    "extrair_numero",
    "extrair_valor_milhoes",
    "formatar_valor_milhoes",
    "percentual_do_pico",
    "repositorio_padrao",
    "salvar_jogadores",
    "validar_integridade_jogadores",
    "validar_posicoes",
    "valor_mercado_atual",
    "valor_mercado_maximo",
]



class BaseJogadores(dict[str, dict[str, Any]]):
    """Dicionário de jogadores acompanhado da versão lida da fonte."""

    def __init__(
        self,
        dados: Mapping[str, Mapping[str, Any]] | None = None,
        *,
        versao_fonte: str = VERSAO_AUSENTE,
    ) -> None:
        super().__init__(
            {
                str(nome): copy.deepcopy(dict(registro))
                for nome, registro in (dados or {}).items()
            }
        )
        self.versao_fonte = versao_fonte

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
    "posicao": "",
    "posicoes_multiplas": [],
    "clube": "N/A",
    "idade": IDADE_PADRAO,
    "grupo": GRUPO_OBSERVACAO,
    "tipo": GRUPO_OBSERVACAO,
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
    if posicao and posicao not in posicoes:
        posicoes.insert(0, posicao)

    dados["posicao"] = posicao or ""
    dados["posicoes_multiplas"] = posicoes

    for campo, valor_padrao in CAMPOS_MINIMOS.items():
        if campo not in dados or dados[campo] is None:
            dados[campo] = copy.deepcopy(valor_padrao)

    try:
        dados["idade"] = int(dados.get("idade", IDADE_PADRAO))
    except (TypeError, ValueError):
        dados["idade"] = IDADE_PADRAO

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
            posicao_nova = normalizar_posicao(enriquecimento.get("posicao"))
            if not posicao_nova:
                # Um enriquecimento parcial não pode criar um atleta sem posição
                # editorial válida; isso evitaria inventar uma função tática.
                continue
            novo_registro = copy.deepcopy(dict(enriquecimento))
            novo_registro["posicao"] = posicao_nova
            dados[nome] = novo_registro
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


def _mensagem_erros_integridade(
    relatorio: RelatorioIntegridade,
    contexto: str,
) -> str:
    detalhes = " | ".join(problema.mensagem for problema in relatorio.erros)
    return (
        f"{contexto} contém erros bloqueantes e não foi salvo. "
        f"Corrija a fonte canônica antes de continuar. {detalhes}"
    )





def validar_integridade_jogadores(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> RelatorioIntegridade:
    """Gera o relatório público de integridade da base normalizada."""
    return validar_jogadores_normalizados(jogadores)


def auditoria_padrao(
    repositorio: JogadoresRepository | None = None,
) -> AuditoriaRepository | None:
    """Retorna auditoria JSONL apenas para a implementação JSON do projeto."""
    if repositorio is None:
        return JsonlAuditoriaRepository(AUDIT_FILE)
    if isinstance(repositorio, JsonJogadoresRepository):
        caminho = repositorio.caminho.with_name(AUDIT_FILE.name)
        return JsonlAuditoriaRepository(caminho)
    return None


def repositorio_padrao() -> JogadoresRepository:
    """Cria a implementação padrão sem manter estado global mutável."""
    return JsonJogadoresRepository(DATA_FILE)


def salvar_jogadores(
    dados: Mapping[str, Any],
    repositorio: JogadoresRepository | None = None,
    *,
    versao_esperada: str | None = None,
    origem: str = "aplicacao",
    estado_anterior: Mapping[str, Mapping[str, Any]] | None = None,
    auditoria: AuditoriaRepository | None = None,
) -> RegistroVersao:
    """Valida e persiste a base respeitando a versão lida pela sessão."""
    estrutural = validar_estrutura_bruta(dados)
    if estrutural.possui_erros:
        raise DataIntegrityError(
            _mensagem_erros_integridade(estrutural, "A base a persistir")
        )

    relatorio = validar_jogadores_normalizados(dados)  # type: ignore[arg-type]
    if relatorio.possui_erros:
        raise DataIntegrityError(
            _mensagem_erros_integridade(relatorio, "A base a persistir")
        )

    if versao_esperada is None and isinstance(dados, BaseJogadores):
        versao_esperada = dados.versao_fonte

    repositorio_ativo = repositorio or repositorio_padrao()

    if estado_anterior is None:
        try:
            estado_anterior = repositorio_ativo.carregar().jogadores
        except DataIntegrityError:
            estado_anterior = {}

    registro = repositorio_ativo.salvar(
        dados,
        versao_esperada=versao_esperada,
        origem=origem,
    )

    auditoria_ativa = auditoria if auditoria is not None else auditoria_padrao(
        repositorio_ativo
    )
    if auditoria_ativa is not None:
        eventos = gerar_eventos_alteracao(
            estado_anterior,
            dados,  # type: ignore[arg-type]
            origem=origem,
            versao_anterior=versao_esperada or VERSAO_AUSENTE,
            versao_nova=registro.versao,
            ocorrido_em=registro.atualizado_em,
        )
        auditoria_ativa.registrar(eventos)

    if isinstance(dados, BaseJogadores):
        dados.versao_fonte = registro.versao
    return registro


def carregar_jogadores(
    repositorio: JogadoresRepository | None = None,
) -> BaseJogadores:
    """Carrega, migra e enriquece os jogadores sem apagar conteúdo editorial."""
    repositorio_ativo = repositorio or repositorio_padrao()
    resultado = repositorio_ativo.carregar()
    dados_brutos = resultado.jogadores

    relatorio_bruto = validar_estrutura_bruta(dados_brutos)
    if relatorio_bruto.possui_erros:
        raise DataIntegrityError(
            _mensagem_erros_integridade(relatorio_bruto, "A fonte de jogadores")
        )

    enriquecimentos = _ler_enriquecimentos()
    alterado = resultado.reparado or _mesclar_aliases(dados_brutos)

    normalizados: dict[str, dict[str, Any]] = {}
    for nome, registro in dados_brutos.items():
        registro_normalizado = _normalizar_registro(nome, registro)
        chave = registro_normalizado.get("nome") or nome
        normalizados[str(chave)] = registro_normalizado
        if registro_normalizado != registro or chave != nome:
            alterado = True

    if _aplicar_enriquecimentos(normalizados, enriquecimentos):
        alterado = True

    normalizados = {
        nome: _normalizar_registro(nome, registro)
        for nome, registro in normalizados.items()
    }

    relatorio_final = validar_jogadores_normalizados(normalizados)
    if relatorio_final.possui_erros:
        raise DataIntegrityError(
            _mensagem_erros_integridade(relatorio_final, "A base normalizada")
        )

    base = BaseJogadores(normalizados, versao_fonte=resultado.versao)
    if alterado:
        registro = salvar_jogadores(
            base,
            repositorio_ativo,
            versao_esperada=resultado.versao,
            origem="self_healing",
            estado_anterior=dados_brutos,
        )
        base.versao_fonte = registro.versao
    return base


def adicionar_jogador(
    jogadores: dict[str, dict[str, Any]],
    dados_novos: Mapping[str, Any],
    repositorio: JogadoresRepository | None = None,
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

    versao_esperada = (
        jogadores.versao_fonte
        if isinstance(jogadores, BaseJogadores)
        else None
    )
    nova_base = BaseJogadores(
        jogadores,
        versao_fonte=versao_esperada or VERSAO_AUSENTE,
    )
    nova_base[nome] = registro
    resultado = salvar_jogadores(
        nova_base,
        repositorio,
        versao_esperada=versao_esperada,
        origem="cadastro_interface",
        estado_anterior=jogadores,
    )

    # Atualiza a sessão somente depois que a persistência termina com sucesso.
    jogadores.clear()
    jogadores.update(nova_base)
    if isinstance(jogadores, BaseJogadores):
        jogadores.versao_fonte = resultado.versao
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
