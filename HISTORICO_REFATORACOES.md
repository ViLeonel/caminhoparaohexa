# HISTÓRICO CONSOLIDADO DE REFATORAÇÕES

## O Caminho para o Hexa 2030

Este documento substitui os arquivos separados `REFATORACAO_ETAPA_1.md` a
`REFATORACAO_ETAPA_7.md` e passa a registrar também as etapas posteriores.

Objetivos:

- manter uma única referência para a base de conhecimento;
- registrar decisões arquiteturais e garantias de integridade;
- separar alterações executadas de recomendações futuras;
- preservar um histórico auditável da evolução do projeto.

> O relatório técnico específico de acessibilidade permanece em
> `RELATORIO_WCAG.md`, pois contém critérios e roteiro de validação próprios.

---

## REFATORAÇÃO — ETAPA 1

## Mudanças
- `caminho_hexa_2030.py` reduzido a entrypoint e roteamento.
- Quatro telas extraídas para `hexa_pages.py`.
- Enriquecimentos externos movidos para `enriquecimentos_tm.json`.
- Mesclagem temporal: campos protegidos nunca são sobrescritos; campos cadastrais só completam lacunas; campos `tm_` só avançam com fonte igual ou mais recente.
- Testes mínimos adicionados em `tests/`.

## Testes
```bash
python -m compileall .
python -m unittest discover -s tests -v
```

## Execução local
```bash
python -m pip install -r requirements.txt
streamlit run caminho_hexa_2030.py
```

## Deploy
Envie todos os arquivos para a raiz do mesmo repositório no GitHub. No Streamlit Community Cloud, mantenha `caminho_hexa_2030.py` como Main file path e faça reboot do app após o commit.


---

## REFATORAÇÃO — ETAPA 2

## Objetivo
Extrair transformações de dados e gerenciamento de estado da interface para módulos puros e testáveis.

## Arquivos adicionados
- `hexa_selectors.py`: filtros, registros do roster, avaliações, mercado, médias e ordenações.
- `hexa_session.py`: chaves, limpeza, opções, normalização e leitura da convocação.
- `tests/test_hexa_selectors.py`
- `tests/test_hexa_session.py`

## Arquivo alterado
- `hexa_pages.py`: passou a consumir os módulos novos e deixou de conter as transformações e helpers de estado extraídos.

## Garantias
- Nenhum campo editorial ou tático foi alterado.
- Nenhum atleta foi removido ou recriado.
- O JSON canônico permaneceu byte a byte igual ao arquivo de entrada.
- Os novos módulos não importam Streamlit nem pandas.
- As funcionalidades visuais não relacionadas foram preservadas.

## Testes executados
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

Resultado: 24 testes aprovados.

Também foram executados:
- import de `hexa_data`, `hexa_taticas`, `hexa_selectors` e `hexa_session`;
- validação dos nomes importados entre módulos locais;
- parse dos dois JSONs;
- comparação SHA-256 do JSON canônico com o arquivo original.

## Não executado
- inicialização real do Streamlit;
- navegação visual em navegador;
- testes em Chrome, Firefox, Edge, Brave e Safari;
- teste concorrente de escrita.


---

## REFATORAÇÃO — ETAPA 3

## Objetivo
Centralizar configurações e remover valores temporais e textuais fixos da interface.

## Novo módulo
- `hexa_config.py`: identidade, menus, anos de referência, grupos editoriais, limites de cadastro, feedback, caminhos e `PAGE_CONFIG`.

## Arquivos alterados
- `caminho_hexa_2030.py`
- `hexa_pages.py`
- `hexa_components.py`
- `hexa_selectors.py`
- `hexa_data.py`
- `hexa_styles.py`

## Comportamento preservado
- JSON canônico e enriquecimentos não foram modificados.
- Campos editoriais e táticos continuam protegidos.
- Limites oficiais de convocação continuam em `hexa_taticas.py`.
- A interface mantém as quatro telas e os mesmos fluxos funcionais.

## Testes
- 30 testes automatizados aprovados.
- Compilação de todos os arquivos Python aprovada.
- JSONs validados: 61 atletas e 58 enriquecimentos.


---

## Refatoração — Etapa 4

## Objetivo
Eliminar estilos e cores inline e fortalecer o design system.

