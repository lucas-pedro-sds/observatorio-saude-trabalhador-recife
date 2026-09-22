import os
import argparse
import glob

import basedosdados as bd
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
BILLING_PROJECT_ID = os.getenv("GCP_BILLING_PROJECT_ID")


def coletar_rais():
    """Estabelecimentos da RAIS em Recife/PE, 2023-2025."""
    query = """
    WITH dicionario_natureza_estabelecimento AS (
      SELECT
        chave AS chave_natureza_estabelecimento,
        valor AS descricao_natureza_estabelecimento
      FROM `basedosdados.br_me_rais.dicionario`
      WHERE TRUE
        AND nome_coluna = 'natureza_estabelecimento'
        AND id_tabela = 'microdados_estabelecimentos'
    ),
    dicionario_tamanho_estabelecimento AS (
      SELECT
        chave AS chave_tamanho_estabelecimento,
        valor AS descricao_tamanho_estabelecimento
      FROM `basedosdados.br_me_rais.dicionario`
      WHERE TRUE
        AND nome_coluna = 'tamanho_estabelecimento'
        AND id_tabela = 'microdados_estabelecimentos'
    ),
    dicionario_tipo_estabelecimento AS (
      SELECT
        chave AS chave_tipo_estabelecimento,
        valor AS descricao_tipo_estabelecimento
      FROM `basedosdados.br_me_rais.dicionario`
      WHERE TRUE
        AND nome_coluna = 'tipo_estabelecimento'
        AND id_tabela = 'microdados_estabelecimentos'
    ),
    dicionario_subsetor_ibge AS (
      SELECT
        chave AS chave_subsetor_ibge,
        valor AS descricao_subsetor_ibge
      FROM `basedosdados.br_me_rais.dicionario`
      WHERE TRUE
        AND nome_coluna = 'subsetor_ibge'
        AND id_tabela = 'microdados_estabelecimentos'
    )
    SELECT
      dados.ano as ano,
      dados.sigla_uf AS sigla_uf,
      diretorio_sigla_uf.nome AS sigla_uf_nome,
      dados.id_municipio AS id_municipio,
      diretorio_id_municipio.nome AS id_municipio_nome,
      dados.quantidade_vinculos_ativos as quantidade_vinculos_ativos,
      dados.quantidade_vinculos_clt as quantidade_vinculos_clt,
      dados.quantidade_vinculos_estatutarios as quantidade_vinculos_estatutarios,
      descricao_natureza_estabelecimento AS natureza_estabelecimento,
      dados.natureza_juridica as natureza_juridica,
      descricao_tamanho_estabelecimento AS tamanho_estabelecimento,
      descricao_tipo_estabelecimento AS tipo_estabelecimento,
      dados.indicador_cei_vinculado as indicador_cei_vinculado,
      dados.indicador_pat as indicador_pat,
      dados.indicador_simples as indicador_simples,
      dados.indicador_rais_negativa as indicador_rais_negativa,
      dados.indicador_atividade_ano as indicador_atividade_ano,
      dados.cnae_1 AS cnae_1,
      diretorio_cnae_1.descricao AS cnae_1_descricao,
      diretorio_cnae_1.descricao_grupo AS cnae_1_descricao_grupo,
      diretorio_cnae_1.descricao_divisao AS cnae_1_descricao_divisao,
      diretorio_cnae_1.descricao_secao AS cnae_1_descricao_secao,
      dados.cnae_2 as cnae_2,
      dados.cnae_2_subclasse AS cnae_2_subclasse,
      diretorio_cnae_2_subclasse.descricao_subclasse AS cnae_2_subclasse_descricao_subclasse,
      diretorio_cnae_2_subclasse.descricao_classe AS cnae_2_subclasse_descricao_classe,
      diretorio_cnae_2_subclasse.descricao_grupo AS cnae_2_subclasse_descricao_grupo,
      diretorio_cnae_2_subclasse.descricao_divisao AS cnae_2_subclasse_descricao_divisao,
      diretorio_cnae_2_subclasse.descricao_secao AS cnae_2_subclasse_descricao_secao,
      descricao_subsetor_ibge AS subsetor_ibge,
      dados.subatividade_ibge as subatividade_ibge,
      dados.cep as cep
    FROM `basedosdados.br_me_rais.microdados_estabelecimentos` AS dados
    LEFT JOIN (SELECT DISTINCT sigla,nome FROM `basedosdados.br_bd_diretorios_brasil.uf`) AS diretorio_sigla_uf
      ON dados.sigla_uf = diretorio_sigla_uf.sigla
    LEFT JOIN (SELECT DISTINCT id_municipio,nome FROM `basedosdados.br_bd_diretorios_brasil.municipio`) AS diretorio_id_municipio
      ON dados.id_municipio = diretorio_id_municipio.id_municipio
    LEFT JOIN `dicionario_natureza_estabelecimento`
      ON dados.natureza_estabelecimento = chave_natureza_estabelecimento
    LEFT JOIN `dicionario_tamanho_estabelecimento`
      ON dados.tamanho_estabelecimento = chave_tamanho_estabelecimento
    LEFT JOIN `dicionario_tipo_estabelecimento`
      ON dados.tipo_estabelecimento = chave_tipo_estabelecimento
    LEFT JOIN (SELECT DISTINCT cnae_1,descricao,descricao_grupo,descricao_divisao,descricao_secao FROM `basedosdados.br_bd_diretorios_brasil.cnae_1`) AS diretorio_cnae_1
      ON dados.cnae_1 = diretorio_cnae_1.cnae_1
    LEFT JOIN (SELECT DISTINCT subclasse,descricao_subclasse,descricao_classe,descricao_grupo,descricao_divisao,descricao_secao FROM `basedosdados.br_bd_diretorios_brasil.cnae_2`) AS diretorio_cnae_2_subclasse
      ON dados.cnae_2_subclasse = diretorio_cnae_2_subclasse.subclasse
    LEFT JOIN `dicionario_subsetor_ibge`
      ON dados.subsetor_ibge = chave_subsetor_ibge
    WHERE dados.sigla_uf = 'PE'
      AND dados.id_municipio = '2611606'
      AND dados.ano BETWEEN 2023 AND 2025
    """
    df = bd.read_sql(query, billing_project_id=BILLING_PROJECT_ID)

    destino = "dados/brutos/rais/rais_recife_2023_2025.csv"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    df.to_csv(destino, index=False)

    return df


