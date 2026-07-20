# Deploy — Hotfix RC5.7.1 Mercado

## 1. Criar a branch

```bash
git checkout main
git pull
git checkout -b hotfix/rc5-7-mercado-nameerror
```

## 2. Aplicar o pacote

Extraia o ZIP na raiz do repositório.

Arquivos de produção:

```text
hexa_components.py
hexa_pages.py
hexa_styles.py
hexa_config.py
```

Arquivos de teste:

```text
tests/test_rc5_6_refino_executivo.py
tests/test_rc5_7_tabelas_executivas.py
tests/test_hotfix_rc57_mercado.py
```

Não apague nem substitua:

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `enriquecimentos_tm.json`;
- `.streamlit/secrets.toml`;
- os demais módulos `hexa_*.py`;
- `requirements.txt`.

## 3. Validar localmente

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
streamlit run caminho_hexa_2030.py
```

## 4. Smoke manual obrigatório

1. Abra **Indicadores**.
2. Role até **Leitura de mercado**.
3. Confirme que o bloco **Resumo de mercado** exibe a quantidade de atletas.
4. Confirme que a tabela consolidada de mercado é renderizada.
5. Navegue para **Escalação**, **Scout** e **Jogadores**.
6. Confirme que as tabelas executivas da RC5.7 permanecem intactas.
7. Repita em desktop e em 320, 375, 390 e 430 px.

## 5. Publicar

```bash
git add hexa_components.py hexa_pages.py hexa_styles.py hexa_config.py \
  tests/test_rc5_6_refino_executivo.py \
  tests/test_rc5_7_tabelas_executivas.py \
  tests/test_hotfix_rc57_mercado.py \
  README_HOTFIX_RC5_7_1_MERCADO.md \
  DEPLOY_HOTFIX_RC5_7_1_MERCADO.md \
  RELATORIO_TESTES_HOTFIX_RC5_7_1_MERCADO.md \
  MANIFESTO_SHA256.txt

git commit -m "fix: corrige NameError no resumo de mercado"
git push -u origin hotfix/rc5-7-mercado-nameerror
```

Após o merge, use **Manage app → Reboot app** se o Streamlit Community Cloud
não reiniciar automaticamente.
