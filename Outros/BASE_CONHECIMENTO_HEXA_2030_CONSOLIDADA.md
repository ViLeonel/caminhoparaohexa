# BASE DE CONHECIMENTO CONSOLIDADA — O CAMINHO PARA O HEXA 2030

> Documento canônico atualizado em 20/07/2026.  
> Versão atual do aplicativo: `1.3.0-regression-phase2`.  
> Este arquivo substitui os antigos README, DEPLOY, relatórios de testes, fontes técnicas e manifestos de releases anteriores para fins de conhecimento do projeto.

---

## 1. Autoridade e uso deste documento

Este é o **único documento técnico canônico** do projeto para contexto, regras, arquitetura, histórico de releases, deploy, validação e decisões de produto.

Em caso de conflito:

1. prevalece o código mais recente da branch principal;
2. depois, os JSONs canônicos;
3. depois, este documento;
4. documentos antigos de release são apenas históricos e devem ser removidos da base de conhecimento.

Arquivos de código, configuração e dados continuam separados porque são fontes executáveis ou canônicas:

- arquivos Python;
- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `enriquecimentos_tm.json`;
- `requirements.txt`;
- `.streamlit/config.toml`;
- `.streamlit/secrets.toml` local ou Secrets do Streamlit Cloud;
- testes automatizados.

---

## 2. Política permanente de documentação

### 2.1 Regra principal

A partir desta consolidação, o ARQUITETO HEXA deve criar o **menor número possível de arquivos de documentação**.

Por padrão, toda nova alteração deve atualizar apenas este arquivo, acrescentando:

- estado atual;
- resumo da mudança;
- arquivos alterados;
- testes realizados;
- testes não realizados;
- riscos;
- passos de deploy;
- histórico da versão.

### 2.2 Arquivos que não devem mais ser criados por release

Não criar automaticamente:

- `README_RC*.md`;
- `README_HOTFIX*.md`;
- `DEPLOY_RC*.md`;
- `DEPLOY_HOTFIX*.md`;
- `RELATORIO_TESTES_*.md`;
- `FONTES_TECNICAS_*.md`;
- `MANIFESTO_SHA256.txt` no repositório ou na base de conhecimento.

O manifesto SHA-256 pode ser gerado **temporariamente dentro do ZIP de entrega**, quando necessário para auditoria, sem virar arquivo permanente de conhecimento.

### 2.3 Exceções permitidas

Um documento separado só é justificável quando houver necessidade real de separação, como:

- `README.md` público e curto para a página inicial do GitHub;
- política de segurança;
- licença;
- contrato externo de API;
- procedimento legal ou de conformidade;
- especificação de migração de banco irreversível;
- arquivo exigido por uma ferramenta ou plataforma.

Mesmo nessas exceções, o conteúdo essencial deve ser resumido neste documento canônico.

### 2.4 Regra para entregas futuras

Quando houver mudança de código:

- entregar os arquivos Python completos;
- entregar ZIP copy-and-paste ready quando mais de um arquivo mudar;
- atualizar este documento dentro do ZIP;
- não criar vários documentos auxiliares;
- relatar exatamente o que foi testado e o que permaneceu sem validação.

---

## 3. Identidade e missão

O projeto **O Caminho para o Hexa 2030** é uma plataforma Streamlit para análise editorial, scout, avaliações trimestrais, leitura de mercado e simulação tática de jogadores brasileiros com horizonte na Copa de 2030.

Responsáveis editoriais:

- Vini Leonel;
- Beto Muñoz.

A conversa e a avaliação dos dois analistas são a fonte editorial central. Dados externos complementam a análise, mas não substituem as decisões próprias do projeto.

---

## 4. Princípios de integridade

Nunca afirmar que algo foi executado, compilado, testado ou validado sem execução real.

Toda entrega deve diferenciar:

- teste realizado;
- análise estática;
- inferência;
- recomendação;
- ponto não verificado.

Funcionalidades não relacionadas ao pedido devem ser preservadas.

Mudanças pequenas ainda exigem o arquivo Python alterado por inteiro, nunca apenas trechos soltos.

---

## 5. Arquitetura atual

### 5.1 Núcleo da aplicação

- `caminho_hexa_2030.py`: entrypoint, configuração da página, carregamento seguro, navegação e composição geral;
- `hexa_config.py`: identidade, menus, caminhos, limites, nomes e versão;
- `hexa_pages.py`: composição das quatro páginas públicas;
- `hexa_components.py`: componentes visuais compartilhados;
- `hexa_styles.py`: design system e CSS;
- `hexa_taticas.py`: posições, formações, compatibilidade e limites de convocação;
- `hexa_data.py`: leitura, normalização, RegEx, integridade e self-healing;
- `hexa_avaliacoes.py`: contrato e cálculos das avaliações trimestrais;
- `hexa_selectors.py`: filtros e transformações puras;
- `hexa_session.py`: estado e reconciliação da convocação;
- `hexa_persistencia_local.py`: persistência das escalações no navegador;
- `hexa_auth.py`: autenticação e identidade;
- `hexa_admin.py`: área administrativa;
- `hexa_messages.py`: mensagens compartilhadas;
- `hexa_models.py`: modelos e schema, quando presente;
- `hexa_repository.py`: contrato de persistência, quando presente;
- `hexa_audit.py`: auditoria operacional, quando presente.

Evitar nomes genéricos como `data.py`, `components.py` e `styles.py`.

### 5.2 Fontes canônicas

- `jogadores_hexa_2030.json`: cadastro, posições editoriais, clube, idade, grupos, tipo legado e dados externos mesclados;
- `avaliacoes_trimestrais_hexa_2030.json`: avaliações temporais;
- `enriquecimentos_tm.json`: fonte auxiliar de enriquecimentos;
- `auditoria_jogadores.jsonl`: histórico operacional, quando gerado;
- `arquivo/avaliacoes_editoriais_legado_pre_t2_2026.json`: arquivo preventivo de dados editoriais anteriores, quando presente.

