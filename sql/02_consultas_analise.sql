-- Consultas analíticas — perguntas do canvas (docs/canvas-projeto.md, seção 3)
-- Rodar no DBeaver com o usuário time_analise (somente leitura).
-- As mesmas consultas estão em analises/eda.ipynb, com a regra de cobertura
-- fatorada numa função Python. Ao mudar uma consulta, mude nos dois lugares.
--
-- ============================================================================
-- CUIDADOS QUE VALEM PARA TODAS AS CONSULTAS (leia antes de interpretar)
-- ============================================================================
-- 1. COBERTURA IRREGULAR DA CAT (o cuidado mais importante). Os arquivos mensais
--    do INSS não têm volume regular: entre set/2024 e mar/2025 e em nov-dez/2025
--    chegam com uma fração do volume normal (nov/2025 tem 1 registro de Recife),
--    e antes de jun/2023 só existem CATs registradas com atraso (a coleta começa
--    no arquivo de jun/2023). Alguns meses (abr/2024, jul/2025) vêm acima do
--    normal. Nenhum ano está completo.
--    Consequências: (a) contagens absolutas de acidentes por período são
--    subestimadas, (b) séries mensais e comparações entre anos ficam distorcidas.
--    A consulta Q0 mostra a cobertura mês a mês. As comparações entre anos
--    usam somente os meses com cobertura adequada. Comparações entre setores
--    (Q3a) usam todos os meses, assumindo que a falha de cobertura atinge todos
--    os setores igualmente, o que afeta as taxas absolutas mas preserva a ordem
--    relativa entre setores.
--    A solução definitiva é obter os arquivos mensais completos junto ao INSS.
--
-- 2. PERÍODO: 2023-2025, os três anos em que CAT e RAIS coexistem. A CAT vai até
--    2026, mas a RAIS não, então toda consulta que cruza as duas filtra a CAT.
--
-- 3. DENOMINADOR: vínculos CLT da RAIS (quantidade_vinculos_clt). Servidores
--    estatutários têm regime próprio e não geram CAT; com
--    quantidade_vinculos_ativos a administração pública domina qualquer ranking
--    de taxa baixa.
--
-- 4. TERRITÓRIO: os dados de acidente só têm o município (Recife). Não existe
--    bairro em nenhuma fonte de acidente. O único recorte abaixo de município
--    é o CEP das empresas na RAIS (5 primeiros dígitos), que descreve onde está
--    o emprego formal, não onde os acidentes acontecem. Isso é a limitação já
--    prevista no canvas (seção 6, risco 1).
--
-- 5. CNAE: a CAT e a RAIS são cruzadas no nível de 4 dígitos (dim_cnae.classe_codigo_4).
--    O CNAE do SINAN mistura CNAE 1.0 e 2.0 no mesmo campo (ex: 85111 é
--    "atendimento hospitalar" na CNAE 1.0), por isso NÃO é usado para
--    análise por setor econômico.
--
-- 6. DUPLICATAS E TEXTOS DA CAT: como os arquivos do INSS se sobrepõem, a
--    pipeline remove registros duplicados (~10,9% das linhas), limpa os
--    espaços à direita dos textos, o sufixo de 2 letras (NU ou UL) do CID-10 e
--    passa o CID-10 para maiúsculas (algumas CATs vêm com "s602").
--    As consultas mantêm btrim()/upper() por segurança e usam left(cid10, 3),
--    a categoria de 3 caracteres, que casa com a dim_cid10.
--    "{ñ class}" é o marcador do INSS para "não classificado" em campos de texto
--    (agente causador, emitente, origem do cadastramento): trate como ausente.
--
-- 7. "ADOECIMENTOS": os agravos de doença do trabalho do SINAN (LER/DORT,
--    perda auditiva, transtornos mentais etc.) não estão carregados. O que
--    existe é o tipo "Doença" da CAT, usado como aproximação.
--
-- 8. TAXAS NÃO SÃO PROVA: as taxas por mil vínculos (Q3a) são indicadores para
--    priorizar investigação, não prova de subnotificação. Setores de baixo
--    risco real (ex: escritórios) também aparecem com taxa baixa, e a
--    administração pública aparece com muitos vínculos CLT e poucas CAT por
--    razões de regime jurídico, não necessariamente por subnotificação.

