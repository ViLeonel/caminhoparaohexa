# RC5.4 — Ajustes de UX no campo, ficha e análises

Pacote incremental para sobrepor na raiz do repositório **O Caminho para o
Hexa 2030**.

## Arquitetura preservada

- `hexa_taticas.py`: coordenadas e regras das formações;
- `hexa_pages.py`: composição das telas e remoção dos controles visuais;
- `hexa_components.py`: card do atleta e componentes de leitura;
- `hexa_styles.py`: responsividade, tipografia e apresentação;
- `hexa_avaliacoes.py`: tradução dos estados internos para rótulos públicos;
- `hexa_config.py`: identificação da versão.

As funções puras de comparação entre analistas e de visualização tática em
lista continuam disponíveis nos módulos de domínio para compatibilidade. Elas
não são mais chamadas pela interface pública.

## Alterações implementadas

1. O centroavante do `4-3-3 Clássico` foi reposicionado para `bottom: 76%`.
2. O campo mantém altura mínima de 520 px em larguras intermediárias, evitando
   que o cartão volte a ultrapassar a borda em janelas baixas.
3. A opção `Campo | Lista` foi removida; a tela usa somente o campo.
4. O título passou a ser `Monte a sua convocação`, com escala fluida por
   `clamp()`.
5. O cartão individual foi redesenhado como card editorial inspirado em
   videogames, com:
   - clube atual;
   - capacidade atual;
   - potencial em 2030;
   - idade em 2030;
   - posição oficial;
   - situação da avaliação.
6. ID e idade de 2026 foram removidos do card público.
7. Situação, saldo e data usam uma grade responsiva em duas linhas:
   - situação ocupa a largura total;
   - saldo e data ficam lado a lado;
   - no mobile, os três itens são empilhados.
8. Os rótulos públicos passaram a ser:
   - `Avaliação Completa`;
   - `Avaliação Parcial`;
   - `Sem Avaliação`.
9. A seção `Consensos e divergências` foi removida da tela de análises.
10. Versão atualizada para `1.1.4-rc5.4-ajustes-ux`.

## Dados preservados

Nenhum JSON faz parte deste pacote. Não foram alterados:

- `jogadores_hexa_2030.json`;
- `avaliacoes_trimestrais_hexa_2030.json`;
- `enriquecimentos_tm.json`;
- campos editoriais protegidos;
- posições oficiais;
- limites de 11 titulares e 15 reservas;
- persistência local por formação.

## Aplicação

Extraia o ZIP na raiz do repositório e substitua somente os arquivos incluídos.
Leia `DEPLOY_RC5_4_AJUSTES_UX.md` antes de publicar.
