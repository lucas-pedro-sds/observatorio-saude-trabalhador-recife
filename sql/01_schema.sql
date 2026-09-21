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
-- CNPJ/CEI do empregador foi descartado; datas de acidente e nascimento foram
-- generalizadas para ano/mês e ano, respectivamente. As datas administrativas
-- restantes (afastamento, despacho de benefício, emissão do CAT) permanecem exatas.
--
-- id_municipio aqui tem 6 dígitos (sem o dígito verificador), diferente dos 7 dígitos
-- da RAIS/CAGED — mesma fonte (INSS), formato diferente, documentado como limitação.
-- cbo_2002 e cid10 não têm FOREIGN KEY: cbo_2002 tem uma pequena fração de códigos
-- órfãos (mesmo motivo do fato_caged); cid10 não tem tabela de dimensão no projeto
-- ainda (fica para quando a base de CID-10 for incorporada).
CREATE TABLE fato_cat (
    id BIGSERIAL PRIMARY KEY,
    ano_acidente SMALLINT NOT NULL,
    mes_acidente SMALLINT NOT NULL,
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
CREATE INDEX idx_fato_cat_ano_mes_acidente ON fato_cat (ano_acidente, mes_acidente);
