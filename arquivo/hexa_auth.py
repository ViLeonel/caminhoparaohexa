"""Autenticação, validação de identidade e autorização administrativa."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

LOGGER = logging.getLogger(__name__)

__all__ = [
    "AuthConfigError",
    "IdentidadeUsuario",
    "Permissao",
    "PoliticaAuth",
    "ProvedorAuth",
    "StAuthProvider",
    "email_normalizado",
    "identidade_atual",
    "lista_administradores",
    "politica_auth",
    "render_controle_login",
    "registrar_erro_configuracao_auth",
    "usuario_autenticado",
    "usuario_eh_admin",
    "usuario_tem_permissao",
]


class AuthConfigError(RuntimeError):
    """Configuração de autenticação ausente ou inválida."""


class Permissao(str, Enum):
    """Permissões administrativas explícitas e auditáveis."""

    VISUALIZAR_ADMIN = "visualizar_admin"
    CONSULTAR_AUDITORIA = "consultar_auditoria"
    EXPORTAR_DADOS = "exportar_dados"
    EDITAR_DADOS = "editar_dados"


@dataclass(frozen=True, slots=True)
class PoliticaAuth:
    """Política local aplicada sobre os claims OIDC entregues pelo Streamlit."""

    exigir_email_verificado: bool = True
    tolerancia_relogio_segundos: int = 60
    administradores_emails: tuple[str, ...] = ()
    administradores_subjects: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class IdentidadeUsuario:
    autenticado: bool
    email: str = ""
    nome: str = ""
    subject: str = ""
    email_verificado: bool | None = None
    emitido_em: int | None = None
    expira_em: int | None = None
    motivo_invalidez: str = ""

    @property
    def origem_auditoria(self) -> str:
        if not self.autenticado:
            return "usuario_anonimo"
        identificador = self.subject or self.email or "usuario_autenticado"
        return f"admin_interface:{identificador}"


@runtime_checkable
class ProvedorAuth(Protocol):
    def esta_autenticado(self) -> bool:
        ...

    def claims(self) -> Mapping[str, Any]:
        ...

    def login(self) -> None:
        ...

    def logout(self) -> None:
        ...


def _streamlit():
    try:
        import streamlit as st
    except ModuleNotFoundError as erro:
        raise AuthConfigError(
            "O Streamlit não está instalado neste ambiente."
        ) from erro
    return st


class StAuthProvider:
    """Adaptador mínimo sobre ``st.login``, ``st.user`` e ``st.logout``."""

    def esta_autenticado(self) -> bool:
        st = _streamlit()
        return bool(getattr(st.user, "is_logged_in", False))

    def claims(self) -> Mapping[str, Any]:
        st = _streamlit()
        if not self.esta_autenticado():
            return {}
        try:
            return st.user.to_dict()
        except AttributeError:
            return dict(st.user)

    def login(self) -> None:
        _streamlit().login()

    def logout(self) -> None:
        _streamlit().logout()


def email_normalizado(valor: Any) -> str:
    return str(valor or "").strip().casefold()


def _booleano_ou_none(valor: Any) -> bool | None:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        normalizado = valor.strip().casefold()
        if normalizado in {"true", "1", "sim", "yes"}:
            return True
        if normalizado in {"false", "0", "nao", "não", "no"}:
            return False
    return None


def _inteiro_ou_none(valor: Any) -> int | None:
    if isinstance(valor, bool) or valor in (None, ""):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero):
        return None
    return int(numero)


def _sequencia_textos(valor: Any, *, campo: str) -> tuple[str, ...]:
    if valor in (None, ""):
        return ()
    if isinstance(valor, str):
        itens: Sequence[Any] = (valor,)
    elif isinstance(valor, Sequence):
        itens = valor
    else:
        raise AuthConfigError(f"{campo} deve ser uma lista de textos.")

    normalizados = tuple(
        texto
        for texto in (str(item or "").strip() for item in itens)
        if texto
    )
    return tuple(dict.fromkeys(normalizados))


def politica_auth(
    secrets: Mapping[str, Any] | None = None,
) -> PoliticaAuth:
    """Lê a política sem expor valores sensíveis em mensagens ou logs."""
    if secrets is None:
        try:
            fonte: Mapping[str, Any] = _streamlit().secrets
            secao_admin = fonte["administradores"]
        except Exception as erro:
            raise AuthConfigError(
                "Configure a seção [administradores] nos Secrets do Streamlit."
            ) from erro
    else:
        fonte = secrets
        try:
            secao_admin = fonte["administradores"]
        except (KeyError, TypeError) as erro:
            raise AuthConfigError(
                "Configure a seção [administradores] nos Secrets do Streamlit."
            ) from erro

    try:
        emails_brutos = secao_admin.get("emails", ())
        subjects_brutos = secao_admin.get("subjects", ())
    except AttributeError as erro:
        raise AuthConfigError(
            "A seção [administradores] precisa ser uma tabela TOML."
        ) from erro

    emails = tuple(
        dict.fromkeys(
            email
            for email in (
                email_normalizado(item)
                for item in _sequencia_textos(
                    emails_brutos,
                    campo="[administradores].emails",
                )
            )
            if email
        )
    )
    subjects = _sequencia_textos(
        subjects_brutos,
        campo="[administradores].subjects",
    )
    if not emails and not subjects:
        raise AuthConfigError(
            "Informe ao menos um e-mail ou subject administrativo."
        )

    try:
        secao_seguranca = fonte.get("seguranca", {})
    except AttributeError:
        secao_seguranca = {}
    if not isinstance(secao_seguranca, Mapping):
        raise AuthConfigError("[seguranca] precisa ser uma tabela TOML.")

    exigir = _booleano_ou_none(
        secao_seguranca.get("exigir_email_verificado", True)
    )
    if exigir is None:
        raise AuthConfigError(
            "[seguranca].exigir_email_verificado deve ser booleano."
        )

    tolerancia = _inteiro_ou_none(
        secao_seguranca.get("tolerancia_relogio_segundos", 60)
    )
    if tolerancia is None or not 0 <= tolerancia <= 300:
        raise AuthConfigError(
            "[seguranca].tolerancia_relogio_segundos deve estar entre 0 e 300."
        )

    return PoliticaAuth(
        exigir_email_verificado=exigir,
        tolerancia_relogio_segundos=tolerancia,
        administradores_emails=emails,
        administradores_subjects=subjects,
    )


def lista_administradores(
    secrets: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Compatibilidade pública: retorna a allowlist normalizada de e-mails."""
    return politica_auth(secrets).administradores_emails


