import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Ocupações e diagnósticos",
    pergunta="Quais ocupações (CBO) e diagnósticos (CID-10) respondem pela maior parte das CATs registradas no "
             "Recife, e essa composição mudou entre o primeiro e o último dos três anos?",
    legenda="Decisão que informa: quais grupos de trabalhadores priorizar e que tendências acompanhar.",
)

comp = dados.q2_composicao()

f1, f2, f3 = st.columns([1.3, 1, 1.7])
escolha = f1.segmented_control("Analisar por", ["Ocupação (CBO)", "Diagnóstico (CID-10)"],
                               default="Ocupação (CBO)")
top_n = f2.slider("Quantos itens", 5, 30, 15)
incluir_ni = f3.toggle("Incluir \"não informado\"", value=False,
                       help="CATs sem CBO ou sem CID-10 preenchido. Ficam fora por padrão porque não "
                            "apontam um grupo a priorizar.")

dimensao = "CID-10" if escolha == "Diagnóstico (CID-10)" else "CBO"
base = comp[comp.dimensao == dimensao]
if not incluir_ni:
    base = base[base.codigo != "NI"]
base = base.head(top_n)
rotulos = [f"{v.encurtar(d, 50)} ({c})" for d, c in zip(base.descricao, base.codigo)]

# ---------------------------------------------------------------- concentração

total_dim = comp[comp.dimensao == dimensao]
chega_50 = total_dim[total_dim.pct_acumulado >= 50]
chega_80 = total_dim[total_dim.pct_acumulado >= 80]
m1, m2, m3 = st.columns(3)
with m1.container(border=True):
    st.metric("Mais frequente", v.encurtar(base.iloc[0].descricao, 34), help=base.iloc[0].descricao)
with m2.container(border=True):
    st.metric("Itens que somam 50% das CATs",
              int(chega_50.ranking.min()) if not chega_50.empty else "mais de 30")
with m3.container(border=True):
    st.metric("Itens que somam 80% das CATs",
              int(chega_80.ranking.min()) if not chega_80.empty else "mais de 30",
              help="Contando o grupo \"não informado\" na posição em que ele aparece.")

esq, dir_ = st.tabs(["Participação no total", "Mudança 2023 → 2025"])
with esq:
    st.markdown("**Participação no total de CATs, 2023–2025**")
    fig = v.barras_horizontais(
        rotulos, base.pct_total, "% das CATs",
        hover=[f"<b>{d}</b><br>{v.num(n)} CATs · {v.pct(p)} do total<br>{v.pct(a)} acumulado até aqui"
               for d, n, p, a in zip(base.descricao, base.cats, base.pct_total, base.pct_acumulado)],
    )
    v.mostrar(fig)

with dir_:
    st.markdown("**Participação em 2023 e em 2025**")
    fig = v.halteres(rotulos, base.pct_2023, base.pct_2025, "2023", "2025", "% das CATs do ano", sufixo="%")
    v.mostrar(fig)

variacao = (base.pct_2025 - base.pct_2023)
maior_alta = base.loc[variacao.idxmax()]
maior_queda = base.loc[variacao.idxmin()]
st.caption(
    f"Maior ganho de participação: {maior_alta.descricao} ({v.num(variacao.max(), 1)} p.p.). "
    f"Maior perda: {maior_queda.descricao} ({v.num(variacao.min(), 1)} p.p.). "
    "Sem teste estatístico: com poucos casos, oscilações de 1 ou 2 pontos são ruído."
)

st.markdown("**Tabela**")
st.dataframe(
    base.assign(variacao=variacao)[["ranking", "codigo", "descricao", "cats", "pct_total", "pct_acumulado",
                                    "pct_2023", "pct_2025", "variacao"]],
    hide_index=True, width="stretch",
    column_config={
        "ranking": st.column_config.NumberColumn("Posição", width="small"),
        "codigo": "Código",
        "descricao": st.column_config.TextColumn("Descrição", width="large"),
        "cats": st.column_config.NumberColumn("CATs 2023–2025", format="localized"),
        "pct_total": st.column_config.NumberColumn("% do total", format="localized"),
        "pct_acumulado": st.column_config.NumberColumn("% acumulado", format="localized"),
        "pct_2023": st.column_config.NumberColumn("% em 2023", format="localized"),
        "pct_2025": st.column_config.NumberColumn("% em 2025", format="localized"),
        "variacao": st.column_config.NumberColumn("Variação (p.p.)", format="localized"),
    },
)

v.metodo(
    """
- **Ranking e % acumulado**: todas as CATs com data de acidente entre 2023 e 2025.
- **2023 × 2025**: participação de cada item só nos **meses do calendário com cobertura adequada nos dois anos**,
  para não confundir mudança de perfil com falha de cobertura ou sazonalidade.
- CID-10 agrupado na **categoria de 3 caracteres** (ex.: S61 = ferimento do punho e da mão).
- A posição no ranking conta o grupo "não informado", mesmo quando ele está oculto.
"""
)