def coletar_caged():
    """Dados do CAGED em Recife/PE, 2023-2025."""
    query = """
    WITH 
dicionario_categoria AS (
    SELECT
        chave AS chave_categoria,
        valor AS descricao_categoria
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'categoria'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_grau_instrucao AS (
    SELECT
        chave AS chave_grau_instrucao,
        valor AS descricao_grau_instrucao
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'grau_instrucao'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_raca_cor AS (
    SELECT
        chave AS chave_raca_cor,
        valor AS descricao_raca_cor
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'raca_cor'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_sexo AS (
    SELECT
        chave AS chave_sexo,
        valor AS descricao_sexo
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'sexo'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_empregador AS (
    SELECT
        chave AS chave_tipo_empregador,
        valor AS descricao_tipo_empregador
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_empregador'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_estabelecimento AS (
    SELECT
        chave AS chave_tipo_estabelecimento,
        valor AS descricao_tipo_estabelecimento
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_estabelecimento'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_movimentacao AS (
    SELECT
        chave AS chave_tipo_movimentacao,
        valor AS descricao_tipo_movimentacao
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_movimentacao'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_deficiencia AS (
    SELECT
        chave AS chave_tipo_deficiencia,
        valor AS descricao_tipo_deficiencia
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_deficiencia'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_indicador_trabalho_intermitente AS (
    SELECT
        chave AS chave_indicador_trabalho_intermitente,
        valor AS descricao_indicador_trabalho_intermitente
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'indicador_trabalho_intermitente'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_indicador_trabalho_parcial AS (
    SELECT
        chave AS chave_indicador_trabalho_parcial,
        valor AS descricao_indicador_trabalho_parcial
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'indicador_trabalho_parcial'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_indicador_aprendiz AS (
    SELECT
        chave AS chave_indicador_aprendiz,
        valor AS descricao_indicador_aprendiz
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'indicador_aprendiz'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_origem_informacao AS (
    SELECT
        chave AS chave_origem_informacao,
        valor AS descricao_origem_informacao
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'origem_informacao'
        AND id_tabela = 'microdados_movimentacao'
)
SELECT
    dados.ano as ano,
    dados.mes as mes,
    dados.sigla_uf AS sigla_uf,
    diretorio_sigla_uf.nome AS sigla_uf_nome,
    dados.id_municipio AS id_municipio,
    diretorio_id_municipio.nome AS id_municipio_nome,
    dados.cnae_2_secao as cnae_2_secao,
    dados.cnae_2_subclasse AS cnae_2_subclasse,
    diretorio_cnae_2_subclasse.descricao_subclasse AS cnae_2_subclasse_descricao_subclasse,
    diretorio_cnae_2_subclasse.descricao_classe AS cnae_2_subclasse_descricao_classe,
    diretorio_cnae_2_subclasse.descricao_grupo AS cnae_2_subclasse_descricao_grupo,
    diretorio_cnae_2_subclasse.descricao_divisao AS cnae_2_subclasse_descricao_divisao,
    diretorio_cnae_2_subclasse.descricao_secao AS cnae_2_subclasse_descricao_secao,
    dados.saldo_movimentacao as saldo_movimentacao,
    dados.cbo_2002 AS cbo_2002,
    diretorio_cbo_2002.descricao AS cbo_2002_descricao,
    diretorio_cbo_2002.descricao_familia AS cbo_2002_descricao_familia,
    diretorio_cbo_2002.descricao_subgrupo AS cbo_2002_descricao_subgrupo,
    diretorio_cbo_2002.descricao_subgrupo_principal AS cbo_2002_descricao_subgrupo_principal,
    diretorio_cbo_2002.descricao_grande_grupo AS cbo_2002_descricao_grande_grupo,
    descricao_categoria AS categoria,
    descricao_grau_instrucao AS grau_instrucao,
    dados.idade as idade,
    dados.horas_contratuais as horas_contratuais,
    descricao_raca_cor AS raca_cor,
    descricao_sexo AS sexo,
    descricao_tipo_empregador AS tipo_empregador,
    descricao_tipo_estabelecimento AS tipo_estabelecimento,
    descricao_tipo_movimentacao AS tipo_movimentacao,
    descricao_tipo_deficiencia AS tipo_deficiencia,
    descricao_indicador_trabalho_intermitente AS indicador_trabalho_intermitente,
    descricao_indicador_trabalho_parcial AS indicador_trabalho_parcial,
    dados.salario_mensal as salario_mensal,
    dados.tamanho_estabelecimento_janeiro as tamanho_estabelecimento_janeiro,
    descricao_indicador_aprendiz AS indicador_aprendiz,
    descricao_origem_informacao AS origem_informacao,
    dados.indicador_fora_prazo as indicador_fora_prazo
FROM `basedosdados.br_me_caged.microdados_movimentacao` AS dados
LEFT JOIN (SELECT DISTINCT sigla,nome  FROM `basedosdados.br_bd_diretorios_brasil.uf`) AS diretorio_sigla_uf
    ON dados.sigla_uf = diretorio_sigla_uf.sigla
LEFT JOIN (SELECT DISTINCT id_municipio,nome  FROM `basedosdados.br_bd_diretorios_brasil.municipio`) AS diretorio_id_municipio
    ON dados.id_municipio = diretorio_id_municipio.id_municipio
LEFT JOIN (SELECT DISTINCT subclasse,descricao_subclasse,descricao_classe,descricao_grupo,descricao_divisao,descricao_secao  FROM `basedosdados.br_bd_diretorios_brasil.cnae_2`) AS diretorio_cnae_2_subclasse
    ON dados.cnae_2_subclasse = diretorio_cnae_2_subclasse.subclasse
LEFT JOIN (SELECT DISTINCT cbo_2002,descricao,descricao_familia,descricao_subgrupo,descricao_subgrupo_principal,descricao_grande_grupo  FROM `basedosdados.br_bd_diretorios_brasil.cbo_2002`) AS diretorio_cbo_2002
    ON dados.cbo_2002 = diretorio_cbo_2002.cbo_2002
LEFT JOIN `dicionario_categoria`
    ON dados.categoria = chave_categoria
LEFT JOIN `dicionario_grau_instrucao`
    ON dados.grau_instrucao = chave_grau_instrucao
LEFT JOIN `dicionario_raca_cor`
    ON dados.raca_cor = chave_raca_cor
LEFT JOIN `dicionario_sexo`
    ON dados.sexo = chave_sexo
LEFT JOIN `dicionario_tipo_empregador`
    ON dados.tipo_empregador = chave_tipo_empregador
LEFT JOIN `dicionario_tipo_estabelecimento`
    ON dados.tipo_estabelecimento = chave_tipo_estabelecimento
LEFT JOIN `dicionario_tipo_movimentacao`
    ON dados.tipo_movimentacao = chave_tipo_movimentacao
LEFT JOIN `dicionario_tipo_deficiencia`
    ON dados.tipo_deficiencia = chave_tipo_deficiencia
LEFT JOIN `dicionario_indicador_trabalho_intermitente`
    ON dados.indicador_trabalho_intermitente = chave_indicador_trabalho_intermitente
LEFT JOIN `dicionario_indicador_trabalho_parcial`
    ON dados.indicador_trabalho_parcial = chave_indicador_trabalho_parcial
LEFT JOIN `dicionario_indicador_aprendiz`
    ON dados.indicador_aprendiz = chave_indicador_aprendiz
LEFT JOIN `dicionario_origem_informacao`
    ON dados.origem_informacao = chave_origem_informacao
WHERE dados.sigla_uf = 'PE'
  AND dados.id_municipio = '2611606'
  AND dados.ano BETWEEN 2023 AND 2025
    """
    df = bd.read_sql(query, billing_project_id=BILLING_PROJECT_ID)

    destino = "dados/brutos/caged/caged_recife_2023_2025.csv"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    df.to_csv(destino, index=False)

    return df


