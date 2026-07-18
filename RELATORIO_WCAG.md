# RELATÓRIO DE ACESSIBILIDADE — ETAPA 7

## Escopo

Revisão estática e automatizada orientada à WCAG 2.2 nível AA para contraste, teclado,
leitor de tela, semântica, zoom e modo de alto contraste.

## Implementado

1. Auditoria matemática de contraste com luminância relativa.
2. Tokens semânticos de cor e foco.
3. Foco visível consistente em widgets, links, expansores e controles.
4. Alvos mínimos de 44 px para controles principais.
5. Link “Pular para o conteúdo principal”.
6. Regiões rotuladas para campo, lista tática e banco.
7. `aria-live` para resumo dinâmico da convocação.
8. Hierarquia das seções principais baseada em H1 e H2.
9. Alternativas textuais para notas, escalação e tabelas.
10. Regras de reflow, zoom, movimento reduzido e `forced-colors`.
11. Modo de alto contraste persistido no `session_state`.

## Contraste automatizado

As combinações principais do tema padrão foram testadas com limite mínimo 4,5:1
para texto normal. O tema de alto contraste usa fundo preto e textos/brilhos
claros com contraste superior ao requisito AA.

## Verificação parcial

A análise automatizada não substitui testes reais de:

- VoiceOver no Safari;
- NVDA ou JAWS no Windows;
- TalkBack no Android;
- ordem de tabulação gerada pelo runtime do Streamlit;
- zoom real de 200% em cada navegador;
- contraste de componentes internos alterados por futuras versões do Streamlit.

## Roteiro manual mínimo

1. Percorrer toda a aplicação apenas com Tab, Shift+Tab, Enter, Espaço e Escape.
2. Confirmar que o link de salto aparece ao receber foco.
3. Ativar o modo de alto contraste e revisar todas as quatro páginas.
4. Testar zoom de 200% sem perda de conteúdo ou rolagem horizontal essencial.
5. No leitor de tela, confirmar anúncio do título, navegação, vagas e resumo.
6. Confirmar que tabelas possuem contexto textual imediatamente anterior.
