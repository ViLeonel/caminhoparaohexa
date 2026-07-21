# Política de Segurança

## Escopo

Esta política cobre o código, as configurações, os dados editoriais e os ambientes de implantação de **O Caminho para o Hexa 2030**.

## Como relatar uma vulnerabilidade

Não publique credenciais, dados editoriais privados, detalhes de exploração ou provas de conceito em issues públicas.

Relate de forma privada aos responsáveis do repositório, informando:

- componente afetado;
- versão ou commit;
- passos mínimos para reprodução;
- impacto estimado;
- evidências sem dados pessoais ou segredos;
- sugestão de mitigação, quando houver.

## Compromissos operacionais

- segredos reais nunca devem ser versionados;
- a branch principal deve exigir Pull Request e checks verdes;
- ações de CI devem usar permissões mínimas e versões imutáveis;
- a área administrativa permanece sem edição pública nesta fase;
- alterações de dados devem manter auditoria, controle de concorrência e preservação editorial;
- credenciais expostas devem ser revogadas e substituídas, não apenas removidas do Git.

## Ambientes

Produção e homologação devem usar segredos, URLs de callback e contas administrativas separados.

## Dados

Os campos editoriais de Vini e Beto são ativos protegidos. Dados externos devem permanecer em namespace próprio e nunca substituir posições ou avaliações editoriais.
