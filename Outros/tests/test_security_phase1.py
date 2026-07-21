"""Testes de segurança adicionados na Fase 1."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hexa_audit import JsonlAuditoriaRepository, gerar_eventos_alteracao
from hexa_auth import (
    IdentidadeUsuario,
    Permissao,
    identidade_atual,
    politica_auth,
    registrar_erro_configuracao_auth,
    usuario_eh_admin,
    usuario_tem_permissao,
)


class ProvedorFalso:
    def __init__(self, claims, autenticado=True):
        self._claims = claims
        self._autenticado = autenticado
        self.logout_chamado = False

    def esta_autenticado(self):
        return self._autenticado

    def claims(self):
        return self._claims

    def login(self):
        return None

    def logout(self):
        self.logout_chamado = True


SECRETS = {
    "administradores": {
        "emails": ["Admin@Example.com"],
        "subjects": ["oidc-admin-1"],
    },
    "seguranca": {
        "exigir_email_verificado": True,
        "tolerancia_relogio_segundos": 60,
    },
}


class AuthSecurityTests(unittest.TestCase):
    def test_politica_normaliza_email(self):
        politica = politica_auth(SECRETS)
        self.assertEqual(
            politica.administradores_emails,
            ("admin@example.com",),
        )

    def test_token_expirado_e_rejeitado(self):
        agora = 1_700_000_000
        identidade = identidade_atual(
            ProvedorFalso(
                {
                    "sub": "oidc-admin-1",
                    "email": "admin@example.com",
                    "email_verified": True,
                    "iat": agora - 500,
                    "exp": agora - 61,
                }
            ),
            secrets=SECRETS,
            agora=agora,
        )
        self.assertFalse(identidade.autenticado)
        self.assertIn("expirou", identidade.motivo_invalidez)

    def test_email_nao_verificado_e_rejeitado(self):
        agora = int(time.time())
        identidade = identidade_atual(
            ProvedorFalso(
                {
                    "sub": "oidc-admin-1",
                    "email": "admin@example.com",
                    "email_verified": False,
                    "iat": agora,
                    "exp": agora + 3600,
                }
            ),
            secrets=SECRETS,
            agora=agora,
        )
        self.assertFalse(identidade.autenticado)

    def test_subject_autoriza_sem_depender_de_email(self):
        identidade = IdentidadeUsuario(
            autenticado=True,
            subject="oidc-admin-1",
        )
        self.assertTrue(
            usuario_eh_admin(
                identidade=identidade,
                secrets=SECRETS,
            )
        )

    def test_edicao_permanece_desabilitada(self):
        identidade = IdentidadeUsuario(
            autenticado=True,
            subject="oidc-admin-1",
        )
        self.assertTrue(
            usuario_tem_permissao(
                Permissao.VISUALIZAR_ADMIN,
                identidade=identidade,
                secrets=SECRETS,
            )
        )
        self.assertFalse(
            usuario_tem_permissao(
                Permissao.EDITAR_DADOS,
                identidade=identidade,
                secrets=SECRETS,
            )
        )


    def test_erro_de_secrets_vai_somente_para_log(self):
        from hexa_auth import AuthConfigError

        with self.assertLogs("hexa_auth", level="WARNING") as logs:
            registrar_erro_configuracao_auth(
                AuthConfigError(
                    "Configure a seção [administradores] nos Secrets do Streamlit."
                )
            )
        self.assertIn(
            "Secrets sem seção [administradores].",
            "\n".join(logs.output),
        )

class AuditSecurityTests(unittest.TestCase):
    def test_ator_e_preservado_em_alteracao_e_releitura(self):
        eventos = gerar_eventos_alteracao(
            {"Atleta": {"clube": "A"}},
            {"Atleta": {"clube": "B"}},
            origem="teste",
            versao_anterior="1",
            versao_nova="2",
            ator_email="admin@example.com",
            ator_nome="Admin",
            ator_id="oidc-admin-1",
        )
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0].ator_id, "oidc-admin-1")

        with TemporaryDirectory() as pasta:
            repositorio = JsonlAuditoriaRepository(
                Path(pasta) / "auditoria.jsonl"
            )
            repositorio.registrar(eventos)
            relidos = repositorio.listar()
            self.assertEqual(relidos[0].ator_email, "admin@example.com")
            self.assertEqual(relidos[0].ator_nome, "Admin")
            self.assertEqual(relidos[0].ator_id, "oidc-admin-1")


if __name__ == "__main__":
    unittest.main()
