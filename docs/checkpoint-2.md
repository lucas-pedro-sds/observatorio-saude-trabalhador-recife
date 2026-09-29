

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
    
