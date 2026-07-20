# Fontes técnicas — RC5.4

Consultadas em 20/07/2026:

- Streamlit — `st.markdown`: referência oficial para renderização de HTML
  controlado na interface.
- Streamlit — App testing: documentação oficial do `AppTest`.
- Streamlit — Layouts and containers: referência oficial para colunas e
  composição de telas.

Decisões aplicadas:

- componentes HTML continuam renderizados pelo mecanismo já utilizado pelo
  projeto, sem dependência externa;
- testes isolados usam `streamlit.testing.v1.AppTest`;
- a responsividade visual permanece no design system CSS do projeto;
- nenhuma biblioteca ou arquivo de fonte foi adicionado.
