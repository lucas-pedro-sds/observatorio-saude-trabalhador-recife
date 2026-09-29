import plotly.graph_objects as go
import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Sinais de subnotificação",
    pergunta="Onde há muito vínculo formal e pouca notificação: sinal de subnotificação, não de segurança?",
    legenda="Decisão que informa: onde investigar se a ausência de CAT é segurança real ou falta de registro.",
)

sub = dados.q3a_subnotificacao()
sub["grande_setor"] = sub.secao.map(dados.SECOES_CNAE).fillna(sub.secao)

f1, f2 = st.columns([1, 2])
top_n = f1.slider("Quantos setores", 5, 30, 15)
opcoes = sorted(sub.grande_setor.unique())
excluir = f2.multiselect(
    "Ocultar grandes setores", opcoes, placeholder="Nenhum oculto",
    help="Útil para tirar da lista setores de risco realmente baixo (escritórios), que também aparecem aqui.",
)
base = sub[~sub.grande_setor.isin(excluir)]
ranking = base.sort_values("diferenca", ascending=False).head(top_n)

with st.container(border=True):
    st.markdown(
        ":material/search: Leia como **indicador para investigar**, não como prova. Um setor aparece aqui quando "
        "registra menos CATs do que teria se acidentasse na taxa média da cidade. Isso pode ser subnotificação ou "
        "risco realmente baixo."
    )

esq, dir_ = st.tabs(["CATs faltando", "Tamanho do setor × registro"])
with esq:
    st.markdown("**CATs \"faltando\" em relação à taxa da cidade, 2023–2025**")
    rotulos = [f"{v.encurtar(a, 50)} ({c})" for a, c in zip(ranking.atividade, ranking.cnae)]
    fig = v.barras_horizontais(
        rotulos, ranking.diferenca, "CATs esperadas − registradas", casas=0,
        hover=[f"<b>{a}</b><br>{v.num(e)} esperadas · {v.num(o)} registradas<br>"
               f"{v.num(vi)} vínculos CLT somados em 3 anos"
               for a, e, o, vi in zip(ranking.atividade, ranking.esperados, ranking.acidentes, ranking.vinculos_ano)],
    )
    v.mostrar(fig)

with dir_:
    st.markdown("**Tamanho do setor × CATs registradas em relação ao esperado**")
    p = v.paleta()
    fig = go.Figure()
    grupos = (
        ("Abaixo da metade do esperado", base.razao < 0.5, p["series"][0]),
        ("Metade do esperado ou mais", base.razao >= 0.5, p["neutro"]),
    )
    for nome, filtro, c in grupos:
        d = base[filtro]
        fig.add_trace(go.Scatter(
            x=d.vinculos_ano, y=d.razao, mode="markers", name=nome,
            marker=dict(color=c, size=9, line=dict(color=p["superficie"], width=1.5)),
            customdata=d[["atividade", "acidentes", "esperados"]].values,
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,} registradas · "
                          "%{customdata[2]:,} esperadas<br>razão %{y:.2f}<extra></extra>",
        ))
    fig.add_hline(y=1, line=dict(color=p["tinta_2"], width=1, dash="dot"),
                  annotation_text="taxa da cidade", annotation_position="top left",
                  annotation_font=dict(color=p["tinta_2"], size=12))
    fig.update_xaxes(type="log", title_text="vínculos CLT somados em 2023–2025 (escala log)")
    fig.update_yaxes(title_text="registradas ÷ esperadas", rangemode="tozero")
    v.mostrar(v.estilizar(fig, max(280, 30 * len(ranking) + 60), legenda=True))

verif = dados.q3b_verificacao()
st.caption(
    f"Setores grandes e bem abaixo da linha são os mais relevantes para investigar. Verificação: "
    f"{v.pct(verif.pct, 2)} das {v.num(verif.acidentes_cat)} CATs do período caem em setores sem vínculo CLT "
    "na RAIS. Se esse percentual fosse alto, as taxas estariam distorcidas por diferença de classificação entre "
    "as bases."
)

st.markdown("**Tabela**")
st.dataframe(
    base.sort_values("diferenca", ascending=False)[
        ["cnae", "atividade", "grande_setor", "vinculos_ano", "acidentes", "por_mil", "esperados", "diferenca",
         "razao"]],
    hide_index=True, width="stretch",
    column_config={
        "cnae": "CNAE",
        "atividade": st.column_config.TextColumn("Atividade econômica", width="large"),
        "grande_setor": "Grande setor",
        "vinculos_ano": st.column_config.NumberColumn("Vínculos CLT (3 anos)", format="localized"),
        "acidentes": st.column_config.NumberColumn("CATs registradas", format="localized"),
        "por_mil": st.column_config.NumberColumn("Por mil vínculos", format="localized"),
        "esperados": st.column_config.NumberColumn("CATs esperadas", format="localized"),
        "diferenca": st.column_config.NumberColumn("Esperadas − registradas", format="localized"),
        "razao": st.column_config.NumberColumn("Registradas ÷ esperadas", format="localized"),
    },
)

v.metodo(
    """
- **Esperado** = vínculos CLT do setor (somados em 2023, 2024 e 2025) × taxa da cidade inteira no mesmo período.
- Ordenado pela **diferença esperado − registrado**, e não pela taxa crescente, que só listaria setores pequenos
  com zero CAT.
- **Vínculos CLT**: com todos os vínculos ativos, a administração pública (estatutários, que não geram CAT)
  dominaria o ranking.
- A taxa absoluta é subestimada pela cobertura irregular da CAT, mas a taxa da cidade usada como referência sofre a
  mesma subestimação. Por isso a leitura é **comparativa entre setores**.
- Só entram setores com **≥ 3.000 vínculos somados** (cerca de 1.000 por ano).
"""
)
