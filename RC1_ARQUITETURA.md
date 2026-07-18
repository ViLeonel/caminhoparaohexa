# RC1 — Arquitetura Base

## Objetivo

Consolidar o núcleo técnico antes de novas funcionalidades. Esta versão
candidata preserva integralmente os dados editoriais e táticos e protege
os contratos públicos entre módulos.

## Identificação

- Versão: `1.0.0-rc1`
- Entrypoint: `caminho_hexa_2030.py`
- Persistência atual: JSON por `JsonJogadoresRepository`
- Python-alvo: 3.10 a 3.14
- Dependências fixadas: `streamlit==1.59.2`, `pandas==2.3.3`

## Garantias adicionadas

- APIs públicas declaradas por `__all__`.
- Teste exato do import crítico usado pelo entrypoint.
- Verificação estática de símbolos importados.
- Detecção automática de ciclos entre módulos locais.
- Smoke test em processo Python novo.
- Validação de sintaxe com gramática Python 3.10.
- Workflow GitHub Actions com matriz Python 3.10–3.14.
- Arquivos operacionais excluídos da release e do Git.
- Remoção de imports comprovadamente não utilizados.
- JSONs canônicos preservados sem alterações.

## Comandos locais

```bash
python -m pip install -r requirements.txt
python -m compileall -q .
python -m unittest discover -s tests -v
python scripts/rc1_smoke.py
streamlit run caminho_hexa_2030.py
```

## Streamlit Community Cloud

O `requirements.txt` deve permanecer na raiz, junto do entrypoint.
Para maior previsibilidade, use Python 3.12 na criação de um novo app.
A versão de Python de um app existente só pode ser alterada excluindo e
recriando o deploy com a versão desejada nas configurações avançadas.

## Limites desta validação

A matriz 3.10–3.14 foi configurada no GitHub Actions, mas apenas o runtime
disponível no ambiente de geração foi executado localmente. A confirmação
real das cinco versões ocorrerá quando o workflow rodar no GitHub.
