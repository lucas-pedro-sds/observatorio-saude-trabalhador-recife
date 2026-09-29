import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Setores com mais acidentes por trabalhador",
    pergunta="Quais atividades econômicas (CNAE) concentram mais acidentes e adoecimentos do trabalho no Recife, "
             "proporcionalmente ao número de trabalhadores formais, e como isso mudou nos últimos três anos?",
    legenda="Decisão que informa: onde priorizar inspeções e ações.",
)

setores = dados.q1a_setores()
cidade = dados.q1b_cidade().set_index("ano")

f1, f2, f3 = st.columns([1, 1, 2])
ano = f1.segmented_control("Ano do ranking", [2023, 2024, 2025], default=2025) or 2025
top_n = f2.slider("Quantos setores", 5, min(30, len(setores)), 15)
busca = f3.text_input("Buscar atividade", placeholder="ex.: hospitalar, construção, comércio")

coluna = f"taxa_{ano}"
base = setores
if busca:
    base = base[base.atividade.str.contains(busca, case=False, na=False)]
ranking = base.sort_values(coluna, ascending=False).head(top_n)
taxa_cidade = cidade.loc[ano, "taxa"]

if ranking.empty:
    st.info("Nenhuma atividade encontrada com esse termo entre os setores que passam nos critérios mínimos.")
    st.stop()

rotulos = [f"{v.encurtar(a, 52)} ({c})" for a, c in zip(ranking.atividade, ranking.cnae)]

esq, dir_ = st.tabs(["Ranking", "Mudança 2023 → 2025"])
with esq:
    st.markdown(f"**Acidentes por mil vínculos CLT em {ano}**")
    fig = v.barras_horizontais(
        rotulos, ranking[coluna], "acidentes por mil vínculos/ano",
        hover=[f"<b>{a}</b><br>{v.num(t, 1)} por mil vínculos<br>{v.num(vi)} vínculos CLT em 2025"
               for a, t, vi in zip(ranking.atividade, ranking[coluna], ranking.vinculos_2025)],
    )
    fig.add_vline(x=taxa_cidade, line=dict(color=v.paleta()["tinta_2"], width=1, dash="dot"))
    fig.add_annotation(x=taxa_cidade, y=1, yref="paper", yanchor="bottom", showarrow=False,
                       text=f"cidade: {v.num(taxa_cidade, 1)}", font=dict(color=v.paleta()["tinta_2"], size=12))
    fig.update_layout(margin_t=36)
    v.mostrar(fig)

with dir_:
    st.markdown("**Como a taxa mudou de 2023 para 2025**")
    fig = v.halteres(rotulos, ranking.taxa_2023, ranking.taxa_2025, "2023", "2025",
                     "acidentes por mil vínculos/ano")
    v.mostrar(fig)

subiram = (ranking.taxa_2025 > ranking.taxa_2023).sum()
st.caption(
    f"Dos {len(ranking)} setores exibidos, {subiram} tiveram taxa maior em 2025 que em 2023. A taxa da cidade foi "
    f"de {v.num(cidade.loc[2023, 'taxa'], 1)} para {v.num(cidade.loc[2025, 'taxa'], 1)} no mesmo período. "
    "Variações pequenas são ruído: a taxa usa só 7 ou 8 meses por ano."
)

st.markdown("**Tabela completa**")
tabela = base.sort_values(coluna, ascending=False).assign(variacao=lambda d: d.taxa_2025 - d.taxa_2023)
st.dataframe(
    tabela[["cnae", "atividade", "vinculos_2025", "ocorrencias", "doencas",
            "taxa_2023", "taxa_2024", "taxa_2025", "variacao"]],
    hide_index=True, width="stretch",
    column_config={
        "cnae": "CNAE",
        "atividade": st.column_config.TextColumn("Atividade econômica", width="large"),
        "vinculos_2025": st.column_config.NumberColumn("Vínculos CLT 2025", format="localized"),
        "ocorrencias": st.column_config.NumberColumn("CATs (meses adequados)", format="localized"),
        "doencas": st.column_config.NumberColumn("Doenças do trabalho", format="localized"),
        "taxa_2023": st.column_config.NumberColumn("Taxa 2023", format="localized"),
        "taxa_2024": st.column_config.NumberColumn("Taxa 2024", format="localized"),
        "taxa_2025": st.column_config.NumberColumn("Taxa 2025", format="localized"),
        "variacao": st.column_config.NumberColumn("Variação 2023–2025", format="localized"),
    },
)

v.metodo(
    """
- **Taxa** = CATs ÷ vínculos CLT da RAIS × 1.000, **anualizada**: cada ano usa só os meses com cobertura adequada
  da CAT (pelo menos metade da mediana mensal), e o denominador é ajustado para esses meses
  (vínculos × meses adequados ÷ 12). Supõe sazonalidade pequena.
- **Vínculos CLT**, não todos os ativos: servidores estatutários têm regime próprio e não geram CAT.
- CAT e RAIS são cruzadas pela **classe CNAE de 4 dígitos**.
- Só entram setores com **≥ 2.000 vínculos CLT em cada ano** e **≥ 30 CATs no total**, para evitar taxas
  instáveis de setores pequenos.
- **"Adoecimentos"**: os agravos de doença do SINAN não estão carregados; o tipo "Doença" da CAT é a aproximação.
"""
)
