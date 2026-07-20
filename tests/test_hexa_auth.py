from __future__ import annotations

import unittest

from hexa_auth import (
    AuthConfigError,
    IdentidadeUsuario,
    email_normalizado,
    identidade_atual,
    lista_administradores,
    usuario_eh_admin,
)


class ProvedorFake:
    def __init__(self, autenticado=False, claims=None):
        self.autenticado = autenticado
        self._claims = claims or {}
        self.login_chamado = False
        self.logout_chamado = False

    def esta_autenticado(self):
        return self.autenticado

    def claims(self):
        return self._claims

    def login(self):
        self.login_chamado = True

    def logout(self):
        self.logout_chamado = True


class TestAuth(unittest.TestCase):
    def test_email_normalizado(self):
        self.assertEqual(
            email_normalizado("  ADMIN@EXEMPLO.COM "),
            "admin@exemplo.com",
        )

    def test_identidade_anonima(self):
        identidade = identidade_atual(ProvedorFake())
        self.assertFalse(identidade.autenticado)
        self.assertEqual(identidade.email, "")

    def test_identidade_autenticada(self):
        identidade = identidade_atual(
            ProvedorFake(
                True,
                {
                    "email": "ADMIN@EXEMPLO.COM",
                    "name": "Vini",
                    "sub": "123",
                },
            )
        )
        self.assertEqual(
            identidade,
            IdentidadeUsuario(
                autenticado=True,
                email="admin@exemplo.com",
                nome="Vini",
                subject="123",
            ),
        )
        self.assertIn("admin@exemplo.com", identidade.origem_auditoria)

    def test_allowlist_remove_duplicados(self):
        secrets = {
            "administradores": {
                "emails": [
                    "Admin@Exemplo.com",
                    "admin@exemplo.com",
                    "outro@exemplo.com",
                ]
            }
        }
        self.assertEqual(
            lista_administradores(secrets),
            ("admin@exemplo.com", "outro@exemplo.com"),
        )

    def test_allowlist_invalida(self):
        with self.assertRaises(AuthConfigError):
            lista_administradores({})

    def test_admin_autorizado(self):
        provedor = ProvedorFake(
            True,
            {"email": "admin@exemplo.com"},
        )
        secrets = {
            "administradores": {
                "emails": ["ADMIN@EXEMPLO.COM"]
            }
        }
        self.assertTrue(
            usuario_eh_admin(provedor, secrets=secrets)
        )

    def test_usuario_autenticado_nao_autorizado(self):
        provedor = ProvedorFake(
            True,
            {"email": "visitante@exemplo.com"},
        )
        secrets = {
            "administradores": {
                "emails": ["admin@exemplo.com"]
            }
        }
        self.assertFalse(
            usuario_eh_admin(provedor, secrets=secrets)
        )


if __name__ == "__main__":
    unittest.main()
