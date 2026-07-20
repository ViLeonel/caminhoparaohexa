# RC5.5 — Dados do jogador e valor de mercado

Entrega incremental sobre o hotfix `1.1.6-hotfix-card-perfil`.

## Arquitetura preservada

- `hexa_components.py`: HTML semântico dos dados do jogador e do valor de mercado;
- `hexa_pages.py`: composição e ordem da ficha individual;
- `hexa_styles.py`: design responsivo dos agrupamentos e indicadores;
- `hexa_config.py`: versão da aplicação.

Nenhum JSON canônico, regra tática, avaliação trimestral, persistência local ou
dependência foi alterado.

## Modelo visual implementado

### Dados do jogador

A antiga lista plana foi substituída por três grupos semânticos:

1. **Identificação**
   - nome completo;
   - nascimento;
   - naturalidade;
   - altura;
   - pé preferencial.

2. **Vínculo profissional**
   - empresário;
   - entrada no clube;
   - contrato;
   - opção contratual;
   - última renovação;
   - equipador.

3. **Referência cadastral externa**
   - posição principal na fonte externa;
   - posições externas adicionais.

Campos vazios continuam omitidos. No desktop, Identificação e Vínculo
profissional ficam lado a lado; a referência externa ocupa a largura total.
No mobile, todos os grupos são empilhados em uma coluna.

O nome público do expander foi alterado para **Dados do jogador**.

### Valor de mercado

Os quatro indicadores foram convertidos em cartões próprios:

- valor atual;
- pico de valor de mercado;
- percentual do pico;
- diferença para o pico.

As datas ficaram em uma faixa separada e a observação editorial passou a ter
tipografia menor e itálica, preservando sua função secundária na hierarquia.

## Versão

`1.1.7-rc5.5-dados-jogador-mercado`
