"""Modelos tipados e validação de integridade dos jogadores."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, TypedDict

from hexa_config import IDADE_MAXIMA_CADASTRO, IDADE_MINIMA_CADASTRO
from hexa_taticas import POSICOES_OFICIAIS, normalizar_posicao

__all__ = [
    "DadosExternos",
    "Jogador",
    "JogadorObrigatorio",
    "ProblemaIntegridade",
    "RelatorioIntegridade",
    "SeveridadeIntegridade",
    "chave_canonica_nome",
    "validar_estrutura_bruta",
    "validar_jogadores_normalizados",
]



class DadosExternos(TypedDict, total=False):
    tm_nascimento: str
    tm_naturalidade: str
    tm_altura: str
    tm_altura_metros: float
    tm_nacionalidades: list[str]
    tm_pe: str
    tm_empresario: str
    tm_clube_desde: str
    tm_contrato: str
    tm_ultima_renovacao: str
    tm_equipador: str
    tm_posicao_site: str
    tm_posicoes_secundarias_site: list[str]
    tm_valor_mercado: str
    tm_valor_mercado_milhoes: float
    tm_valor_maximo: str
    tm_valor_maximo_milhoes: float
    tm_data_valor_maximo: str
    tm_ultima_atualizacao: str
    tm_fonte: str
    tm_extraido_em: str


class JogadorObrigatorio(TypedDict):
    nome: str
    posicao: str
    posicoes_multiplas: list[str]
    clube: str
    idade: int
    grupo: str
    tipo: str
    nota_vini: float
    nota_roberto: float
    pontos_fortes: str
    pontos_fracos: str
    historico: str


class Jogador(JogadorObrigatorio, total=False):
    nome_completo: str


class SeveridadeIntegridade(str, Enum):
    ERRO = "erro"
    AVISO = "aviso"


@dataclass(frozen=True, slots=True)
class ProblemaIntegridade:
    severidade: SeveridadeIntegridade
    codigo: str
    mensagem: str
    jogador: str | None = None
    campo: str | None = None


@dataclass(frozen=True, slots=True)
class RelatorioIntegridade:
    problemas: tuple[ProblemaIntegridade, ...] = ()

    @property
    def erros(self) -> tuple[ProblemaIntegridade, ...]:
        return tuple(
            problema
            for problema in self.problemas
            if problema.severidade is SeveridadeIntegridade.ERRO
        )

    @property
    def avisos(self) -> tuple[ProblemaIntegridade, ...]:
        return tuple(
            problema
            for problema in self.problemas
            if problema.severidade is SeveridadeIntegridade.AVISO
        )

    @property
    def possui_erros(self) -> bool:
        return bool(self.erros)

    @property
    def valido(self) -> bool:
        return not self.possui_erros

    def mensagens(self) -> list[str]:
        return [problema.mensagem for problema in self.problemas]


def chave_canonica_nome(valor: Any) -> str:
    """Normaliza um nome apenas para comparação e detecção de duplicidades."""
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"\s+", " ", texto).strip().casefold()
    return texto


def _problema(
    severidade: SeveridadeIntegridade,
    codigo: str,
    mensagem: str,
    jogador: str | None = None,
    campo: str | None = None,
) -> ProblemaIntegridade:
    return ProblemaIntegridade(severidade, codigo, mensagem, jogador, campo)


def validar_estrutura_bruta(jogadores: Mapping[str, Any]) -> RelatorioIntegridade:
    """Valida riscos estruturais antes de qualquer normalização ou salvamento."""
    problemas: list[ProblemaIntegridade] = []
    nomes_canonicos: dict[str, str] = {}

    for chave, registro in jogadores.items():
        nome_chave = str(chave).strip()
        if not nome_chave:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "chave_vazia",
                    "Existe um jogador com chave vazia no JSON.",
                )
            )
            continue

        if not isinstance(registro, Mapping):
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "registro_nao_objeto",
                    f"{nome_chave}: o registro precisa ser um objeto JSON.",
                    nome_chave,
                )
            )
            continue

        nome_registro = str(registro.get("nome") or "").strip()
        nome_efetivo = nome_registro or nome_chave
        canonica = chave_canonica_nome(nome_efetivo)
        if not canonica:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "nome_vazio",
                    f"{nome_chave}: o nome do jogador está vazio.",
                    nome_chave,
                    "nome",
                )
            )
        elif canonica in nomes_canonicos and nomes_canonicos[canonica] != nome_chave:
            outro = nomes_canonicos[canonica]
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "nome_duplicado",
                    f"{nome_chave}: nome duplicado após normalização; conflita com '{outro}'.",
                    nome_chave,
                    "nome",
                )
            )
        else:
            nomes_canonicos[canonica] = nome_chave

        if nome_registro and nome_registro != nome_chave:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.AVISO,
                    "chave_nome_divergente",
                    f"{nome_chave}: a chave difere do campo nome ('{nome_registro}').",
                    nome_chave,
                    "nome",
                )
            )

        posicao_bruta = registro.get("posicao")
        posicoes_brutas = registro.get("posicoes_multiplas")
        if posicao_bruta not in (None, "") and normalizar_posicao(posicao_bruta) is None:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "posicao_bruta_invalida",
                    f"{nome_chave}: posição não reconhecida ({posicao_bruta}).",
                    nome_chave,
                    "posicao",
                )
            )
        if posicoes_brutas is not None and not isinstance(posicoes_brutas, (list, tuple)):
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "posicoes_multiplas_brutas_tipo",
                    f"{nome_chave}: posicoes_multiplas precisa ser uma lista.",
                    nome_chave,
                    "posicoes_multiplas",
                )
            )

        if "idade" in registro:
            try:
                idade = int(registro.get("idade"))
            except (TypeError, ValueError):
                idade = -1
            if not IDADE_MINIMA_CADASTRO <= idade <= IDADE_MAXIMA_CADASTRO:
                problemas.append(
                    _problema(
                        SeveridadeIntegridade.ERRO,
                        "idade_bruta_invalida",
                        f"{nome_chave}: idade inválida antes da normalização.",
                        nome_chave,
                        "idade",
                    )
                )

        for campo_nota in ("nota_vini", "nota_roberto"):
            if campo_nota not in registro:
                continue
            try:
                nota = float(registro.get(campo_nota))
            except (TypeError, ValueError):
                nota = -1.0
            if not 0.0 <= nota <= 10.0:
                problemas.append(
                    _problema(
                        SeveridadeIntegridade.ERRO,
                        "nota_bruta_invalida",
                        f"{nome_chave}: {campo_nota} deve estar entre 0 e 10.",
                        nome_chave,
                        campo_nota,
                    )
                )

    return RelatorioIntegridade(tuple(problemas))


def validar_jogadores_normalizados(
    jogadores: Mapping[str, Mapping[str, Any]],
) -> RelatorioIntegridade:
    """Valida o contrato final que qualquer repositório deve persistir."""
    problemas: list[ProblemaIntegridade] = []
    nomes_canonicos: dict[str, str] = {}

    for chave, dados in jogadores.items():
        nome_chave = str(chave).strip()
        nome = str(dados.get("nome") or "").strip()

        if not nome:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "nome_vazio",
                    f"{nome_chave}: o nome do jogador é obrigatório.",
                    nome_chave,
                    "nome",
                )
            )
        elif nome != nome_chave:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "chave_nome_divergente",
                    f"{nome_chave}: a chave canônica deve ser igual ao campo nome ('{nome}').",
                    nome_chave,
                    "nome",
                )
            )

        canonica = chave_canonica_nome(nome or nome_chave)
        if canonica in nomes_canonicos and nomes_canonicos[canonica] != nome_chave:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "nome_duplicado",
                    f"{nome_chave}: duplicidade normalizada com '{nomes_canonicos[canonica]}'.",
                    nome_chave,
                    "nome",
                )
            )
        else:
            nomes_canonicos[canonica] = nome_chave

        posicao = dados.get("posicao")
        posicoes = dados.get("posicoes_multiplas")
        if posicao not in POSICOES_OFICIAIS:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "posicao_invalida",
                    f"{nome_chave}: posição principal inválida ({posicao}).",
                    nome_chave,
                    "posicao",
                )
            )

        if not isinstance(posicoes, list):
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "posicoes_multiplas_tipo",
                    f"{nome_chave}: posicoes_multiplas precisa ser uma lista.",
                    nome_chave,
                    "posicoes_multiplas",
                )
            )
            posicoes_validacao: list[Any] = []
        else:
            posicoes_validacao = posicoes

        for item in posicoes_validacao:
            if item not in POSICOES_OFICIAIS:
                problemas.append(
                    _problema(
                        SeveridadeIntegridade.ERRO,
                        "posicao_secundaria_invalida",
                        f"{nome_chave}: posição múltipla inválida ({item}).",
                        nome_chave,
                        "posicoes_multiplas",
                    )
                )

        if posicao in POSICOES_OFICIAIS and posicao not in posicoes_validacao:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "posicao_principal_ausente",
                    f"{nome_chave}: a posição principal precisa constar em posicoes_multiplas.",
                    nome_chave,
                    "posicoes_multiplas",
                )
            )

        try:
            idade = int(dados.get("idade"))
        except (TypeError, ValueError):
            idade = -1
        if not IDADE_MINIMA_CADASTRO <= idade <= IDADE_MAXIMA_CADASTRO:
            problemas.append(
                _problema(
                    SeveridadeIntegridade.ERRO,
                    "idade_invalida",
                    f"{nome_chave}: idade deve estar entre {IDADE_MINIMA_CADASTRO} e {IDADE_MAXIMA_CADASTRO}.",
                    nome_chave,
                    "idade",
                )
            )

        for campo in ("nota_vini", "nota_roberto"):
            try:
                nota = float(dados.get(campo))
            except (TypeError, ValueError):
                nota = -1.0
            if not 0.0 <= nota <= 10.0:
                problemas.append(
                    _problema(
                        SeveridadeIntegridade.ERRO,
                        "nota_invalida",
                        f"{nome_chave}: {campo} deve estar entre 0 e 10.",
                        nome_chave,
                        campo,
                    )
                )

        if not str(dados.get("grupo") or "").strip():
            problemas.append(
                _problema(
                    SeveridadeIntegridade.AVISO,
                    "grupo_vazio",
                    f"{nome_chave}: grupo editorial não informado.",
                    nome_chave,
                    "grupo",
                )
            )

        if not str(dados.get("clube") or "").strip():
            problemas.append(
                _problema(
                    SeveridadeIntegridade.AVISO,
                    "clube_vazio",
                    f"{nome_chave}: clube não informado.",
                    nome_chave,
                    "clube",
                )
            )

    return RelatorioIntegridade(tuple(problemas))