### 5.3 Dependências fixadas

```text
streamlit==1.59.2
pandas==2.3.3
streamlit-aggrid==1.2.1.post2
```

---

## 6. Preservação sagrada dos dados

Nunca sobrescrever, apagar ou recriar automaticamente, para jogadores existentes:

- `nota_vini`;
- `nota_roberto`;
- `pontos_fortes`;
- `pontos_fracos`;
- `historico`;
- `posicao`;
- `posicoes_multiplas`;
- `grupo`;
- `tipo`.

Dados externos devem usar namespace explícito, preferencialmente `tm_`.

Novos jogadores podem receber valores neutros. Jogadores existentes nunca podem perder conteúdo editorial.

O self-healing deve:

- corrigir aliases antigos;
- completar apenas campos ausentes;
- normalizar valores;
- salvar somente se houver alteração;
- usar escrita atômica;
- criar backup;
- evitar substituir JSON irrecuperável sem autorização;
- preservar posições definidas pelos analistas;
- registrar versão e origem quando a arquitetura de persistência suportar isso.

### 6.1 Regra do treinador

As posições do projeto têm prioridade absoluta sobre posições de fontes externas.

`tm_posicao_site` e `tm_posicoes_secundarias_site` são apenas referências cadastrais e não alteram automaticamente:

- `posicao`;
- `posicoes_multiplas`.

---

## 7. Posições oficiais

Usar exclusivamente:

1. Goleiro
2. Lateral-direito
3. Lateral-esquerdo
4. Zagueiro
5. Volante
6. Mezzala esquerdo
7. Mezzala direito
8. Meia-esquerda
9. Meia-direita
10. Meia-armador
11. Ponta-esquerda
12. Ponta-direita
13. Segundo atacante
14. Centroavante

Nomenclaturas externas devem ser convertidas para equivalentes dessa lista somente para referência e compatibilidade controlada.

---

## 8. Estado atual do produto

### 8.1 Navegação pública

Os nomes atuais são:

- `🏟️ Escalação`;
- `🔎 Scout`;
- `📋 Jogadores`;
- `📊 Indicadores`.

### 8.2 Decisões permanentes

- JSON continua como fonte temporária de dados;
- banco externo permanece adiado enquanto não houver edição persistente multiusuário;
- notas públicas são somente leitura;
- `tipo` permanece no JSON, mas não é exibido nem usado funcionalmente;
- não existe opção de cortar jogador;
- não existem botões públicos de compartilhamento;
- seleção de atletas começa vazia;
- campo aceita 11 titulares;
- banco aceita até 15 reservas;
- não pode haver duplicidade;
- cada formação mantém estado próprio;
- ficha individual começa vazia e usa busca pesquisável;
- formulário público usa apenas `Sugerir jogador` e `Sugerir melhoria`.

---

## 9. Escalação

A página de escalação utiliza apenas visualização em campo. A antiga visualização em lista foi removida da interface.

Título atual:

```text
Monte a sua convocação
```

Regras:

- 11 titulares;
- até 15 reservas;
- 11 reservas posicionais espelham os slots titulares;
- 4 vagas livres aceitam qualquer posição oficial;
- titular e reserva não podem se repetir;
- seletores exibem apenas jogadores compatíveis;
- cada tática possui estado separado;
- persistência opcional no `localStorage`;
- botão de limpeza remove titulares e reservas da formação ativa;
- é possível apagar escalações salvas no navegador.

O 4-3-3 Clássico teve o centroavante reposicionado para permanecer integralmente dentro do campo em desktop e mobile.

---

## 10. Scout e ficha individual

### 10.1 Card do jogador

O card editorial inspirado em videogame exibe:

- `Ciclo 2030`;
- situação da avaliação;
- nome do jogador;
- posições curtas, por exemplo `PD - MEI - MCD`;
- clube atual;
- capacidade atual;
- potencial em 2030;
- idade projetada para 2030.

Não exibe:

- ID do atleta;
- idade de 2026;
- posição longa no canto inferior;
- texto `Seleção Brasileira`.

### 10.2 Situações da avaliação

Apresentação pública:

- `Avaliação Completa`;
- `Avaliação Parcial`;
- `Sem Avaliação`.

Contrato interno original pode usar `Completa`, `Parcial` e `Não avaliada`, desde que a camada visual normalize corretamente.

### 10.3 Dados do jogador

O expander chama-se:

```text
Dados do jogador
```

Estrutura atual:

#### Identificação

- nome completo;
- nascimento;
- naturalidade;
- altura;
- pé preferencial.

#### Vínculo profissional

- clube atual;
- empresário;
- no clube desde;
- contrato até;
- opção de contrato;
- última renovação;
- equipador.

Campos vazios não são exibidos.

O antigo bloco `Referência cadastral externa` foi removido da interface pública por ser informação secundária sem utilidade suficiente nessa tela.

### 10.4 Ordem da ficha

Na coluna de dados:

1. Dados do jogador;
2. Valor de mercado;
3. histórico de avaliações, quando disponível.

---

## 11. Avaliações trimestrais

### 11.1 Fonte e chave

A fonte canônica é `avaliacoes_trimestrais_hexa_2030.json`.

Chave lógica:

```text
id_atleta + periodo
```

A primeira avaliação oficial é T2 2026, com data de referência 30/06/2026.

Cada registro contém dados brutos de Vini e Beto:

- capacidade atual;
- potencial 2030;
- observações;
- snapshot de posição;
- snapshot de clube;
- período;
- data de referência.

Médias, saldos, cobertura, divergências e histórico são calculados em Python.

Ausência permanece `null`. Zero é nota válida.

