"""Componentes visuais reutilizáveis do aplicativo."""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import streamlit as st

from hexa_avaliacoes import (
    calcular_metricas_avaliacao,
    formatar_numero,
    formatar_status_avaliacao,
)
from hexa_config import ANO_BASE_DADOS, ANO_COPA
from hexa_data import (
    extrair_altura_metros,
    formatar_valor_milhoes,
    percentual_do_pico,
    valor_mercado_atual,
    valor_mercado_maximo,
)
from hexa_taticas import (
    ABREVIACOES,
    LIMITE_CONVOCADOS,
    LIMITE_RESERVAS,
    LIMITE_TITULARES,
    SlotTatico,
    indice_adaptabilidade,
)

__all__ = [
    "ColunaTabelaExecutiva",
    "KPI",
    "calcular_resumo_elenco",
    "render_avaliacao_leitura",
    "render_banco_reservas",
    "render_cabecalho",
    "render_cabecalho_secao",
    "render_campo",
    "render_cartao_perfil",
    "render_comparativo_mercado",
    "render_dados_transfermarkt",
    "render_dossie",
    "render_grade_dados",
    "render_kpis",
    "render_legenda_adaptabilidade",
    "render_quadro_avaliacao_executivo",
    "render_lista_tatica",
    "render_resumo_elenco",
    "render_tabela_executiva",
]


def _esc(valor: Any, padrao: str = "Não informado") -> str:
    texto = padrao if valor in (None, "", []) else str(valor)
    return html.escape(texto)


TomKPI = Literal["neutro", "destaque", "positivo", "informativo"]


@dataclass(frozen=True, slots=True)
class KPI:
    """Indicador compacto, semântico e reutilizável."""

    rotulo: str
    valor: Any
    contexto: str | None = None
    tom: TomKPI = "neutro"


FormatoTabelaExecutiva = Literal[
    "texto",
    "decimal_1",
    "decimal_2",
    "sinal_2",
    "inteiro",
    "percentual_1",
    "moeda_milhoes",
    "data",
]
AlinhamentoTabelaExecutiva = Literal["esquerda", "centro", "direita"]
FiltroTabelaExecutiva = Literal["texto", "numero", "data"]
FixacaoTabelaExecutiva = Literal["left", "right"]


@dataclass(frozen=True, slots=True)
class ColunaTabelaExecutiva:
    """Contrato visual e funcional de uma coluna da grade executiva."""

    chave: str
    rotulo: str
    formato: FormatoTabelaExecutiva = "texto"
    alinhamento: AlinhamentoTabelaExecutiva = "esquerda"
    destaque: bool = False
    progresso: bool = False
    largura: str | int | None = None
    filtro: FiltroTabelaExecutiva | None = None
    ordenavel: bool = True
    fixada: FixacaoTabelaExecutiva | None = None
    min_largura: int | None = None


_FORMATOS_NUMERICOS: frozenset[str] = frozenset(
    {
        "decimal_1",
        "decimal_2",
        "sinal_2",
        "inteiro",
        "percentual_1",
        "moeda_milhoes",
    }
)


def _numero_tabela(valor: Any) -> float | None:
    if valor in (None, "") or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _formatar_data_tabela(valor: Any) -> str:
    """Normaliza datas conhecidas sem transformar texto inválido em informação."""
    if valor in (None, ""):
        return "—"
    texto = str(valor).strip()
    if not texto:
        return "—"

    partes = texto[:10].replace(".", "/").split("/")
    if len(partes) == 3 and all(parte.isdigit() for parte in partes):
        dia, mes, ano = partes
        if len(ano) == 4:
            return f"{dia.zfill(2)}/{mes.zfill(2)}/{ano}"

    partes_iso = texto[:10].split("-")
    if len(partes_iso) == 3 and all(parte.isdigit() for parte in partes_iso):
        ano, mes, dia = partes_iso
        if len(ano) == 4:
            return f"{dia.zfill(2)}/{mes.zfill(2)}/{ano}"
    return texto


def _data_iso_grade(valor: Any) -> str | None:
    """Converte datas DD/MM/AAAA ou ISO em ISO para ordenação e filtro."""
    if valor in (None, ""):
        return None
    texto = str(valor).strip()
    if not texto:
        return None

    partes = texto[:10].replace(".", "/").split("/")
    if len(partes) == 3 and all(parte.isdigit() for parte in partes):
        dia, mes, ano = partes
        if len(ano) == 4:
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"

    partes_iso = texto[:10].split("-")
    if len(partes_iso) == 3 and all(parte.isdigit() for parte in partes_iso):
        ano, mes, dia = partes_iso
        if len(ano) == 4:
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
    return None


def _formatar_valor_tabela(
    valor: Any,
    formato: FormatoTabelaExecutiva,
) -> str:
    if valor in (None, ""):
        return "—"
    if formato == "texto":
        return str(valor)
    if formato == "data":
        return _formatar_data_tabela(valor)

    numero = _numero_tabela(valor)
    if numero is None:
        return "—"
    if formato == "decimal_1":
        return f"{numero:.1f}".replace(".", ",")
    if formato == "decimal_2":
        return f"{numero:.2f}".replace(".", ",")
    if formato == "sinal_2":
        return f"{numero:+.2f}".replace(".", ",")
    if formato == "inteiro":
        return str(int(round(numero)))
    if formato == "percentual_1":
        return f"{numero:.1f}%".replace(".", ",")
    if formato == "moeda_milhoes":
        return formatar_valor_milhoes(numero)
    return str(valor)


