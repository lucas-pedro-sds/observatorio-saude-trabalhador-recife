"""Fonte de dados do dashboard: o PostgreSQL ao vivo ou a cópia salva em dashboard/snapshot/.

As consultas são as mesmas de analises/eda.ipynb (Q0 a Q4), sem os LIMITs: o corte
para o top N é feito na página, pelo filtro. Se uma regra mudar no notebook, mude aqui também
e rode `python dashboard/exportar_dados.py` para atualizar a cópia.

De onde os dados vêm (variável DASHBOARD_FONTE, no .env ou em Secrets):
- "banco": sempre do PostgreSQL;
- "arquivos": sempre da cópia em snapshot/ (é o que o app publicado na nuvem usa);
- vazio (padrão): do banco se houver credenciais e ele responder; senão, da cópia.

Credenciais do banco: no Streamlit Community Cloud, em Secrets (seção [db]); localmente, no .env
da raiz (as mesmas variáveis de pipeline/03_carga.py).
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

PASTA_COPIA = Path(__file__).parent / "snapshot"
EXPORTAR_PARA = None  # exportar_dados.py preenche: cada consulta feita no banco também é salva aqui

load_dotenv(find_dotenv(usecwd=True))


def _config(chave, secao=None):
    """Lê de st.secrets (nuvem) e, na falta, do ambiente/.env (local)."""
    try:
        return st.secrets[secao][chave] if secao else st.secrets[chave]
    except Exception:  # sem secrets.toml, ou chave ausente
        return None


def _credenciais():
    return {
        "user": _config("user", "db") or os.getenv("DB_USER"),
        "password": _config("password", "db") or os.getenv("DB_PASSWORD"),
        "host": _config("host", "db") or os.getenv("DB_HOST"),
        "port": _config("port", "db") or os.getenv("DB_PORT"),
        "name": _config("name", "db") or os.getenv("DB_NAME"),
    }


@st.cache_resource
def _engine():
    c = _credenciais()
    # NullPool: a conexão abre na consulta e fecha logo depois. O Aiven gratuito tem só 12 vagas
    # para o time inteiro, e um pool deixaria conexões paradas ocupando vaga enquanto o app roda.
    # sslmode=prefer: usa SSL no Aiven (que exige) e também funciona num Postgres local sem SSL.
    return create_engine(
        f"postgresql+psycopg2://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['name']}?sslmode=prefer",
        poolclass=NullPool,
        connect_args={"connect_timeout": 15},
    )


@st.cache_data(ttl=600, show_spinner="Conectando ao banco…")
def _banco_responde():
    try:
        with _engine().connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def fonte():
    """'banco' ou 'arquivos', conforme DASHBOARD_FONTE e a disponibilidade do banco."""
    escolha = (_config("DASHBOARD_FONTE") or os.getenv("DASHBOARD_FONTE") or "").strip().lower()
    if escolha in ("banco", "arquivos"):
        return escolha
    if not all(_credenciais().values()):
        return "arquivos"
    return "banco" if _banco_responde() else "arquivos"


def descricao_fonte():
    """Texto curto para a barra lateral dizendo de onde vêm os números."""
    if fonte() == "banco":
        return "Dados ao vivo do banco."
    try:
        info = json.loads((PASTA_COPIA / "_info.json").read_text(encoding="utf-8"))
        data = datetime.fromisoformat(info["gerado_em"]).strftime("%d/%m/%Y")
    except Exception:
        data = "data desconhecida"
    return f"Dados da cópia salva em {data}."


@st.cache_data(ttl=6 * 3600, show_spinner="Consultando o banco…")
def _consultar_banco(sql):
    with _engine().connect() as conexao:
        return pd.read_sql(text(sql), conexao)


@st.cache_data(show_spinner=False)
def _ler_copia(nome):
    arquivo = PASTA_COPIA / f"{nome}.parquet"
    if not arquivo.exists():
        st.error(f"Sem conexão com o banco e sem a cópia `{arquivo.name}`. "
                 "Rode `python dashboard/exportar_dados.py` com o banco acessível.")
        st.stop()
    return pd.read_parquet(arquivo)


def _ler(nome, sql):
    """Resultado de uma consulta do dashboard. `nome` é também o nome do arquivo da cópia."""
    if EXPORTAR_PARA is not None or fonte() == "banco":
        df = _consultar_banco(sql)
        if EXPORTAR_PARA is not None:
            df.to_parquet(Path(EXPORTAR_PARA) / f"{nome}.parquet", index=False)
        return df
    return _ler_copia(nome)


def _cobertura(inicio="2023-01-01", fim="2025-12-01"):
    """CTEs meses/mensal/cobertura: mês adequado = pelo menos metade da mediana mensal do período."""
    return f"""