def coletar_cat():
    """Comunicações de Acidente de Trabalho (CAT) em Recife/PE, unificando os arquivos mensais.

    A coluna "UF Munic. Acidente" vem corrompida na fonte (INSS, valores tipo
    "{ class}" em boa parte das linhas), então o filtro geográfico usa "Munic Empr"
    (município do empregador) como aproximação — ver limitação registrada no README.
    Código 261160 = Recife (código IBGE truncado, sem o dígito verificador).
    """
    arquivos = sorted(glob.glob("dados/brutos/cat/D.SDA.PDA.005.CAT.*.csv"))
    partes = [pd.read_csv(arquivo, sep=";", encoding="latin1") for arquivo in arquivos]
    df = pd.concat(partes, ignore_index=True)
    df = df[df["Munic Empr"].str.startswith("261160", na=False)]

    destino = "dados/brutos/cat/cat_recife_unificado.csv"
    df.to_csv(destino, index=False)

    return df


def coletar_cid10():
    """Tabela de referência do CID-10 (código de subcategoria/categoria + descrições).

    Não tem filtro geográfico — é uma classificação internacional, não específica
    de Recife. Vem do mesmo diretório do basedosdados usado para CNAE/CBO.
    """
    query = """
    SELECT
      subcategoria,
      descricao_subcategoria,
      categoria,
      descricao_categoria,
      capitulo,
      descricao_capitulo
    FROM `basedosdados.br_bd_diretorios_brasil.cid_10`
    """
    df = bd.read_sql(query, billing_project_id=BILLING_PROJECT_ID)

    destino = "dados/brutos/cid10/cid10.csv"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    df.to_csv(destino, index=False)

    return df


