# RELATÓRIO DE INTEGRIDADE DOS DADOS

## Escopo

Validação executada sobre `jogadores_hexa_2030.json` após a introdução do schema tipado e das regras de integridade da Etapa 10.

## Resultado

- Atletas analisados: 61
- Erros bloqueantes: 0
- Avisos: 0
- Registros descartados: 0
- Alterações no JSON: 0

## Regras verificadas

- cada registro é um objeto;
- nome obrigatório;
- chave canônica igual ao campo `nome`;
- ausência de duplicidades após normalização de acentos, caixa e espaços;
- idade entre 15 e 45;
- notas de Vini e Roberto entre 0 e 10;
- posição principal pertencente à lista oficial;
- `posicoes_multiplas` como lista;
- posição principal presente em `posicoes_multiplas`;
- posições múltiplas pertencentes à lista oficial;
- preservação dos campos editoriais e táticos;
- enriquecimento parcial não cria jogador sem posição editorial válida.

## Política de bloqueio

Erros estruturais interrompem carregamento e salvamento. O aplicativo não descarta registros inválidos silenciosamente e não grava uma base parcialmente recuperada.

Avisos podem ser exibidos na interface sem bloquear a leitura. Atualmente a base não produz avisos.

## Limitações

A validação garante contrato estrutural e regras locais. Ela não confirma automaticamente a veracidade esportiva de clube, idade, notas, histórico ou dados de mercado.
