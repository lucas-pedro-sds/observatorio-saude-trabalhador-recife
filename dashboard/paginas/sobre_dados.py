import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import visual as v

v.cabecalho(
    "Sobre os dados",
    legenda="De onde vêm os números do painel e o que é preciso saber antes de interpretá-los.",
)

st.subheader("Cobertura mensal da CAT")
q0 = dados.q0_cobertura()
p = v.paleta()
fig = go.Figure()
for nome, filtro, c in (("Cobertura adequada", q0.cobertura_adequada, p["series"][0]),
                        ("Arquivo incompleto", ~q0.cobertura_adequada, p["neutro"])):
    d = q0[filtro]
    fig.add_trace(go.Bar(
        x=d.mes, y=d.acidentes_cat, name=nome, marker=dict(color=c, cornerradius=3),
        customdata=[v.mes_ano(m) for m in d.mes],
        hovertemplate=f"%{{customdata}}<br>%{{y:,}} CATs<extra>{nome}</extra>",
    ))
v.eixo_mensal(fig, q0.mes)
fig.update_yaxes(title_text="CATs com acidente no mês")
fig.update_layout(barmode="overlay", bargap=0.15)
v.mostrar(v.estilizar(fig, 320, legenda=True))
adequados = int(q0.cobertura_adequada.sum())
st.caption(
    f"{adequados} de {len(q0)} meses têm cobertura adequada (pelo menos metade da mediana mensal). Os arquivos "
    "mensais do INSS chegam incompletos entre set/2024 e mar/2025 e em nov–dez/2025. Comparações entre anos usam "
    "só os meses adequados."
)

st.subheader("Cuidados de leitura")
st.markdown(
    """
1. **Nenhum ano da CAT está completo.** Contagens absolutas subestimam o real; por isso o painel trabalha com
   taxas e participações calculadas nos meses com cobertura adequada.
2. **Território:** as fontes de acidente só identificam o município (Recife). Não há bairro, então o recorte
   territorial do painel é o setor econômico (CNAE).
3. **Município da CAT** é o do empregador, não o local exato do acidente (a coluna de local está corrompida na fonte).
4. **"Adoecimentos":** os agravos de doença do SINAN não estão carregados; o tipo "Doença" da CAT é a aproximação.
5. **Denominador:** vínculos **CLT** da RAIS. Servidores estatutários têm regime próprio e não geram CAT.
6. **Período:** 2023–2025, os três anos em que CAT e RAIS coexistem.
7. **SINAN 2023–2025 é preliminar** e pode mudar em revisões do Ministério da Saúde.
"""
)

st.subheader("Fontes")
st.dataframe(
    pd.DataFrame([
        ("CAT — Comunicação de Acidente de Trabalho", "INSS · dadosabertos.inss.gov.br", "Acidentes e doenças do "
         "trabalho de celetistas"),
        ("RAIS — Relação Anual de Informações Sociais", "MTE, via basedosdados.org", "Vínculos formais por "
         "estabelecimento (denominador)"),
        ("SINAN — acidente de trabalho grave (ACGR)", "DATASUS", "Notificações da rede de saúde, inclusive "
         "de informais"),
        ("CNAE 2.0", "CONCLA/IBGE", "Atividades econômicas"),
        ("CBO 2002", "MTE", "Ocupações"),
        ("CID-10", "basedosdados.org", "Diagnósticos"),
    ], columns=["Fonte", "Origem", "Uso no painel"]),
    hide_index=True, width="stretch",
)
st.caption("Metodologia completa e consultas SQL: analises/eda.ipynb e sql/02_consultas_analise.sql no repositório.")
