import argparse
import importlib
import os
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(__file__))
transformacao = importlib.import_module("02_transformacao")

load_dotenv()

# Ordem fixa: dimensões antes de fatos, porque os fatos têm FOREIGN KEY para elas.
TABELAS = {
    "dim_cbo": transformacao.transformar_cbo,
    "dim_cnae": transformacao.transformar_cnae,
    "fato_rais": transformacao.transformar_rais,
    "fato_caged": transformacao.transformar_caged,
    "fato_cat": transformacao.transformar_cat,
}


def criar_engine():
    usuario = os.getenv("DB_USER")
    senha = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    porta = os.getenv("DB_PORT")
    banco = os.getenv("DB_NAME")
    return create_engine(f"postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{banco}?sslmode=require")


def carregar(nomes_tabelas, engine):
    """Limpa (TRUNCATE) e recarrega cada tabela, na ordem de dependência.

    TRUNCATE ... CASCADE é usado porque dim_cbo/dim_cnae têm fatos referenciando
    elas via FOREIGN KEY — recarregar uma dimensão sozinha também esvazia os fatos
    dependentes (efeito esperado: se a dimensão mudou, os fatos ligados a ela
    precisam ser recarregados de qualquer forma).
    """
    with engine.begin() as conexao:
        for nome in nomes_tabelas:
            conexao.execute(text(f"TRUNCATE TABLE {nome} RESTART IDENTITY CASCADE"))

    for nome in nomes_tabelas:
        df = TABELAS[nome]()
        _carregar_em_lotes(nome, df, engine)
        print(f"{nome}: {len(df)} linhas carregadas")


def _carregar_em_lotes(nome, df, engine, tamanho_lote=100_000, tentativas=3):
    """Insere em pedaços menores, cada um com seu próprio commit.

    Necessário porque um to_sql() único para uma tabela de mais de 1 milhão de
    linhas é UMA transação gigante — se a conexão cair no meio (aconteceu com o
    Aiven, plano gratuito com recursos limitados), a transação inteira é desfeita
    e todo o progresso se perde. Em lotes, só o lote atual precisa ser refeito.
    """
    total = len(df)
    for inicio in range(0, total, tamanho_lote):
        lote = df.iloc[inicio : inicio + tamanho_lote]
        for tentativa in range(1, tentativas + 1):
            try:
                lote.to_sql(nome, engine, if_exists="append", index=False, chunksize=5000, method="multi")
                break
            except Exception as erro:
                if tentativa == tentativas:
                    raise
                print(f"{nome}: falha no lote {inicio}-{inicio + len(lote)} (tentativa {tentativa}/{tentativas}): {erro}")
                time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carrega os dados tratados no banco Postgres")
    parser.add_argument(
        "tabelas",
        nargs="*",
        choices=list(TABELAS.keys()),
        help="tabelas a carregar (padrão: todas, na ordem dimensão -> fato)",
    )
    args = parser.parse_args()
    selecionadas = set(args.tabelas) if args.tabelas else set(TABELAS.keys())
    ordem = [nome for nome in TABELAS if nome in selecionadas]

    carregar(ordem, criar_engine())
