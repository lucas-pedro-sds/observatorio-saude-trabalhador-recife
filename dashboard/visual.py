"""Paleta, formatação pt-BR e estilo dos gráficos Plotly no tema bege.

As três cores categóricas foram validadas para daltonismo (todas as combinações
de pares) contra a superfície de cada tema. Use no máximo três séries por gráfico.
"""

import plotly.graph_objects as go
import streamlit as st

PALETAS = {
    "light": {
        "superficie": "#FBF8F2",
        "tinta": "#2F2A24",
        "tinta_2": "#6B6358",
        "discreta": "#8F8578",
        "grade": "#E6DED0",
        "eixo": "#CFC4B2",
        "neutro": "#CBC1B1",  # marca "fora da regra" (ex.: mês sem cobertura adequada)
        "series": ["#B35C33", "#008C82", "#6E4C9A"],  # terracota, verde-azulado, roxo
    },
    "dark": {
        "superficie": "#221F1B",
        "tinta": "#F1EBE0",
        "tinta_2": "#C9BFB1",
        "discreta": "#8F8578",
        "grade": "#34302A",
        "eixo": "#4A443C",
        "neutro": "#5A534B",
        "series": ["#C8693C", "#1A9690", "#9A7BD0"],
    },
}


def paleta():
    """Paleta do tema ativo (claro/escuro) escolhido pelo usuário no menu do Streamlit."""
    tipo = getattr(st.context.theme, "type", None) or "light"
    return PALETAS.get(tipo, PALETAS["light"])


def cor(i):
    return paleta()["series"][i]


# ---------------------------------------------------------------- formatação


def num(valor, casas=0):
    """1234567.8 -> '1.234.568' (pt-BR)."""
    if valor is None:
        return "–"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(valor, casas=1):
    return f"{num(valor, casas)}%"


def encurtar(texto, limite=48):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


# ---------------------------------------------------------------- gráficos


def _margem_rotulos(rotulos):
    """Margem esquerda para rótulos de categoria. Explícita porque o automargin do Plotly
    às vezes mede antes da fonte carregar e corta os rótulos."""
    return int(min(440, 16 + 6.6 * max(len(str(r)) for r in rotulos)))


def estilizar(fig, altura=380, legenda=False, margem_esq=64):
    """Aplica o estilo comum: fundo transparente, grade discreta, texto na tinta do tema."""
    p = paleta()
    fig.update_layout(
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13, color=p["tinta_2"]),
        margin=dict(l=margem_esq, r=40, t=16 if not legenda else 48, b=56, pad=4),
        separators=",.",
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None,
                    font=dict(color=p["tinta_2"])),
        hoverlabel=dict(bgcolor=p["superficie"], bordercolor=p["eixo"],
                        font=dict(color=p["tinta"], size=13)),
        bargap=0.28,
    )
    eixo = dict(gridcolor=p["grade"], linecolor=p["eixo"], zerolinecolor=p["eixo"],
                tickfont=dict(color=p["discreta"]), tickformat=",~r", title=dict(font=dict(color=p["tinta_2"]), standoff=12),
                automargin=True)
    fig.update_xaxes(**eixo)
    fig.update_yaxes(**eixo)
    return fig


def barras_horizontais(rotulos, valores, titulo_eixo, hover, cor_barra=None, casas=1, altura=None):
    """Ranking em barras horizontais, maior no topo, com o valor escrito no fim da barra."""
    p = paleta()
    fig = go.Figure(go.Bar(
        x=valores, y=rotulos, orientation="h",
        marker=dict(color=cor_barra or p["series"][0], line=dict(width=0), cornerradius=4),
        text=[num(v, casas) for v in valores], textposition="outside",
        textfont=dict(color=p["tinta_2"], size=12), cliponaxis=False,
        customdata=hover, hovertemplate="%{customdata}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_xaxes(title_text=titulo_eixo, showgrid=True)
    return estilizar(fig, altura or max(260, 30 * len(rotulos) + 80), margem_esq=_margem_rotulos(rotulos))


def halteres(rotulos, antes, depois, nome_antes, nome_depois, titulo_eixo, sufixo=""):
    """Comparação de dois momentos por item: um segmento ligando os dois pontos."""
    p = paleta()
    fig = go.Figure()
    for rotulo, a, b in zip(rotulos, antes, depois):
        fig.add_trace(go.Scatter(x=[a, b], y=[rotulo, rotulo], mode="lines",
                                 line=dict(color=p["eixo"], width=2), hoverinfo="skip", showlegend=False))
    for nome, valores, c in ((nome_antes, antes, p["series"][1]), (nome_depois, depois, p["series"][0])):
        fig.add_trace(go.Scatter(
            x=valores, y=rotulos, mode="markers", name=nome,
            marker=dict(color=c, size=11, line=dict(color=p["superficie"], width=2)),
            hovertemplate=f"<b>%{{y}}</b><br>{nome}: %{{x:,.1f}}{sufixo}<extra></extra>",
        ))
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="")
    fig.update_xaxes(title_text=titulo_eixo)
    return estilizar(fig, max(280, 30 * len(rotulos) + 110), legenda=True, margem_esq=_margem_rotulos(rotulos))


MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def mes_ano(data):
    return f"{MESES[data.month - 1]}/{data:%y}"


def eixo_mensal(fig, meses):
    """Rótulos de mês em português, a cada trimestre (o Plotly só traz nomes em inglês)."""
    ticks = [m for m in meses if m.month % 3 == 1]
    fig.update_xaxes(tickvals=ticks, ticktext=[mes_ano(m) for m in ticks])


def mostrar(fig):
    st.plotly_chart(fig, width="stretch", theme=None,
                    config={"displayModeBar": False, "locale": "pt-BR"})


# ---------------------------------------------------------------- texto


def cabecalho(titulo, pergunta=None, legenda=None):
    st.title(titulo)
    if pergunta:
        st.markdown(f"> {pergunta}")
    if legenda:
        st.caption(legenda)


def metodo(texto):
    """Nota de método recolhida, para quem quer saber como o número foi calculado."""
    with st.expander("Como este número foi calculado"):
        st.markdown(texto)