meses AS (
  SELECT generate_series('{inicio}'::date, '{fim}'::date, interval '1 month')::date AS mes
),
mensal AS (
  SELECT m.mes, count(f.id) AS n
  FROM meses m
  LEFT JOIN fato_cat f ON date_trunc('month', f.data_acidente)::date = m.mes
  GROUP BY m.mes
),
cobertura AS (
  SELECT mes, n,
         n >= 0.5 * (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY n) FROM mensal) AS ok
  FROM mensal
)"""


# ---------------------------------------------------------------- visão geral


def resumo_cat():
    """Totais da CAT no período, por tipo, sexo e óbito."""
    return _ler("resumo_cat", """
SELECT count(*) AS total,
       count(*) FILTER (WHERE btrim(tipo_acidente) ILIKE 'T_pico') AS tipicos,
       count(*) FILTER (WHERE btrim(tipo_acidente) = 'Trajeto') AS trajeto,
       count(*) FILTER (WHERE btrim(tipo_acidente) ILIKE 'Doen%') AS doencas,
       count(*) FILTER (WHERE indica_obito_acidente = 'Sim') AS obitos,
       count(*) FILTER (WHERE sexo = 'Masculino') AS homens,
       count(*) FILTER (WHERE sexo = 'Feminino') AS mulheres
FROM fato_cat
WHERE data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
""").iloc[0]


def cat_por_secao():
    """CATs 2023–2025 por seção da CNAE (letra), com a descrição da seção."""
    return _ler("cat_por_secao", """
SELECT d.secao, count(*) AS cats
FROM fato_cat f
JOIN dim_cnae d ON d.classe_codigo_4 = f.cnae
WHERE f.data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY d.secao
ORDER BY cats DESC
""")


# ---------------------------------------------------------------- Q0


def q0_cobertura():
    return _ler("q0_cobertura", f"""
WITH {_cobertura()}
SELECT mes, n AS acidentes_cat, ok AS cobertura_adequada
FROM cobertura
ORDER BY mes
""").astype({"mes": "datetime64[ns]"})


# ---------------------------------------------------------------- Q1


def q1a_setores():
    """Taxa anualizada por mil vínculos CLT, por CNAE (4 dígitos) e ano, só meses adequados."""
    return _ler("q1a_setores", f"""
