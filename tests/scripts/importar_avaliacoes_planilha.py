#!/usr/bin/env python3
"""Importa a planilha trimestral para os JSONs canônicos da RC5.

O script usa somente a biblioteca padrão para não adicionar dependências ao
Streamlit. Registros existentes são append-only: uma alteração retroativa exige
a opção explícita ``--permitir-correcao-retroativa``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
REL_ID = f"{{{NS_REL}}}id"

CAMPOS_LEGADOS = (
    "nota_vini",
    "nota_roberto",
    "pontos_fortes",
    "pontos_fracos",
    "historico",
)

POSICOES_OFICIAIS = {
    "Goleiro",
    "Lateral-direito",
    "Lateral-esquerdo",
    "Zagueiro",
    "Volante",
    "Mezzala esquerdo",
    "Mezzala direito",
    "Meia-esquerda",
    "Meia-direita",
    "Meia-armador",
    "Ponta-esquerda",
    "Ponta-direita",
    "Segundo atacante",
    "Centroavante",
}


class ImportacaoError(RuntimeError):
    pass


def _normalizar_cabecalho(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.casefold()).strip()


def _indice_coluna(referencia: str) -> int:
    letras = re.match(r"[A-Z]+", referencia.upper())
    if letras is None:
        raise ImportacaoError(f"Referência de célula inválida: {referencia}")
    indice = 0
    for letra in letras.group(0):
        indice = indice * 26 + ord(letra) - 64
    return indice - 1


def _ler_shared_strings(arquivo: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in arquivo.namelist():
        return []
    raiz = ET.fromstring(arquivo.read("xl/sharedStrings.xml"))
    resultado: list[str] = []
    for si in raiz.findall(f"{{{NS_MAIN}}}si"):
        textos = [no.text or "" for no in si.iter(f"{{{NS_MAIN}}}t")]
        resultado.append("".join(textos))
    return resultado


def _mapear_planilhas(arquivo: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(arquivo.read("xl/workbook.xml"))
    rels = ET.fromstring(arquivo.read("xl/_rels/workbook.xml.rels"))
    destinos = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall(f"{{{NS_PACKAGE_REL}}}Relationship")
    }
    resultado: dict[str, str] = {}
    folhas = workbook.find(f"{{{NS_MAIN}}}sheets")
    if folhas is None:
        return resultado
    for folha in folhas:
        nome = folha.attrib["name"]
        destino = destinos[folha.attrib[REL_ID]].lstrip("/")
        if not destino.startswith("xl/"):
            destino = "xl/" + destino
        resultado[nome] = destino
    return resultado


def _valor_celula(
    celula: ET.Element,
    compartilhadas: list[str],
) -> Any:
    tipo = celula.attrib.get("t")
    valor = celula.find(f"{{{NS_MAIN}}}v")
    if tipo == "inlineStr":
        textos = [no.text or "" for no in celula.iter(f"{{{NS_MAIN}}}t")]
        return "".join(textos)
    if valor is None or valor.text is None:
        return None
    texto = valor.text
    if tipo == "s":
        return compartilhadas[int(texto)]
    if tipo == "str":
        return texto
    if tipo == "b":
        return texto == "1"
    try:
        numero = float(texto)
    except ValueError:
        return texto
    return int(numero) if numero.is_integer() else numero


def _ler_folha(caminho: Path, nome_folha: str) -> list[list[Any]]:
    with zipfile.ZipFile(caminho) as arquivo:
        compartilhadas = _ler_shared_strings(arquivo)
        folhas = _mapear_planilhas(arquivo)
        if nome_folha not in folhas:
            raise ImportacaoError(
                f"A planilha não contém a aba '{nome_folha}'."
            )
        raiz = ET.fromstring(arquivo.read(folhas[nome_folha]))
        dados = raiz.find(f"{{{NS_MAIN}}}sheetData")
        if dados is None:
            return []

        linhas: list[list[Any]] = []
        for linha_xml in dados.findall(f"{{{NS_MAIN}}}row"):
            valores: dict[int, Any] = {}
            maior = -1
            for celula in linha_xml.findall(f"{{{NS_MAIN}}}c"):
                referencia = celula.attrib.get("r", "")
                coluna = _indice_coluna(referencia)
                valores[coluna] = _valor_celula(celula, compartilhadas)
                maior = max(maior, coluna)
            linhas.append(
                [valores.get(indice) for indice in range(maior + 1)]
                if maior >= 0
                else []
            )
        return linhas


def _mapa_colunas(cabecalho: list[Any]) -> dict[str, int]:
    return {
        _normalizar_cabecalho(valor): indice
        for indice, valor in enumerate(cabecalho)
        if valor not in (None, "")
    }


def _obter(
    linha: list[Any],
    colunas: dict[str, int],
    *apelidos: str,
    obrigatorio: bool = False,
) -> Any:
    for apelido in apelidos:
        indice = colunas.get(_normalizar_cabecalho(apelido))
        if indice is not None:
            return linha[indice] if indice < len(linha) else None
    if obrigatorio:
        raise ImportacaoError(
            "Coluna obrigatória ausente: " + " / ".join(apelidos)
        )
    return None


def _nota(valor: Any, contexto: str) -> float | None:
    if valor in (None, ""):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError) as erro:
        raise ImportacaoError(f"{contexto}: nota inválida ({valor}).") from erro
    if numero < 0 or numero > 10:
        raise ImportacaoError(f"{contexto}: nota fora de 0 a 10.")
    if abs(numero * 2 - round(numero * 2)) > 1e-9:
        raise ImportacaoError(f"{contexto}: nota não usa passos de 0,5.")
    return numero


def _data_excel(valor: Any) -> str:
    if isinstance(valor, (int, float)):
        return (
            datetime(1899, 12, 30) + timedelta(days=float(valor))
        ).date().isoformat()
    texto = str(valor or "").strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            continue
    raise ImportacaoError(f"Data de referência inválida: {valor}")


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _extrair_avaliacoes(planilha: Path) -> list[dict[str, Any]]:
    linhas = _ler_folha(planilha, "Avaliações Trimestrais")
    if len(linhas) < 2:
        raise ImportacaoError("A aba de avaliações está vazia.")
    colunas = _mapa_colunas(linhas[0])
    resultado: list[dict[str, Any]] = []

    for numero_linha, linha in enumerate(linhas[1:], start=2):
        id_atleta = _texto(
            _obter(linha, colunas, "ID do atleta", obrigatorio=True)
        )
        nome = _texto(_obter(linha, colunas, "Atleta", obrigatorio=True))
        if not id_atleta and not nome:
            continue
        try:
            ano = int(_obter(linha, colunas, "Ano", obrigatorio=True))
        except (TypeError, ValueError) as erro:
            raise ImportacaoError(
                f"Linha {numero_linha}: ano inválido."
            ) from erro
        trimestre = _texto(
            _obter(linha, colunas, "Trimestre", obrigatorio=True)
        ).upper()
        if trimestre not in {"T1", "T2", "T3", "T4"}:
            raise ImportacaoError(
                f"Linha {numero_linha}: trimestre inválido."
            )
        if ano == 2026 and trimestre == "T1":
            raise ImportacaoError("T1 2026 não pode ser importado.")

        data_referencia = _data_excel(
            _obter(
                linha,
                colunas,
                "Data de referência",
                obrigatorio=True,
            )
        )
        posicao = _texto(
            _obter(linha, colunas, "Posição", obrigatorio=True)
        )
        if posicao not in POSICOES_OFICIAIS:
            raise ImportacaoError(
                f"Linha {numero_linha}: posição inválida ({posicao})."
            )
        clube = _texto(_obter(linha, colunas, "Clube", obrigatorio=True))

        contexto = f"Linha {numero_linha}/{nome}"
        registro = {
            "id_atleta": id_atleta,
            "nome": nome,
            "periodo": f"{ano}-{trimestre}",
            "ano": ano,
            "trimestre": trimestre,
            "data_referencia": data_referencia,
            "posicao_snapshot": posicao,
            "clube_snapshot": clube,
            "vini": {
                "capacidade_atual": _nota(
                    _obter(
                        linha,
                        colunas,
                        "Capacidade atual Vini",
                        "Capacidade atual — Vini",
                    ),
                    f"{contexto}/Vini/capacidade",
                ),
                "potencial_2030": _nota(
                    _obter(
                        linha,
                        colunas,
                        "Potencial 2030 Vini",
                        "Potencial 2030 — Vini",
                    ),
                    f"{contexto}/Vini/potencial",
                ),
                "observacao": _texto(
                    _obter(
                        linha,
                        colunas,
                        "Observações do Vini",
                        "Observacao do Vini",
                    )
                ),
            },
            "beto": {
                "capacidade_atual": _nota(
                    _obter(
                        linha,
                        colunas,
                        "Capacidade atual Beto",
                        "Capacidade atual — Beto",
                    ),
                    f"{contexto}/Beto/capacidade",
                ),
                "potencial_2030": _nota(
                    _obter(
                        linha,
                        colunas,
                        "Potencial 2030 Beto",
                        "Potencial 2030 — Beto",
                    ),
                    f"{contexto}/Beto/potencial",
                ),
                "observacao": _texto(
                    _obter(
                        linha,
                        colunas,
                        "Observações do Beto",
                        "Observacao do Beto",
                    )
                ),
            },
        }
        resultado.append(registro)

    chaves = [(item["id_atleta"], item["periodo"]) for item in resultado]
    if len(chaves) != len(set(chaves)):
        raise ImportacaoError("A planilha contém atleta/período duplicado.")
    return resultado


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _ler_json(caminho: Path) -> Any:
    try:
        return json.loads(caminho.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ImportacaoError(f"JSON inválido: {caminho}: {erro}") from erro


def _escrever_atomico(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps(
        dados,
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    atual = caminho.read_text(encoding="utf-8-sig") if caminho.exists() else None
    if atual == conteudo:
        return
    if caminho.exists():
        backup = caminho.with_suffix(caminho.suffix + ".bak")
        shutil.copy2(caminho, backup)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=caminho.parent,
        delete=False,
    ) as temporario:
        temporario.write(conteudo)
        temporario.flush()
        os.fsync(temporario.fileno())
        nome_temporario = Path(temporario.name)
    os.replace(nome_temporario, caminho)


def _atualizar_jogadores_e_arquivar(
    jogadores_path: Path,
    avaliacoes: list[dict[str, Any]],
    arquivo_legado: Path,
) -> dict[str, dict[str, Any]]:
    jogadores = _ler_json(jogadores_path)
    if not isinstance(jogadores, dict):
        raise ImportacaoError("O JSON de jogadores precisa ser um objeto.")

    ids_por_nome = {item["nome"]: item["id_atleta"] for item in avaliacoes}
    if set(jogadores) != set(ids_por_nome):
        faltam = sorted(set(jogadores) - set(ids_por_nome))
        sobram = sorted(set(ids_por_nome) - set(jogadores))
        raise ImportacaoError(
            f"Nomes incompatíveis. Sem avaliação: {faltam}; "
            f"sem cadastro: {sobram}."
        )

    if not arquivo_legado.exists():
        arquivo = {
            "schema_version": "1.0",
            "projeto": "O Caminho para o Hexa 2030",
            "motivo": (
                "Arquivamento preventivo antes da desativação pública "
                "das avaliações editoriais legadas na RC5."
            ),
            "criado_em_utc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "fonte": {
                "arquivo": jogadores_path.name,
                "sha256": _sha256(jogadores_path),
                "total_atletas": len(jogadores),
            },
            "campos_arquivados": list(CAMPOS_LEGADOS),
            "observacao": (
                "Os campos permanecem no JSON cadastral durante a transição, "
                "mas a interface RC5 não os lê nem os exibe."
            ),
            "avaliacoes_legadas": {
                nome: {
                    "id_atleta": ids_por_nome[nome],
                    **{
                        campo: registro.get(campo)
                        for campo in CAMPOS_LEGADOS
                    },
                }
                for nome, registro in sorted(
                    jogadores.items(),
                    key=lambda item: item[0].casefold(),
                )
            },
        }
        _escrever_atomico(arquivo_legado, arquivo)

    ids_existentes: set[str] = set()
    for nome, registro in jogadores.items():
        id_novo = ids_por_nome[nome]
        id_atual = str(registro.get("id_atleta") or "")
        if id_atual and id_atual != id_novo:
            raise ImportacaoError(
                f"{nome}: ID existente {id_atual} diverge de {id_novo}."
            )
        if id_novo in ids_existentes:
            raise ImportacaoError(f"ID duplicado: {id_novo}.")
        registro["id_atleta"] = id_novo
        ids_existentes.add(id_novo)

    _escrever_atomico(jogadores_path, jogadores)
    return jogadores


def _mesclar_avaliacoes(
    saida: Path,
    novos: list[dict[str, Any]],
    fonte: dict[str, Any],
    permitir_correcao: bool,
) -> dict[str, Any]:
    existentes: list[dict[str, Any]] = []
    historico_fontes: list[dict[str, Any]] = []
    if saida.exists():
        documento = _ler_json(saida)
        existentes = list(documento.get("avaliacoes", []))
        historico_fontes = list(documento.get("historico_importacoes", []))

    indice = {
        (item["id_atleta"], item["periodo"]): item
        for item in existentes
    }
    for item in novos:
        chave = (item["id_atleta"], item["periodo"])
        anterior = indice.get(chave)
        if anterior is None:
            indice[chave] = item
        elif anterior != item:
            if not permitir_correcao:
                raise ImportacaoError(
                    "Correção retroativa detectada em "
                    f"{chave[0]}/{chave[1]}. Revise a diferença ou use "
                    "--permitir-correcao-retroativa conscientemente."
                )
            indice[chave] = item

    historico_fontes.append(fonte)
    documento_saida = {
        "schema_version": "1.0",
        "projeto": "O Caminho para o Hexa 2030",
        "fonte": fonte,
        "historico_importacoes": historico_fontes,
        "avaliacoes": sorted(
            indice.values(),
            key=lambda item: (
                item["data_referencia"],
                item["nome"].casefold(),
            ),
        ),
    }
    _escrever_atomico(saida, documento_saida)
    return documento_saida


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("planilha", type=Path)
    parser.add_argument(
        "--jogadores",
        type=Path,
        default=Path("jogadores_hexa_2030.json"),
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("avaliacoes_trimestrais_hexa_2030.json"),
    )
    parser.add_argument(
        "--arquivo-legado",
        type=Path,
        default=Path(
            "arquivo/avaliacoes_editoriais_legado_pre_t2_2026.json"
        ),
    )
    parser.add_argument(
        "--permitir-correcao-retroativa",
        action="store_true",
    )
    argumentos = parser.parse_args()

    planilha = argumentos.planilha.resolve()
    if not planilha.exists():
        raise ImportacaoError(f"Planilha não encontrada: {planilha}")

    avaliacoes = _extrair_avaliacoes(planilha)
    _atualizar_jogadores_e_arquivar(
        argumentos.jogadores,
        avaliacoes,
        argumentos.arquivo_legado,
    )

    fonte = {
        "arquivo": planilha.name,
        "sha256": _sha256(planilha),
        "aba": "Avaliações Trimestrais",
        "importado_em_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "politica": (
            "Somente dados brutos; indicadores são recalculados "
            "pelo aplicativo."
        ),
    }
    documento = _mesclar_avaliacoes(
        argumentos.saida,
        avaliacoes,
        fonte,
        argumentos.permitir_correcao_retroativa,
    )
    print(
        f"Importação concluída: {len(avaliacoes)} registro(s) lido(s); "
        f"{len(documento['avaliacoes'])} registro(s) na base temporal."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