## Alterações
- Cores removidas de `hexa_components.py` e `hexa_pages.py`.
- Posicionamento do campo convertido em classes CSS.
- Progresso de mercado convertido em classes discretas de 0 a 100.
- Adaptabilidade representada por classe semântica e texto.
- Legenda deixou de depender de nomes de cores.
- Botão de feedback convertido em classe reutilizável.
- Estados de foco visível adicionados.
- Preferência por movimento reduzido respeitada.
- Classes semânticas para resumo, mercado e dossiê.
- Testes automáticos impedem regressão para estilos inline.

## Compatibilidade
Nenhum JSON, regra tática, limite de convocação ou campo editorial foi alterado.


---

## REFATORAÇÃO — ETAPA 5

## Objetivo
Fortalecer estados vazios, mensagens de persistência e feedback operacional.

## Alterações
- Novo `hexa_messages.py` com mensagens compartilhadas e funções puras.
- Resumo textual de titulares, reservas e vagas restantes.
- Aviso explícito sobre persistência temporária no Streamlit Community Cloud.
- Confirmação de cadastro orientando versionamento no GitHub.
- Estados vazios específicos para perfil, roster, avaliações e mercado.
- Distinção textual entre dado não informado, não pesquisado, não aplicável, conteúdo editorial não registrado e cálculo sem base.
- Feedback por e-mail informa que o botão apenas abre o cliente e não envia automaticamente.
- Sentinela legada `N/A` convertida para `Não informado pela fonte` na apresentação do roster.

## Arquivos alterados
- `hexa_pages.py`
- `hexa_components.py`
- `hexa_selectors.py`

## Arquivos adicionados
- `hexa_messages.py`
- `tests/test_hexa_messages.py`

## Testes executados
- `python -m compileall -q .`
- `python -m unittest discover -s tests -v`
- Resultado: 41 testes aprovados.
- Validação dos dois arquivos JSON.
- Nenhum dado canônico foi alterado.

## Não executado
- Inicialização real do Streamlit.
- Testes visuais e em navegadores.
- Escrita real no Streamlit Community Cloud.
- Envio real de e-mail.


---

## REFATORAÇÃO — ETAPA 6

## Objetivo
Implementar uma visualização mobile alternativa da formação tática, preservando a mesma convocação e o mesmo estado da sessão.

## Alterações
- Adicionado modo de visualização `Campo` ou `Lista`.
- Criada transformação pura `construir_visualizacao_tatica_lista`.
- Criada classificação dos slots em Goleiro, Defesa, Meio-campo e Ataque.
- Adicionado componente `render_lista_tatica`.
- Mantidas vagas abertas na lista.
- Exibidos posição, nome, notas e adaptabilidade em texto.
- Adicionados estilos responsivos para a lista e redução da altura do campo em telas menores.
- Nenhum dado editorial, tático ou externo foi alterado.

## Arquivos alterados
- `hexa_pages.py`
- `hexa_components.py`
- `hexa_selectors.py`
- `hexa_styles.py`
- `tests/test_hexa_selectors.py`
- `tests/test_hexa_design_system.py`

## Testes executados
- `python -m compileall -q .`
- `python -m unittest discover -s tests -v`
- Verificação das seis formações na estrutura em lista.
- Validação dos dois arquivos JSON.

## Resultado
- 43 testes aprovados.
- Todas as seis formações preservam 11 slots.
- `jogadores_hexa_2030.json`: 61 atletas.
- `enriquecimentos_tm.json`: 58 registros.

## Não verificado
- Execução visual real do Streamlit.
- Testes em navegadores.
- Leitor de tela e navegação real por teclado.


---

## REFATORAÇÃO — ETAPA 7

Revisão WCAG 2.2 AA e modo de alto contraste.

Arquivos principais alterados: `caminho_hexa_2030.py`, `hexa_components.py`,
`hexa_pages.py`, `hexa_styles.py`.

Arquivos adicionados: `hexa_accessibility.py`, `tests/test_wcag_accessibility.py`
e `RELATORIO_WCAG.md`.


---

## Etapa 8 — Fábricas táticas e documentação consolidada

### Objetivo

Reduzir duplicidades na definição das seis formações sem alterar nenhuma
regra esportiva, posição permitida, nome de slot, tag, coordenada ou ordem de
exibição.

### Alterações arquiteturais

O grande literal `TATICAS` foi substituído por uma composição baseada em:

- `_slot()`: fábrica central de slots, com validação de nome, posições e
  coordenadas percentuais;
- `_combinar_linhas()`: composição ordenada de linhas, com rejeição de nomes
  duplicados;
