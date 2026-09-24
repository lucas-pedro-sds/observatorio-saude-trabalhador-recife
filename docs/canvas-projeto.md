# Canvas do Projeto — M6 Experiência Prática

**Como usar:** copie este arquivo para `docs/canvas-projeto.md` no repositório da equipe e preencha durante o E2 (qua 16/09). O canvas é validado pelo mentor ao fim do E2: aprovado, aprovado com ajustes, ou devolvido com pendências claras (pendências resolvidas até o E3). O canvas aprovado fica versionado no repositório — ele é a referência dos checkpoints: as perguntas daqui são as que o CP1 verifica (critério 1.4) e as que a análise e o dashboard precisam responder (critérios 2.1 e 2.2).

Lembre da regra do E2: **não existe viabilidade sem amostra baixada e aberta.**

---

## Identificação

|  |  |
| --- | --- |
| **Nome da equipe** | Uma Ponte |
| **Integrantes** | <ul><li>Lia Marinho</li><li>Gabriel Caminha</li><li>Lucas Pedro</li><li>Gabriel Araújo</li><li>Guilherme Santana</li><li>Guilherme Melo</li><li>Robertha Miranda</li><li>Matheus Henrique</li></ul> |
| **Mentor** | Diógenes Diniz e Andrei Lima |
| **Tema** | Observatório de Saúde do Trabalhador (Recife) |
| **Repositório GitHub** | [observatorio-saude-trabalhador-recife](https://github.com/lucas-pedro-sds/observatorio-saude-trabalhador-recife) |

---

## 1. Problema de negócio

```
A gerência da VISAT (Secretaria de Saúde do Recife) precisa decidir onde inspecionar e que política de saúde do trabalhador levar a cada território, mas hoje o diagnóstico do perfil do trabalhador recifense é feito sob demanda, com relatórios pontuais — sem a dinamicidade de um observatório contínuo. Isso limita o direcionamento de políticas e
inspeções aos territórios de maior vulnerabilidade.
```

---

## 2. Público / decisor

```
A gerência da VISAT (Vigilância em Saúde do Trabalhador), responsável por decidir onde inspecionar e que política de saúde do trabalhador levar a cada território.
```

---

## 3. Perguntas analíticas

| #            | Pergunta                                                                                      | Que decisão ela informa?                                      | Respondível com os dados? (verificado na amostra) |
| ------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| 1            | 1-Quais atividades econômicas (CNAE) concentram mais acidentes e adoecimentos do trabalho no Recife, proporcionalmente ao número de trabalhadores formais, e como isso mudou nos últimos três anos?                    | Onde priorizar inspeções e ações territoriais                 | Sim (CAT + RAIS)                                  |
| 2            | Quais ocupações (CBO) e diagnósticos (CID-10) respondem pela maior parte das CATs registradas no Recife, e essa composição mudou entre o primeiro e o último dos três anos?                  | Quais grupos prioritários e tendências                        | Sim (CAT)                                         |
| 3            | Onde há muito vínculo formal e pouca notificação — sinal de subnotificação, não de segurança? | Onde investigar subnotificação vs. real segurança             | Sim (CAT + RAIS)                                  |
| 4 (opcional) | A procura pela rede de saúde acompanha o mapa do trabalho formal ou aponta para o informal?   | Ajustar oferta de serviços vs. informalidade                  | Parcial (CAT + RAIS; SINAN depois)                |

---

## 4. Fontes de dados

| Fonte                                                | Link                                                                                                             | Formato | Volume estimado               | Licença/acesso          | Amostra baixada e aberta? | Colunas-chave confirmadas na amostra |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------- | ----------------------- | ------------------------- | ------------------------------------ |
| Comunicação de Acidente de Trabalho (CAT)            | https://dadosabertos.inss.gov.br/dataset/inss-comunicacao-de-acidente-de-trabalho-cat                            | CSV/ZIP | Nacional (recorte Recife)     | Pública e gratuita      | Sim                       | Agente Causador, Data Acidente, CBO, CID-10, CNAE 2.0, Município, Natureza da Lesão, Sexo |
| Relação Anual de Informações Sociais (RAIS)          | https://basedosdados.org/dataset/3e7c4d58-96ba-448e-b053-d385a829ef00                                           | SQL/CSV | Nacional (recorte Recife)     | Pública e gratuita      | Sim                       | CBO, CNAE, município, vínculos, sexo, idade |
| Cadastro Geral de Empregados e Desempregados (CAGED) | https://basedosdados.org/dataset/562b56a3-0b01-4735-a049-eeac5681f056                                           | SQL/CSV | Nacional (recorte Recife)     | Pública e gratuita      | Sim                       | CBO, CNAE, município, movimentação |
| SINAN (Doenças e Agravos de Notificação)             | https://datasus.saude.gov.br/acesso-a-informacao/doencas-e-agravos-de-notificacao-de-2007-em-diante-sinan/       | DBF/CSV | Nacional                      | Pública e gratuita      | Não                       | Notificações de agravos relacionados ao trabalho |
| CBO (Classificação Brasileira de Ocupações)          | https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo                                                        | Excel/CSV | Pequeno                     | Pública e gratuita      | Sim                       | Código e nome da ocupação |
| CONCLA / CNAE (Classificação Nacional de Atividades Econômicas) | https://concla.ibge.gov.br                                                                              | Excel/CSV | Pequeno                     | Pública e gratuita      | Sim                       | Código e nome da atividade econômica |

---

## 5. Escopo e entregáveis — a regra do fatiável

**Fatia mínima (compromisso):**

```
(CAT + RAIS, só de Recife, dos últimos 3 anos, mostrando a taxa de acidente por mil vínculos, separado por atividade econômica (CNAE) e por bairro.)
```

**Extensões desejáveis (apenas se sobrar tempo):**

```
- Incluir dados do SINAN (agravos relacionados ao trabalho)
- Incluir PNAD (para estimar informalidade)
- Melhorar a granularidade territorial (se possível chegar em bairro)
```

**Fora de escopo (o que decidimos NÃO fazer):**

```
- Área institucional com repositório e buscador de legislação (desenvolvimento de portal — já separado pela demandante)
- Outros municípios além de Recife
- Períodos anteriores aos últimos 3 anos
- Modelos preditivos / Machine Learning
```
---

## 6. Riscos e mitigação

| Risco | Sinal precoce | Mitigação | Responsável por monitorar |
|-------|---------------|-----------|---------------------------|
| Granularidade dos dados é por município (cidade) e não por bairro | Não encontrar coluna de bairro na CAT ou RAIS | Documentar a limitação no README e no canvas; usar município + CNAE como recorte territorial; tentar geocodificação ou agregação se sobrar tempo | Análise |
| Volume muito grande da CAT e da RAIS | Download lento, erro de memória ou pipeline travando | Filtrar apenas Recife e os últimos 3 anos desde a coleta; processar em chunks; manter amostra pequena para testes | Engenharia de Dados / Pipeline |
| Versões diferentes de CNAE e CBO entre as bases | Join falhando ou códigos não baterem | Baixar as tabelas oficiais da CONCLA e da CBO antes de fazer o join; criar tabelas de dimensão no banco | Modelagem e Banco de Dados |
| Escopo crescer demais (querer colocar SINAN + PNAD + mapa fino cedo) | Canvas com muitas extensões ou novas perguntas no meio do sprint | Seguir a regra do fatiável: entregar a fatia mínima (CAT + RAIS) primeiro; só depois adicionar extensões | Coordenação / PO |

---

## 7. Divisão de papéis

| Papel | Titular | Sombra / Apoio |
|---|---|---|
| **Product Owner (PO)** |  Lucas Pedro | Lia Marinho |
| **QA de Dados** | Gabriel Caminha | — |
| **Engenharia de Dados** | Gabriel Araújo | Matheus |
| **Modelagem e Banco de Dados** | Gabriel Araújo | Matheus |
| **Análise de Dados** | Guilherme Santana| Guilherme Melo |
| **Visualização de Dados** | Robertha Miranda | Gabriel Caminha |
| **Narrativa e Pitch** | Lia Marinho |  Robertha Miranda, Matheus |

**Canal de comunicação da equipe (fora do horário de aula):**

```
(grupo no WhatsApp: https://chat.whatsapp.com/IjXCaMyyh3YDV5yvutjb1w?s=cl&p=a&mlu=4&ilr=4)
```

---

## Validação do mentor (preenchida pelo mentor no E2)

| | |
|---|---|
| **Status** | (x) Aprovado ( ) Aprovado com ajustes ( ) Devolvido com pendências |
| **Data** | |
| **Amostra baixada e aberta verificada?** | ( ) Sim ( ) Não |
| **Pendências (com prazo até o E3 — seg 21/09)** | |