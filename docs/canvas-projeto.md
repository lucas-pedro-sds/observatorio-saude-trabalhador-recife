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

| # | Pergunta | Que decisão ela informa? | Respondível com os dados? (verificado na amostra) |
|---|---|---|---|
| 1 | Onde se concentram os acidentes e adoecimentos, por território e por CNAE? | | |
| 2 | Que ocupações (CBO) e diagnósticos (CID-10) aparecem mais, e o perfil mudou? | | |
| 3 | Onde há muito vínculo formal e pouca notificação — sinal de subnotificação, não de segurança? | | |
| 4 (opcional) | | | |
| 5 (opcional) | | | |

---

## 4. Fontes de dados

| Fonte | Link | Formato | Volume estimado | Licença/acesso | Amostra baixada e aberta? (sim/não) | Colunas-chave confirmadas na amostra |
|---|---|---|---|---|---|---|
| Comunicação de Acidente de Trabalho (CAT) | https://dados.gov.br/dados/conjuntos-dados/inss-comunicacao-de-acidente-de-trabalho-cat1 | CSV | Nacional (recorte Pernambuco) | Livre | Sim | Agente Causador, Data Acidente, CBO, CID-10, CNAE 2.0 Empregador, Emitente CAT, Óbito, Munic Empr, Natureza da Lesão, Sexo |
| Cadastro Geral de Empregados e Desempregados (CAGED) | https://basedosdados.org/dataset/562b56a3-0b01-4735-a049-eeac5681f056?table=95106d6f-e36e-4fed-b8e9-99c41cd99ecf | SQL/CSV | Nacional (recorte Pernambuco) | Livre | Não | saldo_movimentacao, tipo_movimentacao, causa_desligamento, cbo_2002, idade, sexo, raca_cor, grau_instrucao, cnae_2_0_subclasse, salario_mensal, qtd_dias_trabalhados, id_municipio, sigla_uf |
| Relação Anual de Informações Sociais (RAIS) | https://basedosdados.org/dataset/3e7c4d58-96ba-448e-b053-d385a829ef00?table=86b69f96-0bfe-45da-833b-6edc9a0af213 | SQL/CSV | Nacional (recorte Pernambuco) | Livre | Não | causa_afastamento, qtd_dias_afastamento, causa_desligamento, mes_admissao, mes_desligamento, cbo_2002, idade, sexo, raca_cor, grau_instrucao, tempo_emprego, cnae_2_0, qtd_hora_contratual, tamanho_estabelecimento, id_municipio, valor_remunera_media |

---

## 5. Escopo e entregáveis — a regra do fatiável

Defina primeiro a fatia mínima: o menor recorte que ainda exercita o ciclo completo (banco → pipeline → análise → dashboard). Ela é o compromisso da equipe. As extensões só entram se a fatia mínima estiver pronta — e nada entra após o congelamento de escopo (05/10).

**Fatia mínima (compromisso):**

```
(CAT + RAIS, só de Recife, dos últimos 3 anos, mostrando a taxa de acidente por mil vínculos, separado por atividade econômica (CNAE) e por bairro.)
```

**Extensões desejáveis (apenas se sobrar tempo):**

```
(ex.: ampliar para o Nordeste; incluir cobertura vacinal)
```

**Fora de escopo (o que decidimos NÃO fazer):**

```
(ex.: Municípios diferentes de Recife; )
(ex.: Períodos anteriores aos últimos 3 anos definidos )
```
---

## 6. Riscos e mitigação

Ao menos 3 riscos do **seu** projeto (não genéricos). Consulte a tabela de riscos comuns no [`guia-do-projeto.md`](guia-do-projeto.md).

| Risco | Sinal precoce | Mitigação | Responsável por monitorar |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

---

## 7. Divisão de papéis

Todos codificam — papéis distribuem responsabilidade de acompanhamento, não exclusividade de execução. Cada papel tem uma pessoa sombra (backup). Em equipes de 4, coordenação acumula com outro papel; em equipes de 5–6, dados/pipeline e análise podem ser duplicados.

| Papel | Titular | Sombra / Apoio |
|---|---|---|
| **Product Owner (PO)** | Lia Marinho | Lucas Pedro |
| **QA de Dados** | Gabriel Caminha | — |
| **Engenharia de Dados** | Gabriel Araújo | Matheus |
| **Modelagem e Banco de Dados** | Gabriel Araújo | Matheus |
| **Análise de Dados** | Guilherme Santana| Guilherme Melo |
| **Visualização de Dados** | Robertha Miranda | — |
| **Narrativa e Pitch** | Lia Marinho |  Robertha Miranda, Matheus |

**Canal de comunicação da equipe (fora do horário de aula):**

```
(grupo no WhatsApp)
```

---

## Validação do mentor (preenchida pelo mentor no E2)

| | |
|---|---|
| **Status** | ( ) Aprovado ( ) Aprovado com ajustes ( ) Devolvido com pendências |
| **Data** | |
| **Amostra baixada e aberta verificada?** | ( ) Sim ( ) Não |
| **Pendências (com prazo até o E3 — seg 21/09)** | |