### 11.2 Quadro executivo

O quadro trimestral compartilhado possui:

- Indicador;
- Vini;
- Beto;
- Média.

Indicadores:

- Capacidade atual — desempenho no período;
- Potencial 2030 — projeção para o ciclo.

A coluna de média recebe destaque visual.

A tabela deve:

- ocupar integralmente o cartão;
- não deixar faixa vazia após a última linha;
- manter a coluna destacada até a borda inferior;
- usar `caption`, `scope` e estrutura semântica;
- funcionar em telas estreitas;
- manter leitura linear;
- preservar foco visível.

### 11.3 Resumo individual

Situação ocupa largura completa. Saldo projetado e data de referência ficam abaixo.

Valores e datas não devem quebrar de forma desnecessária.

---

## 12. Tabelas executivas compartilhadas

Desde a RC5.7, todas as tabelas públicas devem usar o componente executivo compartilhado em `hexa_components.py`.

Aplicações:

- quadro trimestral;
- lista de jogadores;
- rankings de capacidade;
- rankings de potencial;
- evolução;
- regressão;
- avaliações parciais;
- leitura consolidada de mercado.

Regras visuais:

- sem `st.dataframe` ou `st.table` nas páginas públicas, salvo decisão posterior explícita;
- conteúdo dinâmico escapado;
- cabeçalho fixo em tabelas longas;
- primeira coluna fixa em tabelas largas;
- rolagem horizontal responsiva;
- rolagem vertical controlada;
- percentuais exibem texto e barra complementar;
- destaque não depende apenas de cor;
- margem inferior da tabela deve ser zero;
- última linha não deve criar borda ou faixa residual.

---

## 13. Valor de mercado

Valor de mercado é referência externa e não representa avaliação esportiva definitiva.

Distinguir sempre:

- valor atual;
- maior valor da carreira;
- diferença absoluta para o pico;
- percentual do pico;
- data do pico;
- data da última atualização.

A seção possui indicadores com espaçamento confortável e uma faixa separada para datas.

A observação:

```text
Valor de mercado é uma referência externa e não equivale à avaliação esportiva do projeto.
```

deve aparecer:

- em itálico;
- com menor peso hierárquico;
- em tamanho `0.75rem`;
- com espaçamento superior;
- separada por divisor sutil.

---

## 14. Tratamento numérico

Normalizar por RegEx e preservar texto original quando útil para auditoria.

Exemplos:

```text
40,00 M. €  → 40.0
175 mil €   → 0.175
1,50 M. €   → 1.5
1,93 m      → 1.93
```

Nunca inferir avaliação esportiva a partir do valor de mercado.

---

## 15. UX, responsividade e acessibilidade

Diretrizes obrigatórias:

- mobile-first;
- contraste compatível com WCAG;
- significado não pode depender somente de cor;
- alvos de toque confortáveis;
- tipografia legível;
- estados vazios claros;
- listas longas pesquisáveis;
- zoom de 200%;
- foco de teclado visível;
- HTML semântico;
- evitar seletores internos frágeis do Streamlit;
- evitar CDN e fontes externas quando houver alternativa nativa;
- testar mentalmente e, quando possível, tecnicamente em Chrome, Firefox, Edge, Brave e Safari.

Larguras mínimas de smoke mobile:

```text
320 px
375 px
390 px
430 px
```

---

## 16. Autenticação, administração e auditoria

A autenticação administrativa usa OIDC nativo do Streamlit quando configurado.

Regras:

- login e logout ficam na barra lateral;
- administrador é validado por allowlist de e-mail;
- menu administrativo aparece somente para usuário autorizado;
- a página administrativa valida autorização novamente;
- ocultar menu não é proteção suficiente;
- Secrets reais nunca devem ser versionados;
- `.streamlit/secrets.example.toml` pode servir como modelo;
- conteúdo público permanece disponível sem login.

A auditoria operacional, quando ativa, usa JSONL separado da fonte canônica.

Limitação conhecida: armazenamento gravado em runtime no Streamlit Community Cloud pode ser efêmero.

---

## 17. Persistência

### 17.1 JSON

A escrita persistente deve:

- usar bloqueio otimista por SHA-256;
- impedir sessão antiga de sobrescrever versão nova;
- gravar de forma atômica;
- manter backup;
- registrar metadados de versão, data UTC e origem;
- não sobrescrever arquivo inválido automaticamente.

JSON não é solução multiusuário definitiva.

### 17.2 Persistência local da escalação

O navegador pode armazenar:

- tática ativa;
- titulares;
- reservas;
- estados separados por formação.

Não armazena:

- avaliações;
- observações;
- mercado;
- dados pessoais.

Limitações:

- não sincroniza entre dispositivos;
- pode ser apagado pelo usuário;
- pode ser bloqueado por política de privacidade;
- depende do navegador.

---

## 18. Protocolo de alteração de código

Antes de implementar:

1. ler todos os arquivos disponibilizados;
2. mapear dependências;
3. explicar brevemente arquitetura e raciocínio;
4. preservar funcionalidades não relacionadas;
5. preservar dados editoriais;
6. entregar arquivos Python completos;
7. gerar ZIP quando mais de um arquivo mudar;
8. atualizar este documento, sem criar vários documentos auxiliares.

Validações recomendadas:

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

Também verificar:

- imports;
- símbolos importados;
- ciclos entre módulos;
- JSONs;
- aliases;
- posições oficiais;
- seis formações;
- 11 titulares por formação;
- regras de convocação;
- inicialização do Streamlit;
- endpoint `/_stcore/health`;
- dependências ausentes;
- hashes dos JSONs antes e depois.

---

## 19. Deploy padrão

### 19.1 Branch

```bash
git checkout main
git pull
git checkout -b tipo/nome-da-alteracao
```

