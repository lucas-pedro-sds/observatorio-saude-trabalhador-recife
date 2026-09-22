# Observatório de Saúde do Trabalhador — Recife (VISAT)

Projeto Integrador — NExT Dados (CESAR School). Ciclo completo de dados:
fonte pública bruta → banco PostgreSQL → pipeline Python → EDA → dashboard
orientado à decisão, para a Secretaria de Saúde do Recife (VISAT).

## Equipe

`[EQUIPE] listar integrantes e papéis — ver docs/canvas-projeto.md`

## Problema

A gerência da VISAT decide onde inspecionar e que política de saúde do
trabalhador levar a que território, mas hoje o diagnóstico é feito sob
demanda, sem um observatório contínuo. Ver detalhamento em
`docs/canvas-projeto.md`.

## Fontes de dados

| Fonte | Origem | Data de coleta | Volume | Licença |
|---|---|---|---|---|
| CAT (Comunicação de Acidente de Trabalho) | dadosabertos.inss.gov.br | 2023-2025 | 15.729 notificações | Dados abertos |
| RAIS / Novo CAGED | basedosdados.org, gov.br/trabalho-e-emprego | 2023-2025 | 533k (RAIS) + 1,27M (CAGED) | Dados abertos |
| SINAN (grupo ACGR, acidente de trabalho) | ftp.datasus.gov.br, via pacote `pysus` | 2023-2025 (dados PRELIM) | ~3.650 notificações | Dados abertos |
| SINAN (grupo ACBI, acidente com material biológico) | ftp.datasus.gov.br, via pacote `pysus` | 2023-2025 (dados PRELIM) | ~5.424 notificações | Dados abertos |
| CONCLA (CNAE) | concla.ibge.gov.br | tabela de referência | 673 classes | Pública |
| CBO | gov.br/trabalho-e-emprego | tabela de referência | 2.725 ocupações | Pública |
| CID-10 | basedosdados.org (`br_bd_diretorios_brasil.cid_10`) | tabela de referência | 14.941 códigos | Pública |

### Dicionário de dados (mínimo)

Preencher por tabela carregada no banco (nome da coluna, tipo, descrição,
exemplo). Sugestão de estrutura por tabela — copiar para cada uma:

```
### tabela: cat
| coluna | tipo | descrição | exemplo |
|---|---|---|---|
| cbo | varchar | código da ocupação (CBO) | `[preencher]` |
| cid10 | varchar | diagnóstico (CID-10) | `[preencher]` |
| cnae | varchar | atividade econômica (CNAE 2.0) | `[preencher]` |
| municipio | varchar | município do acidente/notificação | `[preencher]` |
| data_acidente | date | data do evento | `[preencher]` |
```

## Como rodar o projeto

**Antes de tudo, o que você precisa fazer depende do seu papel:**

- **Time de análise** (só consultar os dados já tratados): vá direto para a seção "Acesso ao banco para análise (DBeaver)" abaixo — não precisa instalar nada em Python nem rodar a pipeline.
- **Engenharia de dados** (rodar a pipeline de coleta/transformação/carga do zero): siga os passos 1-4 abaixo. Atenção: isso **não é totalmente reprodutível só com `git clone`** — veja os avisos em cada passo.

### 1. Pré-requisitos

- **Python 3.11** especificamente (no Windows). Não use 3.12/3.13: `basedosdados` e `pysus` juntos forçam o `pip` a instalar uma versão antiga e fixa de uma dependência transitiva (`cffi==1.15.1`) que **não tem instalador pronto para Python 3.12+ no Windows** — sem 3.11, o `pip install` trava pedindo o "Microsoft Visual C++ Build Tools" (~6GB) para compilar do zero. Confirmado testando em ambiente limpo; ver detalhe técnico no final desta seção.
- Conta no Google Cloud com um projeto de billing configurado (necessário para RAIS/CAGED/CID-10, que usam `basedosdados`/BigQuery — ver `docs/` ou perguntar no grupo do time como configurar `gcloud auth application-default login`)
- VSCode com extensões: Python, Jupyter, PostgreSQL (ou pgAdmin à parte)

### 2. Clonar e instalar dependências

