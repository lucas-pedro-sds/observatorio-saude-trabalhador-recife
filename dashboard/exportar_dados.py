"""Salva em dashboard/snapshot/ o resultado de todas as consultas do dashboard.

É a cópia que o app usa quando não há banco: no Streamlit Community Cloud e no plano B
offline da apresentação. São só tabelas já agregadas (contagens, taxas e percentuais),
sem nenhum registro individual.

Rodar da raiz do repositório, com o banco acessível pelo .env, sempre que os dados ou
as consultas de dashboard/dados.py mudarem, e fazer commit da pasta snapshot/:

    python dashboard/exportar_dados.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
logging.getLogger("streamlit").setLevel(logging.ERROR)  # avisos de "rodando fora do Streamlit"

import dados  # noqa: E402

CONSULTAS = [
    dados.resumo_cat, dados.cat_por_secao, dados.q0_cobertura, dados.q1a_setores, dados.q1b_cidade,
    dados.q2_composicao, dados.q3a_subnotificacao, dados.q3b_verificacao, dados.q4a_situacao,
    dados.q4b_cat_emitida, dados.q4c_mensal,
]

dados.PASTA_COPIA.mkdir(exist_ok=True)
dados.EXPORTAR_PARA = dados.PASTA_COPIA

for consulta in CONSULTAS:
    consulta()
    linhas = len(dados.pd.read_parquet(dados.PASTA_COPIA / f"{consulta.__name__}.parquet"))
    print(f"  {consulta.__name__}: {linhas} linhas")

(dados.PASTA_COPIA / "_info.json").write_text(
    json.dumps({"gerado_em": datetime.now().isoformat(timespec="seconds")}, indent=2) + "\n", encoding="utf-8"
)
print(f"Cópia salva em {dados.PASTA_COPIA}")