WITH {_cobertura()},
meses_ok AS (
  SELECT extract(year FROM mes)::int AS ano, count(*) FILTER (WHERE ok) AS n_meses
  FROM cobertura
  GROUP BY 1
),
acidentes AS (
  SELECT extract(year FROM f.data_acidente)::int AS ano,
         f.cnae AS classe4,
         count(*) AS ocorrencias,
         count(*) FILTER (WHERE btrim(f.tipo_acidente) ILIKE 'Doen%') AS doencas
  FROM fato_cat f
  JOIN cobertura c ON c.mes = date_trunc('month', f.data_acidente)::date AND c.ok
  GROUP BY 1, 2
),
vinculos AS (
  SELECT r.ano, d.classe_codigo_4 AS classe4, sum(r.quantidade_vinculos_clt) AS vinculos
  FROM fato_rais r
  JOIN dim_cnae d ON d.classe_codigo = r.cnae_2_classe
  WHERE r.ano BETWEEN 2023 AND 2025
  GROUP BY 1, 2
),
taxas AS (
  SELECT v.ano, v.classe4, v.vinculos,
         coalesce(a.ocorrencias, 0) AS ocorrencias,
         coalesce(a.doencas, 0) AS doencas,
         1000.0 * coalesce(a.ocorrencias, 0) / (v.vinculos * m.n_meses / 12.0) AS taxa
  FROM vinculos v
  JOIN meses_ok m ON m.ano = v.ano
  LEFT JOIN acidentes a ON a.ano = v.ano AND a.classe4 = v.classe4
  WHERE v.vinculos > 0
)
SELECT d.classe_codigo_4 AS cnae,
       d.denominacao AS atividade,
       max(t.vinculos) FILTER (WHERE t.ano = 2025) AS vinculos_2025,
       sum(t.ocorrencias) AS ocorrencias,
       sum(t.doencas) AS doencas,
       round(max(t.taxa) FILTER (WHERE t.ano = 2023), 1) AS taxa_2023,
       round(max(t.taxa) FILTER (WHERE t.ano = 2024), 1) AS taxa_2024,
       round(max(t.taxa) FILTER (WHERE t.ano = 2025), 1) AS taxa_2025
FROM taxas t
JOIN dim_cnae d ON d.classe_codigo_4 = t.classe4
GROUP BY d.classe_codigo_4, d.denominacao
HAVING count(*) = 3 AND min(t.vinculos) >= 2000 AND sum(t.ocorrencias) >= 30
""")


def q1b_cidade():
    return _ler("q1b_cidade", f"""
WITH {_cobertura()},
meses_ok AS (
  SELECT extract(year FROM mes)::int AS ano, count(*) FILTER (WHERE ok) AS n_meses
  FROM cobertura
  GROUP BY 1
),
acidentes AS (
  SELECT extract(year FROM f.data_acidente)::int AS ano, count(*) AS ocorrencias
  FROM fato_cat f
  JOIN cobertura c ON c.mes = date_trunc('month', f.data_acidente)::date AND c.ok
  GROUP BY 1
),
vinculos AS (
  SELECT ano, sum(quantidade_vinculos_clt) AS vinculos
  FROM fato_rais
  WHERE ano BETWEEN 2023 AND 2025
  GROUP BY 1
)
SELECT v.ano,
       m.n_meses AS meses_adequados,
       v.vinculos AS vinculos_clt,
       a.ocorrencias,
       round(1000.0 * a.ocorrencias / (v.vinculos * m.n_meses / 12.0), 1) AS taxa
FROM vinculos v
JOIN meses_ok m ON m.ano = v.ano
JOIN acidentes a ON a.ano = v.ano
ORDER BY v.ano
""")


# ---------------------------------------------------------------- Q2


def q2_composicao():
    """Top 30 CBO e CID-10 (categoria) das CATs 2023–2025, com participação em 2023 × 2025."""
    return _ler("q2_composicao", f"""