def _conteudo_celula_tabela(
    valor: Any,
    coluna: ColunaTabelaExecutiva,
) -> tuple[str, str, float | None]:
    subtexto: str | None = None
    valor_principal = valor

    if (
        isinstance(valor, Sequence)
        and not isinstance(valor, (str, bytes, bytearray))
        and len(valor) == 2
    ):
        valor_principal, subtexto = valor[0], str(valor[1] or "")

    texto = _formatar_valor_tabela(valor_principal, coluna.formato)
    classes_tom: list[str] = []
    numero = _numero_tabela(valor_principal)
    if coluna.formato == "sinal_2" and numero is not None:
        if numero > 0:
            classes_tom.append("executive-table-value--positive")
        elif numero < 0:
            classes_tom.append("executive-table-value--negative")

    subtexto_html = (
        f'<span class="executive-table-caption">{_esc(subtexto, "")}</span>'
        if subtexto
        else ""
    )
    valor_html = (
        f'<span class="executive-table-value {" ".join(classes_tom)}">'
        f'{_esc(texto, "—")}</span>{subtexto_html}'
    )
    progresso = (
        min(max(numero, 0.0), 100.0)
        if coluna.progresso and numero is not None
        else None
    )
    return valor_html, texto, progresso


def _render_tabela_executiva_html(
    registros: Sequence[Mapping[str, Any]],
    colunas: Sequence[ColunaTabelaExecutiva],
    *,
    rotulo_aria: str,
    legenda: str | None = None,
) -> None:
    """Fallback semântico para quadros pequenos ou dependência indisponível."""
    if not registros or not colunas:
        return

    classes_card = ["executive-table-card"]
    if len(colunas) > 5:
        classes_card.append("executive-table-card--wide")
    if len(registros) > 12:
        classes_card.append("executive-table-card--tall")

    colgroup = "".join(
        (
            f'<col style="width:{_esc(coluna.largura, "")}">'
            if coluna.largura
            else "<col>"
        )
        for coluna in colunas
    )
    cabecalho = "".join(
        (
            '<th scope="col" '
            f'class="executive-table-align--{coluna.alinhamento}'
            f'{" executive-table-column--accent" if coluna.destaque else ""}">'
            f'{_esc(coluna.rotulo)}</th>'
        )
        for coluna in colunas
    )

    linhas_html: list[str] = []
    for registro in registros:
        celulas: list[str] = []
        for indice, coluna in enumerate(colunas):
            valor_html, _, progresso = _conteudo_celula_tabela(
                registro.get(coluna.chave),
                coluna,
            )
            classes = [
                f"executive-table-align--{coluna.alinhamento}",
            ]
            if coluna.destaque:
                classes.append("executive-table-column--accent")
            if progresso is not None:
                classes.append("executive-table-cell--progress")

            conteudo = valor_html
            if progresso is not None:
                conteudo += (
                    '<span class="executive-table-progress" aria-hidden="true">'
                    f'<span style="width:{progresso:.1f}%"></span>'
                    "</span>"
                )

            tag = "th" if indice == 0 else "td"
            escopo = ' scope="row"' if indice == 0 else ""
            celulas.append(
                f'<{tag}{escopo} class="{" ".join(classes)}">'
                f"{conteudo}</{tag}>"
            )
        linhas_html.append(f'<tr>{"".join(celulas)}</tr>')

    legenda_html = (
        f'<caption class="sr-only">{_esc(legenda)}</caption>'
        if legenda
        else ""
    )
    st.markdown(
        f'<section class="{" ".join(classes_card)}" '
        f'aria-label="{_esc(rotulo_aria)}">'
        '<div class="executive-table-scroll" tabindex="0">'
        '<table class="executive-table">'
        f"{legenda_html}"
        f"<colgroup>{colgroup}</colgroup>"
        f"<thead><tr>{cabecalho}</tr></thead>"
        f'<tbody>{"".join(linhas_html)}</tbody>'
        "</table></div></section>",
        unsafe_allow_html=True,
    )


def _valor_grade(valor: Any, coluna: ColunaTabelaExecutiva) -> Any:
    """Mantém tipos de ordenação separados da apresentação visual."""
    if (
        isinstance(valor, Sequence)
        and not isinstance(valor, (str, bytes, bytearray))
        and len(valor) == 2
    ):
        principal, subtexto = valor[0], str(valor[1] or "").strip()
        texto_principal = _formatar_valor_tabela(principal, coluna.formato)
        return (
            f"{texto_principal} — {subtexto}"
            if subtexto
            else texto_principal
        )

    if coluna.formato in _FORMATOS_NUMERICOS:
        return _numero_tabela(valor)
    if coluna.formato == "data":
        return _data_iso_grade(valor)
    if valor in (None, "", []):
        return None
    return str(valor)


def _registros_dataframe(
    registros: Sequence[Mapping[str, Any]],
    colunas: Sequence[ColunaTabelaExecutiva],
):
    """Cria DataFrame tipado somente com as colunas declaradas."""
    import pandas as pd

    linhas = [
        {
            coluna.chave: _valor_grade(registro.get(coluna.chave), coluna)
            for coluna in colunas
        }
        for registro in registros
    ]
    dataframe = pd.DataFrame(
        linhas,
        columns=[coluna.chave for coluna in colunas],
    )
    for coluna in colunas:
        if coluna.formato in _FORMATOS_NUMERICOS:
            dataframe[coluna.chave] = pd.to_numeric(
                dataframe[coluna.chave],
                errors="coerce",
            )
    return dataframe


def _largura_grade(
    coluna: ColunaTabelaExecutiva,
) -> tuple[int | None, int, int]:
    """Traduz largura declarativa em largura fixa, mínima e proporção flex."""
    minimo_padrao = (
        170
        if coluna.formato == "texto"
        else 132
        if coluna.formato in {"moeda_milhoes", "percentual_1", "data"}
        else 112
    )
    minimo = coluna.min_largura or minimo_padrao
    flex = 1

    if isinstance(coluna.largura, int):
        return coluna.largura, min(minimo, coluna.largura), flex

    if isinstance(coluna.largura, str):
        texto = coluna.largura.strip()
        if texto.endswith("px"):
            try:
                largura = int(float(texto[:-2]))
                return largura, min(minimo, largura), flex
            except ValueError:
                pass
        if texto.endswith("%"):
            try:
                percentual = float(texto[:-1])
                flex = max(1, min(6, round(percentual / 10)))
            except ValueError:
                pass
    return None, minimo, flex