def _baixar_grupo_sinan(grupo, anos):
    """Baixa e converte arquivos PRELIM do SINAN para um grupo/anos dados.

    A função de conveniência do pysus (sinan()) está retornando vazio nessa versão
    (confirmado: bug/config da biblioteca, não ausência de dado — os arquivos existem
    no FTP do DATASUS). Contorna baixando via ftplib direto e convertendo com
    pyreaddbc, dependência que o próprio pysus já traz. Arquivos são nacionais
    (<GRUPO>BR<ano>.dbc, não por estado) — filtragem geográfica é feita por quem chama.
    """
    import ftplib

    import pyreaddbc
    from dbfread import DBF

    pasta = "dados/brutos/sinan"
    os.makedirs(pasta, exist_ok=True)

    partes = []
    ftp = ftplib.FTP("ftp.datasus.gov.br", timeout=60)
    ftp.login()
    for ano in anos:
        nome = f"{grupo}BR{ano}"
        caminho_dbc = f"{pasta}/{nome}.dbc"
        caminho_dbf = f"{pasta}/{nome}.dbf"
        with open(caminho_dbc, "wb") as arquivo:
            ftp.retrbinary(f"RETR /dissemin/publicos/SINAN/DADOS/PRELIM/{nome}.dbc", arquivo.write)
        pyreaddbc.dbc2dbf(caminho_dbc, caminho_dbf)
        tabela = DBF(caminho_dbf, encoding="latin1")
        partes.append(pd.DataFrame(iter(tabela)))
    ftp.quit()

    return pd.concat(partes, ignore_index=True)


