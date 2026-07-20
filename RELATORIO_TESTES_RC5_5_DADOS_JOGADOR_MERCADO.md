# Relatório de testes — RC5.5 Dados do jogador e valor de mercado

## Testes realizados

### Compilação

- `python -m compileall` no pacote de trabalho: **aprovado**;
- compilação individual dos quatro módulos alterados: **aprovada**;
- compilação do novo teste: **aprovada**.

### Testes automatizados

- suíte acumulada RC5.4 + RC5.5: **14 testes executados, 14 aprovados**;
- grupos dos dados do jogador: aprovados;
- omissão de campos vazios: aprovada;
- conversão de listas externas para texto: aprovada;
- título `Dados do jogador`: aprovado;
- expander compacto: aprovado;
- quatro indicadores de mercado: aprovados;
- observação menor e itálica: aprovada;
- regras táticas acumuladas da RC5.4: aprovadas.

### Imports e nomes importados

- import de `hexa_components`, `hexa_pages`, `hexa_styles` e `hexa_config`
  em ambiente isolado com stubs somente para módulos não disponibilizados:
  **aprovado**;
- nenhum nome importado ausente foi detectado nos módulos alterados.

### Streamlit

- Streamlit efetivamente instalado: `1.59.2`;
- `st.expander(..., type="compact")` confirmado na assinatura instalada;
- AppTest isolado: **zero exceções**;
- expander encontrado com o rótulo `Dados do jogador`;
- servidor Streamlit isolado iniciado;
- `GET /_stcore/health`: **HTTP 200 / ok**.

### JSONs canônicos

Os arquivos foram apenas lidos e validados:

- `jogadores_hexa_2030.json`: 61 atletas;
  SHA-256 `ab7ee9718cd2c34dd0393b9d746359b9cf2ba70fcf1bc557b696d1a5331cdbfb`;
- `avaliacoes_trimestrais_hexa_2030.json`: 61 avaliações;
  SHA-256 `eb846b4886080beb2e1bbce119a650cc1f93c9b9d14940446c97cbfbc18a3e8d`;
- `enriquecimentos_tm.json`: 58 registros;
  SHA-256 `72dd628b1c5dcdfe83125c02b254b389f1ec3ae4d61372888d011bd064bcab58`.

Nenhum JSON foi incluído ou modificado pela entrega.

## Verificações com ressalva

- o ambiente de execução tinha pandas `2.2.3`, enquanto o projeto fixa
  pandas `2.3.3`;
- `pip check` não ficou limpo por um conflito externo entre `moviepy 2.2.1`
  e `pillow 12.2.0`, não relacionado aos arquivos desta entrega.

Por isso, a varredura de dependências do ambiente completo não pode ser
considerada aprovada, embora o código alterado não introduza dependências novas.

## Testes não realizados

- entrada principal completa com autenticação, persistência e todos os módulos
  reais do repositório;
- suíte histórica completa fora dos testes disponibilizados;
- inspeção visual real em Chrome, Firefox, Edge, Brave e Safari;
- smoke manual em Streamlit Community Cloud;
- execução no ambiente exato com pandas `2.3.3`.
