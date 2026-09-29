// A procura pela rede de saúde acompanha o mapa do trabalho formal ou aponta para o informal?

SELECT 
    sinan.nu_ano AS ano_acidente,
    CASE 
        WHEN sinan.sit_trab = 1 THEN 'Trabalho Formal (Com Carteira Assinada)'
        WHEN sinan.sit_trab IN (2, 3, 4) THEN 'Trabalho Informal (Autônomo, Sem Carteira, Doméstico)'
        WHEN sinan.sit_trab IN (5, 6, 7) THEN 'Outros Vínculos (Militar, Servidor, Não Remunerado, Avulso)'
        ELSE 'Não Informado / Sem Registro'
    END AS categoria_trabalho,
    COUNT(sinan.id) AS total_atendimentos_sus,
    
    -- Calcula o percentual de forma justa, baseado apenas no total daquele ano específico
    ROUND(
        (COUNT(sinan.id) * 100.0) / SUM(COUNT(sinan.id)) OVER(PARTITION BY sinan.nu_ano), 
        2
    ) AS percentual_proporcao_no_ano

FROM fato_sinan_acgr sinan
WHERE sinan.mun_acid = '261160' -- Filtro do território de Recife nos dados baixados
  AND sinan.nu_ano IN (2023, 2024, 2025)
GROUP BY 
    sinan.nu_ano,
    CASE 
        WHEN sinan.sit_trab = 1 THEN 'Trabalho Formal (Com Carteira Assinada)'
        WHEN sinan.sit_trab IN (2, 3, 4) THEN 'Trabalho Informal (Autônomo, Sem Carteira, Doméstico)'
        WHEN sinan.sit_trab IN (5, 6, 7) THEN 'Outros Vínculos (Militar, Servidor, Não Remunerado, Avulso)'
        ELSE 'Não Informado / Sem Registro'
    END
ORDER BY 
    ano_acidente ASC, 
    total_atendimentos_sus DESC;

A procura pela rede de saúde ainda é majoritariamente registrada como de trabalhadores formais (60,66%), refletindo o mapa do trabalho formal. No entanto, os dados apontam que a informalidade já responde por mais de 1/4 (25,89%) de todos os acidentes graves atendidos no SUS do Recife, considerando os 3 ultimos anos.
Além disso, a análise revela um forte indício de subnotificação epidemiológica, impulsionada pelo alto índice de dados omissos na rede pública, em torno de 12%.

Alerta para: 
1 Capacitação nas UPAs e Policlínicas: Combater o índice de 11,81% de dados não informados, acabar com a invisibilidade.

2 Políticas de Território: Criar ações de prevenção focadas nos 25,89% de informais diretamente nos grandes polos de comércio e serviços autônomos de Recife.




//Mapeamento dos top 20 Cids que aparecem na rede de saúde.

SELECT 
    sinan.nu_ano AS ano_acidente,
    
    -- Classificação do Vínculo Baseada nas Regras de Negócio do SUS
    CASE 
        WHEN sinan.sit_trab = 1 THEN 'Trabalho Formal'
        WHEN sinan.sit_trab IN (2, 3, 4) THEN 'Trabalho Informal'
        ELSE 'Outros / Não Informado'
    END AS categoria_vinculo,
    
    -- Código do CID-10
    COALESCE(sinan.cid_lesao, 'N/I') AS cid_codigo,
    
    -- Descrição do Diagnóstico buscando na dimensão (priorizando subcategoria, depois categoria)
    COALESCE(cid.descricao_subcategoria, cid.descricao_categoria, 'Descrição não encontrada no dicionário') AS diagnostico_lesao,
    
    -- Volumetria (Contagem Absoluta)
    COUNT(sinan.id) AS total_casos,
    
    -- Percentual de representação dentro do total geral de acidentes daquele ano específico
    ROUND(
        (COUNT(sinan.id) * 100.0) / SUM(COUNT(sinan.id)) OVER(PARTITION BY sinan.nu_ano), 
        2
    ) AS percentual_no_ano

FROM fato_sinan_acgr sinan

-- Duplo JOIN na dim_cid10 para garantir o acoplamento de códigos de 3 ou 4 dígitos
LEFT JOIN dim_cid10 cid 
    ON sinan.cid_lesao = cid.subcategoria 
    OR sinan.cid_lesao = cid.categoria

-- Filtros Estritos baseados no Escopo de Recife e Período de 3 anos
WHERE sinan.mun_acid = '261160'              -- Código INSS/SUS do Recife (6 dígitos)
  AND sinan.nu_ano IN (2023, 2024, 2025)       -- Recorte temporal definido no Canvas

-- Agrupamento obrigatório para colunas de agregação
GROUP BY 
    sinan.nu_ano, 
    CASE 
        WHEN sinan.sit_trab = 1 THEN 'Trabalho Formal'
        WHEN sinan.sit_trab IN (2, 3, 4) THEN 'Trabalho Informal'
        ELSE 'Outros / Não Informado'
    END,
    sinan.cid_lesao, 
    cid.descricao_subcategoria, 
    cid.descricao_categoria

-- Ordenação pelo maior volume de casos para extrair a liderança do ranking
ORDER BY 
    total_casos DESC
LIMIT 20;

O Top 20 de CIDs prova que a informalidade e a formalidade em Recife machucam de formas totalmente distintas. O Trabalho Informal está majoritariamente exposto à violência urbana e viária das duas rodas, que esmaga membros inferiores (CID S82) nas avenidas da cidade. Já o Trabalho Formal, protegido pelas barreiras e fiscalizações da CLT no trânsito, concentra seus acidentes graves em ambientes operacionais internos, afetando a manipulação de máquinas e ferramentas com lesões em punhos e mãos (CID S62). A procura pelo SUS, portanto, não apenas aponta para a informalidade, mas desenha com precisão a anatomia da precarização laboral no Recife.
