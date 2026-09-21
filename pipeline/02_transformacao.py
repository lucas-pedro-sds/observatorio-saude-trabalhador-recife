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

    linha_nao_classificado = pd.DataFrame([{
        "cbo_2002": "999999",
        "cbo_2002_descricao": "Não classificado",
    }])
    df = pd.concat([df, linha_nao_classificado], ignore_index=True)

    return df


def transformar_rais():
    """Estabelecimentos da RAIS em Recife, com tipos protegidos e sem descrições redundantes.

    Descarta cnae_1 (classificação antiga, sem tabela de dimensão no projeto) e todas
    as colunas de descrição de cnae_2/cnae_2_subclasse — essas descrições já vêm de
    transformar_cnae(), então mantê-las aqui só duplicaria texto em ~580 mil linhas.

    Descarta também natureza_estabelecimento: o LEFT JOIN com o dicionário de tradução
    na consulta SQL de coletar_rais() (01_coleta.py) nunca bateu nenhuma linha (100%
    NULL nas 533 mil linhas) — provável descompasso de tipo na condição do JOIN no
    BigQuery. Não fizemos parte da fatia mínima do canvas, então descartamos em vez
    de reprocessar a coleta; fica documentado como limitação conhecida no README.
    """
    colunas_codigo = ["sigla_uf", "id_municipio", "cnae_2", "cnae_2_subclasse", "cep"]
    df = pd.read_csv(
        "dados/brutos/rais/rais_recife_2023_2025.csv",
        dtype={coluna: str for coluna in colunas_codigo},
    )

    colunas_descartadas = [
        "sigla_uf_nome",
        "id_municipio_nome",
        "natureza_estabelecimento",
        "subatividade_ibge",
        "cnae_1",
        "cnae_1_descricao",
        "cnae_1_descricao_grupo",
        "cnae_1_descricao_divisao",
        "cnae_1_descricao_secao",
        "cnae_2_subclasse_descricao_subclasse",
        "cnae_2_subclasse_descricao_classe",
        "cnae_2_subclasse_descricao_grupo",
        "cnae_2_subclasse_descricao_divisao",
        "cnae_2_subclasse_descricao_secao",
    ]
    df = df.drop(columns=colunas_descartadas)
    df["cnae_2_classe"] = df["cnae_2_subclasse"].str[:5]

    return df


def transformar_cat():
    """CAT unificada e filtrada para Recife, com campos sensíveis tratados.

    Descarta: colunas corrompidas/duplicadas na fonte (UF Munic. Acidente,
    CBO.1/CID-10.1/CNAE2.0 Empregador.1 — descrições truncadas, redundantes com as
    tabelas de dimensão), Data Acidente.1/.2 (duplicatas exatas da própria fonte) e
    CNPJ/CEI Empregador (identificador direto da empresa — não pode chegar ao banco
    compartilhado com o time de análise).

    Generaliza: Data Acidente -> ano_acidente/mes_acidente (descarta o dia);
    Data Nascimento -> só ano_nascimento (corte mais forte, por ser mais identificável).

    Nota: o código de "cnae" aqui vem em granularidade diferente do cnae_2_subclasse
    usado na RAIS/CAGED (INSS não usa o mesmo nível de detalhe) — não são diretamente
    comparáveis sem ajuste, documentado como limitação conhecida.
    """
    df = pd.read_csv(
        "dados/brutos/cat/cat_recife_unificado.csv",
        dtype={"CBO": str, "CNAE2.0 Empregador": str},
    )

    df["id_municipio"] = df["Munic Empr"].str.split("-").str[0].str.strip()
    df["cnae"] = df["CNAE2.0 Empregador"].str.zfill(4)

    data_acidente = pd.to_datetime(df["Data Acidente"], format="%d/%m/%Y", errors="coerce")
    df["ano_acidente"] = data_acidente.dt.year
    df["mes_acidente"] = data_acidente.dt.month

    data_nascimento = pd.to_datetime(df["Data Nascimento"], format="%d/%m/%Y", errors="coerce")
    df["ano_nascimento"] = data_nascimento.dt.year

    df = df.rename(columns={
        "CBO": "cbo_2002",
        "CID-10": "cid10",
        "Agente  Causador  Acidente": "agente_causador_acidente",
        "Emitente CAT": "emitente_cat",
        "Espécie do benefício": "especie_beneficio",
        "Filiação Segurado": "filiacao_segurado",
        "Indica Óbito Acidente": "indica_obito_acidente",
        "Natureza da Lesão": "natureza_lesao",
        "Origem de Cadastramento CAT": "origem_cadastramento_cat",
        "Parte Corpo Atingida": "parte_corpo_atingida",
        "Sexo": "sexo",
        "Tipo do Acidente": "tipo_acidente",
        "UF Munic. Empregador": "uf_empregador",
        "Tipo de Empregador": "tipo_empregador",
    })

    for coluna_data in ["Data  Afastamento", "Data Despacho Benefício", "Data Emissão CAT"]:
        df[coluna_data] = pd.to_datetime(df[coluna_data], format="%d/%m/%Y", errors="coerce")
    df = df.rename(columns={
        "Data  Afastamento": "data_afastamento",
        "Data Despacho Benefício": "data_despacho_beneficio",
        "Data Emissão CAT": "data_emissao_cat",
    })

    colunas_descartadas = [
        "UF  Munic.  Acidente",
        "CBO.1",
        "CID-10.1",
        "CNAE2.0 Empregador",
        "CNAE2.0 Empregador.1",
        "Data Acidente",
        "Data Acidente.1",
        "Data Acidente.2",
        "Data Nascimento",
        "Munic Empr",
        "CNPJ/CEI Empregador",
    ]
    df = df.drop(columns=colunas_descartadas)

    return df


