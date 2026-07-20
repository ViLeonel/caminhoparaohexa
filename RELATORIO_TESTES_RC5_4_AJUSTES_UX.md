# Relatório de testes — RC5.4 Ajustes de UX

Data de execução: 20/07/2026.

## Ambiente

- Python: `3.13.5`
- Streamlit instalado: `1.59.2`
- pandas instalado: `2.3.3`

## Testes realizados

### 1. Instalação das dependências

Executado:

```bash
python -m pip install -r requirements.txt
```

Resultado: código de saída 0. Foram instaladas as versões fixadas no projeto.

### 2. Compilação

Executado sobre o pacote RC5.4:

```bash
python -m compileall -q hexa_rc5_4_ajustes_ux
```

Resultado: código de saída 0.

### 3. Testes automatizados da entrega

Executado:

```bash
python -m unittest discover -s tests -v
```

Resultado: 8 testes aprovados.

Cobertura específica:

- posição segura do centroavante no `4-3-3 Clássico`;
- 11 slots em todas as seis formações;
- rótulos públicos de situação;
- remoção da visualização em lista;
- novo título da convocação;
- remoção de consensos e divergências;
- remoção de ID e idade de 2026;
- presença do novo card e da grade responsiva;
- altura mínima do campo em larguras intermediárias.

### 4. Validação dos JSONs reais

Os três arquivos foram abertos com `json.loads`:

- `jogadores_hexa_2030.json`: 61 atletas;
- `avaliacoes_trimestrais_hexa_2030.json`: 61 registros;
- `enriquecimentos_tm.json`: 58 enriquecimentos.

`carregar_avaliacoes` foi executado com o JSON trimestral e a base real de
jogadores. Resultado:

- período: `2026-T2`;
- 61 avaliações carregadas;
- nenhuma exceção de integridade.

### 5. Regras táticas

`validar_taticas(jogadores)` foi executado com a base real.

Resultado: lista de erros vazia.

Também foi confirmado que:

- existem seis formações;
- todas mantêm exatamente 11 titulares;
- o centroavante do `4-3-3 Clássico` usa `left: 50%` e `bottom: 76%`.

### 6. Imports e nomes importados

Foram importados com sucesso:

- `hexa_config`;
- `hexa_taticas`;
- `hexa_avaliacoes`;
- `hexa_components`;
- `hexa_styles`;
- `hexa_pages`.

Como os módulos completos `hexa_data`, `hexa_session`, `hexa_messages` e
`hexa_persistencia_local` não foram disponibilizados nesta execução, o teste de
imports de `hexa_components` e `hexa_pages` usou stubs isolados com os mesmos
nomes públicos importados. Isso valida os contratos desta entrega, mas não
substitui o teste no repositório completo.

### 7. Streamlit AppTest isolado

Um aplicativo mínimo real chamou:

- `aplicar_estilos`;
- `render_cartao_perfil`;
- `_render_resumo_avaliacao`.

Resultado:

- 0 exceções;
- card com Alexsandro renderizado;
- capacidade, potencial e idade em 2030 presentes;
- `Avaliação Completa` presente;
- data `30/06/2026` presente.

### 8. Inicialização do servidor Streamlit

O aplicativo mínimo da etapa anterior foi iniciado em modo headless.

Resultado:

```text
GET /_stcore/health -> HTTP 200 / ok
```

### 9. Integridade dos dados

Hashes SHA-256 verificados nos arquivos originais:

```text
ab7ee9718cd2c34dd0393b9d746359b9cf2ba70fcf1bc557b696d1a5331cdbfb  jogadores_hexa_2030.json
eb846b4886080beb2e1bbce119a650cc1f93c9b9d14940446c97cbfbc18a3e8d  avaliacoes_trimestrais_hexa_2030.json
72dd628b1c5dcdfe83125c02b254b389f1ec3ae4d61372888d011bd064bcab58  enriquecimentos_tm.json
```

Nenhum JSON foi escrito. Os JSONs não fazem parte do ZIP.

## Aviso do ambiente

Subprocessos Python registraram no `stderr` um aviso de aquecimento interno do
`artifact_tool`. O aviso não pertence ao projeto. Compilação, testes, AppTest e
servidor retornaram sucesso.

## Não realizado

- suíte completa do repositório, porque os demais módulos e testes não estavam
  presentes no ambiente;
- inicialização do entrypoint completo com implementações reais de autenticação,
  dados, sessão e persistência local;
- validação visual em navegador real;
- Chrome, Firefox, Edge, Brave e Safari;
- larguras 320, 375, 390 e 430 px em navegador;
- zoom real de 200%;
- deploy no GitHub e Streamlit Community Cloud.

Esses itens permanecem obrigatórios antes do merge e estão descritos no guia de
deploy.
