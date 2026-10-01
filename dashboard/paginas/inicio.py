import plotly.graph_objects as go
import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Saúde do trabalhador no Recife",
    legenda="Acidentes e doenças do trabalho registrados em CAT (INSS), comparados aos vínculos formais "
            "da RAIS e às notificações do SINAN, de 2023 a 2025. Painel de apoio à VISAT para decidir "
            "onde inspecionar e que política levar a cada setor.",
)

cat = dados.resumo_cat()
cidade = dados.q1b_cidade().set_index("ano")
setores = dados.q1a_setores()
comp = dados.q2_composicao()
sub = dados.q3a_subnotificacao()
situacao = dados.q4a_situacao().set_index("grupo")
emitida = dados.q4b_cat_emitida().set_index("cat_emitida")

# ---------------------------------------------------------------- indicadores

k1, k2, k3, k4 = st.columns(4)
with k1.container(border=True, height="stretch"):
    st.metric("CATs registradas, 2023–2025", v.num(cat.total),
              help="Toda CAT com data de acidente no período. A cobertura mensal dos arquivos do INSS é "
                   "irregular, então esse total subestima o real (ver Sobre os dados).")
with k2.container(border=True, height="stretch"):
    t23, t25 = cidade.loc[2023, "taxa"], cidade.loc[2025, "taxa"]
    st.metric("Taxa por mil vínculos (2025)", v.num(t25, 1),
              delta=f"{v.num(t25 - t23, 1)} desde 2023", delta_color="inverse",
              help="Acidentes por mil vínculos CLT, anualizada com os meses de cobertura adequada da CAT.")
with k3.container(border=True, height="stretch"):
    st.metric("Vínculos CLT (RAIS 2025)", v.num(cidade.loc[2025, "vinculos_clt"]),
              help="Denominador das taxas. Servidores estatutários ficam de fora porque não geram CAT.")
with k4.container(border=True, height="stretch"):
    st.metric("Óbitos registrados em CAT", v.num(cat.obitos),
              help=f"{v.pct(100 * cat.obitos / cat.total, 2)} das CATs do período.")

st.caption(
    f"Das CATs do período, {v.pct(100 * cat.tipicos / cat.total)} são acidentes típicos, "
    f"{v.pct(100 * cat.trajeto / cat.total)} de trajeto e {v.pct(100 * cat.doencas / cat.total)} doenças "
    f"do trabalho. {v.pct(100 * cat.homens / cat.total)} das vítimas são homens."
)

# ---------------------------------------------------------------- achados por pergunta

st.subheader("O que os dados respondem")

top_setor = setores.sort_values("taxa_2025", ascending=False).iloc[0]
cbo = comp[comp.dimensao == "CBO"]
cid = comp[comp.dimensao == "CID-10"]
n_cbo_metade = int((cbo.pct_acumulado < 50).sum() + 1)
top_cbo = cbo[cbo.codigo != "NI"].iloc[0]  # "não informado" não é resposta
top_cid = cid[cid.codigo != "NI"].iloc[0]
top_sub = sub.iloc[0]
sem_registro = situacao.loc["Sem registro, autônomo ou avulso", "pct"]
sem_cat = emitida.reindex(["CAT não emitida", "Ignorado"])["pct"].fillna(0).sum()

c1, c2 = st.columns(2)
with c1.container(border=True, height="stretch"):
    st.markdown("**1 · Setores com mais acidentes por trabalhador**")
    st.markdown(
        f"**{top_setor.atividade}** lidera em 2025, com **{v.num(top_setor.taxa_2025, 1)}** acidentes por mil "
        f"vínculos, {v.num(top_setor.taxa_2025 / t25, 1)} vezes a taxa da cidade ({v.num(t25, 1)})."
    )
    st.page_link("paginas/p1_setores.py", label="Ver ranking de setores", icon=":material/arrow_forward:")