def transformar_cnae():
    """Estrutura hierárquica do CNAE 2.0, já reduzida às linhas de Classe (nível
    usado como chave de junção) e com dois códigos limpos (sem ponto/traço):

    - classe_codigo (5 dígitos): chave para cnae_2_classe da RAIS/CAGED.
    - classe_codigo_4 (4 dígitos, sem o dígito verificador): chave para o campo
      "cnae" da CAT, que vem nessa granularidade menor (confirmado: prefixo único,
      sem ambiguidade, em toda a tabela).

    Inclui uma linha sintética "Não classificado" (código 99999/9999) para cobrir
    o placeholder 9999999 que aparece na RAIS/CAGED sem Classe real correspondente.
    """
    df = pd.read_excel(
        "dados/brutos/cnae/CNAE20_EstruturaDetalhada.xls",
        sheet_name="Est. Detalhada CNAE 2.0",
    )

    df = df[df["Seção"] != "Seção"]  # remove linhas de cabeçalho repetidas no meio do arquivo
    df = df.reset_index(drop=True)
    df["Seção"] = df["Seção"].ffill()
    df["Divisão"] = df["Divisão"].ffill()
    df["Grupo"] = df["Grupo"].ffill()

    df["classe_codigo"] = df["Classe"].str.replace(".", "", regex=False).str.replace("-", "", regex=False)
    df["classe_codigo_4"] = df["classe_codigo"].str[:4]

    df = df.rename(columns={"Seção": "secao", "Divisão": "divisao", "Grupo": "grupo", "Denominação": "denominacao"})
    df = df.dropna(subset=["classe_codigo"])  # mantém só as linhas de Classe (as demais já cumpriram seu papel no ffill)
    df = df[["secao", "divisao", "grupo", "classe_codigo", "classe_codigo_4", "denominacao"]]

    linha_nao_classificado = pd.DataFrame([{
        "secao": None,
        "divisao": None,
        "grupo": None,
        "classe_codigo": "99999",
        "classe_codigo_4": "9999",
        "denominacao": "Não classificado",
    }])
    df = pd.concat([df, linha_nao_classificado], ignore_index=True)

    return df

def transformar_caged():
    """Estabelecimentos do CAGED em Recife, sem descrições redundantes.

    Descarta cnae_1 (classificação antiga, sem tabela de dimensão no projeto) e todas
    as colunas de descrição de cnae_2/cnae_2_subclasse — essas descrições já vêm de
    transformar_cnae(), então mantê-las aqui só duplicaria texto em ~1,2 milhão de linhas.

    Descarta também origem_informacao: 100% NULL nesse recorte, sem informação real.
    """
    colunas_codigo = ["cbo_2002", "id_municipio", "cnae_2_secao", "cnae_2_subclasse"]
    df = pd.read_csv(
        "dados/brutos/caged/caged_recife_2023_2025.csv",
        dtype={coluna: str for coluna in colunas_codigo},
    )

    colunas_descartadas = [
        "sigla_uf",
        "sigla_uf_nome",
        "id_municipio_nome",
        "cbo_2002_descricao",
        "cbo_2002_descricao_familia",
        "cbo_2002_descricao_subgrupo",
        "cbo_2002_descricao_subgrupo_principal",
        "cbo_2002_descricao_grande_grupo",
        "cnae_2_subclasse_descricao_subclasse",
        "cnae_2_subclasse_descricao_classe",
        "cnae_2_subclasse_descricao_grupo",
        "cnae_2_subclasse_descricao_divisao",
        "cnae_2_subclasse_descricao_secao",
        "origem_informacao",
    ]
    df = df.drop(columns=colunas_descartadas)
    df["cnae_2_classe"] = df["cnae_2_subclasse"].str[:5]
    return df
