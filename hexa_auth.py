"""Autenticação e autorização da área administrativa."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

__all__ = [
    "AuthConfigError",
    "IdentidadeUsuario",
    "ProvedorAuth",
    "StAuthProvider",
    "email_normalizado",
    "identidade_atual",
    "lista_administradores",
    "render_controle_login",
    "usuario_autenticado",
    "usuario_eh_admin",
]


class AuthConfigError(RuntimeError):
    """Configuração de autenticação ausente ou inválida."""


@dataclass(frozen=True, slots=True)
class IdentidadeUsuario:
    autenticado: bool
    email: str = ""
    nome: str = ""
    subject: str = ""

    @property
    def origem_auditoria(self) -> str:
        if not self.autenticado:
            return "usuario_anonimo"
        identificador = self.email or self.subject or "usuario_autenticado"
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
    """Adaptador mínimo sobre st.login, st.user e st.logout."""

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


def lista_administradores(
    secrets: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Lê a allowlist de administradores sem expor segredos."""
    if secrets is None:
        fonte = _streamlit().secrets
    else:
        fonte = secrets

    try:
        secao = fonte["administradores"]
        emails = secao["emails"]
    except (KeyError, TypeError) as erro:
        raise AuthConfigError(
            "Configure [administradores].emails nos Secrets do Streamlit."
        ) from erro

    if isinstance(emails, str):
        valores: Sequence[Any] = (emails,)
    elif isinstance(emails, Sequence):
        valores = emails
    else:
        raise AuthConfigError(
            "[administradores].emails deve ser uma lista de e-mails."
        )

    normalizados = tuple(
        email
        for email in (email_normalizado(item) for item in valores)
        if email
    )
    if not normalizados:
        raise AuthConfigError(
            "A lista de administradores não pode estar vazia."
        )
    return tuple(dict.fromkeys(normalizados))


def identidade_atual(
    provedor: ProvedorAuth | None = None,
) -> IdentidadeUsuario:
    provedor_ativo = provedor or StAuthProvider()
    if not provedor_ativo.esta_autenticado():
        return IdentidadeUsuario(autenticado=False)

    claims = provedor_ativo.claims()
    return IdentidadeUsuario(
        autenticado=True,
        email=email_normalizado(claims.get("email")),
        nome=str(
            claims.get("name")
            or claims.get("preferred_username")
            or ""
        ).strip(),
        subject=str(claims.get("sub") or "").strip(),
    )


def usuario_autenticado(
    provedor: ProvedorAuth | None = None,
) -> bool:
    return identidade_atual(provedor).autenticado


def usuario_eh_admin(
    provedor: ProvedorAuth | None = None,
    *,
    secrets: Mapping[str, Any] | None = None,
) -> bool:
    identidade = identidade_atual(provedor)
    if not identidade.autenticado or not identidade.email:
        return False
    return identidade.email in set(lista_administradores(secrets))


def render_controle_login() -> IdentidadeUsuario:
    """Renderiza login/logout sem liberar funções administrativas."""
    st = _streamlit()
    provedor = StAuthProvider()
    identidade = identidade_atual(provedor)

    st.sidebar.markdown("### Acesso administrativo")

    if identidade.autenticado:
        rotulo = identidade.nome or identidade.email or "Usuário autenticado"
        st.sidebar.caption(f"Conectado como {rotulo}")
        if st.sidebar.button(
            "Sair",
            key="auth_logout",
            width="stretch",
        ):
            provedor.logout()
        return identidade

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
    return identidade