### 19.2 Aplicação

Copiar os arquivos completos para a raiz preservando:

- JSONs canônicos;
- `requirements.txt`;
- `.streamlit/secrets.toml`;
- módulos não relacionados;
- testes existentes.

### 19.3 Validação

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

### 19.4 Publicação

```bash
git add .
git commit -m "tipo: descrição objetiva"
git push -u origin nome-da-branch
```

Abrir Pull Request e fazer merge apenas após testes e smoke manual.

### 19.5 Streamlit Community Cloud

Após o merge:

1. aguardar redeploy automático;
2. abrir `Manage app` se a versão anterior permanecer;
3. usar `Reboot app`;
4. repetir smoke manual.

### 19.6 Rollback

Reverter o commit da release ou hotfix.

JSONs canônicos não precisam de rollback quando não foram alterados.

---

## 20. Smoke manual atual

### Escalação

- campo começa vazio;
- 11 titulares;
- até 15 reservas;
- sem duplicidade;
- compatibilidade posicional;
- persistência por formação;
- limpeza completa;
- CA do 4-3-3 dentro do campo;
- desktop e mobile.

### Scout

- busca vazia por padrão;
- card sem ID e sem idade 2026;
- posições curtas abaixo do nome;
- dados do jogador antes do mercado;
- clube atual no vínculo;
- campos vazios omitidos;
- avaliação completa, parcial e ausente;
- histórico quando houver mais de um período.

### Jogadores

- busca por nome ou clube;
- filtros;
- tabela executiva;
- rolagem horizontal;
- primeira coluna fixa;
- percentuais legíveis.

### Indicadores

- KPIs do período;
- rankings;
- avaliações parciais;
- atletas sem avaliação;
- resumo de mercado;
- tabela executiva de mercado;
- ausência de `NameError`;
- KPI `Atletas com valor` usa `len(mercado)`.

---

## 21. Estado dos dados verificado em 20/07/2026

```text
jogadores_hexa_2030.json
79 jogadores
SHA-256: 1f61c0901c77b7c576ffab02db13a68fbdbe2a7a404585e5a303bd655168f5e8

avaliacoes_trimestrais_hexa_2030.json
79 avaliações
SHA-256: 8e43594f268ac00c2097e056891f05c168f4f73058519051b3641cc9b6b656f2

avaliacoes_trimestrais_atletas_hexa_2030.xlsx
79 atletas
1.580 linhas trimestrais
SHA-256: e5565da0f3cb5fa1b091f4c2b597caebbb16ac9b13fb0a4bb4b296b9fbaa7442
```

Esses hashes são referência temporal e mudam quando houver atualização autorizada.

---

## 22. Histórico consolidado de releases

### RC1 — `1.0.0-rc1`

- arquitetura modular;
- APIs públicas por `__all__`;
- proteção de imports;
- detecção de ciclos;
- smoke em processo novo;
- matriz GitHub Actions Python 3.10–3.14;
- JSONs preservados.

### RC2 — Auditoria

- auditoria operacional em JSONL;
- diff por campo;
- origem e versões registradas;
- separação entre auditoria e histórico editorial.

### RC3 — Autenticação administrativa

- OIDC nativo;
- allowlist;
- menu condicional;
- página protegida;
- identidade disponível para auditoria;
- sem formulário de edição pública.

### RC4 — `1.0.0-rc4-ux-convocacao`

- UX da convocação;
- 11 reservas posicionais e 4 livres;
- ausência de duplicidade;
- estados separados por formação;
- identidade editorial Vini e Beto;
- cabeçalho e responsividade.

### RC5 — Avaliações trimestrais

- nova fonte temporal;
- `id_atleta` estável;
- T2 2026 como primeira avaliação oficial;
- cálculos derivados em Python;
- arquivo preventivo do legado;
- status completa, parcial e não avaliada.

### Hotfix RC5.0.1

Causa:

- entrypoint antigo chamava o novo roteador com argumentos insuficientes.

Correção:

- carregamento da base trimestral;
- chamada nomeada com `menu`, `jogadores`, `base_avaliacoes` e `periodo`.

### RC5.1 — `1.1.1-rc5.1-finalizacao-ux`

- persistência local das escalações;
- reconciliação sem duplicidade;
- indicadores compactos;
- busca melhorada;
- nomenclatura explícita de pico de mercado.

### Hotfix mobile e dados — `1.1.2-hotfix-mobile-dados`

- sidebar com estado automático;
- controle nativo preservado no mobile;
- navegação antes do acesso administrativo;
- correção da apresentação de posições externas;
- remoção pública de nacionalidades.

### RC5.3 — `1.1.3-rc5.3-refinamento-visual`

- escala tipográfica;
- tema em `.streamlit/config.toml`;
- KPIs compactos;
- dados contratuais com `<dl>`;
- remoção de redundâncias;
- alto contraste reforçado.

### RC5.4 — `1.1.4-rc5.4-ajustes-ux`

- correção do CA no 4-3-3;
- remoção da visualização em lista;
- título `Monte a sua convocação`;
- card de jogador;
- status claros;
- remoção de consensos e divergências.

### RC5.4.1 — `1.1.5-rc5.4.1-card-mercado`

- posições curtas abaixo do nome;
- remoção da posição longa;
- remoção de `Seleção Brasileira`;
- mercado movido para baixo dos dados do jogador.

### Hotfix do card — `1.1.6-hotfix-card-perfil`

Causa:

- chamada de `_idade_em_2030`, função inexistente.

Correção:

- uso de `_idade_projetada_2030`;
- normalização correta dos status.

### RC5.5 — `1.1.7-rc5.5-dados-jogador-mercado`

- `Dados externos e contratuais` passou a `Dados do jogador`;
- grupos visuais;
- cartões de mercado;
- melhor hierarquia e espaçamento;
- observação de mercado reduzida.

