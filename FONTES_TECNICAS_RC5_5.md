# Fontes técnicas — RC5.5

Consultadas em 20/07/2026:

- Streamlit — `st.expander`:
  https://docs.streamlit.io/develop/api-reference/layout/st.expander
- Streamlit — `st.markdown`:
  https://docs.streamlit.io/develop/api-reference/text/st.markdown
- Streamlit — layouts e containers:
  https://docs.streamlit.io/develop/concepts/design/layouts-and-containers

Decisão aplicada: o expander usa a API pública `type="compact"` disponível na
versão 1.59.2 fixada pelo projeto. O conteúdo interno continua sendo renderizado
por HTML semântico via `st.markdown(..., unsafe_allow_html=True)`, sem seletores
CSS adicionais sobre internals do Streamlit.
