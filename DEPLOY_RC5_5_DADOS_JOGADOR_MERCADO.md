# Deploy — RC5.5 Dados do jogador e valor de mercado

## 1. Criar a branch

```bash
git checkout main
git pull
git checkout -b rc5-5-dados-jogador-mercado
```

## 2. Aplicar o pacote

Extraia o ZIP na raiz do repositório.

Arquivos alterados:

```text
hexa_components.py
hexa_pages.py
hexa_styles.py
hexa_config.py
tests/test_rc5_5_dados_jogador_mercado.py
```

Não substitua nem remova:

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `enriquecimentos_tm.json`;
- `.streamlit/secrets.toml`;
- `requirements.txt`;
- os demais módulos `hexa_*.py`.

## 3. Validar localmente

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

## 4. Smoke manual obrigatório

### Dados do jogador

1. Abra Alexsandro, Allan e um atleta com campos contratuais incompletos.
2. Confirme o título **Dados do jogador**.
3. Confirme os grupos **Identificação**, **Vínculo profissional** e
   **Referência cadastral externa**.
4. Confirme que campos vazios não aparecem.
5. Confirme que listas de posições externas aparecem como texto separado por
   vírgulas.
6. Teste em 320, 375, 390 e 430 px e com zoom de 200%.

### Valor de mercado

1. Confirme quatro cartões de indicadores com espaçamento uniforme.
2. Confirme que as datas ficam em uma faixa separada.
3. Confirme que a observação está menor e em itálico.
4. Confirme que o conteúdo não quebra horizontalmente no mobile.
5. Teste alto contraste e navegação por teclado.

## 5. Publicar

```bash
git add hexa_components.py hexa_pages.py hexa_styles.py hexa_config.py   tests/test_rc5_5_dados_jogador_mercado.py   README_RC5_5_DADOS_JOGADOR_MERCADO.md   DEPLOY_RC5_5_DADOS_JOGADOR_MERCADO.md   RELATORIO_TESTES_RC5_5_DADOS_JOGADOR_MERCADO.md   FONTES_TECNICAS_RC5_5.md MANIFESTO_SHA256.txt

git commit -m "feat: refina dados do jogador e valor de mercado"
git push -u origin rc5-5-dados-jogador-mercado
```

Abra o Pull Request e faça o merge somente após a suíte completa e o smoke
manual.

## 6. Streamlit Community Cloud

Após o merge:

1. aguarde o redeploy automático;
2. abra `Manage app` se a versão antiga continuar ativa;
3. use `Reboot app`;
4. execute o smoke manual.

## Rollback

Reverta o commit da RC5.5. Nenhum JSON precisa de rollback.