def _filtro_grade(coluna: ColunaTabelaExecutiva) -> str:
    filtro = coluna.filtro
    if filtro is None:
        if coluna.formato in _FORMATOS_NUMERICOS:
            filtro = "numero"
        elif coluna.formato == "data":
            filtro = "data"
        else:
            filtro = "texto"

    return {
        "numero": "agNumberColumnFilter",
        "data": "agDateColumnFilter",
        "texto": "agTextColumnFilter",
    }[filtro]


def _formatador_javascript(formato: FormatoTabelaExecutiva, JsCode):
    vazio = (
        "if (params.value === null || params.value === undefined || "
        "params.value === '') return '—';"
    )
    if formato == "texto":
        return None
    if formato == "data":
        return JsCode(
            f"""
            function(params) {{
                {vazio}
                const texto = String(params.value).slice(0, 10);
                const partes = texto.split('-');
                if (partes.length !== 3) return texto;
                return `${{partes[2]}}/${{partes[1]}}/${{partes[0]}}`;
            }}
            """
        )

    casas = 1 if formato in {"decimal_1", "percentual_1"} else 2
    if formato == "inteiro":
        casas = 0
    prefixo = "'€ ' +" if formato == "moeda_milhoes" else ""
    sufixo = " + ' mi'" if formato == "moeda_milhoes" else ""
    if formato == "percentual_1":
        sufixo = " + '%'"
    sinal = (
        "const sinal = numero > 0 ? '+' : '';"
        if formato == "sinal_2"
        else "const sinal = '';"
    )
    return JsCode(
        f"""
        function(params) {{
            {vazio}
            const numero = Number(params.value);
            if (!Number.isFinite(numero)) return '—';
            {sinal}
            const formatado = new Intl.NumberFormat('pt-BR', {{
                minimumFractionDigits: {casas},
                maximumFractionDigits: {casas}
            }}).format(numero);
            return {prefixo}sinal + formatado{sufixo};
        }}
        """
    )


def _comparador_data_javascript(JsCode):
    return JsCode(
        """
        function(filterLocalDateAtMidnight, cellValue) {
            if (!cellValue) return -1;
            const partes = String(cellValue).slice(0, 10).split('-');
            if (partes.length !== 3) return -1;
            const dataCelula = new Date(
                Number(partes[0]),
                Number(partes[1]) - 1,
                Number(partes[2])
            );
            if (dataCelula < filterLocalDateAtMidnight) return -1;
            if (dataCelula > filterLocalDateAtMidnight) return 1;
            return 0;
        }
        """
    )


def _estilo_progresso_javascript(JsCode):
    return JsCode(
        """
        function(params) {
            const numero = Number(params.value);
            if (!Number.isFinite(numero)) return null;
            const percentual = Math.max(0, Math.min(100, numero));
            return {
                backgroundImage:
                    'linear-gradient(90deg, #F97316, #EAB308, #22C55E)',
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'left bottom',
                backgroundSize: `${percentual}% 4px`
            };
        }
        """
    )


def _css_grade(*, alto_contraste: bool) -> dict[str, dict[str, str]]:
    borda = "#F8FAFC" if alto_contraste else "rgba(148, 163, 184, .28)"
    foco = "#FFFFFF" if alto_contraste else "#60A5FA"
    return {
        ".ag-root-wrapper": {
            "border": f"1px solid {borda}",
            "border-radius": "14px",
            "overflow": "hidden",
            "background-color": "#0F172A",
        },
        ".ag-header": {
            "background-color": "#0F172A",
            "border-bottom": f"1px solid {borda}",
        },
        ".ag-header-cell": {
            "color": "#93C5FD",
            "font-size": "12px",
            "font-weight": "700",
            "letter-spacing": ".045em",
            "text-transform": "uppercase",
            "border-right": f"1px solid {borda}",
        },
        ".ag-header-cell-label": {
            "gap": "4px",
        },
        ".ag-cell": {
            "display": "flex",
            "align-items": "center",
            "color": "#F8FAFC",
            "font-size": "14px",
            "font-weight": "600",
            "border-right": f"1px solid {borda}",
            "font-variant-numeric": "tabular-nums",
        },
        ".ag-row": {
            "border-bottom": f"1px solid {borda}",
        },
        ".ag-row-even": {
            "background-color": "#0B1324",
        },
        ".ag-row-odd": {
            "background-color": "#111C31",
        },
        ".ag-row-hover": {
            "background-color": "#1E293B !important",
        },
        ".ag-cell-focus": {
            "outline": f"2px solid {foco} !important",
            "outline-offset": "-2px",
        },
        ".ag-pinned-left-cols-container": {
            "box-shadow": "2px 0 0 rgba(148, 163, 184, .28)",
        },
        ".hexa-grid-header-accent": {
            "background-color": "rgba(58, 53, 35, .98) !important",
            "color": "#FDE68A !important",
        },
        ".hexa-grid-accent": {
            "background-color": "rgba(234, 179, 8, .10)",
            "color": "#FACC15",
            "font-weight": "700",
        },
        ".hexa-grid-positive": {
            "color": "#22C55E !important",
            "font-weight": "700",
        },
        ".hexa-grid-negative": {
            "color": "#FCA5A5 !important",
            "font-weight": "700",
        },
        ".hexa-grid-align-center": {
            "justify-content": "center",
            "text-align": "center",
        },
        ".hexa-grid-align-right": {
            "justify-content": "flex-end",
            "text-align": "right",
        },
        ".ag-overlay-no-rows-center": {
            "color": "#CBD5E1",
        },
        ".ag-input-field-input": {
            "min-height": "32px",
            "color": "#F8FAFC",
            "background-color": "#0F172A",
        },
        ".ag-menu": {
            "color": "#F8FAFC",
            "background-color": "#111827",
            "border": f"1px solid {borda}",
        },
        ".ag-tool-panel-wrapper": {
            "color": "#F8FAFC",
            "background-color": "#111827",
        },
    }


def _altura_grade(
    total_linhas: int,
    *,
    linha: int,
    cabecalho: int,
    mostrar_barra: bool,
    altura_maxima: int,
) -> int:
    barra = 48 if mostrar_barra else 0
    calculada = cabecalho + barra + max(total_linhas, 1) * linha + 4
    return max(132, min(calculada, altura_maxima))