### RC5.6 — `1.1.8-rc5.6-refino-executivo`

- remoção da referência cadastral externa;
- clube atual no vínculo;
- quadro executivo de avaliação;
- novos nomes da navegação;
- refinamento da observação de mercado.

### RC5.7 — `1.1.9-rc5.7-tabelas-executivas`

- componente compartilhado de tabelas;
- correção da faixa vazia inferior;
- adoção em todas as páginas públicas;
- rolagem e colunas fixas;
- conteúdo escapado.

### Hotfix RC5.7.1 — `1.1.10-hotfix-rc5.7-mercado`

Causa:

- refatoração criou `mercado`, mas o KPI ainda usava `df_mercado`.

Correção:

```python
len(mercado)
```

Proteção:

- teste executa `render_tela_analise()` até a seção de mercado;
- valida KPI e tabela consolidada;
- confirma ausência do nome obsoleto.

---

## 23. Incidentes que devem permanecer como testes de regressão

1. Contrato do entrypoint incompatível com `render_tela`.
2. Função de projeção de idade chamada com nome incorreto.
3. Variável antiga `df_mercado` após migração para lista `mercado`.
4. Centroavante fora dos limites visuais do campo.
5. Faixa vazia abaixo da última linha da tabela.
6. Duplicidade entre titulares e reservas.
7. Sidebar mobile sem controle de reabertura.
8. JSON inválido sobrescrito por mecanismo automático.
9. Posição externa alterando posição editorial.
10. Campo ausente convertido indevidamente em zero.

---

## 24. Fontes técnicas consolidadas

Fontes oficiais consultadas nas releases recentes:

- Streamlit — configuração `config.toml`;
- Streamlit — visão geral de theming;
- Streamlit — customização de fontes;
- Streamlit — `st.expander`;
- Streamlit — `st.markdown`;
- Streamlit — layouts e containers;
- Streamlit — AppTest.

Diretrizes aplicadas:

- usar APIs públicas;
- evitar seletores internos instáveis;
- evitar CDN;
- usar fonte sans-serif incorporada;
- manter HTML semântico;
- validar comportamento na versão fixada em `requirements.txt`.

---

## 25. Arquivos documentais absorvidos e agora obsoletos

Este documento absorve o conteúdo relevante dos seguintes grupos:

```text
README_RC*.md
README_HOTFIX*.md
DEPLOY_RC*.md
DEPLOY_HOTFIX*.md
RELATORIO_TESTES_*.md
FONTES_TECNICAS_*.md
MANIFESTO_SHA256.txt
BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md anterior
```

Também absorve documentação histórica anterior:

```text
INSTRUCOES_GPT.txt
COMO_CONFIGURAR_O_GPT.md
CONTEXTO_PROJETO.md
REGRAS_NEGOCIO_E_DADOS.md
PROMPTS_DE_TESTE.md
RC1_ARQUITETURA.md
RC2_AUDITORIA.md
RC3_AUTH_ADMIN.md
RC4_UX_CONVOCACAO.md
RC5_AVALIACOES_HISTORICO.md
HOTFIX_RC5_ENTRYPOINT.md
RC5_1_FINALIZACAO.md
HISTORICO_REFATORACOES.md
RELATORIO_INTEGRIDADE_DADOS.md
RELATORIO_WCAG.md
```

Após confirmar este arquivo no Git, os documentos acima não precisam permanecer na base de conhecimento.

---

## 26. Limpeza recomendada do repositório

Manter:

```text
BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md
README.md                          # somente se for a página pública do GitHub
requirements.txt
arquivos Python
JSONs canônicos
.streamlit/
tests/
scripts/
```

Remover ou arquivar fora da branch principal:

```text
README_RC*.md
README_HOTFIX*.md
DEPLOY_RC*.md
DEPLOY_HOTFIX*.md
RELATORIO_TESTES_*.md
FONTES_TECNICAS_*.md
MANIFESTO_SHA256.txt
pastas temporárias de staging, verify e pacotes de release
```

Comando sugerido, executado somente após substituir e revisar o arquivo canônico:

```bash
git rm --ignore-unmatch \
  'README_RC*.md' \
  'README_HOTFIX*.md' \
  'DEPLOY_RC*.md' \
  'DEPLOY_HOTFIX*.md' \
  'RELATORIO_TESTES_*.md' \
  'FONTES_TECNICAS_*.md' \
  'MANIFESTO_SHA256.txt'
```

Não remover:

- `README.md` público, se existir;
- `requirements.txt`;
- código;
- testes;
- JSONs;
- Secrets locais;
- arquivos de configuração.

---

## 27. Conjunto mínimo para a base de conhecimento do GPT

Enviar somente:

1. `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`;
2. arquivos Python atuais;
3. `jogadores_hexa_2030.json`;
4. `avaliacoes_trimestrais_hexa_2030.json`;
5. `enriquecimentos_tm.json`;
6. `requirements.txt`;
7. arquivos de configuração estritamente necessários.

Não enviar os antigos documentos de release.

---

## 28. Estado de validação desta consolidação

Realizado:

- leitura da base consolidada anterior;
- leitura dos documentos de release e hotfix até RC5.7.1;
- deduplicação conceitual de arquitetura, deploy, testes e histórico;
- conferência da versão atual no código;
- conferência dos nomes atuais dos menus;
- validação dos três JSONs;
- cálculo dos hashes atuais;
- verificação da presença das regras críticas;
- criação de um único arquivo canônico.

Não realizado:

- alteração do repositório Git do usuário;
- exclusão real dos documentos na branch principal;
- execução do aplicativo;
- smoke visual;
- deploy no Streamlit Community Cloud.

---

## 29. Resumo executivo

A documentação permanente do projeto passa a ser **um único arquivo canônico**.