- `_linha_goleiro()`: linha compartilhada pelas seis formações;
- `_linha_defensiva_quatro()`: linha defensiva compartilhada;
- uma fábrica específica para cada formação;
- `FABRICAS_TATICAS`: registro ordenado e extensível;
- `construir_taticas()`: materialização de dicionários independentes;
- `TATICAS`: resultado público compatível com os módulos existentes.

### Garantias de regressão

A refatoração preserva integralmente, para cada formação:

- nome da formação;
- ordem das formações;
- quantidade de 11 slots;
- nome e ordem dos slots;
- posições compatíveis e sua prioridade;
- coordenadas `left` e `bottom`;
- tags táticas;
- comportamento de `indice_adaptabilidade`;
- compatibilidade com `hexa_pages.py`, `hexa_components.py`,
  `hexa_selectors.py` e `hexa_session.py`.

Foram adicionadas assinaturas SHA-256 da estrutura completa das seis formações.
Qualquer alteração futura em nome, ordem, posição, coordenada ou tag quebrará o
teste de regressão de forma explícita.

### Extensibilidade

Uma nova formação pode ser adicionada por meio de:

1. uma função fábrica que retorna `dict[str, SlotTatico]`;
2. composição com `_linha_goleiro()`, `_linha_defensiva_quatro()` e linhas
   específicas;
3. registro em `FABRICAS_TATICAS`;
4. inclusão consciente da nova assinatura de regressão após revisão dos
   analistas.

A estrutura continua em Python nesta etapa. A migração para arquivo externo de
configuração fica preparada, mas não foi implementada para evitar introduzir
validação e persistência adicionais sem necessidade atual.

### Documentação

Os sete arquivos anteriores `REFATORACAO_ETAPA_*.md` foram incorporados neste
arquivo. Eles não fazem parte do novo pacote, reduzindo a quantidade de arquivos
necessários na base de conhecimento.

### Testes executados

- compilação de todos os arquivos Python;
- suíte completa com 57 testes;
- validação das seis formações;
- comparação estrutural entre a versão da Etapa 7 e a versão refatorada;
- validação de ordem e nomes do registro;
- validação de independência das estruturas geradas;
- validação de coordenadas entre 0% e 100%;
- validação de tags;
- validação de posições oficiais;
- validação dos dois arquivos JSON.

### Resultado

A comparação estrutural com a Etapa 7 foi idêntica para as seis formações.
Nenhum arquivo JSON foi alterado.

### Pontos não executados

- inicialização real do Streamlit;
- inspeção visual das seis formações em navegador;
- testes em Chrome, Firefox, Edge, Brave e Safari;
- interação real com troca de formação e manutenção do `session_state`.

---

---

# Etapa 9 — Interface de repositório de jogadores

## Objetivo

Desacoplar as regras de dados e a interface da tecnologia de persistência,
mantendo o JSON como fonte canônica atual.

## Implementação

Foi criado `hexa_repository.py` com:

- `JogadoresRepository`, contrato baseado em `Protocol`;
- `ResultadoLeitura`, resultado tipado com indicação de reparo;
- `JsonJogadoresRepository`, implementação padrão em JSON;
- `DataIntegrityError`, erro compartilhado de integridade.

A implementação JSON concentra:

- leitura com `utf-8-sig`;
- validação da estrutura raiz;
- reparo restrito a vírgulas ausentes entre objetos de primeiro nível;
- preservação do original corrompido;
- escrita em arquivo temporário;
- validação do temporário antes da substituição;
- backup `.json.bak`;
- substituição atômica.

`hexa_data.py` continua responsável por:

- normalização;
- aliases;
- enriquecimentos externos;
- proteção editorial e tática;
- validações de domínio.

As funções públicas aceitam injeção opcional de repositório:

```python
carregar_jogadores(repositorio=None)
salvar_jogadores(dados, repositorio=None)
adicionar_jogador(jogadores, dados_novos, repositorio=None)
```

Sem argumento, a aplicação usa `JsonJogadoresRepository(DATA_FILE)`.

## Segurança adicional

O cadastro agora cria uma cópia da base, persiste essa cópia e somente depois
atualiza o estado em memória. Uma falha de gravação não deixa a sessão divergente
da fonte canônica.

## Testes adicionados

- leitura e escrita JSON;
- geração de backup;
- preservação de JSON irrecuperável;
- reparo controlado;
- uso de repositório em memória;
- normalização com repositório injetado;
- ausência de mutação da sessão quando a gravação falha;
- atualização da sessão após gravação bem-sucedida.

## Resultado

