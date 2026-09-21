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
| CAT (Comunicação de Acidente de Trabalho) | dadosabertos.inss.gov.br | `[EQUIPE]` | `[EQUIPE]` | Dados abertos |
| RAIS / Novo CAGED | basedosdados.org, gov.br/trabalho-e-emprego | `[EQUIPE]` | `[EQUIPE]` | Dados abertos |
| SINAN (extensão) | datasus.saude.gov.br | `[EQUIPE]` | `[EQUIPE]` | Dados abertos |
| CONCLA (CNAE) | concla.ibge.gov.br | `[EQUIPE]` | tabela de referência | Pública |
| CBO | gov.br/trabalho-e-emprego | `[EQUIPE]` | tabela de referência | Pública |

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

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ (local ou Docker)
- VSCode com extensões: Python, Jupyter, PostgreSQL (ou pgAdmin à parte)

### 2. Clonar e instalar dependências

```bash
git clone <link-do-repo>
cd repo-visat
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar o banco

```bash
# criar o banco (ajuste usuário/senha conforme seu Postgres local)
createdb visat_recife

# aplicar o schema
psql -d visat_recife -f sql/01_schema.sql
```

Configure as credenciais em um arquivo `.env` na raiz (não versionar):

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=visat_recife
DB_USER=postgres
DB_PASSWORD=sua_senha
```

### 4. Rodar o pipeline (fonte → banco), fim a fim

```bash
python pipeline/01_coleta.py
python pipeline/02_transformacao.py
python pipeline/03_carga.py
```

### 5. Rodar a EDA

```bash
jupyter notebook analises/eda.ipynb
```

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

`Filtro geográfico da CAT usa município do empregador, não o local exato do acidente, pois a coluna está corrompida.O filtro de datas do RAIS e CAGED está entre 2023 e 2025, pois no rais não foram encontrados dados do RAIS e, em relação ao CAGED, somente dados pagos podem ser encontrados de 2026, com limite para fevereiro`