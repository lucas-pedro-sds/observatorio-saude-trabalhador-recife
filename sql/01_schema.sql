-- Schema do Observatório de Saúde do Trabalhador (Recife/VISAT)
-- Modelo fato/dimensão: dim_* são tabelas de referência (poucas linhas, reutilizadas
-- via JOIN); fato_* são os eventos observados (uma linha por acidente/vínculo/movimentação).
--
-- Ordem de criação importa: dimensões primeiro, porque os fatos referenciam elas.

-- ============================================================
-- DIMENSÕES
-- ============================================================

CREATE TABLE dim_cbo (
    cbo_2002 VARCHAR(6) PRIMARY KEY,
    cbo_2002_descricao TEXT NOT NULL
);

CREATE TABLE dim_cnae (
    classe_codigo VARCHAR(5) PRIMARY KEY,       -- chave para cnae_2_classe (RAIS/CAGED)
    classe_codigo_4 VARCHAR(4) NOT NULL UNIQUE, -- chave para cnae (CAT, granularidade menor)
    secao VARCHAR(1),
    divisao VARCHAR(2),
    grupo VARCHAR(3),
    denominacao TEXT NOT NULL
);

-- Sem FK direta de cid_acid/cid_lesao (fato_sinan) para cá: um código pode ser de
-- categoria (3 caracteres) ou subcategoria (4 caracteres) — uma FK só cobre uma
-- coluna. Quem consultar faz LEFT JOIN em categoria OU subcategoria.
CREATE TABLE dim_cid10 (
    subcategoria VARCHAR(4) PRIMARY KEY,
    descricao_subcategoria TEXT,
    categoria VARCHAR(3) NOT NULL,
    descricao_categoria TEXT,
    capitulo VARCHAR(5),
    descricao_capitulo TEXT
);

CREATE INDEX idx_dim_cid10_categoria ON dim_cid10 (categoria);

-- ============================================================
-- FATOS
-- ============================================================

-- Estabelecimentos da RAIS em Recife (2023-2025). Uma linha por estabelecimento/ano.
CREATE TABLE fato_rais (
    id BIGSERIAL PRIMARY KEY,
    ano SMALLINT NOT NULL,
    sigla_uf VARCHAR(2) NOT NULL,
    id_municipio VARCHAR(7) NOT NULL,
    quantidade_vinculos_ativos INTEGER,
    quantidade_vinculos_clt INTEGER,
    quantidade_vinculos_estatutarios INTEGER,
    natureza_juridica INTEGER,
    tamanho_estabelecimento TEXT,
    tipo_estabelecimento TEXT,
    indicador_cei_vinculado SMALLINT,
    indicador_pat SMALLINT,
    indicador_simples SMALLINT,
    indicador_rais_negativa SMALLINT,
    indicador_atividade_ano SMALLINT,
    cnae_2 VARCHAR(5),
    cnae_2_subclasse VARCHAR(7),
    cnae_2_classe VARCHAR(5) REFERENCES dim_cnae (classe_codigo),
    subsetor_ibge TEXT,
    cep VARCHAR(8)
);

CREATE INDEX idx_fato_rais_cnae_2_classe ON fato_rais (cnae_2_classe);
CREATE INDEX idx_fato_rais_ano ON fato_rais (ano);

-- Movimentações de emprego do CAGED em Recife (2023-2025). Uma linha por movimentação.
-- cbo_2002 não tem FOREIGN KEY: ~0,03% dos códigos (fora o placeholder 999999, já
-- coberto por um registro em dim_cbo) não existem na tabela de referência baixada —
-- ver "Limitações conhecidas dos dados" no README. Enforcar FK aqui quebraria a carga
-- por causa desses poucos códigos órfãos; quem consultar usa LEFT JOIN.
CREATE TABLE fato_caged (
    id BIGSERIAL PRIMARY KEY,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    id_municipio VARCHAR(7) NOT NULL,
    cnae_2_secao VARCHAR(1),
    cnae_2_subclasse VARCHAR(7),
    cnae_2_classe VARCHAR(5) REFERENCES dim_cnae (classe_codigo),
    saldo_movimentacao INTEGER,
    cbo_2002 VARCHAR(6),
    categoria TEXT,
    grau_instrucao TEXT,
    idade SMALLINT,
    horas_contratuais NUMERIC(5, 2),
    raca_cor TEXT,
    sexo VARCHAR(20),
    tipo_empregador TEXT,
    tipo_estabelecimento TEXT,
    tipo_movimentacao TEXT,
    tipo_deficiencia TEXT,
    indicador_trabalho_intermitente TEXT,
    indicador_trabalho_parcial TEXT,
    salario_mensal NUMERIC(12, 2),
    tamanho_estabelecimento_janeiro INTEGER,
    indicador_aprendiz TEXT,
    indicador_fora_prazo SMALLINT
);

CREATE INDEX idx_fato_caged_cnae_2_classe ON fato_caged (cnae_2_classe);
CREATE INDEX idx_fato_caged_cbo_2002 ON fato_caged (cbo_2002);
CREATE INDEX idx_fato_caged_ano_mes ON fato_caged (ano, mes);

