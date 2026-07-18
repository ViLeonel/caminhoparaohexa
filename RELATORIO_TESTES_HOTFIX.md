# Relatório de testes — Hotfix RC5.0.1

## Causa reproduzida

O traceback enviado mostra uma integração parcial:

```text
hexa_pages.render_tela(menu, jogadores, base_avaliacoes, periodo)
```

passou a exigir quatro argumentos na RC5, mas o entrypoint publicado ainda
executava:

```text
render_tela(menu, jogadores)
```

A falha ocorre no roteamento, antes da renderização das telas.

## Correção testada

O hotfix restaura o entrypoint temporal completo e usa argumentos nomeados:

```python
render_tela(
    menu=menu,
    jogadores=jogadores,
    base_avaliacoes=base_avaliacoes,
    periodo=periodo,
)
```

## Testes executados

### Compilação

```bash
python -m compileall -q .
```

Resultado: aprovado, código de saída 0.

### Suíte automatizada

```bash
python -m unittest discover -s tests -v
```

Resultado: **24 testes executados e 24 aprovados**.

A suíte inclui:

- três testes específicos do contrato do entrypoint;
- integridade das avaliações T2 2026;
- regressão dos indicadores;
- saldo negativo;
- avaliação parcial;
- histórico temporal;
- append-only;
- convocação posicional;
- ausência de uso público das avaliações legadas.

### Streamlit AppTest

O entrypoint corrigido foi iniciado com `streamlit.testing.v1.AppTest`.

Resultado:

- exceções Streamlit: **0**;
- controles de rádio detectados: 2;
- seletores detectados: 29.

### JSON

Arquivos lidos e validados por `json.loads` no workspace integrado:

- `jogadores_hexa_2030.json`: 61 atletas;
- `avaliacoes_trimestrais_hexa_2030.json`: 61 avaliações;
- arquivo legado: 61 atletas arquivados.

Nenhum JSON foi modificado ou incluído no hotfix.

## Aviso do ambiente de testes

O subprocesso registrou um aviso isolado do aquecimento interno de
`artifact_tool` (`hydrateCrdtFromProto`). Esse aviso pertence ao ambiente de
geração de artefatos, não ao aplicativo Streamlit. Os comandos terminaram com
código 0 e o AppTest não encontrou exceções.

## Não executado

- deploy real no Streamlit Community Cloud;
- teste nos navegadores Chrome, Firefox, Edge, Brave e Safari;
- autenticação OIDC real;
- inspeção dos logs após o commit no repositório do usuário.