-- ============================================================================
-- DIAGNÓSTICO — cobertura mensal da CAT
-- ============================================================================

-- [Q0] Acidentes da CAT por mês e se a cobertura é adequada
-- Regra: mês adequado = pelo menos metade da mediana mensal do período.
-- Esta mesma definição é repetida nas consultas que comparam anos ou meses.
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
)
SELECT to_char(mes, 'YYYY-MM') AS mes,
       n AS acidentes_cat,
       ok AS cobertura_adequada
FROM cobertura
ORDER BY mes;

-- ============================================================================
-- PERGUNTA 1 — Quais atividades econômicas (CNAE) concentram mais acidentes e adoecimentos
-- do trabalho no Recife, proporcionalmente ao número de trabalhadores formais, e como isso
-- mudou nos últimos três anos?
-- ============================================================================
-- Método: taxa por mil vínculos CLT (RAIS) por ano, 2023 a 2025 (os três anos em que
-- CAT e RAIS coexistem). Como a CAT tem meses com cobertura muito baixa (cuidado 1),
-- cada ano usa só os seus meses com cobertura adequada, e a taxa é anualizada:
-- ocorrências nesses meses divididas por (vínculos x meses adequados / 12). Assim
-- 2023 (CAT começa em jun) e 2024/2025 (buracos em outros meses) ficam na mesma escala.
-- Isso supõe que a sazonalidade dos acidentes é pequena: leia variações pequenas
-- como ruído. "Ocorrências" somam acidente típico, de trajeto e doença do trabalho.
-- Só entram setores com pelo menos 2.000 vínculos CLT em cada ano e 30 ocorrências no total.

-- [Q1a] Ranking de setores pela taxa em 2025, com a evolução desde 2023
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
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
       d.denominacao AS atividade_economica,
       max(t.vinculos) FILTER (WHERE t.ano = 2025) AS vinculos_clt_2025,
       sum(t.ocorrencias) AS ocorrencias_meses_adequados,
       sum(t.doencas) AS doencas_do_trabalho,
       round(max(t.taxa) FILTER (WHERE t.ano = 2023), 1) AS taxa_2023,
       round(max(t.taxa) FILTER (WHERE t.ano = 2024), 1) AS taxa_2024,
       round(max(t.taxa) FILTER (WHERE t.ano = 2025), 1) AS taxa_2025,
       round(max(t.taxa) FILTER (WHERE t.ano = 2025)
             - max(t.taxa) FILTER (WHERE t.ano = 2023), 1) AS variacao_2023_2025
FROM taxas t
JOIN dim_cnae d ON d.classe_codigo_4 = t.classe4
GROUP BY d.classe_codigo_4, d.denominacao
HAVING count(*) = 3 AND min(t.vinculos) >= 2000 AND sum(t.ocorrencias) >= 30
ORDER BY taxa_2025 DESC
LIMIT 20;

-- [Q1b] Referência: taxa da cidade inteira por ano, pela mesma regra da Q1a
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
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
       m.n_meses AS meses_com_cobertura_adequada,
       v.vinculos AS vinculos_clt,
       a.ocorrencias,
       round(1000.0 * a.ocorrencias / (v.vinculos * m.n_meses / 12.0), 1) AS taxa_por_mil_vinculos_ano
FROM vinculos v
JOIN meses_ok m ON m.ano = v.ano
JOIN acidentes a ON a.ano = v.ano
ORDER BY v.ano;

-- ============================================================================
-- PERGUNTA 2 — Quais ocupações (CBO) e diagnósticos (CID-10) respondem pela maior parte
-- das CATs registradas no Recife, e essa composição mudou entre o primeiro e o último
-- dos três anos?
-- ============================================================================
-- "Maior parte": ranking de todas as CATs de 2023-2025, com a participação
-- acumulada (pct_acumulado). As linhas até ~50% ou ~80% são o grupo que
-- "responde pela maior parte".
-- "Mudou entre o primeiro e o último ano": participação em 2023 x 2025, só nos
-- meses do calendário com cobertura adequada NOS DOIS anos (hoje, jun a out),
-- para não confundir mudança de perfil com falha de cobertura ou sazonalidade.
-- A variação é em pontos percentuais, sem teste estatístico: com poucos casos,
-- oscilações pequenas são ruído.

