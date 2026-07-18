# RC2 — Histórico estruturado de alterações

## Escopo

Esta release adiciona auditoria operacional fora do JSON canônico.

## Arquivos

- `hexa_audit.py`: modelos, diff e repositório JSONL.
- `auditoria_jogadores.jsonl`: gerado apenas quando houver alteração persistida.
- `hexa_data.py`: integração após gravação canônica bem-sucedida.

## Evento

Cada linha JSON contém:

- `id_evento`;
- `ocorrido_em`;
- `jogador`;
- `campo`;
- `acao`;
- `valor_anterior`;
- `valor_novo`;
- `origem`;
- `versao_anterior`;
- `versao_nova`.

## Limitação do Streamlit Community Cloud

O arquivo JSONL gravado em runtime pode ser perdido em reinícios ou novos
deploys. Para retenção permanente sem banco, ele precisa ser copiado e
versionado no GitHub. A auditoria definitiva multiusuário deve migrar para
um banco com autenticação.

## Validação

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
python scripts/rc1_smoke.py
```