def coletar_sinan_acgr():
    """Notificações de Acidente de Trabalho geral (SINAN/ACGR) em Recife, 2023-2025.

    2023-2025 só existem como PRELIM (dado preliminar, ainda não consolidado pelo
    Ministério da Saúde) — ver limitação no README.

    Filtra por MUN_ACID (local real do acidente), não ID_MUNICIP (local da
    notificação, que infla o número por Recife ser polo regional de saúde).
    """
    df = _baixar_grupo_sinan("ACGR", ["23", "24", "25"])
    df = df[df["MUN_ACID"].astype(str) == "261160"]

    destino = "dados/brutos/sinan/sinan_acgr_recife_2023_2025.csv"
    df.to_csv(destino, index=False)

    return df


def coletar_sinan_acbi():
    """Notificações de Acidente com Material Biológico (SINAN/ACBI) em Recife, 2023-2025.

    Formulário diferente do ACGR (68 colunas, focado em protocolo de biossegurança —
    tipo de exposição, EPI usado, esquema vacinal — não em diagnóstico CID). Mesma
    limitação de dado PRELIM que o ACGR.

    Não existe MUN_ACID nesse formulário (só faz sentido para acidente geral, não
    exposição biológica). Filtra por MUN_EMP (município do empregador) como proxy do
    local do acidente — mesma lógica já usada na CAT, e pelo mesmo motivo: é a melhor
    aproximação disponível, não o local exato. ID_MUNICIP (notificação) infla o número
    por Recife ser polo regional de saúde (2.347 vs. 1.706 em teste com 2023).
    """
    df = _baixar_grupo_sinan("ACBI", ["23", "24", "25"])
    df = df[df["MUN_EMP"].astype(str) == "261160"]

    destino = "dados/brutos/sinan/sinan_acbi_recife_2023_2025.csv"
    df.to_csv(destino, index=False)

    return df


def carregar_cbo():
    """Tabela de ocupações CBO 2002 (dimensão usada no join com CAGED)."""
    return pd.read_csv(
        "dados/brutos/cbo/ESTRUTURA CBO/CBO2002 - Ocupacao.csv",
        sep=";",
        encoding="latin1",
    )


def carregar_cnae():
    """Estrutura hierárquica do CNAE 2.0 (Seção/Divisão/Grupo/Classe)."""
    return pd.read_excel("dados/brutos/cnae/CNAE20_EstruturaDetalhada.xls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta os dados brutos do observatório")
    parser.add_argument(
        "fontes",
        nargs="*",
        choices=["rais", "caged", "cat", "cbo", "cnae", "cid10", "sinan_acgr", "sinan_acbi"],
        help="fontes a coletar (padrão: todas)",
    )
    args = parser.parse_args()
    fontes = args.fontes or ["rais", "caged", "cat", "cbo", "cnae", "cid10", "sinan_acgr", "sinan_acbi"]

    if "rais" in fontes:
        coletar_rais()
    if "caged" in fontes:
        coletar_caged()
    if "cat" in fontes:
        coletar_cat()
    if "cbo" in fontes:
        carregar_cbo()
    if "cnae" in fontes:
        carregar_cnae()
    if "cid10" in fontes:
        coletar_cid10()
    if "sinan_acgr" in fontes:
        coletar_sinan_acgr()
    if "sinan_acbi" in fontes:
        coletar_sinan_acbi()
