# RC5.6 — Refinamento executivo

Entrega incremental sobre a RC5.5 e o hotfix 1.1.6.

## Escopo implementado

### Dados do jogador
- remoção integral do bloco `Referência cadastral externa`;
- preservação dos grupos `Identificação` e `Vínculo profissional`;
- inclusão de `Clube atual` no grupo `Vínculo profissional`;
- campos vazios continuam omitidos;
- nenhum dado editorial ou JSON canônico foi alterado.

### Valor de mercado
- aumento do espaçamento entre as datas e a observação;
- inclusão de divisor sutil antes da observação;
- observação mantida em itálico;
- tamanho da observação reduzido para `0.75rem` (12 px).

### Avaliação trimestral
- substituição do `st.dataframe` por um quadro executivo semântico;
- colunas para indicador, Vini, Beto e média;
- média destacada visualmente;
- descrições auxiliares para capacidade atual e potencial 2030;
- layout responsivo para telas estreitas;
- tabela HTML acessível com `caption`, `scope` e leitura linear.

### Navegação e títulos
- `Campo de Jogo` → `Escalação`;
- `Jogadores, Scout e Avaliações` → `Scout`;
- `Lista de Jogadores` → `Jogadores`;
- `Análises & Mercado` → `Indicadores`.

## Arquivos alterados

- `hexa_components.py`
- `hexa_pages.py`
- `hexa_styles.py`
- `hexa_config.py`
- `tests/test_rc5_6_refino_executivo.py`

## Versão

`1.1.8-rc5.6-refino-executivo`