WITH {_cobertura()},
comparaveis AS (
  SELECT extract(month FROM mes)::int AS mes_do_ano
  FROM cobertura
  WHERE extract(year FROM mes) IN (2023, 2025)
  GROUP BY 1
  HAVING bool_and(ok) AND count(*) = 2
),
cats AS (
  SELECT EXTRACT(YEAR FROM data_acidente)::int AS ano,
         EXTRACT(YEAR FROM data_acidente) IN (2023, 2025)
           AND EXTRACT(MONTH FROM data_acidente)::int IN (SELECT mes_do_ano FROM comparaveis) AS comparavel,
         cbo_2002,
         UPPER(LEFT(REPLACE(BTRIM(cid10), '.', ''), 3)) AS cid_categoria
  FROM fato_cat
  WHERE data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
),
itens AS (
  SELECT 'CBO' AS dimensao, COALESCE(cbo_2002, 'NI') AS codigo, ano, comparavel FROM cats
  UNION ALL
  SELECT 'CID-10', COALESCE(cid_categoria, 'NI'), ano, comparavel FROM cats
),
total AS (
  SELECT dimensao, codigo, COUNT(*) AS n,
         100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY dimensao) AS pct_total,
         100.0 * SUM(COUNT(*)) OVER (PARTITION BY dimensao ORDER BY COUNT(*) DESC, codigo)
               / SUM(COUNT(*)) OVER (PARTITION BY dimensao) AS pct_acumulado,
         ROW_NUMBER() OVER (PARTITION BY dimensao ORDER BY COUNT(*) DESC, codigo) AS ranking
  FROM itens
  GROUP BY dimensao, codigo
),
comp AS (
  SELECT dimensao, codigo, ano,
         100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY dimensao, ano) AS pct
  FROM itens
  WHERE comparavel
  GROUP BY dimensao, codigo, ano
),
pct AS (
  SELECT dimensao, codigo,
         MAX(pct) FILTER (WHERE ano = 2023) AS pct_2023,
         MAX(pct) FILTER (WHERE ano = 2025) AS pct_2025
  FROM comp
  GROUP BY dimensao, codigo
),
descr AS (
  SELECT 'CBO' AS dimensao, cbo_2002 AS codigo, MAX(cbo_2002_descricao) AS descricao
  FROM dim_cbo
  GROUP BY cbo_2002
  UNION ALL
  SELECT 'CID-10', categoria, MAX(descricao_categoria)
  FROM dim_cid10
  GROUP BY categoria
)
SELECT t.dimensao,
       t.ranking,
       t.codigo,
       CASE WHEN t.codigo = 'NI' THEN 'Não informado'
            ELSE COALESCE(d.descricao, 'Sem descrição na tabela de referência') END AS descricao,
       t.n AS cats,
       ROUND(t.pct_total, 1) AS pct_total,
       ROUND(t.pct_acumulado, 1) AS pct_acumulado,
       ROUND(COALESCE(p.pct_2023, 0), 1) AS pct_2023,
       ROUND(COALESCE(p.pct_2025, 0), 1) AS pct_2025
FROM total t
LEFT JOIN pct p ON p.dimensao = t.dimensao AND p.codigo = t.codigo
LEFT JOIN descr d ON d.dimensao = t.dimensao AND d.codigo = t.codigo
WHERE t.ranking <= 30
ORDER BY t.dimensao, t.ranking
""")


# ---------------------------------------------------------------- Q3


def q3a_subnotificacao():
    """Esperado (vínculos × taxa da cidade) − observado, por CNAE com ≥ 3.000 vínculos-ano."""
    return _ler("q3a_subnotificacao", """
WITH acidentes AS (
  SELECT cnae AS classe4, count(*) AS acidentes
  FROM fato_cat
  WHERE data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY cnae
),
vinculos AS (
  SELECT d.classe_codigo_4 AS classe4, sum(r.quantidade_vinculos_clt) AS vinculos_ano
  FROM fato_rais r
  JOIN dim_cnae d ON d.classe_codigo = r.cnae_2_classe
  WHERE r.ano BETWEEN 2023 AND 2025
  GROUP BY d.classe_codigo_4
),
geral AS (
  SELECT (SELECT sum(acidentes) FROM acidentes)::numeric
         / (SELECT sum(vinculos_ano) FROM vinculos) AS taxa
)
SELECT v.classe4 AS cnae,
       d.denominacao AS atividade,
       d.secao,
       v.vinculos_ano,
       coalesce(a.acidentes, 0) AS acidentes,
       round(1000.0 * coalesce(a.acidentes, 0) / v.vinculos_ano, 2) AS por_mil,
       round(v.vinculos_ano * g.taxa, 0) AS esperados,
       round(v.vinculos_ano * g.taxa - coalesce(a.acidentes, 0), 0) AS diferenca,
       round(coalesce(a.acidentes, 0) / (v.vinculos_ano * g.taxa), 2) AS razao