```text
63 testes executados
63 aprovados
```

Nenhum arquivo de jogadores ou enriquecimentos foi alterado.

# Etapa 10 — Schema e integridade dos jogadores

- criado `hexa_models.py` com `TypedDict`, severidades e relatórios;
- validação estrutural antes de normalização;
- validação final antes de qualquer salvamento;
- notas limitadas a 0–10;
- idade validada entre os limites configurados;
- nomes e chaves canônicas validados;
- duplicidades normalizadas detectadas;
- posição principal obrigatória em `posicoes_multiplas`;
- registros não estruturados deixam de ser descartados silenciosamente;
- enriquecimentos parciais não criam atletas com posição inventada;
- interface exibe avisos não bloqueantes;
- relatório da base atual: 61 atletas, 0 erros e 0 avisos;
- suíte ampliada para 72 testes.

# Etapa 11 — Concorrência e versionamento da escrita JSON

## Objetivo

Impedir que uma sessão antiga sobrescreva alterações gravadas por outra sessão, mantendo o JSON como fonte canônica temporária.

## Implementação

- Cada leitura calcula SHA-256 dos bytes atuais do JSON.
- `ResultadoLeitura` passa a transportar a versão da fonte.
- `BaseJogadores` mantém `versao_fonte` junto ao dicionário carregado.
- Toda gravação originada de uma sessão envia `versao_esperada`.
- O repositório adquire um bloqueio exclusivo curto antes da comparação e substituição.
- Se o hash atual divergir do esperado, `ConflitoConcorrenciaError` interrompe a operação.
- O arquivo temporário é validado antes da substituição.
- O backup `.json.bak` e a escrita atômica foram preservados.
- Um arquivo lateral `.meta.json` registra hash, data UTC e origem da última gravação.
- O formulário informa conflitos e solicita recarregamento.
- O estado da sessão não é modificado quando ocorre conflito.

## Testes

- Duas sessões carregando a mesma versão.
- Primeira sessão gravando com sucesso.
- Segunda sessão sendo recusada com versão obsoleta.
- Preservação do conteúdo mais recente.
- Preservação do estado local da sessão que falhou.
- Registro de versão, data e origem.
- Carregamento real de 61 atletas sem alteração do JSON.

Resultado consolidado: 75 testes aprovados.

## Hotfix pós-Etapa 11 — Compatibilidade do runtime Python

- Substituído `from datetime import UTC` por `from datetime import datetime, timezone`.
- Substituído `datetime.now(UTC)` por `datetime.now(timezone.utc)`.
- Motivo: `datetime.UTC` existe apenas a partir do Python 3.11 e pode causar `ImportError` em runtimes Streamlit configurados com Python 3.10 ou anterior.
- Adicionado teste de regressão para impedir a reintrodução dessa dependência.
- Resultado da suíte após o hotfix: 76 testes aprovados.

## Hotfix de compatibilidade Python 3.10 — importação de tipos

- Removido `typing.NotRequired`, disponível nativamente apenas no Python 3.11+.
- O modelo foi dividido em `JogadorObrigatorio` e `Jogador(..., total=False)`.
- Nenhuma dependência adicional foi incluída.
- Mantida a mesma intenção de schema: campos principais obrigatórios e `nome_completo` opcional.

## RC1 — Arquitetura Base

- Definida a versão `1.0.0-rc1`.
- APIs públicas declaradas explicitamente com `__all__`.
- Adicionado teste de importação idêntico ao entrypoint do Streamlit.
- Adicionada validação de símbolos importados e ciclos entre módulos.
- Criado smoke test isolado em `scripts/rc1_smoke.py`.
- Criada matriz de CI para Python 3.10, 3.11, 3.12, 3.13 e 3.14.
- Adicionado `.gitignore` para backups, locks, temporários e metadados.
- Removidos imports comprovadamente não utilizados.
- JSONs canônicos preservados.

## Etapa 12 — Histórico estruturado de alterações

- Criado `hexa_audit.py` com eventos imutáveis e tipados.
- Auditoria armazenada em `auditoria_jogadores.jsonl`, fora do JSON canônico.
- Cada evento registra atleta, campo, valores anterior e novo, data UTC, origem e versões.
- Campos sem alteração não geram evento.
- Cadastro e self-healing passam a registrar diferenças após a gravação canônica.
- Falhas na gravação canônica não geram histórico falso.
- Repositório JSONL possui bloqueio, deduplicação por ID e substituição atômica.
- Nenhum dado editorial existente foi modificado.