def _identidade_dos_claims(
    claims: Mapping[str, Any],
    *,
    politica: PoliticaAuth | None,
    agora: int,
) -> IdentidadeUsuario:
    email = email_normalizado(claims.get("email"))
    subject = str(claims.get("sub") or "").strip()
    nome = str(
        claims.get("name")
        or claims.get("preferred_username")
        or ""
    ).strip()
    email_verificado = _booleano_ou_none(claims.get("email_verified"))
    emitido_em = _inteiro_ou_none(claims.get("iat"))
    expira_em = _inteiro_ou_none(claims.get("exp"))
    tolerancia = politica.tolerancia_relogio_segundos if politica else 60

    motivo = ""
    if not subject:
        motivo = "O provedor não informou o identificador estável do usuário."
    elif expira_em is not None and agora > expira_em + tolerancia:
        motivo = "A sessão de autenticação expirou."
    elif emitido_em is not None and emitido_em > agora + tolerancia:
        motivo = "O token possui horário de emissão inválido."
    elif (
        politica is not None
        and politica.exigir_email_verificado
        and email
        and email_verificado is not True
    ):
        motivo = "O provedor não confirmou a verificação do e-mail."

    return IdentidadeUsuario(
        autenticado=not motivo,
        email=email,
        nome=nome,
        subject=subject,
        email_verificado=email_verificado,
        emitido_em=emitido_em,
        expira_em=expira_em,
        motivo_invalidez=motivo,
    )


def identidade_atual(
    provedor: ProvedorAuth | None = None,
    *,
    secrets: Mapping[str, Any] | None = None,
    agora: int | None = None,
    validar_politica: bool = True,
) -> IdentidadeUsuario:
    provedor_ativo = provedor or StAuthProvider()
    if not provedor_ativo.esta_autenticado():
        return IdentidadeUsuario(autenticado=False)

    claims = provedor_ativo.claims()
    politica = (
        politica_auth(secrets)
        if validar_politica
        else None
    )
    return _identidade_dos_claims(
        claims,
        politica=politica,
        agora=int(time.time() if agora is None else agora),
    )


