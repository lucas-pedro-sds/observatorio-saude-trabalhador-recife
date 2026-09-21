import pandas as pd


def transformar_cbo():
    """Tabela de ocupações CBO 2002, pronta para join com CAGED/RAIS.
    """
    df = pd.read_csv(
        "dados/brutos/cbo/ESTRUTURA CBO/CBO2002 - Ocupacao.csv",
        sep=";",
        encoding="latin1",
        dtype={"CODIGO": str},
    )
    df = df.rename(columns={"CODIGO": "cbo_2002", "TITULO": "cbo_2002_descricao"})
    return df


def transformar_cnae():
    """Estrutura hierárquica do CNAE 2.0 (Seção/Divisão/Grupo/Classe).
    """
    df = pd.read_excel(
        "dados/brutos/cnae/CNAE20_EstruturaDetalhada.xls",
        sheet_name="Est. Detalhada CNAE 2.0",

    )
    """ Foi encontrado um problema no dataframe, onde algumas linhas estavam com valores dos títulos das colunas 
    "Seção", "Divisão" e "Grupo" vazios. Para resolver esse problema, utilizamos um filtro dentro do dataframe e exclusão dos valores.
    Depois disso, resetamos os índices do dataframe para que eles fiquem sequenciais e consistentes. Em seguida, utilizamos o método ffill() para preencher os valores vazios das colunas "Seção", "Divisão" e "Grupo" com os valores anteriores, garantindo que cada linha tenha informações completas sobre a hierarquia do CNAE. 
    Por fim, renomeamos as colunas para nomes mais amigáveis e retornamos o dataframe transformado.
    """

    df = df[df["Seção"] != 'Seção']  # Filtra as linhas onde a coluna "Seção" não é igual a 'Seção'
    df = df.reset_index(drop=True)
    df["Seção"] = df["Secao"].ffill()
    df["Divisão"] = df["Divisao"].ffill()
    df["Grupo"] = df["Grupo"].ffill()
    df["Denominação"] = df["Denominacao"].ffill()
    df = df.rename(columns={"Seção": "secao", "Divisão": "divisao", "Grupo": "grupo", "Classe": "classe"})
    return df