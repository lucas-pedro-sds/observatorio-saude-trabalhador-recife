import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Rede de saúde e trabalho informal",
    pergunta="A procura pela rede de saúde acompanha o mapa do trabalho formal ou aponta para o informal?",
    legenda="Decisão que informa: ajustar a oferta de serviços à informalidade. Resposta parcial: sem PNAD não há "
            "taxa de informalidade da cidade, e o SINAN não tem território abaixo do município.",
)

situacao = dados.q4a_situacao()
emitida = dados.q4b_cat_emitida()
mensal = dados.q4c_mensal()

esq, dir_ = st.columns(2)
with esq:
    st.markdown("**Situação de trabalho das vítimas de acidente grave (SINAN, 2023–2025)**")
    fig = v.barras_horizontais(
        situacao.grupo, situacao.pct, "% das notificações",
        hover=[f"<b>{g}</b><br>{v.num(n)} notificações ({v.pct(p)})"
               for g, n, p in zip(situacao.grupo, situacao.notificacoes, situacao.pct)],
        altura=260,
    )
    v.mostrar(fig)
    st.caption(f"{v.num(situacao.notificacoes.sum())} notificações. Trabalhadores sem registro não entram na CAT: "
               "o SINAN é a única fonte que os enxerga.")

with dir_:
    st.markdown("**Celetistas notificados no SINAN: foi emitida CAT?**")
    fig = v.barras_horizontais(
        emitida.cat_emitida, emitida.pct, "% dos celetistas notificados", cor_barra=v.cor(1),
        hover=[f"<b>{g}</b><br>{v.num(n)} notificações ({v.pct(p)})"
               for g, n, p in zip(emitida.cat_emitida, emitida.notificacoes, emitida.pct)],
        altura=260,
    )
    v.mostrar(fig)
    st.caption("\"Não emitida\" e \"ignorado\" são acidentes que chegaram à rede de saúde e podem não ter virado CAT.")

# ---------------------------------------------------------------- série mensal

st.markdown("**CAT e SINAN mês a mês**")
p = v.paleta()
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=mensal.mes, y=mensal.acidentes_cat, name="CAT (INSS)", mode="lines",
    line=dict(color=p["series"][0], width=2),
    customdata=[v.mes_ano(m) for m in mensal.mes],
    hovertemplate="%{customdata}: %{y:,} CATs<extra>CAT</extra>",
))
fig.add_trace(go.Scatter(
    x=mensal.mes, y=mensal.notificacoes_sinan, name="SINAN, acidente grave", mode="lines",
    line=dict(color=p["series"][1], width=2),
    customdata=[v.mes_ano(m) for m in mensal.mes],
    hovertemplate="%{customdata}: %{y:,} notificações<extra>SINAN</extra>",
))
# meses em que a CAT não tem cobertura adequada ficam sombreados
fora = mensal[~mensal.cobertura_adequada]
for mes in fora.mes:
    fig.add_vrect(x0=mes, x1=mes + pd.DateOffset(months=1), fillcolor=p["grade"], opacity=0.6,
                  line_width=0, layer="below")
v.eixo_mensal(fig, mensal.mes)
fig.update_yaxes(title_text="registros no mês", rangemode="tozero")
fig.update_layout(hovermode="closest")
v.mostrar(v.estilizar(fig, 340, legenda=True))

adequados = mensal[mensal.cobertura_adequada]
correlacao = adequados.acidentes_cat.corr(adequados.notificacoes_sinan)
st.caption(
    f"Faixas sombreadas: meses em que os arquivos da CAT chegaram incompletos. Nos {len(adequados)} meses com "
    f"cobertura adequada, a correlação entre as duas séries é de {v.num(correlacao, 2)}: CAT e SINAN "
    "praticamente não andam juntos, o que é indício (não resultado) de que capturam públicos diferentes."
)

v.metodo(
    """
- **SINAN, grupo ACGR** (acidente de trabalho grave), filtrado pelo município do acidente (`MUN_ACID`).
  Os anos 2023–2025 são dados **preliminares** do Ministério da Saúde.
- Agrupamento de `sit_trab` pela ficha do SINAN: 1, 4 e 5 = vínculo formal; 2, 3 e 10 = sem registro,
  autônomo ou avulso; demais = outras situações. **Validar os códigos com a VISAT.**
- Campo `cat` do SINAN: 1 = emitida, 2 = não emitida, 3 = não se aplica, 9 = ignorado. Só para `sit_trab = 1` (CLT).
- A correlação usa só os meses em que a CAT tem cobertura adequada.
"""
)
