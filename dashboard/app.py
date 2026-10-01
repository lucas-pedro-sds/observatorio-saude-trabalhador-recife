"""Observatório de Saúde do Trabalhador — Recife. Dashboard para a gerência da VISAT.

Rodar da raiz do repositório (para o Streamlit achar .streamlit/config.toml):

    streamlit run dashboard/app.py
"""

import streamlit as st

import dados

st.set_page_config(
    page_title="Observatório de Saúde do Trabalhador · Recife",
    page_icon="🩺",
    layout="wide",
)

paginas = {
    "": [
        st.Page("paginas/inicio.py", title="Visão geral", icon=":material/home:", default=True),
    ],
    "Perguntas do observatório": [
        st.Page("paginas/p1_setores.py", title="1 · Setores com mais acidentes", icon=":material/factory:"),
        st.Page("paginas/p2_ocupacoes_diagnosticos.py", title="2 · Ocupações e diagnósticos",
                icon=":material/badge:"),
        st.Page("paginas/p3_subnotificacao.py", title="3 · Sinais de subnotificação",
                icon=":material/visibility_off:"),
        st.Page("paginas/p4_rede_saude.py", title="4 · Rede de saúde e informalidade",
                icon=":material/local_hospital:"),
    ],
    "Referência": [
        st.Page("paginas/sobre_dados.py", title="Sobre os dados", icon=":material/info:"),
    ],
}

pagina = st.navigation(paginas)

with st.sidebar:
    st.markdown("**Observatório de Saúde do Trabalhador**")
    st.caption("Recife · 2023–2025 · CAT, RAIS e SINAN")
    st.caption("Equipe Uma Ponte · NExT Dados (CESAR School). Dados públicos do INSS, MTE e DATASUS.")
    st.caption(dados.descricao_fonte())

pagina.run()