def render_grade_dados(
    registros: Sequence[Mapping[str, Any]],
    colunas: Sequence[ColunaTabelaExecutiva],
    *,
    rotulo_aria: str,
    chave: str,
    mostrar_barra: bool = True,
    altura_maxima: int = 560,
) -> bool:
    """Renderiza AG Grid Community em modo somente leitura.

    Retorna ``True`` quando a grade interativa foi carregada. Em ambientes
    sem a dependência opcional, retorna ``False`` para permitir fallback HTML.
    """
    if not registros or not colunas:
        return True

    try:
        from st_aggrid import AgGrid, DataReturnMode, JsCode
    except ModuleNotFoundError:
        return False

    densidade = str(
        st.session_state.get("densidade_tabelas", "Compacta")
    ).casefold()
    confortavel = densidade == "confortável"
    altura_linha = 50 if confortavel else 42
    altura_cabecalho = 50 if confortavel else 44

    dataframe = _registros_dataframe(registros, colunas)
    definicoes_colunas: list[dict[str, Any]] = []

    for coluna in colunas:
        largura, min_largura, flex = _largura_grade(coluna)
        classes = [f"hexa-grid-align-{coluna.alinhamento}"]
        if coluna.destaque:
            classes.append("hexa-grid-accent")

        definicao: dict[str, Any] = {
            "field": coluna.chave,
            "headerName": coluna.rotulo,
            "headerTooltip": (
                "Clique para ordenar. Use o menu da coluna para filtrar."
            ),
            "sortable": coluna.ordenavel,
            "filter": _filtro_grade(coluna),
            "resizable": True,
            "editable": False,
            "minWidth": min_largura,
            "cellClass": classes,
            "wrapHeaderText": True,
            "autoHeaderHeight": False,
        }
        if largura is not None:
            definicao["width"] = largura
        else:
            definicao["flex"] = flex
        if coluna.fixada:
            definicao["pinned"] = coluna.fixada
            definicao["lockPinned"] = False
        if coluna.destaque:
            definicao["headerClass"] = "hexa-grid-header-accent"

        formatador = _formatador_javascript(coluna.formato, JsCode)
        if formatador is not None:
            definicao["valueFormatter"] = formatador

        filtro_params: dict[str, Any] = {
            "buttons": ["reset", "apply"],
            "closeOnApply": True,
            "debounceMs": 250,
            "maxNumConditions": 2,
        }
        if coluna.formato == "texto":
            filtro_params["trimInput"] = True
        if coluna.formato == "data":
            definicao["cellDataType"] = "dateString"
            filtro_params["comparator"] = _comparador_data_javascript(JsCode)
        definicao["filterParams"] = filtro_params

        if coluna.formato == "sinal_2":
            definicao["cellClassRules"] = {
                "hexa-grid-positive": "Number(x) > 0",
                "hexa-grid-negative": "Number(x) < 0",
            }
        if coluna.progresso:
            definicao["cellStyle"] = _estilo_progresso_javascript(JsCode)

        definicoes_colunas.append(definicao)

    opcoes_grade = {
        "columnDefs": definicoes_colunas,
        "defaultColDef": {
            "sortable": True,
            "filter": True,
            "resizable": True,
            "editable": False,
            "suppressMovable": False,
            "menuTabs": ["filterMenuTab", "generalMenuTab", "columnsMenuTab"],
        },
        "rowHeight": altura_linha,
        "headerHeight": altura_cabecalho,
        "multiSortKey": "shift",
        "animateRows": False,
        "enableCellTextSelection": True,
        "ensureDomOrder": True,
        "suppressRowClickSelection": True,
        "suppressCellFocus": False,
        "suppressSetFilterByDefault": True,
        "overlayNoRowsTemplate": (
            '<span class="ag-overlay-no-rows-center">'
            "Nenhum registro corresponde aos filtros.</span>"
        ),
        "localeText": {
            "filterOoo": "Filtrar...",
            "equals": "Igual a",
            "notEqual": "Diferente de",
            "contains": "Contém",
            "notContains": "Não contém",
            "startsWith": "Começa com",
            "endsWith": "Termina com",
            "lessThan": "Menor que",
            "lessThanOrEqual": "Menor ou igual a",
            "greaterThan": "Maior que",
            "greaterThanOrEqual": "Maior ou igual a",
            "inRange": "Entre",
            "blank": "Em branco",
            "notBlank": "Não está em branco",
            "andCondition": "E",
            "orCondition": "OU",
            "applyFilter": "Aplicar",
            "resetFilter": "Redefinir",
            "clearFilter": "Limpar",
            "cancelFilter": "Cancelar",
            "noRowsToShow": "Nenhum registro para exibir",
            "loadingOoo": "Carregando...",
            "searchOoo": "Pesquisar...",
            "pinColumn": "Fixar coluna",
            "pinLeft": "Fixar à esquerda",
            "pinRight": "Fixar à direita",
            "noPin": "Não fixar",
            "autosizeThisColumn": "Ajustar esta coluna",
            "autosizeAllColumns": "Ajustar todas as colunas",
            "resetColumns": "Redefinir colunas",
            "columns": "Colunas",
            "filters": "Filtros",
        },
    }

    altura = _altura_grade(
        len(dataframe),
        linha=altura_linha,
        cabecalho=altura_cabecalho,
        mostrar_barra=mostrar_barra,
        altura_maxima=altura_maxima,
    )
    alto_contraste = bool(
        st.session_state.get("modo_alto_contraste", False)
    )
    st.markdown(
        f'<span class="sr-only">{_esc(rotulo_aria)}</span>',
        unsafe_allow_html=True,
    )
    AgGrid(
        dataframe,
        gridOptions=opcoes_grade,
        height=altura,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False,
        theme="streamlit",
        custom_css=_css_grade(alto_contraste=alto_contraste),
        key=chave,
        update_on=[],
        show_toolbar=mostrar_barra,
        show_search=mostrar_barra,
        show_download_button=mostrar_barra,
        server_sync_strategy="client_wins",
        use_json_serialization="auto",
    )
    return True