-- [Q2a] Ocupações (CBO) que concentram as CATs, e a composição em 2023 x 2025
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
comparaveis AS (
  SELECT extract(month FROM mes)::int AS mes_do_ano
  FROM cobertura
  WHERE extract(year FROM mes) IN (2023, 2025)
  GROUP BY 1
  HAVING bool_and(ok) AND count(*) = 2
),
total AS (
  SELECT cbo_2002, count(*) AS n
  FROM fato_cat
  WHERE data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY 1
),
comp AS (
  SELECT extract(year FROM data_acidente)::int AS ano, cbo_2002, count(*) AS n
  FROM fato_cat
  WHERE extract(year FROM data_acidente) IN (2023, 2025)
    AND extract(month FROM data_acidente)::int IN (SELECT mes_do_ano FROM comparaveis)
  GROUP BY 1, 2
),
pct AS (
  SELECT cbo_2002,
         100.0 * sum(n) FILTER (WHERE ano = 2023) / (SELECT sum(n) FROM comp WHERE ano = 2023) AS pct_2023,
         100.0 * sum(n) FILTER (WHERE ano = 2025) / (SELECT sum(n) FROM comp WHERE ano = 2025) AS pct_2025
  FROM comp
  GROUP BY 1
)
SELECT t.cbo_2002,
       coalesce(o.cbo_2002_descricao, '(código fora da tabela CBO)') AS ocupacao,
       t.n AS cats_2023_2025,
       round(100.0 * t.n / sum(t.n) OVER (), 1) AS pct_do_total,
       round(100.0 * sum(t.n) OVER (ORDER BY t.n DESC, t.cbo_2002) / sum(t.n) OVER (), 1) AS pct_acumulado,
       round(coalesce(p.pct_2023, 0), 1) AS pct_2023,
       round(coalesce(p.pct_2025, 0), 1) AS pct_2025,
       round(coalesce(p.pct_2025, 0) - coalesce(p.pct_2023, 0), 1) AS variacao_pp
FROM total t
LEFT JOIN pct p USING (cbo_2002)
LEFT JOIN dim_cbo o USING (cbo_2002)
ORDER BY t.n DESC, t.cbo_2002
LIMIT 20;

-- [Q2b] Diagnósticos (CID-10, categoria de 3 caracteres) que concentram as CATs, e a composição em 2023 x 2025
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
comparaveis AS (
  SELECT extract(month FROM mes)::int AS mes_do_ano
  FROM cobertura
  WHERE extract(year FROM mes) IN (2023, 2025)
  GROUP BY 1
  HAVING bool_and(ok) AND count(*) = 2
),
cid AS (
  SELECT categoria, min(descricao_categoria) AS descricao
  FROM dim_cid10
  GROUP BY categoria
),
cat AS (
  SELECT data_acidente, upper(left(btrim(cid10), 3)) AS categoria
  FROM fato_cat
),
total AS (
  SELECT categoria, count(*) AS n
  FROM cat
  WHERE data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY 1
),
comp AS (
  SELECT extract(year FROM data_acidente)::int AS ano, categoria, count(*) AS n
  FROM cat
  WHERE extract(year FROM data_acidente) IN (2023, 2025)
    AND extract(month FROM data_acidente)::int IN (SELECT mes_do_ano FROM comparaveis)
  GROUP BY 1, 2
),
pct AS (
  SELECT categoria,
         100.0 * sum(n) FILTER (WHERE ano = 2023) / (SELECT sum(n) FROM comp WHERE ano = 2023) AS pct_2023,
         100.0 * sum(n) FILTER (WHERE ano = 2025) / (SELECT sum(n) FROM comp WHERE ano = 2025) AS pct_2025
  FROM comp
  GROUP BY 1
)
SELECT t.categoria AS cid10_categoria,
       coalesce(c.descricao, '(código fora da tabela CID-10)') AS diagnostico,
       t.n AS cats_2023_2025,
       round(100.0 * t.n / sum(t.n) OVER (), 1) AS pct_do_total,
       round(100.0 * sum(t.n) OVER (ORDER BY t.n DESC, t.categoria) / sum(t.n) OVER (), 1) AS pct_acumulado,
       round(coalesce(p.pct_2023, 0), 1) AS pct_2023,
       round(coalesce(p.pct_2025, 0), 1) AS pct_2025,
       round(coalesce(p.pct_2025, 0) - coalesce(p.pct_2023, 0), 1) AS variacao_pp