-- Comunicações de Acidente de Trabalho (CAT) em Recife (2023-2025). Uma linha por CAT.
--
-- Campos sensíveis já tratados na transformação (ver 02_transformacao.py e README):
-- CNPJ/CEI do empregador foi descartado. Data de nascimento segue generalizada para
-- só o ano (ano_nascimento). Data do acidente é exata (data_acidente) por decisão do
-- time em 21/09/2026, revertendo a generalização anterior — ver README para o
-- trade-off de privacidade envolvido. As datas administrativas (afastamento, despacho
-- de benefício, emissão do CAT) também são exatas.
--
-- id_municipio aqui tem 6 dígitos (sem o dígito verificador), diferente dos 7 dígitos
-- da RAIS/CAGED — mesma fonte (INSS), formato diferente, documentado como limitação.
-- cbo_2002 e cid10 não têm FOREIGN KEY: cbo_2002 tem uma pequena fração de códigos
-- órfãos (mesmo motivo do fato_caged); cid10 não tem tabela de dimensão no projeto
-- ainda (fica para quando a base de CID-10 for incorporada).
CREATE TABLE fato_cat (
    id BIGSERIAL PRIMARY KEY,
    data_acidente DATE NOT NULL,
    ano_nascimento SMALLINT,
    id_municipio VARCHAR(6) NOT NULL,
    cbo_2002 VARCHAR(6),
    cid10 VARCHAR(10),
    cnae VARCHAR(4) REFERENCES dim_cnae (classe_codigo_4),
    agente_causador_acidente TEXT,
    emitente_cat TEXT,
    especie_beneficio TEXT,
    filiacao_segurado TEXT,
    indica_obito_acidente TEXT,
    natureza_lesao TEXT,
    origem_cadastramento_cat TEXT,
    parte_corpo_atingida TEXT,
    sexo VARCHAR(20),
    tipo_acidente TEXT,
    uf_empregador TEXT,
    tipo_empregador TEXT,
    data_afastamento DATE,
    data_despacho_beneficio DATE,
    data_emissao_cat DATE
);

CREATE INDEX idx_fato_cat_cnae ON fato_cat (cnae);
CREATE INDEX idx_fato_cat_data_acidente ON fato_cat (data_acidente);

-- Notificações de Acidente de Trabalho do SINAN (grupo ACGR) em Recife, 2023-2025.
-- Uma linha por notificação. Dados PRELIM (preliminares, ainda não consolidados pelo
-- Ministério da Saúde) — ver "Limitações conhecidas dos dados" no README.
--
-- mun_acid é o município de onde o acidente aconteceu de verdade (diferente de
-- id_municip, que é o município de notificação — mais impreciso, pois Recife é polo
-- regional de saúde e recebe notificação de gente de outras cidades).
--
-- cid_acid/cid_lesao não têm FK (ver comentário em dim_cid10). cnae/cnae_prin/
-- id_ocupa_n (CBO) também não têm FK: granularidade e formato ainda não conferidos
-- contra dim_cnae/dim_cbo — fica para quando houver necessidade real de JOIN.
--
-- Mantém todas as colunas da fonte (54, ver transformar_sinan() em 02_transformacao.py)
-- sem descartar nenhuma — não é óbvio ainda quais o time de análise vai usar.
CREATE TABLE fato_sinan (
    id BIGSERIAL PRIMARY KEY,
    tp_not INTEGER,
    id_agravo VARCHAR(3),
    dt_notific DATE,
    sem_not INTEGER,
    nu_ano INTEGER,
    sg_uf_not VARCHAR(2),
    id_municip VARCHAR(6),
    id_regiona VARCHAR(4),
    id_unidade VARCHAR(7),
    dt_acid DATE,
    sem_acid INTEGER,
    ano_nasc SMALLINT,
    nu_idade_n INTEGER,
    cs_sexo VARCHAR(1),
    cs_gestant INTEGER,
    cs_raca SMALLINT,
    cs_escol_n SMALLINT,
    sg_uf INTEGER,
    id_mn_resi VARCHAR(6),
    id_rg_resi VARCHAR(4),
    id_pais VARCHAR(1),
    id_ocupa_n VARCHAR(6),
    sit_trab SMALLINT,
    nutempo INTEGER,
    tptempo SMALLINT,
    local_acid INTEGER,
    cnae VARCHAR(5),
    uf_emp VARCHAR(2),
    mun_emp VARCHAR(6),
    terceiriza SMALLINT,
    cnae_prin VARCHAR(5),
    hora_acid SMALLINT,
    min_acid SMALLINT,
    hora_jor SMALLINT,
    min_jor SMALLINT,
    uf_acid VARCHAR(2),
    mun_acid VARCHAR(6),
    cid_acid VARCHAR(4),
    tipo_acid VARCHAR(1),
    mais_trab SMALLINT,
    nu_trab INTEGER,
    atende_med SMALLINT,
    dt_atende DATE,
    uf_atende VARCHAR(2),
    mun_atende VARCHAR(6),
    uni_atende VARCHAR(7),
    part_corp1 INTEGER,
    part_corp2 SMALLINT,
    part_corp3 SMALLINT,
    cid_lesao VARCHAR(4),
    regime SMALLINT,
    evolucao SMALLINT,
    dt_obito DATE,
    cat VARCHAR(1)
);

CREATE INDEX idx_fato_sinan_dt_acid ON fato_sinan (dt_acid);
CREATE INDEX idx_fato_sinan_mun_acid ON fato_sinan (mun_acid);
CREATE INDEX idx_fato_sinan_cid_acid ON fato_sinan (cid_acid);