with c2.container(border=True, height="stretch"):
    st.markdown("**2 · Ocupações e diagnósticos mais frequentes**")
    concentracao = (
        f"As {n_cbo_metade} primeiras ocupações somam metade das CATs."
        if n_cbo_metade <= len(cbo) else
        f"O perfil é disperso: as {len(cbo)} primeiras ocupações somam {v.pct(cbo.pct_acumulado.max())} das CATs."
    )
    st.markdown(
        f"**{v.encurtar(top_cbo.descricao, 60)}** é a ocupação com mais CATs "
        f"({v.pct(top_cbo.pct_total)}), e **{v.encurtar(top_cid.descricao, 60)}** o diagnóstico mais "
        f"comum ({v.pct(top_cid.pct_total)}). {concentracao}"
    )
    st.page_link("paginas/p2_ocupacoes_diagnosticos.py", label="Ver ocupações e diagnósticos",
                 icon=":material/arrow_forward:")

c3, c4 = st.columns(2)
with c3.container(border=True, height="stretch"):
    st.markdown("**3 · Onde pode haver subnotificação**")
    st.markdown(
        f"**{top_sub.atividade}** tem muitos vínculos e poucas CATs: seriam esperadas "
        f"**{v.num(top_sub.esperados)}** pela taxa da cidade, mas foram registradas **{v.num(top_sub.acidentes)}**. "
        "Não prova subnotificação, mas indica onde investigar."
    )
    st.page_link("paginas/p3_subnotificacao.py", label="Ver setores a investigar", icon=":material/arrow_forward:")
with c4.container(border=True, height="stretch"):
    st.markdown("**4 · Rede de saúde e trabalho informal**")
    st.markdown(
        f"**{v.pct(sem_registro)}** dos acidentes graves notificados no SINAN são de trabalhadores sem registro, "
        f"autônomos ou avulsos, que a CAT não alcança. Entre os celetistas notificados, **{v.pct(sem_cat)}** "
        "não tiveram CAT emitida ou a informação foi ignorada."
    )
    st.page_link("paginas/p4_rede_saude.py", label="Ver rede de saúde", icon=":material/arrow_forward:")

# ---------------------------------------------------------------- panorama

st.subheader("Panorama")
g1, g2 = st.columns([2, 3])

with g1:
    st.markdown("**Acidentes por mil vínculos CLT, cidade inteira**")
    p = v.paleta()
    fig = go.Figure(go.Bar(
        x=[str(a) for a in cidade.index], y=cidade.taxa,
        marker=dict(color=p["series"][0], cornerradius=4),
        text=[v.num(t, 1) for t in cidade.taxa], textposition="outside", cliponaxis=False,
        textfont=dict(color=p["tinta_2"]),
        customdata=cidade[["ocorrencias", "meses_adequados"]].values,
        hovertemplate="<b>%{x}</b><br>%{y:.1f} por mil vínculos<br>%{customdata[0]:,} CATs em "
                      "%{customdata[1]} meses adequados<extra></extra>",
    ))
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(title_text="por mil vínculos/ano", rangemode="tozero")
    v.mostrar(v.estilizar(fig, 320))
    st.caption("Taxa anualizada com os meses de cobertura adequada de cada ano (7, 8 e 7 meses).")

with g2:
    st.markdown("**CATs por grande setor da economia, 2023–2025**")
    secoes = dados.cat_por_secao()
    secoes["nome"] = secoes.secao.map(dados.SECOES_CNAE).fillna(secoes.secao)
    secoes["pct"] = 100 * secoes.cats / secoes.cats.sum()
    top = secoes.head(8)
    fig = v.barras_horizontais(
        top.nome, top.pct, "% das CATs", casas=1,
        hover=[f"<b>{n}</b><br>{v.num(c)} CATs ({v.pct(p_)})" for n, c, p_ in zip(top.nome, top.cats, top.pct)],
        altura=320,
    )
    v.mostrar(fig)
    st.caption("Seções da CNAE 2.0. Contagem absoluta: setores grandes aparecem mais. "
               "A taxa por trabalhador está na pergunta 1.")