FROM total t
LEFT JOIN pct p USING (categoria)
LEFT JOIN cid c USING (categoria)
ORDER BY t.n DESC, t.categoria
LIMIT 20;

-- ============================================================================
-- PERGUNTA 3 — Onde há muito vínculo formal e pouca notificação (sinal de subnotificação, não de segurança)?
-- ============================================================================

-- [Q3a] Setores com mais acidentes "faltando" em relação à taxa da cidade (2023-2025)
-- Taxa geral = acidentes da CAT dividido pelos vínculos CLT de todos os setores.
-- Para cada CNAE, esperado = vínculos CLT do setor multiplicado pela taxa geral.
-- Ordenado pela diferença esperado - observado, e não pela taxa crescente, que só
-- lista setores pequenos ou de risco baixo com 0 CAT.
-- Vínculos contados por ano e somados no período; só setores com pelo menos
-- 3.000 vínculos-ano (~1.000 por ano), para evitar taxas instáveis.
-- Leia a razão observado/esperado e a diferença como comparação ENTRE setores: como a
-- CAT está incompleta (cuidado 1), as taxas absolutas estão subestimadas, mas a
-- taxa geral usada como referência sofre a mesma subestimação.
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
       d.denominacao AS atividade_economica,
       v.vinculos_ano AS vinculos_clt_ano,
       coalesce(a.acidentes, 0) AS acidentes_cat,
       round(1000.0 * coalesce(a.acidentes, 0) / v.vinculos_ano, 2) AS acidentes_por_mil_vinculos,
       round(v.vinculos_ano * g.taxa, 0) AS acidentes_esperados,
       round(v.vinculos_ano * g.taxa - coalesce(a.acidentes, 0), 0) AS diferenca_esperado_menos_observado,
       round(coalesce(a.acidentes, 0) / (v.vinculos_ano * g.taxa), 2) AS razao_observado_esperado
FROM vinculos v
CROSS JOIN geral g
LEFT JOIN acidentes a ON a.classe4 = v.classe4
JOIN dim_cnae d ON d.classe_codigo_4 = v.classe4
WHERE v.vinculos_ano >= 3000
ORDER BY diferenca_esperado_menos_observado DESC
LIMIT 20;

-- [Q3b] Verificação de consistência: acidentes da CAT em setores sem nenhum vínculo CLT na RAIS 2023-2025
-- Se esse percentual for alto, as taxas da Q3a estão distorcidas por diferença de classificação.
WITH vinculos AS (
  SELECT DISTINCT d.classe_codigo_4 AS classe4
  FROM fato_rais r
  JOIN dim_cnae d ON d.classe_codigo = r.cnae_2_classe
  WHERE r.ano BETWEEN 2023 AND 2025 AND r.quantidade_vinculos_clt > 0
)
SELECT count(*) AS acidentes_cat,
       count(*) FILTER (WHERE v.classe4 IS NULL) AS em_setor_sem_vinculo_na_rais,
       round(100.0 * count(*) FILTER (WHERE v.classe4 IS NULL) / count(*), 2) AS pct
FROM fato_cat f
LEFT JOIN vinculos v ON v.classe4 = f.cnae
WHERE f.data_acidente BETWEEN '2023-01-01' AND '2025-12-31';

-- ============================================================================
-- PERGUNTA 4 (opcional) — A procura pela rede de saúde acompanha o mapa do trabalho formal ou aponta para o informal?
-- Resposta PARCIAL, como previsto no canvas: sem PNAD não há taxa de informalidade
-- da cidade para comparar, e o SINAN não tem território abaixo do município.
-- Os códigos de situação de trabalho seguem a ficha do SINAN (busca em fontes do
-- Ministério da Saúde e secretarias estaduais), coerentes com a distribuição dos
-- dados, mas os PDFs oficiais não puderam ser lidos automaticamente: validar com a VISAT.
-- ============================================================================