```bash
git clone <link-do-repo>
cd observatorio-saude-trabalhador-recife
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Detalhe técnico do problema do `cffi`** (por que precisa ser Python 3.11): sozinho, `basedosdados` pede uma versão moderna de `cffi` (via `cryptography`/`google-auth`, sem problema). Sozinho, `pysus` nem usa `cffi`. Mas **os dois instalados juntos** fazem o resolvedor de dependências do `pip` recuar para uma combinação mais antiga de pacotes — incluindo `cffi==1.15.1` — para satisfazer as duas listas de exigências ao mesmo tempo. Essa versão específica do `cffi` só tem instalador pronto (wheel) para Windows até o Python 3.11; em 3.12/3.13 o `pip` tenta compilar do zero e precisa do Visual C++ Build Tools. Testamos forçar uma versão mais nova do `cffi` antes de instalar os outros pacotes — não resolveu, o `pip` reverte de qualquer forma. Se alguém preferir não trocar de versão do Python, a alternativa é instalar o "Microsoft C++ Build Tools" (aba "Desktop development with C++" no instalador do Visual Studio).

### 3. Configurar o `.env`

O banco é **compartilhado na nuvem (Aiven)**, não local — não precisa instalar PostgreSQL na sua máquina. Copie `.env.example` para `.env` e preencha:

```
GCP_BILLING_PROJECT_ID=<seu-projeto-gcp>
DB_HOST=<peça no grupo do time>
DB_PORT=<peça no grupo do time>
DB_NAME=defaultdb
DB_USER=<peça no grupo do time>
DB_PASSWORD=<peça no grupo do time>
```

O schema (`sql/01_schema.sql`) já está aplicado no banco compartilhado — só aplique de novo se estiver testando localmente (ex: Postgres via Docker) antes de mexer em algo sensível.

### 4. Rodar o pipeline (fonte → banco), fim a fim

```bash
python pipeline/01_coleta.py
python pipeline/02_transformacao.py
python pipeline/03_carga.py
```

**Aviso importante**: `01_coleta.py` sozinho **não funciona do zero num clone limpo** para todas as fontes:
- `rais`, `caged`, `cid10` (via `basedosdados`) e `sinan` (via FTP direto) baixam da fonte automaticamente — funcionam com só o `.env` configurado.
- `cat`, `cbo`, `cnae` **leem arquivos que já precisam estar em `dados/brutos/<fonte>/`** — essas pastas ficam fora do Git (dados sensíveis/brutos não são versionados, ver `.gitignore`), então cada pessoa precisa baixar manualmente do INSS/CONCLA/MTE (ver `docs/canvas-projeto.md` para os links) antes de rodar essas três.

Rode `python pipeline/01_coleta.py <fonte>` (ex: `rais`, `sinan`) para testar só uma fonte por vez.

### 5. Rodar a EDA

```bash
jupyter notebook analises/eda.ipynb
```

## Acesso ao banco para análise (DBeaver)

O time de análise não precisa da pipeline Python — só consultar o banco já populado, com um usuário de leitura (`time_analise`).

1. Peça host, porta e senha do usuário `time_analise` no grupo do time (não ficam neste README por segurança).
2. No DBeaver: Nova Conexão → PostgreSQL → preencher Host/Porta/Banco (`defaultdb`)/Usuário (`time_analise`)/Senha.
3. Na aba SSL, marcar "Use SSL", modo `require` (o Aiven exige conexão criptografada).
4. Test Connection (aceitar o download do driver se pedido).

Esse usuário só tem permissão de leitura (`SELECT`) — não altera dado.

## Estrutura do repositório

```
repo-visat/
├── README.md
├── requirements.txt
├── dados/
│   ├── amostra/
│   └── brutos/
├── sql/
│   ├── 01_schema.sql
│   └── 02_consultas_analise.sql
├── pipeline/
│   ├── 01_coleta.py
│   ├── 02_transformacao.py
│   └── 03_carga.py
├── analises/
│   └── eda.ipynb
├── dashboard/
├── pitch/
│   ├── roteiro.md
│   ├── slides/
│   └── demo-plano-b.mp4
└── docs/
    ├── canvas-projeto.md
    ├── checkpoint-1.md
    ├── checkpoint-2.md
    └── plano-recuperacao.md
```

## Cronograma / entregável parcial de cada noite

`[EQUIPE] copiar o cronograma do guia do projeto e marcar aqui o que foi
entregue a cada sessão — dois checkouts seguidos sem entregável escala
para a coordenação.`

## Limitações conhecidas dos dados

`Filtro geográfico da CAT usa município do empregador, não o local exato do acidente, pois a coluna está corrompida. O filtro de datas do RAIS e CAGED está entre 2023 e 2025, pois na RAIS não foram encontrados dados mais recentes e, em relação ao CAGED, somente dados pagos podem ser encontrados a partir de 2026, com limite até fevereiro.

