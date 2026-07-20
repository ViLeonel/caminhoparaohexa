# Deploy — RC5.4 Ajustes de UX

## 1. Criar a branch

```bash
git checkout main
git pull
git checkout -b rc5-4-ajustes-ux
```

## 2. Aplicar o pacote

Extraia o ZIP na raiz do repositório, preservando a pasta `tests/`.

Arquivos substituídos:

```text
hexa_avaliacoes.py
hexa_components.py
hexa_config.py
hexa_pages.py
hexa_styles.py
hexa_taticas.py
```

Arquivo adicionado:

```text
tests/test_rc5_4_ajustes_ux.py
```

Não apague nem substitua:

```text
jogadores_hexa_2030.json
avaliacoes_trimestrais_hexa_2030.json
enriquecimentos_tm.json
requirements.txt
.streamlit/config.toml
.streamlit/secrets.toml
```

## 3. Revisar as diferenças

```bash
git status
git diff --stat
git diff -- jogadores_hexa_2030.json
git diff -- avaliacoes_trimestrais_hexa_2030.json
git diff -- enriquecimentos_tm.json
```

Os três comandos de `git diff` para JSON devem ficar vazios.

## 4. Validar no repositório completo

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

## 5. Smoke manual obrigatório

### Campo de Jogo

Teste o `4-3-3 Clássico` em desktop e em 320, 375, 390 e 430 px:

1. confirme o título `Monte a sua convocação`;
2. confirme que não existe seletor `Campo | Lista`;
3. selecione um centroavante;
4. confirme que o card inteiro fica dentro do campo;
5. teste janela baixa, rolagem, orientação horizontal e zoom de 200%;
6. confirme que as demais posições e formações continuam funcionais.

### Ficha individual

Abra um atleta com avaliação completa, um parcial e um sem avaliação:

1. confirme o novo card visual;
2. confira clube, capacidade, potencial e idade em 2030;
3. confirme que ID e idade de 2026 não aparecem;
4. confirme os rótulos `Avaliação Completa`, `Avaliação Parcial` e
   `Sem Avaliação`;
5. confirme que saldo e data não quebram em duas linhas.

### Análises & Mercado

1. confirme que rankings, avaliações parciais, não avaliados e mercado continuam;
2. confirme que `Consensos e divergências` não aparece;
3. confira os indicadores do período e a tabela de mercado.

### Regressão geral

- navegue pelas quatro páginas;
- teste alto contraste;
- teste sidebar mobile;
- confira persistência, limpeza e restauração da convocação;
- confirme ausência de jogadores duplicados entre titulares e reservas.

## 6. Commit e push

```bash
git add   hexa_avaliacoes.py   hexa_components.py   hexa_config.py   hexa_pages.py   hexa_styles.py   hexa_taticas.py   tests/test_rc5_4_ajustes_ux.py   README_RC5_4_AJUSTES_UX.md   DEPLOY_RC5_4_AJUSTES_UX.md   RELATORIO_TESTES_RC5_4_AJUSTES_UX.md   FONTES_TECNICAS_RC5_4.md   MANIFESTO_SHA256.txt

git commit -m "feat: ajusta campo, ficha e analises da RC5.4"
git push -u origin rc5-4-ajustes-ux
```

Abra um Pull Request e faça o merge somente após a suíte completa e o smoke
manual.

## 7. Streamlit Community Cloud

1. mantenha `caminho_hexa_2030.py` como **Main file path**;
2. preserve os Secrets OIDC;
3. aguarde o deploy automático após o merge;
4. caso a versão anterior permaneça ativa, abra `Manage app` e use `Reboot app`;
5. acompanhe os logs;
6. repita o smoke de campo, ficha e análises.

## Rollback

```bash
git revert <hash-do-merge>
git push
```

Depois use `Reboot app` no Streamlit Community Cloud. Nenhum rollback de JSON é
necessário, pois este pacote não contém nem modifica dados.