Toda nova release deve:

- atualizar este arquivo;
- evitar README, DEPLOY e relatório separados;
- manter manifesto apenas como artefato temporário;
- preservar código, JSONs e testes em arquivos próprios;
- registrar de forma compacta a mudança, os testes e o deploy no histórico deste documento.

---

## 23. Atualização cadastral por imagens — 20/07/2026

### 23.1 Escopo

Foram processadas 20 fichas externas fornecidas pelo usuário.

- 18 atletas foram adicionados com IDs `ATH-0062` a `ATH-0079`;
- Kauã Prates (`ATH-0046`) e João Victor (`ATH-0045`) já existiam e foram deduplicados;
- os dois registros existentes receberam somente atualização do carimbo de auditoria externo;
- nenhuma nota, posição editorial, grupo, tipo ou texto da conversa de atleta existente foi substituído;
- novos atletas receberam grupo e tipo neutros `Observação`, notas editoriais `0.0` e textos editoriais vazios;
- dados externos foram armazenados em campos `tm_`;
- posições externas foram convertidas para o vocabulário oficial apenas nos campos táticos iniciais dos novos atletas.

### 23.2 Atletas adicionados

Léo Jardim, Carlos Augusto, Cuiabano, Léo Pereira, Dodô, Gerson, Gabriel Sara, Lucas Paquetá, Marcos Leonardo, Kaio Jorge, Sávio, Henrique Menke, Vitor Reis, Igor Felisberto, Zé Lucas, Lucca, Riquelme Fillipi, Pedrinho.

### 23.3 Arquivos alterados

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `avaliacoes_trimestrais_atletas_hexa_2030.xlsx`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

Nenhum arquivo Python e nenhuma dependência foram alterados. O site incorpora os atletas automaticamente porque carrega os JSONs canônicos.

### 23.4 Estado resultante

- 79 atletas no cadastro;
- 79 registros oficiais em `2026-T2`;
- 1.580 linhas na grade trimestral de 2026 a 2030;
- planilha reconstruída a partir dos JSONs canônicos, com fórmulas, validações, filtros e painel.

### 23.5 Testes

A entrega executa validação estrutural dos JSONs, preservação dos campos protegidos, unicidade de nomes e IDs, vocabulário de posições, consistência entre cadastro e avaliações, compilação dos Python disponibilizados, imports possíveis no conjunto recebido, regras táticas e verificação estrutural da planilha.

O smoke completo do Streamlit depende dos módulos do repositório que não foram disponibilizados nesta conversa.

---

## 30. Atualização cadastral final por imagens — 20/07/2026

### 30.1 Escopo

Foram processadas 10 fichas adicionais fornecidas pelo usuário.

- 9 atletas foram adicionados com IDs `ATH-0080` a `ATH-0088`;
- Lucca (`ATH-0077`) já estava cadastrado e foi deduplicado;
- nenhum campo editorial ou tático de atleta existente foi sobrescrito;
- os novos atletas receberam estado editorial neutro, sem notas ou opiniões inventadas;
- dados externos foram isolados em campos `tm_`;
- posições externas foram convertidas para o vocabulário oficial somente na criação dos novos registros.

### 30.2 Atletas adicionados

Pedro Cobra, Pedro Gabriel, Arthur Dias, João Pedro Chermont, Rayan Lucas, Riquelme Felipe, Abner Vinícius, Lucas Piton, Ângelo.

### 30.3 Estado resultante

- 88 atletas no cadastro;
- 88 registros oficiais em `2026-T2`;
- 1,760 linhas trimestrais entre 2026 e 2030;
- aplicativo atualizado por meio dos JSONs canônicos, sem mudança em Python;
- planilha ampliada preservando fórmulas, validações, filtros e painel.

### 30.4 Arquivos alterados

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `avaliacoes_trimestrais_atletas_hexa_2030.xlsx`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

### 30.5 Validação

Foram verificados JSON, IDs, posições oficiais, preservação dos campos protegidos,
correspondência entre cadastro e avaliações, fórmulas da planilha, regras táticas
e compilação dos arquivos Python disponibilizados. O smoke completo do
Streamlit continua condicionado à disponibilidade de todos os módulos do
repositório e da dependência `streamlit` no ambiente de execução.

---

## 31. Grade interativa e densidade compacta — 20/07/2026

### 31.1 Escopo

- tabelas de dados públicas migradas para AG Grid Community por meio de
  `render_grade_dados()` em `hexa_components.py`;
- nenhuma página importa ou chama `streamlit-aggrid` diretamente;
- ordenação simples e múltipla, filtros por coluna, pesquisa geral,
  redimensionamento, movimentação, fixação e download CSV foram habilitados;
- edição de células permanece desabilitada;
- filtros de texto, número e data usam somente recursos Community;
- o filtro categórico Enterprise não foi habilitado;
- valores numéricos e datas permanecem tipados para ordenação correta;
- a primeira coluna pode permanecer fixa nas grades largas;
- altura padrão das linhas reduzida para 42 px, com opção acessível
  `Confortável` de 50 px;
- quadros-resumo pequenos, como as duas linhas da avaliação individual,
  permanecem em HTML sem barra de ferramentas;
- a tabela de mercado passou a exibir `Empresário`, lido do campo externo
  `tm_empresario`, com estado `Não informado` quando ausente;
- nenhum JSON canônico foi alterado.

### 31.2 Arquivos alterados

- `caminho_hexa_2030.py`;
- `hexa_components.py`;
- `hexa_config.py`;
- `hexa_pages.py`;
- `hexa_styles.py`;
- `requirements.txt`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

### 31.3 Arquitetura

`hexa_pages.py` declara dados, colunas, chaves estáveis e intenção visual.
Toda dependência de AG Grid, tipagem, formatação, localização, densidade,
tema, acessibilidade e fallback HTML fica encapsulada em
`hexa_components.py`.

