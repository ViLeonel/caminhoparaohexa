# Deploy — RC5.6 Refinamento executivo

## 1. Criar a branch

```bash
git checkout main
git pull
git checkout -b rc5-6-refino-executivo
```

## 2. Aplicar o pacote

Extraia o ZIP na raiz do repositório.

Arquivos alterados:

```text
hexa_components.py
hexa_pages.py
hexa_styles.py
hexa_config.py
tests/test_rc5_6_refino_executivo.py
README_RC5_6_REFINO_EXECUTIVO.md
DEPLOY_RC5_6_REFINO_EXECUTIVO.md
RELATORIO_TESTES_RC5_6_REFINO_EXECUTIVO.md
MANIFESTO_SHA256.txt
```

Não substitua nem apague:

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `enriquecimentos_tm.json`;
- `.streamlit/secrets.toml`;
- `requirements.txt`;
- os demais módulos `hexa_*.py`.

## 3. Validar no repositório completo

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

## 4. Smoke manual obrigatório

### Scout
1. Abra Alexsandro e confirme que `Referência cadastral externa` não aparece.
2. Confirme `Clube atual: LOSC Lille` em `Vínculo profissional`.
3. Confirme que campos vazios permanecem omitidos.
4. Confirme que `Dados do jogador` continua antes de `Valor de mercado`.

### Valor de mercado
1. Confirme o espaçamento entre as datas e a observação.
2. Confirme que a observação está em itálico e visualmente menor.
3. Teste em 320, 375, 390 e 430 px.

### Avaliação trimestral
1. Confirme o novo quadro executivo.
2. Confirme as colunas Indicador, Vini, Beto e Média.
3. Confirme a média em destaque.
4. Teste avaliações completas, parciais e sem notas.
5. Teste zoom de 200% e navegação por teclado.

### Navegação
Confirme os quatro nomes:

```text
Escalação
Scout
Jogadores
Indicadores
```

## 5. Publicar

```bash
git add hexa_components.py hexa_pages.py hexa_styles.py hexa_config.py   tests/test_rc5_6_refino_executivo.py   README_RC5_6_REFINO_EXECUTIVO.md   DEPLOY_RC5_6_REFINO_EXECUTIVO.md   RELATORIO_TESTES_RC5_6_REFINO_EXECUTIVO.md   MANIFESTO_SHA256.txt

git commit -m "feat: refina dados, avaliações e navegação"
git push -u origin rc5-6-refino-executivo
```

Abra o Pull Request e faça o merge somente após os testes e o smoke manual.

## 6. Streamlit Community Cloud

Após o merge:

1. aguarde o redeploy automático;
2. se necessário, abra `Manage app`;
3. selecione `Reboot app`;
4. repita o smoke manual.

## Rollback

Reverta o commit da RC5.6. Nenhum JSON canônico precisa de rollback.
