# Arquitetura Técnica

## 1. Visão Geral

O sistema adota uma **arquitetura em camadas** inspirada no DDD, separando responsabilidades entre apresentação, aplicação, domínio e infraestrutura.  
O backend é uma API FastAPI em Python 3.13. O motor de IA usa **LangGraph** para orquestrar chamadas paralelas ao **Google Gemini**. O banco de dados é **PostgreSQL**.

---

## 2. Camadas da Aplicação

```
┌─────────────────────────────────────────────────────────┐
│                  Camada de API (FastAPI)                  │
│  routes/chamados.py  routes/prompts.py  routes/campos.py │
│  Validação de entrada · HTTP status codes · Swagger UI   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Camada de Controle                       │
│           controllers/input_dados.py                     │
│  Orquestração do fluxo · Cálculo de média e mediana      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Camada de Domínio                        │
│  domain/models.py    domain/graph.py                     │
│  Agregados Pydantic · Grafo LangGraph · Tipos de domínio │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Camada de Infraestrutura                 │
│  infrastructure/nodes.py   infrastructure/database.py    │
│  LLM (Gemini) · PostgreSQL · Langfuse · RabbitMQ         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Componentes e Responsabilidades

### 3.1 Backend (`backend/`)

| Componente | Localização | Responsabilidade |
|---|---|---|
| **Entry Point** | `main.py` | Inicializa o servidor Uvicorn |
| **App Factory** | `src/app/__init__.py` | Monta a aplicação FastAPI e registra routers |
| **Config** | `src/app/config.py` | Instancia e exporta o grafo compilado |
| **Routes — Chamados** | `src/app/api/routes/input_dados.py` | Endpoint de avaliação individual |
| **Routes — Prompts** | `src/app/api/routes/prompts.py` | CRUD de Prompts (Dimensões de Avaliação) |
| **Routes — Campos** | `src/app/api/routes/campos.py` | CRUD de Campos Extraídos |
| **Controller** | `src/app/controllers/input_dados.py` | Orquestra a chamada ao grafo e calcula estatísticas |
| **Domain Models** | `src/app/domain/models.py` | Modelos Pydantic de entrada/saída da API |
| **Graph Types** | `src/app/domain/graph.py` | Estado do grafo, enums e modelos internos do LangGraph |
| **Nodes** | `src/app/infrastructure/nodes.py` | Nós do grafo: `entrada` (fan-out) e `avaliar` (LLM) |
| **Database** | `src/app/infrastructure/database.py` | Context manager de conexão PostgreSQL (psycopg2) |
| **System Prompts** | `src/app/prompts/system/*.md` | Templates Markdown das 3 dimensões padrão |
| **Utils** | `src/app/utils/file.py` | Carrega system prompts do disco |
| **SQL Schema** | `backend/bd/database.sql` | DDL completo: tabelas, funções, triggers, índices |

### 3.2 Frontend (`frontend/`)

| Componente | Localização | Responsabilidade |
|---|---|---|
| **App** | `src/App.jsx` | BrowserRouter, layout com Sidebar e rotas |
| **Sidebar** | `src/components/Sidebar.jsx` | Navegação entre módulos |
| **Avaliação** | `src/pages/Avaliacao.jsx` | Interface para submissão e visualização de avaliações |
| **Prompt Manager** | `src/pages/PromptManager.jsx` | CRUD de Prompts via interface visual |
| **Campos Manager** | `src/pages/CamposManager.jsx` | CRUD de Campos Extraídos via interface visual |

---

## 4. Fluxo de Avaliação Individual (síncrone)

```
Cliente HTTP
    │
    │  POST /chamados/avaliacao_individual
    │  { "chat": "ATENDENTE: ..." }
    ▼
[API Route] input_dados.py
    │  valida schema (Pydantic)
    ▼
[Controller] InputDadosController.processar_chat(chat)
    │  chama grafo.invoke({ chat_avaliado, avaliacoes: [] })
    ▼
[Nó: entrada] — fan-out via Send
    ├──► [Nó: avaliar] TipoAvaliacao.ComunicacaoClareza
    │        └── LLM Gemini (system_prompt + chat) → { nota, justificativa }
    ├──► [Nó: avaliar] TipoAvaliacao.ProfissionalismoConformidade
    │        └── LLM Gemini (system_prompt + chat) → { nota, justificativa }
    └──► [Nó: avaliar] TipoAvaliacao.ResolucaoEficiencia
             └── LLM Gemini (system_prompt + chat) → { nota, justificativa }
    │  (execução paralela)
    ▼
[Controller] agrega lista de ResultadoAvaliacao
    │  calcula média e mediana
    ▼
[API Route] retorna HTTP 200 + ResultadoFinal (JSON)
```

---

## 5. Fluxo de Avaliação em Lote (assíncrono — roadmap)

```
Cliente HTTP
    │
    │  POST /chamados/lotes
    │  { "cnpj": "...", "chats": ["...", "..."] }
    ▼
[API Route]
    │  cria Lote no PostgreSQL (status = pending)
    │  publica N mensagens no RabbitMQ
    ▼
[Worker RabbitMQ] (processo separado)
    │  consome mensagem
    │  atualiza status do Chamado → processing
    │  chama grafo.invoke(...)
    │  persiste DetalheAvaliacao no PostgreSQL
    │  atualiza status do Chamado → done/error
    │  incrementa lote.itens_prontos
    │  se todos prontos → atualiza lote.status → done
    ▼
[Cliente HTTP]
    │  GET /chamados/lotes/{lote_id} → status e progresso
```

---

## 6. Fluxo de Extração de Metadados (proposto)

```
[Após Avaliação]
    │
    ▼
[Nó: extrair_metadados]
    │  carrega lista de CamposExtraídos ativos do banco
    │  monta prompt dinâmico com todos os campos e suas descrições
    │  chama LLM Gemini → retorna JSON com os campos preenchidos
    │  inclui metadados no ResultadoFinal
    ▼
[Armazenamento]
    │  salva JSON completo (avaliações + metadados) vinculado ao CNPJ
```

---

## 7. Modelo de Dados Resumido

```
lotes
  └── avaliacoes (Chamados)
        └── detalhes_avaliacao (por Dimensão)

prompts (Dimensões de Avaliação)
campos_extraidos (Metadados a Extrair)
logs (auditoria e erros)
```

Ver [database-schema.md](./database-schema.md) para detalhes completos.

---

## 8. Integrações Externas

| Serviço | Tipo | Uso | Obrigatório |
|---|---|---|---|
| **Google Gemini** (via `langchain-google-genai`) | LLM API | Avaliação e extração via prompts estruturados | ✅ Sim |
| **PostgreSQL** | Banco relacional | Persistência de chamados, resultados, prompts e campos | ✅ Sim |
| **RabbitMQ** | Fila de mensagens | Processamento assíncrono de lotes | ⚠️ Para lotes |
| **Langfuse** | Observabilidade | Rastreamento de execuções LLM | ❌ Opcional |

---

## 9. Decisões Arquiteturais

| Decisão | Escolha | Motivação |
|---|---|---|
| Orquestração de LLM | **LangGraph** | Suporte nativo a paralelismo via `Send`, estado tipado, extensível |
| LLM Provider | **Google Gemini 2.0 Flash** | Custo/benefício, velocidade, suporte a structured output |
| Backend framework | **FastAPI** | Performance, validação automática Pydantic, Swagger integrado |
| Banco de dados | **PostgreSQL** | Suporte a JSONB, funções PL/pgSQL, triggers, escalabilidade |
| Multi-tenancy | **CNPJ como chave** | Simples, sem overhead de schemas por tenant, adequado ao volume esperado |
| Outputs LLM | **Structured Output** | Evita pós-processamento frágil de strings; Pydantic valida na borda |
| Prompts | **Arquivos Markdown + DB** | Templates no repositório; prompts customizados pelo cliente no banco |

Ver [adr/001-langgraph-parallel-evaluation.md](./adr/001-langgraph-parallel-evaluation.md) para detalhes da decisão de paralelismo.

---

## 10. Estrutura de Diretórios

```
nps_automatico/
├── backend/
│   ├── main.py                          # Entry point
│   ├── pyproject.toml                   # Dependências (uv)
│   ├── .env.example
│   ├── bd/
│   │   └── database.sql                 # DDL PostgreSQL
│   ├── docker/
│   │   └── backend.dockerfile
│   └── src/app/
│       ├── __init__.py                  # App factory FastAPI
│       ├── config.py                    # Grafo compilado
│       ├── api/
│       │   └── routes/
│       │       ├── input_dados.py       # POST /chamados/...
│       │       ├── prompts.py           # CRUD /prompts
│       │       └── campos.py            # CRUD /campos
│       ├── controllers/
│       │   └── input_dados.py           # Orquestração
│       ├── domain/
│       │   ├── graph.py                 # Tipos LangGraph
│       │   └── models.py                # Modelos Pydantic
│       ├── infrastructure/
│       │   ├── nodes.py                 # Nós do grafo (LLM)
│       │   └── database.py              # Conexão PostgreSQL
│       ├── prompts/system/
│       │   ├── Comunicação e Clareza.md
│       │   ├── Profissionalismo e Conformidade.md
│       │   └── Resolução e Eficiência.md
│       └── utils/
│           ├── file.py                  # Leitor de prompts
│           └── validacoes.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      # Roteamento principal
│   │   ├── components/Sidebar.jsx
│   │   └── pages/
│   │       ├── Avaliacao.jsx
│   │       ├── PromptManager.jsx
│   │       └── CamposManager.jsx
│   └── Dockerfile
├── docs/                                # ← Documentação DDD
├── docker-compose.yml
└── README.md
```