FROM vinculos v
CROSS JOIN geral g
LEFT JOIN acidentes a ON a.classe4 = v.classe4
JOIN dim_cnae d ON d.classe_codigo_4 = v.classe4
WHERE v.vinculos_ano >= 3000
ORDER BY diferenca DESC
""")


def q3b_verificacao():
    return _ler("q3b_verificacao", """
WITH vinculos AS (
  SELECT DISTINCT d.classe_codigo_4 AS classe4
  FROM fato_rais r
  JOIN dim_cnae d ON d.classe_codigo = r.cnae_2_classe
  WHERE r.ano BETWEEN 2023 AND 2025 AND r.quantidade_vinculos_clt > 0
)
SELECT count(*) AS acidentes_cat,
       count(*) FILTER (WHERE v.classe4 IS NULL) AS sem_vinculo,
       round(100.0 * count(*) FILTER (WHERE v.classe4 IS NULL) / count(*), 2) AS pct
FROM fato_cat f
LEFT JOIN vinculos v ON v.classe4 = f.cnae
WHERE f.data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
""").iloc[0]


# ---------------------------------------------------------------- Q4


def q4a_situacao():
    return _ler("q4a_situacao", """
SELECT CASE WHEN sit_trab IN (1, 4, 5) THEN 'Vínculo formal (CLT ou servidor)'
            WHEN sit_trab IN (2, 3, 10) THEN 'Sem registro, autônomo ou avulso'
            WHEN sit_trab IN (6, 7, 8, 9, 11, 12) THEN 'Outras situações'
            ELSE 'Ignorado ou sem informação' END AS grupo,
       count(*) AS notificacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM fato_sinan_acgr
WHERE dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY 1
ORDER BY notificacoes DESC
""")


def q4b_cat_emitida():
    return _ler("q4b_cat_emitida", """
SELECT CASE cat WHEN '1' THEN 'CAT emitida'
                WHEN '2' THEN 'CAT não emitida'
                WHEN '3' THEN 'Não se aplica'
                WHEN '9' THEN 'Ignorado'
                ELSE 'Sem informação' END AS cat_emitida,
       count(*) AS notificacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM fato_sinan_acgr
WHERE sit_trab = 1
  AND dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY cat
ORDER BY notificacoes DESC
""")


def q4c_mensal():
    return _ler("q4c_mensal", f"""
WITH {_cobertura()},
sinan AS (
  SELECT date_trunc('month', dt_acid)::date AS mes, count(*) AS n
  FROM fato_sinan_acgr
  WHERE dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY 1
)
SELECT c.mes,
       c.n AS acidentes_cat,
       coalesce(s.n, 0) AS notificacoes_sinan,
       c.ok AS cobertura_adequada
FROM cobertura c
LEFT JOIN sinan s ON s.mes = c.mes
ORDER BY c.mes
""").astype({"mes": "datetime64[ns]"})


# ---------------------------------------------------------------- referência

SECOES_CNAE = {
    "A": "Agropecuária", "B": "Indústrias extrativas", "C": "Indústria de transformação",
    "D": "Eletricidade e gás", "E": "Água, esgoto e resíduos", "F": "Construção",
    "G": "Comércio", "H": "Transporte e armazenagem", "I": "Alojamento e alimentação",
    "J": "Informação e comunicação", "K": "Finanças e seguros", "L": "Atividades imobiliárias",
    "M": "Atividades profissionais e científicas", "N": "Serviços administrativos",
    "O": "Administração pública", "P": "Educação", "Q": "Saúde e serviços sociais",
    "R": "Artes, cultura e esporte", "S": "Outros serviços", "T": "Serviços domésticos",
    "U": "Organismos internacionais",
}