def render_tabela_executiva(
    registros: Sequence[Mapping[str, Any]],
    colunas: Sequence[ColunaTabelaExecutiva],
    *,
    rotulo_aria: str,
    legenda: str | None = None,
    chave: str | None = None,
    interativa: bool = True,
    mostrar_barra: bool = True,
    altura_maxima: int = 560,
) -> None:
    """Renderiza grade interativa ou tabela HTML compacta como fallback."""
    if not registros or not colunas:
        return

    if interativa and chave:
        carregada = render_grade_dados(
            registros,
            colunas,
            rotulo_aria=rotulo_aria,
            chave=chave,
            mostrar_barra=mostrar_barra,
            altura_maxima=altura_maxima,
        )
        if carregada:
            return
        chave_aviso = "_aviso_dependencia_grade"
        if not st.session_state.get(chave_aviso, False):
            st.warning(
                "A grade interativa não foi carregada. Exibindo a tabela "
                "compacta de compatibilidade."
            )
            st.session_state[chave_aviso] = True

    _render_tabela_executiva_html(
        registros,
        colunas,
        rotulo_aria=rotulo_aria,
        legenda=legenda,
    )


_TONS_KPI: frozenset[str] = frozenset(
    {"neutro", "destaque", "positivo", "informativo"}
)


def _adaptabilidade(indice: int) -> tuple[str, str]:
    if indice == 0:
        return "adapt-primary", "Função primária"
    if indice == 1:
        return "adapt-secondary", "Função secundária"
    if indice >= 2:
        return "adapt-tertiary", "Função alternativa"
    return "adapt-incompatible", "Compatibilidade não confirmada"


def render_cabecalho(titulo: str, subtitulo: str | None = None) -> None:
    """Renderiza o cabeçalho editorial principal de uma página."""
    subtitulo_html = (
        f'<p class="project-subtitle">{_esc(subtitulo)}</p>'
        if subtitulo
        else ""
    )
    st.markdown(
        '<header class="page-header">'
        f'<h1 class="app-title">{_esc(titulo)}</h1>'
        f"{subtitulo_html}"
        "</header>",
        unsafe_allow_html=True,
    )


def render_cabecalho_secao(
    titulo: str,
    subtitulo: str | None = None,
    *,
    rotulo: str | None = None,
    nivel: Literal[2, 3] = 2,
) -> None:
    """Cria uma hierarquia de seção consistente sem inflar títulos."""
    tag = "h2" if nivel == 2 else "h3"
    rotulo_html = (
        f'<p class="section-eyebrow">{_esc(rotulo)}</p>'
        if rotulo
        else ""
    )
    subtitulo_html = (
        f'<p class="section-subtitle">{_esc(subtitulo)}</p>'
        if subtitulo
        else ""
    )
    st.markdown(
        '<header class="section-header">'
        f"{rotulo_html}"
        f'<{tag} class="section-title section-title-{nivel}">{_esc(titulo)}</{tag}>'
        f"{subtitulo_html}"
        "</header>",
        unsafe_allow_html=True,
    )


def render_kpis(
    itens: Sequence[KPI],
    *,
    titulo: str | None = None,
    descricao: str | None = None,
    rotulo_aria: str = "Indicadores",
) -> None:
    """Renderiza KPIs compactos com leitura linear e sem dependência de ``st.metric``."""
    if not itens:
        return

    cabecalho = ""
    if titulo or descricao:
        titulo_html = (
            f'<h2 class="kpi-group-title">{_esc(titulo)}</h2>'
            if titulo
            else ""
        )
        descricao_html = (
            f'<p class="kpi-group-description">{_esc(descricao)}</p>'
            if descricao
            else ""
        )
        cabecalho = (
            '<header class="kpi-group-header">'
            f"{titulo_html}{descricao_html}"
            "</header>"
        )

    cards: list[str] = []
    for item in itens:
        tom = item.tom if item.tom in _TONS_KPI else "neutro"
        contexto_html = (
            f'<span class="kpi-context">{_esc(item.contexto)}</span>'
            if item.contexto
            else ""
        )
        cards.append(
            f'<article class="kpi-card kpi-{tom}" role="listitem">'
            f'<span class="kpi-label">{_esc(item.rotulo)}</span>'
            f'<strong class="kpi-value">{_esc(item.valor)}</strong>'
            f"{contexto_html}"
            "</article>"
        )

    st.markdown(
        '<section class="kpi-group" '
        f'aria-label="{_esc(rotulo_aria)}">'
        f"{cabecalho}"
        '<div class="kpi-grid" role="list">'
        f'{"".join(cards)}'
        "</div></section>",
        unsafe_allow_html=True,
    )