A coluna natureza_estabelecimento da RAIS foi descartada na transformação: o JOIN com o dicionário de tradução na consulta de coleta nunca bateu nenhuma linha (100% NULL), provavelmente por descompasso de tipo na condição do JOIN no BigQuery. Como não fazia parte da fatia mínima do canvas, optamos por descartar em vez de reprocessar a coleta. subatividade_ibge (RAIS) e origem_informacao (CAGED) também foram descartadas pelo mesmo motivo (100% NULL nesse recorte), mas sem indício de bug de JOIN — parecem campos não populados pela própria fonte para Recife/período filtrado.

A CAT tem colunas de identificação sensíveis tratadas na transformação: CNPJ/CEI Empregador foi descartado por completo (identificador direto da empresa). Data de nascimento é generalizada para só o ano (ano_nascimento). **Data do acidente (`data_acidente`) é mantida exata** — decisão do time em reunião de 21/09/2026, revertendo a generalização anterior (que era ano/mês). Isso reintroduz o risco de reidentificação que a generalização mitigava (data + sexo + CNAE pode identificar alguém em empresas pequenas); o time decidiu que a precisão por dia era necessária para a análise. Restam também três datas administrativas exatas (Data Afastamento, Data Despacho Benefício, Data Emissão CAT), mantidas por serem potencialmente úteis para análise de prazo/subnotificação.

O código de CNAE não tem a mesma granularidade entre fontes: RAIS/CAGED usam Subclasse (7 dígitos), a CAT usa um código de 4 dígitos (Classe sem o dígito verificador). A dim_cnae guarda ambas as chaves (classe_codigo de 5 dígitos e classe_codigo_4) para permitir o JOIN de cada fonte no nível certo.

O SINAN (grupo ACGR, `pipeline/01_coleta.py:coletar_sinan_acgr()`, tabela `fato_sinan_acgr`) tem particularidades: (1) os anos 2023-2025 existem só como **PRELIM** (dado preliminar, ainda não consolidado pelo Ministério da Saúde — pode mudar em revisões futuras, diferente das outras fontes que já usam dado consolidado); (2) a função de conveniência do pacote `pysus` (`sinan()`/`list_files()`) está retornando vazio nessa versão (2.11.2) mesmo quando o dado existe no servidor — contornamos baixando via FTP direto (`ftplib`) e convertendo com `pyreaddbc`, que o próprio `pysus` já traz como dependência; (3) o filtro geográfico usa `MUN_ACID` (local real do acidente), não `ID_MUNICIP` (local da notificação, que infla o número por Recife ser polo regional de saúde — 1.475 vs. 856 registros no teste com dados de 2023); (4) `cid_acid`/`cid_lesao` vêm às vezes como código de categoria (3 caracteres, ex. "V89.", com ponto no lugar do 4º caractere) e às vezes de subcategoria (4 caracteres) — o ponto é removido na transformação, mas a `dim_cid10` não tem `FOREIGN KEY` para esses campos porque uma FK só cobre uma coluna (categoria OU subcategoria); quem consultar precisa checar as duas. `fato_sinan_acgr` mantém as 54 colunas originais da fonte, sem descartar nenhuma — ainda não está claro quais o time de análise vai usar.

O SINAN também tem o grupo **ACBI** (acidente com material biológico — `coletar_sinan_acbi()`, tabela `fato_sinan_acbi`), mantido como tabela separada (não unificada com o ACGR): é um formulário bem diferente (68 colunas, foco em protocolo de biossegurança — tipo de exposição, EPI usado, esquema vacinal —, sem nenhum campo de CID-10). Duas diferenças em relação ao ACGR: (1) não existe `MUN_ACID` nesse formulário, então o filtro geográfico usa `mun_emp` (município do empregador) como proxy do local do acidente, mesma lógica e mesma limitação já documentada para a CAT; (2) `sem_acid` (semana epidemiológica) precisou de `INTEGER` em vez de `SMALLINT` no schema — a fonte tem pelo menos um valor claramente errado (`197729`, ano "1977" não faz sentido no recorte 2023-2025), mas optamos por um tipo mais largo em vez de filtrar a linha, já que não é nosso papel corrigir erro de digitação da fonte original sem confirmar com o time.

Também há um conflito de versão conhecido entre `pysus` e `basedosdados` na dependência `loguru` (`pysus` declara `<0.7`, `basedosdados` exige `>=0.7`) — testado e confirmado que `loguru>=0.7` funciona bem com os dois pacotes, apesar do aviso que o `pip` mostra ao instalar (ver comentário no `requirements.txt`).