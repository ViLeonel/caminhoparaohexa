# Hotfix RC5.0.1 — Sincronização do entrypoint

## Causa confirmada

O deploy combinou o `hexa_pages.py` da RC5, cujo roteador exige:

- `menu`;
- `jogadores`;
- `base_avaliacoes`;
- `periodo`;

com um `caminho_hexa_2030.py` anterior à RC5, que ainda chamava:

```python
render_tela(menu, jogadores)
```

O resultado foi:

```text
TypeError: render_tela() missing 2 required positional arguments:
'base_avaliacoes' and 'periodo'
```

Não há evidência, neste traceback, de falha nos JSONs, nas notas ou nas regras
trimestrais. A aplicação parou antes de renderizar a tela principal.

## Correção

O entrypoint completo da RC5 foi restaurado. Ele agora:

1. carrega `jogadores_hexa_2030.json`;
2. carrega `avaliacoes_trimestrais_hexa_2030.json`;
3. valida os períodos disponíveis;
4. obtém o período ativo;
5. chama o roteador com argumentos nomeados:

```python
render_tela(
    menu=menu,
    jogadores=jogadores,
    base_avaliacoes=base_avaliacoes,
    periodo=periodo,
)
```

Argumentos nomeados tornam o contrato explícito e reduzem o risco de nova
regressão por ordem ou quantidade de parâmetros.

## Arquivos

- `caminho_hexa_2030.py`: arquivo completo corrigido;
- `tests/test_hotfix_rc5_entrypoint.py`: regressão estática do contrato.

## Aplicação

Copie `caminho_hexa_2030.py` para a raiz do repositório, substituindo o arquivo
atual. Copie também o teste para `tests/`.

Depois execute:

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

Faça commit, push, aguarde o deploy e use **Reboot app** apenas se a instância
não reiniciar automaticamente.

## Smoke após deploy

Confirme:

- a aplicação abre sem `TypeError`;
- a barra lateral mostra `T2 2026`;
- a data de referência mostra `30/06/2026`;
- as quatro páginas abrem;
- os dados trimestrais aparecem;
- os logs não repetem a chamada legada.

## Rollback

O rollback consiste em reverter o commit do hotfix. Não altere nem restaure
arquivos JSON para corrigir este erro, pois a causa está no entrypoint.