def render_campo(
    layout: Mapping[str, SlotTatico],
    escalados: Mapping[str, str],
    jogadores: Mapping[str, Mapping[str, Any]],
    avaliacoes_por_nome: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Renderiza o campo usando apenas a avaliação do período selecionado."""
    avaliacoes = avaliacoes_por_nome or {}
    cards: list[str] = []

    for slot, configuracao in layout.items():
        nome = escalados.get(slot)
        posicao_css = (
            f"left:{_esc(configuracao.left)};"
            f"bottom:{_esc(configuracao.bottom)};"
        )
        if not nome or nome not in jogadores:
            cards.append(
                f'<div class="player-node" style="{posicao_css}">'
                '<div class="player-card-pitch player-card-empty">'
                f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
                '<div class="player-name-tag">Selecionar atleta</div>'
                '<div class="player-empty-tag">Vaga aberta</div>'
                "</div></div>"
            )
            continue

        dados = jogadores[nome]
        indice = indice_adaptabilidade(dados, configuracao.posicoes)
        classe, descricao = _adaptabilidade(indice)
        avaliacao = avaliacoes.get(nome)
        metricas = (
            calcular_metricas_avaliacao(avaliacao)
            if avaliacao is not None
            else {
                "capacidade_atual_media": None,
                "potencial_2030_medio": None,
                "status": "Não avaliada",
            }
        )
        atual = formatar_numero(metricas["capacidade_atual_media"])
        potencial = formatar_numero(metricas["potencial_2030_medio"])
        situacao = formatar_status_avaliacao(metricas["status"])

        cards.append(
            f'<div class="player-node" style="{posicao_css}">'
            f'<div class="player-card-pitch {classe}">'
            f'<div class="player-pos-tag">{_esc(configuracao.tag)}</div>'
            f'<div class="player-name-tag" title="{_esc(nome)}">{_esc(nome)}</div>'
            f'<div class="player-rating-tag">Atual {atual} · Pot. {potencial}</div>'
            f'<span class="player-adaptability-tag">{_esc(descricao)} · '
            f'{_esc(situacao)}</span>'
            "</div></div>"
        )

    campo = (
        '<div class="pitch-container" role="region" tabindex="0" '
        'aria-label="Campo tático com titulares">'
        '<div class="pitch-line-center"></div>'
        '<div class="pitch-circle"></div>'
        '<div class="pitch-penalty-top"></div>'
        '<div class="pitch-penalty-bottom"></div>'
        f'{"".join(cards)}</div>'
    )
    st.markdown(campo, unsafe_allow_html=True)


def render_banco_reservas(
    reservas: Sequence[str],
    jogadores: Mapping[str, Mapping[str, Any]],
) -> None:
    st.markdown(f"## Banco selecionado ({len(reservas)}/{LIMITE_RESERVAS})")
    if not reservas:
        st.info(
            "Banco vazio. As vagas podem ser preenchidas gradualmente, "
            "sem impedir a montagem dos titulares."
        )
        return

    cards: list[str] = []
    for nome in reservas:
        dados = jogadores.get(nome, {})
        posicao = str(dados.get("posicao") or "Não informada")
        sigla = ABREVIACOES.get(posicao, "OBS")
        cards.append(
            '<div class="bench-card">'
            f'<div class="bench-number">{_esc(sigla)}</div>'
            f'<div class="bench-name">{_esc(nome)}</div>'
            f'<div class="bench-club">{_esc(dados.get("clube"))}</div>'
            "</div>"
        )

    st.markdown(
        '<div class="bench-box" tabindex="0" role="region" '
        'aria-label="Banco de reservas"><div class="bench-grid">'
        + "".join(cards)
        + "</div></div>",
        unsafe_allow_html=True,
    )


def calcular_resumo_elenco(
    elenco: Sequence[Mapping[str, Any]],
) -> dict[str, float | int]:
    idades = [
        int(jogador.get("idade", 0))
        for jogador in elenco
        if jogador.get("idade")
    ]
    alturas = [
        extrair_altura_metros(jogador.get("tm_altura"), 0.0)
        for jogador in elenco
    ]
    alturas_validas = [valor for valor in alturas if valor > 0]
    valores_atuais = [valor_mercado_atual(jogador) for jogador in elenco]
    valores_atuais_validos = [
        valor for valor in valores_atuais if valor > 0
    ]
    valores_maximos = [valor_mercado_maximo(jogador) for jogador in elenco]
    valores_maximos_validos = [
        valor for valor in valores_maximos if valor > 0
    ]

    return {
        "idade_2030": (
            sum(idades) / len(idades) + 4 if idades else 0.0
        ),
        "altura_media": (
            sum(alturas_validas) / len(alturas_validas)
            if alturas_validas
            else 0.0
        ),
        "valor_atual": sum(valores_atuais_validos),
        "valor_maximo": sum(valores_maximos_validos),
        "cobertura_mercado": len(valores_atuais_validos),
        "cobertura_altura": len(alturas_validas),
    }


def render_resumo_elenco(
    titulares: Sequence[Mapping[str, Any]],
    reservas: Sequence[Mapping[str, Any]],
) -> None:
    elenco = [*titulares, *reservas]
    if not elenco:
        st.info(
            "Preencha titulares ou reservas para gerar o raio-X cadastral "
            "e de mercado da convocação."
        )
        return

    resumo = calcular_resumo_elenco(elenco)
    atual = float(resumo["valor_atual"])
    maximo = float(resumo["valor_maximo"])
    percentual = atual / maximo * 100.0 if maximo > 0 else 0.0

    st.markdown(
        '<div class="summary-box"><div class="summary-grid">'
        '<div><div class="summary-label">Titulares</div>'
        f'<div class="summary-value">{len(titulares)}/{LIMITE_TITULARES}</div></div>'
        '<div><div class="summary-label">Reservas</div>'
        f'<div class="summary-value">{len(reservas)}/{LIMITE_RESERVAS}</div></div>'
        '<div><div class="summary-label">Convocados</div>'
        f'<div class="summary-value summary-highlight">{len(elenco)}/{LIMITE_CONVOCADOS}</div></div>'
        '<div><div class="summary-label">Idade média em 2030</div>'
        f'<div class="summary-value">{float(resumo["idade_2030"]):.1f}</div></div>'
        '<div><div class="summary-label">Valor atual</div>'
        f'<div class="summary-value summary-positive">{_esc(formatar_valor_milhoes(atual))}</div></div>'
        '<div><div class="summary-label">Atual / pico</div>'
        f'<div class="summary-value">{percentual:.0f}%</div></div>'
        "</div>"
        '<div class="summary-footnote">'
        f'Cobertura dos {len(elenco)} selecionados: mercado de '
        f'{int(resumo["cobertura_mercado"])}; altura de '
        f'{int(resumo["cobertura_altura"])}.'
        "</div></div>",
        unsafe_allow_html=True,
    )


def _idade_projetada_2030(dados: Mapping[str, Any]) -> str:
    try:
        idade_base = int(dados.get("idade") or 0)
    except (TypeError, ValueError):
        return "—"
    if idade_base <= 0:
        return "—"
    return str(idade_base + (ANO_COPA - ANO_BASE_DADOS))


def render_cartao_perfil(
    nome: str,
    dados: Mapping[str, Any],
    registro_avaliacao: Mapping[str, Any] | None = None,
) -> None:
    """Renderiza um card editorial inspirado em videogames, sem dados legados."""
    posicoes = dados.get("posicoes_multiplas") or [dados.get("posicao")]
    siglas: list[str] = []
    for posicao in posicoes:
        sigla = ABREVIACOES.get(str(posicao), "OBS")
        if sigla not in siglas:
            siglas.append(sigla)

    metricas = (
        calcular_metricas_avaliacao(registro_avaliacao)
        if registro_avaliacao is not None
        else {
            "capacidade_atual_media": None,
            "potencial_2030_medio": None,
            "status": "Não avaliada",
        }
    )
    capacidade = (
        "—"
        if metricas["capacidade_atual_media"] is None
        else formatar_numero(metricas["capacidade_atual_media"])
    )
    potencial = (
        "—"
        if metricas["potencial_2030_medio"] is None
        else formatar_numero(metricas["potencial_2030_medio"])
    )
    status = formatar_status_avaliacao(metricas.get("status"))
    clube = dados.get("clube") or "Não informado"
    idade_2030 = _idade_projetada_2030(dados)
    posicoes_curtas = " - ".join(siglas) if siglas else "OBS"

    st.markdown(
        '<article class="profile-card" '
        f'aria-label="Card do jogador {_esc(nome)}">'
        '<div class="profile-card-topline">'
        '<span class="profile-card-kicker">Ciclo 2030</span>'
        f'<span class="profile-evaluation-status">{_esc(status)}</span>'
        "</div>"
        '<div class="profile-card-identity">'
        f'<h2>{_esc(nome)}</h2>'
        f'<p class="profile-position-inline">{_esc(posicoes_curtas)}</p>'
        '<p class="profile-club">'
        '<span>Clube atual</span>'
        f'<strong>{_esc(clube)}</strong>'
        "</p>"
        "</div>"
        '<dl class="profile-game-stats">'
        '<div class="profile-game-stat">'
        '<dt>Capacidade atual</dt>'
        f'<dd>{_esc(capacidade)}</dd>'
        "</div>"
        '<div class="profile-game-stat">'
        '<dt>Potencial em 2030</dt>'
        f'<dd>{_esc(potencial)}</dd>'
        "</div>"
        '<div class="profile-game-stat">'
        '<dt>Idade em 2030</dt>'
        f'<dd>{_esc(idade_2030)}</dd>'
        "</div>"
        "</dl>"
        "</article>",
        unsafe_allow_html=True,
    )


def _nota_avaliacao(
    registro: Mapping[str, Any],
    analista: str,
    campo: str,
) -> float | None:
    bloco = registro.get(analista)
    if not isinstance(bloco, Mapping):
        return None
    valor = bloco.get(campo)
    if valor in (None, "") or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _formatar_nota_executiva(valor: Any, casas: int) -> str:
    if valor in (None, "") or isinstance(valor, bool):
        return "—"
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "—"
    return f"{numero:.{casas}f}".replace(".", ",")


def render_quadro_avaliacao_executivo(
    registro: Mapping[str, Any],
    *,
    rotulo_vini: str = "Vini",
    rotulo_beto: str = "Beto",
) -> None:
    """Exibe as notas trimestrais no padrão executivo compartilhado."""
    metricas = calcular_metricas_avaliacao(registro)
    linhas = (
        {
            "indicador": ("Capacidade atual", "Desempenho no período"),
            "vini": _nota_avaliacao(registro, "vini", "capacidade_atual"),
            "beto": _nota_avaliacao(registro, "beto", "capacidade_atual"),
            "media": metricas.get("capacidade_atual_media"),
        },
        {
            "indicador": ("Potencial 2030", "Projeção para o ciclo"),
            "vini": _nota_avaliacao(registro, "vini", "potencial_2030"),
            "beto": _nota_avaliacao(registro, "beto", "potencial_2030"),
            "media": metricas.get("potencial_2030_medio"),
        },
    )
    render_tabela_executiva(
        linhas,
        (
            ColunaTabelaExecutiva(
                "indicador",
                "Indicador",
                largura="43%",
            ),
            ColunaTabelaExecutiva(
                "vini",
                rotulo_vini,
                formato="decimal_1",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "beto",
                rotulo_beto,
                formato="decimal_1",
                alinhamento="centro",
            ),
            ColunaTabelaExecutiva(
                "media",
                "Média",
                formato="decimal_2",
                alinhamento="centro",
                destaque=True,
            ),
        ),
        rotulo_aria="Quadro executivo das avaliações trimestrais",
        legenda="Notas de Vini e Beto e média do período",
        interativa=False,
    )


def render_comparativo_mercado(dados: Mapping[str, Any]) -> None:
    """Exibe valor de mercado com hierarquia visual e metadados separados."""
    atual = valor_mercado_atual(dados)
    maximo = valor_mercado_maximo(dados)
    percentual = percentual_do_pico(dados)
    diferenca = max(maximo - atual, 0.0) if maximo > 0 else 0.0

    if atual <= 0 and maximo <= 0:
        st.info("Não há dados de mercado suficientes para este atleta.")
        return

    percentual_texto = (
        f"{percentual:.1f}%" if percentual is not None else "Sem base"
    )
    st.markdown(
        '<section class="market-card" '
        'aria-label="Resumo do valor de mercado">'
        '<dl class="market-grid">'
        '<div class="market-metric market-metric--primary">'
        '<dt class="market-label">Valor atual</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(atual))}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Pico de valor de mercado</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(maximo))}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Percentual do pico de mercado</dt>'
        f'<dd class="market-value">{_esc(percentual_texto)}</dd>'
        "</div>"
        '<div class="market-metric">'
        '<dt class="market-label">Diferença para o pico de mercado</dt>'
        f'<dd class="market-value">{_esc(formatar_valor_milhoes(diferenca))}</dd>'
        "</div>"
        "</dl>"
        '<dl class="market-dates">'
        '<div class="market-date-item">'
        '<dt>Data do pico de mercado</dt>'
        f'<dd>{_esc(dados.get("tm_data_valor_maximo"))}</dd>'
        "</div>"
        '<div class="market-date-item">'
        '<dt>Última atualização</dt>'
        f'<dd>{_esc(dados.get("tm_ultima_atualizacao"))}</dd>'
        "</div>"
        "</dl>"
        '<p class="market-card-info"><em>'
        "Valor de mercado é uma referência externa e não equivale à "
        "avaliação esportiva do projeto."
        "</em></p>"
        "</section>",
        unsafe_allow_html=True,
    )


def render_dados_transfermarkt(dados: Mapping[str, Any]) -> None:
    """Exibe os dados do jogador agrupados por contexto e omite campos vazios."""
    grupos = (
        (
            "Identificação",
            (
                ("Nome completo", dados.get("nome_completo") or dados.get("nome")),
                ("Nascimento", dados.get("tm_nascimento")),
                ("Naturalidade", dados.get("tm_naturalidade")),
                ("Altura", dados.get("tm_altura")),
                ("Pé preferencial", dados.get("tm_pe")),
            ),
            "",
        ),
        (
            "Vínculo profissional",
            (
                ("Clube atual", dados.get("clube")),
                ("Empresário", dados.get("tm_empresario")),
                ("No clube desde", dados.get("tm_clube_desde")),
                ("Contrato até", dados.get("tm_contrato")),
                ("Opção de contrato", dados.get("tm_opcao_contrato")),
                ("Última renovação", dados.get("tm_ultima_renovacao")),
                ("Equipador", dados.get("tm_equipador")),
            ),
            "",
        ),
    )

    grupos_html: list[str] = []
    for titulo, campos, classe_extra in grupos:
        itens = [
            (rotulo, valor)
            for rotulo, valor in campos
            if valor not in (None, "", [], (), set())
        ]
        if not itens:
            continue

        definicoes = "".join(
            '<div class="player-data-item">'
            f'<dt class="player-data-term">{_esc(rotulo)}</dt>'
            f'<dd class="player-data-description">{_esc(valor)}</dd>'
            "</div>"
            for rotulo, valor in itens
        )
        grupos_html.append(
            f'<section class="player-data-group{classe_extra}">'
            f'<h3 class="player-data-group-title">{_esc(titulo)}</h3>'
            '<dl class="player-data-list">'
            f"{definicoes}</dl>"
            "</section>"
        )

    if not grupos_html:
        st.info("Não há dados do jogador disponíveis.")
        return

    st.markdown(
        '<section class="player-data-panel" '
        'aria-label="Dados do jogador">'
        '<div class="player-data-groups">'
        f'{"".join(grupos_html)}'
        "</div></section>",
        unsafe_allow_html=True,
    )


def render_legenda_adaptabilidade() -> None:
    st.markdown(
        '<div class="legend-box" aria-label="Legenda de adaptabilidade">'
        '<div class="legend-item"><span class="legend-dot legend-primary"></span>'
        "<strong>Função primária</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-secondary"></span>'
        "<strong>Função secundária</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-tertiary"></span>'
        "<strong>Função alternativa</strong></div>"
        '<div class="legend-item"><span class="legend-dot legend-empty"></span>'
        "<strong>Vaga aberta ou compatibilidade não confirmada</strong></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_lista_tatica(
    linhas: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    """Componente de compatibilidade para estruturas táticas já preparadas."""
    secoes: list[str] = []
    for linha, itens in linhas.items():
        cards: list[str] = []
        for item in itens:
            nome = str(item.get("nome") or "Selecionar atleta")
            preenchido = bool(item.get("preenchido"))
            indice = int(item.get("indice_adaptabilidade", -1))
            classe, status = (
                _adaptabilidade(indice)
                if preenchido
                else ("adapt-empty", "Vaga aberta")
            )
            atual = formatar_numero(item.get("capacidade_atual"))
            potencial = formatar_numero(item.get("potencial_2030"))
            situacao = formatar_status_avaliacao(
                item.get("situacao_avaliacao") or "Não avaliada"
            )
            cards.append(
                f'<li class="tactical-list-item {classe}">'
                '<div class="tactical-list-main">'
                f'<span class="tactical-list-tag">{_esc(item.get("tag"))}</span>'
                '<span class="tactical-list-copy">'
                f'<strong class="tactical-list-name">{_esc(nome)}</strong>'
                f'<span class="tactical-list-slot">{_esc(item.get("slot"))}</span>'
                "</span></div>"
                '<span class="tactical-list-meta">'
                f'<span class="tactical-list-status">{_esc(status)}</span>'
                f'<span class="tactical-list-ratings">Atual {atual} · '
                f'Pot. {potencial} · {_esc(situacao)}</span>'
                "</span></li>"
            )
        secoes.append(
            '<section class="tactical-list-section">'
            f'<h2 class="tactical-list-heading">{_esc(linha)}</h2>'
            f'<ul class="tactical-list-grid">{"".join(cards)}</ul>'
            "</section>"
        )

    st.markdown(
        '<div class="tactical-list" role="region" tabindex="0" '
        'aria-label="Escalação em lista">'
        f'{"".join(secoes)}</div>',
        unsafe_allow_html=True,
    )


def render_avaliacao_leitura(
    registro: Mapping[str, Any] | None,
) -> None:
    """Compatibilidade pública: exibe somente o contrato trimestral."""
    if registro is None:
        st.info("Não há avaliação registrada para o período selecionado.")
        return
    metricas = calcular_metricas_avaliacao(registro)
    st.write(
        {
            "capacidade_atual": metricas["capacidade_atual_media"],
            "potencial_2030": metricas["potencial_2030_medio"],
            "saldo_projetado": metricas["saldo_projetado"],
            "situacao": formatar_status_avaliacao(metricas["status"]),
        }
    )


def render_dossie(_: Mapping[str, Any]) -> None:
    """O dossiê legado foi desativado na RC5."""
    st.info(
        "O histórico editorial ativo passa a ser formado pelas observações "
        "trimestrais de Vini e Beto."
    )