-- [Q4a] Quem chega à rede de saúde: situação de trabalho das vítimas notificadas no SINAN
SELECT CASE WHEN sit_trab IN (1, 4, 5) THEN 'Vínculo formal (CLT ou servidor)'
            WHEN sit_trab IN (2, 3, 10) THEN 'Sem registro, autônomo ou avulso'
            WHEN sit_trab IN (6, 7, 8, 9, 11, 12) THEN 'Outras situações'
            ELSE 'Ignorado ou sem informação' END AS grupo,
       count(*) AS notificacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM fato_sinan_acgr
WHERE dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY 1
ORDER BY notificacoes DESC;

-- [Q4b] Empregados com carteira assinada notificados no SINAN: foi emitida CAT?
-- Códigos do campo CAT no SINAN: 1 = sim, 2 = não, 3 = não se aplica, 9 = ignorado
-- (padrão da ficha, coerente com os valores encontrados, a confirmar com a VISAT).
-- Percentual alto de "não" ou "ignorado" entre celetistas indica acidentes que
-- chegaram à rede de saúde e não viraram CAT, ou seja, possível subnotificação na CAT.
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
ORDER BY notificacoes DESC;

-- [Q4c] Contagem mensal de acidentes na CAT e no SINAN, marcando os meses com cobertura adequada da CAT
-- A razão SINAN por CAT só é calculada nos meses com cobertura adequada.
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
sinan AS (
  SELECT date_trunc('month', dt_acid)::date AS mes, count(*) AS n
  FROM fato_sinan_acgr
  WHERE dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY 1
)
SELECT to_char(c.mes, 'YYYY-MM') AS mes,
       c.n AS acidentes_cat,
       coalesce(s.n, 0) AS notificacoes_sinan,
       c.ok AS cobertura_cat_adequada,
       CASE WHEN c.ok THEN round(coalesce(s.n, 0)::numeric / nullif(c.n, 0), 2) END AS sinan_por_cat
FROM cobertura c
LEFT JOIN sinan s ON s.mes = c.mes
ORDER BY c.mes;

-- [Q4d] As duas séries andam juntas? Correlação mensal CAT x SINAN, só nos meses com cobertura adequada
-- Valor de -1 a 1. Poucos meses e cobertura irregular: leia como indício, não como resultado.
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
sinan AS (
  SELECT date_trunc('month', dt_acid)::date AS mes, count(*) AS n
  FROM fato_sinan_acgr
  WHERE dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
  GROUP BY 1
)
SELECT count(*) AS meses_usados,
       round(corr(c.n, coalesce(s.n, 0))::numeric, 2) AS correlacao_cat_sinan
FROM cobertura c
LEFT JOIN sinan s ON s.mes = c.mes
WHERE c.ok;

-- ============================================================================
-- COMPLEMENTARES — respondiam à versão anterior das perguntas 1 e 2 do canvas.
-- Não respondem diretamente às perguntas atuais, mas podem apoiar o dashboard e a narrativa.
-- ============================================================================

-- [C1] Acidentes da CAT por atividade econômica (CNAE), em números absolutos, com o tipo de ocorrência (2023-2025)
SELECT d.classe_codigo_4 AS cnae,
       d.denominacao AS atividade_economica,
       count(*) AS acidentes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_do_total,
       count(*) FILTER (WHERE btrim(f.tipo_acidente) ILIKE 'T%pico') AS tipico,
       count(*) FILTER (WHERE btrim(f.tipo_acidente) ILIKE 'Trajeto') AS trajeto,
       count(*) FILTER (WHERE btrim(f.tipo_acidente) ILIKE 'Doen%') AS doenca
FROM fato_cat f
JOIN dim_cnae d ON d.classe_codigo_4 = f.cnae
WHERE f.data_acidente BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY d.classe_codigo_4, d.denominacao
ORDER BY acidentes DESC
LIMIT 15;

-- [C2] Tipo de ocorrência por ano (típico, trajeto, doença do trabalho) e óbitos, nos meses comparáveis de 2023 e 2025
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
comparaveis AS (
  SELECT extract(month FROM mes)::int AS mes_do_ano
  FROM cobertura
  WHERE extract(year FROM mes) IN (2023, 2025)
  GROUP BY 1
  HAVING bool_and(ok) AND count(*) = 2
),
base AS (
  SELECT extract(year FROM data_acidente)::int AS ano,
         btrim(tipo_acidente) AS tipo,
         btrim(indica_obito_acidente) AS obito
  FROM fato_cat
  WHERE extract(year FROM data_acidente) IN (2023, 2025)
    AND extract(month FROM data_acidente)::int IN (SELECT mes_do_ano FROM comparaveis)
)
SELECT ano,
       tipo,
       count(*) AS ocorrencias,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY ano), 1) AS pct_no_ano,
       count(*) FILTER (WHERE obito ILIKE 'Sim') AS obitos
