# Abertura — Lia (~20 s · Slide 01): Lia Marinho 

Boa noite a todos. Somos a equipe Uma Ponte, e nosso lema resume o projeto: dados que aproximam decisões. Comigo, hoje, estão Lucas Pedro e Matheus Henrique; de forma remota, Gabriel Caminha e Gabriel Araújo. O projeto contou com a mentoria de Diógenes Cruz e Andrei Lima.

## Problema — Lia (~1 min 20 s · Slide 02): Lia Marinho 

A gerência da VISAT precisa decidir, com frequência, onde inspecionar e que política de saúde do trabalhador levar a cada território. Hoje, porém, esse diagnóstico ainda é feito sob demanda, com relatórios pontuais e estáticos. Falta um acompanhamento contínuo do risco. O efeito é direto: inspeções e políticas chegam tarde ou no lugar errado, e as áreas mais vulneráveis ficam sem prioridade. Em três anos de dados, vimos setores com taxa acima de 40 acidentes por mil vínculos e, ao mesmo tempo, setores com milhares de empregos formais e quase nenhuma CAT. Isso não é segurança: é apagão de informação.

## Solução — Lucas (~1 min 20 s · Slide 03): Lucas
 
Para responder a esse problema, construímos um observatório contínuo de saúde do trabalhador para a VISAT.  Unimos CAT e SINAN — acidentes e agravos — com RAIS e CAGED — emprego formal —, padronizamos com CNAE, CBO e CID-10 e entregamos um dashboard que orienta a decisão. O ciclo: dados públicos oficiais entram no pipeline, são limpos e unificados, vão para o banco e alimentam o dashboard. Tudo versionado e atualizável, sem caixa-preta.

## Perguntas — Lucas (~1 min 20 s · Slide 04): Lucas

As quatro perguntas que o painel responde são as que a gestão precisa para priorizar:

-Quais setores concentram mais risco por trabalhador formal;
-Quais ocupações e diagnósticos dominam as CATs;
-Onde há muito vínculo formal e quase nenhuma notificação;
-A procura pela rede de saúde acompanha o formal ou aponta para o informal.

## Demonstração — Caminha (~3 min · Slides 04 e 05 / tela do dashboard): Gabriel Caminha 

Agora vamos ver o dashboard em funcionamento.

Esse painel cruza as CATs do INSS com os vínculos formais da RAIS e com dados do SUS.

Os acidentes são lidos por setor, segundo o CNAE, para mostrar onde os trabalhadores mais se acidentam e adoecem no Recife.

Q1 — Setores (~50 s)

À esquerda: taxa de acidentes por mil trabalhadores formais, nos cinco setores de maior taxa. Usamos taxa, e não o número bruto, para não privilegiar só os setores grandes.

À direita: a mesma taxa para a cidade inteira, com o número de meses em que os dados têm volume regular.Achado: coleta de resíduos lidera — chegou a 48 por mil. Hospitais concentram volume e sobem em 2025. A taxa da cidade foi de cerca de 5 para 6,2 por mil.

Para a VISAT: prioridade de inspeção em coleta e hospitais.

Q2 — Ocupações e diagnósticos (~40 s)

À esquerda, a participação das ocupações no total de CATs; à direita, a dos diagnósticos. Só os seis maiores de cada um. Comparamos 2023 com 2025, nos mesmos meses, para ver se o perfil mudou.Achado: técnico de enfermagem concentra cerca de 11% das CATs. No topo dos diagnósticos seguem lesões de mão, punho e articulações.

Para a VISAT: risco concentrado em enfermagem, limpeza e obras.

Q3 — Subnotificação (~55 s)
O gráfico compara, por setor, o registrado com o previsto: quantos acidentes o setor teria se acompanhasse a média da cidade por mil vínculos.

A tabela traz a razão registrado ÷ previsto: quanto mais perto de zero, menos o setor notifica. É sinal para investigar — não prova de que o setor é seguro.Achado: administração pública registrou só cerca de 11% do esperado. Educação, limpeza e condomínios também ficam abaixo. Construção notifica perto do esperado.

Para a VISAT: cobrar emissão de CAT e fiscalizar nesses setores.

Q4 — Rede de saúde (~30 s)
Aqui entram os acidentes atendidos no SUS.

O gráfico de cima mostra a proporção de cada tipo de trabalho nos acidentes totais, por ano. O de baixo cruza diagnóstico com tipo de trabalho e tem seletor de ano.

(Se o de cima estiver com erro: “O painel de proporção geral está em ajuste; o de baixo, por diagnóstico, é o que está estável.”)Achado: fraturas graves — principalmente de perna e tornozelo — já concentram peso relevante no informal.

Para a VISAT: a rede de saúde completa o que a CAT formal não captura.

Com essas quatro questões, a VISAT vê onde o risco é alto, quem mais se acidenta, onde a CAT não sai e o quanto o informal já pesa no SUS.

# Insights (reforço pós-demo)

## Q1 — Gabriel (~20 s) Gabriel 
Coleta de resíduos: maior taxa, até 48 por mil. Hospitais sobem em 2025. Taxa da cidade: de 5 para 6,2.

VISAT: inspeção prioritária em coleta e hospitais.

## Q2 — Matheus (~20 s) Matheus 
Enfermagem: cerca de 11% das CATs. Lesões de mão e articulações no topo.

VISAT: risco concentrado em enfermagem, limpeza e obras.

## Q3 — Você (~25 s) Lucas
Administração pública: só 11% do esperado. Educação e limpeza também abaixo.

VISAT: cobrar CAT e fiscalizar — apagão, não segurança.

## Q4 — Lia (~20 s) Lia Marinho 
Fraturas graves já concentram peso no informal.

VISAT: a rede de saúde mostra o que a CAT formal não captura.

# Conclusão + limitações + ações — Lia (~1 min 10 s): Lia Marinho 

Três decisões que a VISAT pode tomar agora.Primeiro, risco visível: coleta de resíduos e hospitais — taxas altas e, no caso hospitalar, em alta.

Segundo, quem se acidenta: enfermagem concentra as CATs; lesões de mão e articulações dominam.

Terceiro, apagão: administração pública notificou só cerca de 11% do esperado.

Quarto, informal: já pesa nas fraturas graves que chegam à rede de saúde.Limitações que reconhecemos: a CAT tem cobertura irregular em alguns meses — por isso usamos só os meses com cobertura adequada. O recorte é por município, não por bairro, limitação da fonte oficial. As taxas absolutas ficam subestimadas; o indicador mais robusto é a comparação entre setores, esperado versus observado.Três ações concretas:

**1. Fiscalização direcionada em coleta de resíduos e hospitais;**

**2. Cobrança de CAT na administração pública, na educação e nos condomínios;**

**3. Qualificação da triagem no SUS, para reduzir ocupação omissa e enxergar melhor o informal.**