def usuario_autenticado(
    provedor: ProvedorAuth | None = None,
    *,
    secrets: Mapping[str, Any] | None = None,
) -> bool:
    return identidade_atual(
        provedor,
        secrets=secrets,
        validar_politica=False,
    ).autenticado


_PERMISSOES_ADMIN: frozenset[Permissao] = frozenset(
    {
        Permissao.VISUALIZAR_ADMIN,
        Permissao.CONSULTAR_AUDITORIA,
        Permissao.EXPORTAR_DADOS,
        # EDITAR_DADOS permanece deliberadamente desabilitada nesta fase.
    }
)


def usuario_eh_admin(
    provedor: ProvedorAuth | None = None,
    *,
    identidade: IdentidadeUsuario | None = None,
    secrets: Mapping[str, Any] | None = None,
) -> bool:
    identidade_ativa = identidade or identidade_atual(
        provedor,
        secrets=secrets,
        validar_politica=False,
    )
    if not identidade_ativa.autenticado:
        return False

    politica = politica_auth(secrets)
    if identidade is None:
        identidade_ativa = identidade_atual(
            provedor,
            secrets=secrets,
        )
        if not identidade_ativa.autenticado:
            return False

    por_subject = bool(
        identidade_ativa.subject
        and identidade_ativa.subject in set(
            politica.administradores_subjects
        )
    )
    por_email = bool(
        identidade_ativa.email
        and identidade_ativa.email in set(
            politica.administradores_emails
        )
    )
    return por_subject or por_email


def usuario_tem_permissao(
    permissao: Permissao,
    provedor: ProvedorAuth | None = None,
    *,
    identidade: IdentidadeUsuario | None = None,
    secrets: Mapping[str, Any] | None = None,
) -> bool:
    if permissao not in _PERMISSOES_ADMIN:
        return False
    return usuario_eh_admin(
        provedor,
        identidade=identidade,
        secrets=secrets,
    )


def registrar_erro_configuracao_auth(erro: AuthConfigError) -> None:
    """Registra configuração inválida sem expor detalhes na interface pública."""
    mensagem = str(erro)
    if "[administradores]" in mensagem:
        LOGGER.warning("Secrets sem seção [administradores].")
        return
    LOGGER.warning("Configuração administrativa inválida: %s", mensagem)


def render_controle_login(
    identidade: IdentidadeUsuario | None = None,
) -> IdentidadeUsuario:
    """Renderiza o acesso administrativo sem expor configuração interna."""
    st = _streamlit()
    provedor = StAuthProvider()

    identidade_ativa = identidade
    if identidade_ativa is None:
        try:
            identidade_ativa = identidade_atual(provedor)
        except AuthConfigError as erro:
            registrar_erro_configuracao_auth(erro)
            identidade_ativa = identidade_atual(
                provedor,
                validar_politica=False,
            )

    st.sidebar.markdown("### Área administrativa em construção")

    if identidade_ativa.motivo_invalidez:
        st.sidebar.warning(
            f"{identidade_ativa.motivo_invalidez} Entre novamente para continuar."
        )
        if st.sidebar.button(
            "Encerrar sessão inválida",
            key="auth_logout_invalid",
            width="stretch",
        ):
            provedor.logout()
        return identidade_ativa

    if identidade_ativa.autenticado:
        rotulo = (
            identidade_ativa.nome
            or identidade_ativa.email
            or "Usuário autenticado"
        )
        st.sidebar.caption(f"Conectado como {rotulo}")
        if st.sidebar.button(
            "Sair",
            key="auth_logout",
            width="stretch",
        ):
            provedor.logout()
        return identidade_ativa

    st.sidebar.caption(
        "O conteúdo público permanece disponível. "
        "O login é necessário somente para a área administrativa."
    )
    if st.sidebar.button(
        "Entrar",
        key="auth_login",
        width="stretch",
    ):
        provedor.login()
    return identidade_ativa

