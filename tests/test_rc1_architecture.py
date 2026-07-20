from __future__ import annotations

import ast
import importlib
import importlib.util
import subprocess
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_FILES = {
    path.stem: path
    for path in ROOT.glob("hexa_*.py")
}

def top_level_symbols(tree: ast.Module) -> set[str]:
    symbols: set[str] = set()
    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(item.name)
        elif isinstance(item, ast.Assign):
            symbols.update(
                target.id for target in item.targets if isinstance(target, ast.Name)
            )
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            symbols.add(item.target.id)
        elif isinstance(item, ast.ImportFrom):
            symbols.update(
                alias.asname or alias.name for alias in item.names if alias.name != "*"
            )
    return symbols

def declared_all(tree: ast.Module) -> list[str] | None:
    for item in tree.body:
        target = None
        value = None
        if isinstance(item, ast.Assign):
            if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                target = item.targets[0].id
                value = item.value
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            target = item.target.id
            value = item.value
        if target == "__all__" and isinstance(value, (ast.List, ast.Tuple)):
            result: list[str] = []
            for element in value.elts:
                if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                    raise AssertionError("__all__ deve conter apenas strings literais")
                result.append(element.value)
            return result
    return None

class TestPublicContracts(unittest.TestCase):
    def test_import_critico_exato_do_entrypoint(self) -> None:
        from hexa_data import (
            DataIntegrityError,
            carregar_jogadores,
            validar_integridade_jogadores,
            validar_posicoes,
        )

        self.assertTrue(issubclass(DataIntegrityError, Exception))
        self.assertTrue(callable(carregar_jogadores))
        self.assertTrue(callable(validar_integridade_jogadores))
        self.assertTrue(callable(validar_posicoes))

    def test_todos_os_imports_locais_apontam_para_simbolos_existentes(self) -> None:
        module_symbols = {
            name: top_level_symbols(
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            )
            for name, path in MODULE_FILES.items()
        }
        for importer, path in MODULE_FILES.items():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                base = node.module.split(".")[0]
                if base not in MODULE_FILES:
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    self.assertIn(
                        alias.name,
                        module_symbols[base],
                        f"{importer} importa {alias.name} inexistente de {base}",
                    )

    def test_modulos_publicos_declaram_all_valido(self) -> None:
        for name, path in MODULE_FILES.items():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            exported = declared_all(tree)
            self.assertIsInstance(exported, list, f"{name} não declara __all__")
            assert exported is not None
            self.assertEqual(len(exported), len(set(exported)), f"{name}: __all__ duplicado")
            symbols = top_level_symbols(tree)
            for symbol in exported:
                self.assertIn(
                    symbol,
                    symbols,
                    f"{name} declara {symbol} em __all__, mas não o define/importa",
                )

    def test_all_em_runtime_nos_modulos_puros(self) -> None:
        visual_modules = {"hexa_admin", "hexa_components", "hexa_pages", "hexa_styles"}
        for name in MODULE_FILES:
            if name in visual_modules:
                continue
            module = importlib.import_module(name)
            for symbol in module.__all__:
                self.assertTrue(hasattr(module, symbol), f"{name}.{symbol} ausente")

    @unittest.skipUnless(
        importlib.util.find_spec("streamlit") is not None,
        "Streamlit não está instalado neste ambiente",
    )
    def test_imports_visuais_quando_streamlit_esta_disponivel(self) -> None:
        from hexa_components import render_campo
        from hexa_pages import render_feedback_sidebar, render_tela
        from hexa_styles import aplicar_estilos

        self.assertTrue(callable(render_campo))
        self.assertTrue(callable(render_feedback_sidebar))
        self.assertTrue(callable(render_tela))
        self.assertTrue(callable(aplicar_estilos))

class TestArchitecture(unittest.TestCase):
    def test_grafo_de_imports_locais_nao_tem_ciclos(self) -> None:
        graph: dict[str, set[str]] = defaultdict(set)
        for name in MODULE_FILES:
            graph[name]
        for name, path in MODULE_FILES.items():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    base = node.module.split(".")[0]
                    if base in MODULE_FILES:
                        graph[name].add(base)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        base = alias.name.split(".")[0]
                        if base in MODULE_FILES:
                            graph[name].add(base)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str, trail: tuple[str, ...]) -> None:
            if node in visiting:
                self.fail("Ciclo de import detectado: " + " -> ".join((*trail, node)))
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph[node]:
                visit(dependency, (*trail, node))
            visiting.remove(node)
            visited.add(node)

        for node in list(graph):
            visit(node, ())

    def test_smoke_script_em_processo_novo(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/rc1_smoke.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RC1 smoke test: OK", result.stdout)

    def test_gramatica_compativel_com_python_310(self) -> None:
        paths = [
            *ROOT.glob("*.py"),
            *ROOT.glob("scripts/*.py"),
            *ROOT.glob("tests/*.py"),
        ]
        for path in paths:
            ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
                feature_version=(3, 10),
            )

if __name__ == "__main__":
    unittest.main()