FROM base
GROUP BY ano, tipo
ORDER BY ano, ocorrencias DESC;

-- [C3] Território (proxy): onde está o emprego formal celetista, por CEP de 5 dígitos (RAIS 2025)
-- Vínculos são contados no CEP da empresa declarante, então sedes de grandes
-- empregadores concentram vínculos que podem estar espalhados pela cidade.
SELECT left(cep, 5) AS cep_5_digitos,
       sum(quantidade_vinculos_clt) AS vinculos_clt,
       round(100.0 * sum(quantidade_vinculos_clt) / sum(sum(quantidade_vinculos_clt)) OVER (), 1) AS pct_do_total,
       count(*) FILTER (WHERE quantidade_vinculos_ativos > 0) AS estabelecimentos_com_vinculo
FROM fato_rais
WHERE ano = 2025
GROUP BY left(cep, 5)
ORDER BY vinculos_clt DESC
LIMIT 15;

-- [C4] Território (proxy): onde moram os trabalhadores acidentados em Recife (SINAN, acidentes de trabalho graves)
-- O SINAN tem cobertura mensal estável (~100 notificações por mês), ao contrário da CAT.
SELECT coalesce(n.nome, 'Outros municípios') AS municipio_de_residencia,
       count(*) AS notificacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM fato_sinan_acgr s
LEFT JOIN (VALUES ('261160', 'Recife'),
                  ('260790', 'Jaboatão dos Guararapes'),
                  ('260960', 'Olinda'),
                  ('261070', 'Paulista'),
                  ('260345', 'Camaragibe'),
                  ('261370', 'São Lourenço da Mata')) AS n(codigo, nome)
       ON n.codigo = s.id_mn_resi
WHERE s.dt_acid BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY coalesce(n.nome, 'Outros municípios')
ORDER BY notificacoes DESC;

-- [C5] Perfil do acidentado por sexo e faixa etária, 2023 x 2025, nos meses comparáveis
-- A idade é aproximada (ano do acidente menos ano de nascimento, erro de até 1 ano).
WITH meses AS (
  SELECT generate_series('2023-01-01'::date, '2025-12-01'::date, interval '1 month')::date AS mes
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
),
comparaveis AS (
  SELECT extract(month FROM mes)::int AS mes_do_ano
  FROM cobertura
  WHERE extract(year FROM mes) IN (2023, 2025)
  GROUP BY 1
  HAVING bool_and(ok) AND count(*) = 2
),
base AS (
  SELECT extract(year FROM data_acidente)::int AS ano,
         CASE WHEN btrim(sexo) ILIKE 'Masculino' THEN 'Masculino'
              WHEN btrim(sexo) ILIKE 'Feminino' THEN 'Feminino'
              ELSE 'Não informado' END AS sexo,
         CASE WHEN ano_nascimento IS NULL THEN 'sem informação'
              WHEN extract(year FROM data_acidente) - ano_nascimento < 25 THEN 'até 24 anos'
              WHEN extract(year FROM data_acidente) - ano_nascimento < 35 THEN '25 a 34'
              WHEN extract(year FROM data_acidente) - ano_nascimento < 45 THEN '35 a 44'
              WHEN extract(year FROM data_acidente) - ano_nascimento < 55 THEN '45 a 54'
              ELSE '55 ou mais' END AS faixa_etaria
  FROM fato_cat
  WHERE extract(year FROM data_acidente) IN (2023, 2025)
    AND extract(month FROM data_acidente)::int IN (SELECT mes_do_ano FROM comparaveis)
)
SELECT ano,
       sexo,
       faixa_etaria,
       count(*) AS acidentes,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY ano), 1) AS pct_no_ano
FROM base
GROUP BY ano, sexo, faixa_etaria
ORDER BY ano, sexo, faixa_etaria;
