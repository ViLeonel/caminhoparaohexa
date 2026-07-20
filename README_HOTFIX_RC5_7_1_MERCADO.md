# Hotfix RC5.7.1 — Indicadores de mercado

Hotfix cumulativo sobre a RC5.7.

## Causa confirmada

A RC5.7 substituiu o antigo DataFrame `df_mercado` pela lista de registros
`mercado`, mas um KPI continuou chamando `len(df_mercado)`. Ao abrir a página
**Indicadores**, o caminho de mercado gerava `NameError`.

## Correção

```python
KPI(
    "Atletas com valor",
    len(mercado),
    "Cobertura disponível na fonte externa",
    "informativo",
)
```

## Proteção contra regressão

O novo teste `tests/test_hotfix_rc57_mercado.py` importa `hexa_pages.py` com
dependências controladas e executa realmente `render_tela_analise()` até a
tabela de mercado. O teste confirma:

- ausência do nome obsoleto `df_mercado`;
- KPI com a quantidade correta de atletas;
- renderização da tabela executiva de mercado;
- versão do hotfix.

## Arquivos de produção incluídos

- `hexa_pages.py` — corrigido;
- `hexa_config.py` — versão atualizada;
- `hexa_components.py` — preservado da RC5.7;
- `hexa_styles.py` — preservado da RC5.7.

Nenhum JSON canônico foi alterado.

## Versão

`1.1.10-hotfix-rc5.7-mercado`
