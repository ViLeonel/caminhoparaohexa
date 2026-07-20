# Relatório de testes — Hotfix RC5.7.1 Mercado

## Causa

- `render_tela_analise()` criava a lista `mercado`.
- O KPI ainda referenciava o nome removido `df_mercado`.
- A exceção ocorria antes da tabela consolidada de mercado.

## Correção aplicada

- `len(df_mercado)` foi substituído por `len(mercado)`.
- A versão passou para `1.1.10-hotfix-rc5.7-mercado`.

## Testes realizados

- Compilação individual de 7 arquivos Python: aprovada.
- Suíte acumulada RC5.6 + RC5.7 + hotfix: 15 testes aprovados.
- Teste de regressão executou realmente `render_tela_analise()` até o mercado.
- KPI `Atletas com valor` validado com dois registros.
- Tabela executiva de mercado validada com dois registros.
- Varredura confirmou ausência de `df_mercado` em `hexa_pages.py`.
- Versão do hotfix validada.

## JSONs validados e preservados

- `jogadores_hexa_2030.json`: válido; registros/chaves: 61; SHA-256: `ab7ee9718cd2c34dd0393b9d746359b9cf2ba70fcf1bc557b696d1a5331cdbfb`.
- `avaliacoes_trimestrais_hexa_2030.json`: válido; registros/chaves: 5; SHA-256: `eb846b4886080beb2e1bbce119a650cc1f93c9b9d14940446c97cbfbc18a3e8d`.
- `enriquecimentos_tm.json`: válido; registros/chaves: 58; SHA-256: `72dd628b1c5dcdfe83125c02b254b389f1ec3ae4d61372888d011bd064bcab58`.

## Observação do ambiente

- O processo de testes retornou código 0.
- O ambiente emitiu um aviso não bloqueante do `artifact_tool` durante a inicialização do Python; esse aviso não pertence ao aplicativo e não alterou o resultado da suíte.

## Testes não realizados

- Entry point completo com autenticação, sessão e persistência reais.
- Smoke visual em Chrome, Firefox, Edge, Brave e Safari.
- Deploy efetivo no Streamlit Community Cloud.