O componente opera em modo somente leitura e define explicitamente
`enable_enterprise_modules=False`. Na ausência da dependência, a aplicação
preserva a leitura por meio da tabela HTML compacta.

### 31.4 Deploy

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
streamlit run caminho_hexa_2030.py
```

Após o merge na branch principal, aguardar o redeploy do Streamlit Community
Cloud e executar smoke em desktop e mobile. Caso a dependência não seja
instalada no primeiro build, usar `Manage app` → `Reboot app`.

### 31.5 Smoke manual obrigatório

- ordenar cada tipo de coluna;
- usar `Shift` para multiordenação;
- filtrar texto, número e data;
- limpar filtros;
- pesquisar na barra da grade;
- ocultar, mover, redimensionar e fixar colunas;
- exportar CSV;
- validar a coluna `Empresário`;
- alternar densidade Compacta/Confortável;
- validar teclado e foco;
- validar Chrome, Firefox, Edge, Brave, Safari macOS, Safari iOS e
  Chrome Android;
- confirmar que nenhuma célula é editável;
- confirmar hashes dos JSONs antes e depois.

### 31.6 Testes executados nesta entrega

- compilação individual dos 12 arquivos Python disponibilizados;
- instalação isolada de `streamlit==1.59.2`, `pandas==2.3.3` e
  `streamlit-aggrid==1.2.1.post2`;
- importação real das três dependências e conferência das versões;
- importação dos módulos alterados com stubs apenas para os cinco módulos
  locais ausentes no conjunto recebido;
- smoke do componente com a API real de `streamlit-aggrid`;
- `AppTest` do componente sem exceções;
- inicialização de servidor Streamlit do componente e health check HTTP 200;
- validação de sintaxe, via Node.js, dos oito callbacks JavaScript gerados;
- testes de configuração das densidades Compacta e Confortável;
- confirmação de `enable_enterprise_modules=False` e células não editáveis;
- confirmação dos filtros Community de texto, número e data;
- conversão de datas DD/MM/AAAA para ISO antes da ordenação;
- teste do enriquecimento de `Empresário`, sem mutar os registros de entrada;
- validação das seis formações, todas com 11 slots e sem erros táticos;
- leitura JSON dos dois arquivos canônicos fornecidos;
- comparação SHA-256 antes e depois, sem alteração dos JSONs.

### 31.7 Pontos não validados e impedimentos encontrados

- o smoke do aplicativo completo não foi concluído porque o conjunto local
  recebido não contém `hexa_messages.py`, `hexa_models.py`,
  `hexa_persistencia_local.py`, `hexa_selectors.py` e `hexa_session.py`;
- os JSONs fornecidos são sintaticamente válidos, mas não formam um par
  consistente neste ambiente: o cadastro contém 61 atletas e a base
  trimestral contém 88 avaliações; a validação encontrou 27 IDs
  `ATH-0062` a `ATH-0088` ausentes no cadastro recebido;
- nenhuma tentativa de reparar, sobrescrever ou combinar automaticamente
  esses JSONs foi realizada;
- inspeção visual real em Chrome, Firefox, Edge, Brave e Safari não foi
  executada;
- deploy e smoke no Streamlit Community Cloud não foram executados.



---

## 32. Hotfix de ordenação monetária em Jogadores — 20/07/2026

### 32.1 Problema corrigido

Na seção **Jogadores**, as colunas `Valor atual` e `Pico de mercado` chegavam à
grade como textos já formatados, por exemplo `€ 900 mil`, `€ 9,00 mi` e
`€ 80,00 mi`. Por isso, a AG Grid aplicava ordenação lexicográfica, colocando
`€ 900 mil` antes de valores como `€ 80,00 mi`.

As demais seções já enviavam valores monetários numéricos e não apresentavam
o defeito.

### 32.2 Solução

- `hexa_pages.py` passou a reconstruir somente os dois campos monetários da
  tabela de Jogadores a partir dos valores canônicos do atleta;
- os campos são enviados à grade como números em milhões de euros;
- a apresentação continua usando o formato brasileiro por meio de
  `moeda_milhoes`;
- filtros e ordenação passam a ser numéricos;
- registros sem valor válido permanecem nulos;
- nenhum JSON foi alterado;
- nenhuma outra tabela ou regra funcional foi modificada.

### 32.3 Arquivos alterados

- `hexa_pages.py`;
- `hexa_config.py`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

### 32.4 Testes executados

- compilação de todos os arquivos Python disponibilizados;
- teste unitário da conversão dos valores de `0,9`, `7`, `8`, `9`, `70`,
  `75`, `80` e `140` milhões;
- confirmação de ordenação numérica crescente e decrescente;
- confirmação de que `€ 900 mil` é tratado como `0.9`;
- confirmação de que valores ausentes permanecem `None`;
- confirmação de que os registros de entrada e os JSONs não são mutados;
- inspeção estática das colunas para garantir `formato="moeda_milhoes"`.

### 32.5 Pontos não validados

O smoke visual do aplicativo completo e a validação em navegadores permanecem
dependentes do repositório completo, incluindo os módulos locais não presentes
no conjunto recebido.

---

## 24. Correções pós-Fase 0 — baseline reproduzível

Data: 21/07/2026.

### 24.1 Objetivo

Corrigir os débitos encontrados no diagnóstico da Fase 0 antes do início da
Fase 1 de segurança.

### 24.2 Alterações

- `hexa_persistencia_local.py` passou a tratar falhas de registro ou execução
  do componente opcional `components.v2`, mantendo o restante do aplicativo
  operacional quando `localStorage` não estiver disponível;
- o smoke foi atualizado e movido para `scripts/rc1_smoke.py`;
- foi removida a dependência obsoleta de `hexa_accessibility`;
- o smoke passou a validar os três JSONs obrigatórios;
- `config.toml` foi movido para `.streamlit/config.toml`;
- `secrets.example.toml` foi movido para
  `.streamlit/secrets.example.toml`;
- o workflow foi movido para `.github/workflows/ci.yml`;
- o CI passou a compilar, validar JSON, executar testes de regressão,
  executar o smoke e validar o endpoint de saúde do Streamlit;
- Python 3.14 foi removido da matriz obrigatória até haver compatibilidade
  comprovada de todas as dependências;
- foi criada a suíte `tests/test_phase0.py`.

### 24.3 Arquivos alterados ou adicionados

- `hexa_persistencia_local.py`;
- `scripts/rc1_smoke.py`;
- `tests/test_phase0.py`;
- `.streamlit/config.toml`;
- `.streamlit/secrets.example.toml`;
- `.github/workflows/ci.yml`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

### 24.4 Risco residual

A persistência no navegador é opcional. Quando o componente local falha,
a convocação permanece funcional durante a sessão, mas não é restaurada após
o fechamento do navegador.

A validação visual manual em Chrome, Firefox, Edge, Brave e Safari permanece
como etapa separada, pois o CI cobre inicialização e contratos, não renderização
pixel a pixel em todos os navegadores.

---

## Fase 1 — endurecimento de segurança (21/07/2026)

### Escopo executado

- validação programática de claims OIDC, incluindo `sub`, `iat`, `exp` e `email_verified`;
- tolerância configurável de relógio para tokens;
- autorização centralizada por permissões;
- allowlist administrativa por e-mail normalizado e `sub` estável;
- edição administrativa mantida explicitamente desabilitada;
- preservação do ator nos eventos de auditoria de alteração e em sua releitura;
- redução dos detalhes de erros exibidos ao público;
- CORS e XSRF explicitamente habilitados;
- limite de upload e mensagens reduzido;
- toolbar pública em modo de visualização;
- verificação local contra arquivos sensíveis e padrões comuns de segredos;
- `.gitignore` ampliado;
- `SECURITY.md` criado;
- Dependabot configurado para pip e GitHub Actions;
- workflow com permissões mínimas, concorrência controlada, timeout e actions fixadas por SHA;
- Bandit e `pip-audit` adicionados ao CI.

### Arquivos alterados ou criados

- `caminho_hexa_2030.py`;
- `hexa_admin.py`;
- `hexa_audit.py`;
- `hexa_auth.py`;
- `hexa_config.py`;
- `.gitignore`;
- `.streamlit/config.toml`;
- `.streamlit/secrets.example.toml`;
- `.github/workflows/ci.yml`;
- `.github/dependabot.yml`;
- `scripts/security_check.py`;
- `tests/test_security_phase1.py`;
- `SECURITY.md`;
- este documento.

### Testes realizados

- compilação de todos os arquivos Python;
- 13 testes unitários e de regressão;
- smoke de imports e contratos;
- verificação local do repositório;
- Bandit;
- AppTest nas quatro páginas públicas;
- inicialização real do Streamlit e health check;
- validação dos três JSONs preservados.

### Testes não concluídos neste ambiente

O `pip-audit` foi instalado e chamado, mas a consulta ao serviço de vulnerabilidades não pôde ser concluída porque o ambiente desta execução não resolveu `pypi.org`. O job permanece obrigatório no GitHub Actions, onde deve ser confirmado no Pull Request.

### Configuração de Secrets

Além da allowlist por e-mail, recomenda-se preencher `administradores.subjects` com o claim `sub` estável de cada administrador. Produção e homologação devem usar credenciais e callbacks separados.

---

## Fase 2 — suíte de regressão e ajuste da área administrativa

### Estado

Versão: `1.3.0-regression-phase2`.

A área de login administrativo foi reposicionada abaixo de **Radar do projeto**
na barra lateral e renomeada para **Área administrativa em construção**.

Falhas de configuração da seção `[administradores]` não são mais exibidas ao
visitante. O servidor registra apenas a mensagem operacional:

```text
Secrets sem seção [administradores].
```

A administração permanece sem formulários de edição e a permissão
`EDITAR_DADOS` continua negada.

### Regressões automatizadas

A suíte `tests/test_regression_phase2.py` protege:

- projeção de idade entre o ano-base e 2030;
- diferença entre ausência de nota e nota zero;
- normalização de valores de mercado e altura;
- preservação dos campos editoriais frente a enriquecimentos externos;
- não sobrescrita de JSON irrecuperável;
- remoção de duplicidades entre titulares e reservas;
- cobertura de centroavantes nas formações que exigem a função;
- inicialização das quatro páginas públicas;
- posição da área administrativa abaixo do Radar;
- ausência de detalhes de Secrets na interface pública.

### Arquivos alterados

- `caminho_hexa_2030.py`;
- `hexa_auth.py`;
- `hexa_config.py`;
- `tests/test_regression_phase2.py`;
- `tests/test_security_phase1.py`;
- `BASE_CONHECIMENTO_HEXA_2030_CONSOLIDADA.md`.

### Testes realizados

- compilação de todos os arquivos Python;
- 24 testes unitários e de regressão;
- smoke de imports e contratos;
- verificação de segurança do repositório;
- Bandit;
- AppTest nas quatro páginas públicas;
- inicialização real do Streamlit;
- health check HTTP.

Todos os testes acima foram aprovados.

### Testes não realizados nesta execução

- inspeção visual manual em navegadores reais;
- teste manual em dispositivo móvel;
- `pip-audit` online, pois não houve mudança de dependências e o ambiente de
  execução não possui conectividade confiável com o índice externo.

A validação manual multibrowser e mobile da versão anterior foi informada pelos
responsáveis do projeto, mas não foi repetida tecnicamente nesta execução.

