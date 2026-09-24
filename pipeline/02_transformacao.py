import os

import pandas as pd

# Pasta raiz onde estão as subpastas dos dados brutos (cat, cnae, sinan, cbo, caged, cid10, rais).
BRUTOS_DIR = r"SEU-CAMINHO"


def transformar_cbo():
    """Tabela de ocupações CBO 2002, pronta para join com CAGED/RAIS.
    """
    df = pd.read_csv(
        os.path.join(BRUTOS_DIR, "cbo", "ESTRUTURA CBO", "CBO2002 - Ocupacao.csv"),
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
        os.path.join(BRUTOS_DIR, "rais", "rais_recife_2023_2025.csv"),
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

    Data Acidente é mantida exata (data_acidente) — decisão do time em reunião de
    21/09/2026, revertendo a generalização anterior (ano/mês) para permitir análise
    por dia. Ciente do trade-off de privacidade já discutido (data + sexo + CNAE
    podem reidentificar em empresas pequenas); ver README para o registro completo.
    Data Nascimento continua generalizada para só ano_nascimento (não foi solicitado
    reverter essa, e é o campo mais identificável dos dois).

    Nota: o código de "cnae" aqui vem em granularidade diferente do cnae_2_subclasse
    usado na RAIS/CAGED (INSS não usa o mesmo nível de detalhe) — não são diretamente
    comparáveis sem ajuste, documentado como limitação conhecida.
    """
    df = pd.read_csv(
        os.path.join(BRUTOS_DIR, "cat", "cat_recife_unificado.csv"),
        dtype={"CBO": str, "CNAE2.0 Empregador": str},
    )

    df["id_municipio"] = df["Munic Empr"].str.split("-").str[0].str.strip()
    df["cnae"] = df["CNAE2.0 Empregador"].str.zfill(4)

    df["data_acidente"] = pd.to_datetime(df["Data Acidente"], format="%d/%m/%Y", errors="coerce")

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
        os.path.join(BRUTOS_DIR, "cnae", "CNAE20_EstruturaDetalhada.xls"),
        sheet_name="Est. Detalhada CNAE 2.0",
    )

    # O arquivo bruto tem dois tipos de linha-lixo repetidos periodicamente (herança de
    # exportação paginada): (1) cabeçalho repetido, onde Grupo == "Grupo" literalmente;
    # (2) título repetido ("2.2 - Estrutura detalhada..."), onde só Seção tem texto e
    # Divisão/Grupo/Classe/Denominação ficam NaN. Se não remover as duas ANTES do
    # ffill, o texto do tipo (2) vaza via ffill para as linhas de Classe reais logo
    # abaixo dele, corrompendo a coluna secao silenciosamente.
    df = df[df["Grupo"] != "Grupo"]
    df = df[df["Denominação"].notna() | df["Seção"].isna()]
    df = df.reset_index(drop=True)
    df["Seção"] = df["Seção"].ffill()
    df["Divisão"] = df["Divisão"].ffill()
    df["Grupo"] = df["Grupo"].ffill()

    # Divisão vem com tipo inconsistente no Excel bruto (algumas células como texto,
    # outras como número) e Grupo vem com ponto ("01.1") — normaliza os dois pra texto
    # limpo, do mesmo jeito que já fazemos com a Classe.
    df["Divisão"] = df["Divisão"].apply(lambda v: str(v).zfill(2) if pd.notna(v) else v)
    df["Grupo"] = df["Grupo"].apply(lambda v: v.replace(".", "") if pd.notna(v) else v)

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

def transformar_cid10():
    """Tabela de referência CID-10 (subcategoria = chave de junção, 4 caracteres)."""
    return pd.read_csv(
        os.path.join(BRUTOS_DIR, "cid10", "cid10.csv"),
        dtype={"subcategoria": str, "categoria": str},
    )


def transformar_sinan_acgr():
    """Notificações de Acidente de Trabalho (SINAN/ACGR) em Recife, 2023-2025.

    Protege como texto os códigos que podem ter zero à esquerda ou letras
    (municípios, CNAE, CID-10). Mantém todas as colunas originais (renomeadas para
    minúsculo) — a fonte tem 54 campos e não é óbvio quais o time de análise vai
    usar; a decisão de descartar alguma fica para quando houver uma pergunta
    analítica concreta que não precise dela.

    2023-2025 são dados PRELIM (preliminares, não consolidados pelo Ministério da
    Saúde) — ver limitação no README.
    """
    colunas_codigo = [
        "ID_MUNICIP", "ID_REGIONA", "ID_UNIDADE", "SG_UF_NOT", "ID_MN_RESI",
        "ID_RG_RESI", "ID_PAIS", "ID_OCUPA_N", "CNAE", "UF_EMP", "MUN_EMP",
        "CNAE_PRIN", "UF_ACID", "MUN_ACID", "CID_ACID", "TIPO_ACID", "UF_ATENDE",
        "MUN_ATENDE", "UNI_ATENDE", "CID_LESAO", "CAT",
    ]
    df = pd.read_csv(
        os.path.join(BRUTOS_DIR, "sinan", "sinan_acgr_recife_2023_2025.csv"),
        dtype={coluna: str for coluna in colunas_codigo},
    )
    df.columns = df.columns.str.lower()

    # CID_ACID/CID_LESAO vêm com "." no lugar do 4º caractere quando o código é só de
    # categoria (3 caracteres, ex: "V89."), não subcategoria (4 caracteres, "A000").
    # Sem isso, nenhuma junção com dim_cid10 bateria para esses casos (confirmado:
    # ~24% das notificações usam código de categoria, não subcategoria).
    df["cid_acid"] = df["cid_acid"].str.rstrip(".")
    df["cid_lesao"] = df["cid_lesao"].str.rstrip(".")

    for coluna_data in ["dt_notific", "dt_acid", "dt_atende", "dt_obito"]:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce")

    return df


def transformar_sinan_acbi():
    """Notificações de Acidente com Material Biológico (SINAN/ACBI) em Recife, 2023-2025.

    Formulário diferente do ACGR — sem CID-10, focado em protocolo de biossegurança
    (tipo de exposição, EPI usado, esquema vacinal). Descarta EVO_OUTR e DT_OBITO:
    100% vazias nesse recorte (mesmo padrão de outras fontes — sem indício de bug,
    parecem campos não populados pela fonte para Recife/período filtrado).

    2023-2025 são dados PRELIM (preliminares, não consolidados pelo Ministério da
    Saúde) — ver limitação no README.
    """
    colunas_codigo = [
        "ID_MUNICIP", "ID_REGIONA", "ID_UNIDADE", "SG_UF_NOT", "ID_MN_RESI",
        "ID_RG_RESI", "ID_PAIS", "ID_OCUPA_N", "CNAE", "UF_EMP", "MUN_EMP",
        "TIPO_ACID", "CAT",
    ]
    df = pd.read_csv(
        os.path.join(BRUTOS_DIR, "sinan", "sinan_acbi_recife_2023_2025.csv"),
        dtype={coluna: str for coluna in colunas_codigo},
    )
    df.columns = df.columns.str.lower()

    df = df.drop(columns=["evo_outr", "dt_obito"])

    for coluna_data in ["dt_notific", "dt_acid"]:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce")

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
        os.path.join(BRUTOS_DIR, "caged", "caged_recife_2023_2025.csv"),
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