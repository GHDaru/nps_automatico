# DDD — Visão Geral: Linguagem Ubíqua, Bounded Contexts e Context Map

## 1. Linguagem Ubíqua (Ubiquitous Language)

Os termos abaixo são usados de forma consistente entre a equipe de negócio e a equipe técnica em todo o projeto.

| Termo | Definição |
|---|---|
| **Chamado** | Uma transcrição completa de um atendimento ao cliente (chat, e-mail ou voz transcrito). É a unidade central de análise do sistema. |
| **Atendimento** | Sinônimo de Chamado no contexto de negócio. |
| **Lote** | Conjunto de Chamados enviados de uma só vez para processamento assíncrono em massa. |
| **Avaliação** | Resultado produzido pela IA para um Chamado, composto por notas e justificativas por Dimensão. |
| **Dimensão de Avaliação** | Aspecto específico do atendimento que é analisado (ex.: *Comunicação e Clareza*). Cada Dimensão é definida por um Prompt. |
| **Prompt** | Instrução em linguagem natural (Markdown) que define uma Dimensão de Avaliação e orienta o LLM sobre como avaliar e que nota atribuir. |
| **Campo Extraído** | Metadado que o sistema deve identificar e extrair do Chamado (ex.: nome do cliente, nome do atendente, categoria do problema). |
| **Extrator** | Prompt especializado que instrui o LLM a extrair um conjunto de Campos Extraídos de um Chamado. |
| **Resultado** | Objeto JSON retornado pela API contendo as notas por Dimensão, média, mediana e os metadados extraídos. |
| **Tenant / Cliente** | Empresa contratante identificada pelo CNPJ. Todos os dados são segregados por CNPJ. |
| **Usuário** | Pessoa que acessa o sistema em nome de um Tenant. Pode ser *Administrador* ou *Analista*. |
| **Atendente** | Colaborador do Tenant cujos atendimentos são avaliados (não necessariamente tem acesso ao sistema). |
| **Template** | Prompt pré-configurado que vem instalado com o sistema para uso imediato. |
| **Entrada Ativa** | Modalidade em que o sistema busca chamados em sistemas externos (pull). |
| **Entrada Passiva** | Modalidade em que o chamado é enviado por um usuário ou integração externa (push). |
| **Status** | Estado de processamento de um Lote ou Chamado: `pending`, `processing`, `done`, `error`. |

---

## 2. Bounded Contexts (Contextos Delimitados)

O sistema é dividido em três contextos com responsabilidades distintas.

### 2.1 Contexto: Configuração de Avaliação (`config`)

> **Tipo:** Supporting Domain

Responsável por gerenciar os artefatos de configuração que orientam o motor de IA.

**Responsabilidades:**
- CRUD de Prompts (Dimensões de Avaliação)
- CRUD de Campos Extraídos
- Ativação/desativação de Prompts
- Templates padrão embutidos no sistema

**Agregados principais:** `Prompt`, `CampoExtraído`

**Ator principal:** Administrador do Tenant

---

### 2.2 Contexto: Avaliação de Chamados (`avaliacao`)

> **Tipo:** Core Domain

Coração do sistema. Responsável por receber chamados, orquestrar a avaliação via LLM e persistir os resultados.

**Responsabilidades:**
- Recebimento de chamados individuais (entrada passiva via API)
- Recebimento de lotes de chamados (entrada passiva em massa)
- Integração com sistemas externos para coleta de chamados (entrada ativa — roadmap)
- Orquestração do grafo de avaliação paralela (LangGraph)
- Orquestração da extração de metadados
- Armazenamento do Resultado como JSON com chave CNPJ

**Agregados principais:** `Chamado`, `Lote`, `Resultado`

**Ator principal:** API externa, sistema integrador, usuário via frontend

---

### 2.3 Contexto: Relatórios e Dashboards (`relatorios`)

> **Tipo:** Supporting Domain — Roadmap

Responsável pela visualização analítica dos resultados de avaliação por parte dos clientes.

**Responsabilidades:**
- Consulta de avaliações por Tenant (CNPJ)
- Relatórios de média/mediana por Atendente
- Relatórios de média/mediana por Cliente do Tenant
- Visualização dos detalhes de cada Chamado avaliado
- Filtros temporais e por status

**Agregados principais:** `RelatorioAtendente`, `RelatorioCliente` (leituras sobre `Chamado`)

**Ator principal:** Usuário / Analista do Tenant

---

## 3. Context Map (Mapa de Contextos)

```
┌──────────────────────────────────┐
│   Configuração de Avaliação       │
│   (Supporting Domain)             │
│                                   │
│  Prompt ◄── CRUD API              │
│  CampoExtraído ◄── CRUD API       │
└──────────────┬───────────────────┘
               │  usa (conformista / downstream)
               ▼
┌──────────────────────────────────┐
│   Avaliação de Chamados           │◄── POST /chamados/avaliacao_individual
│   (Core Domain)                   │◄── POST /chamados/lotes
│                                   │◄── Entrada Ativa (roadmap)
│  Chamado ──► LangGraph Grafo      │
│              ├── Avaliador LLM x N│
│              └── Extrator LLM     │
│  Resultado ──► JSON + PostgreSQL  │
└──────────────┬───────────────────┘
               │  leitura (anti-corruption layer)
               ▼
┌──────────────────────────────────┐
│   Relatórios e Dashboards         │
│   (Supporting Domain — Roadmap)   │
│                                   │
│  RelatorioAtendente               │
│  RelatorioCliente                 │
└──────────────────────────────────┘
```

### Relacionamentos entre contextos

| Produtor | Consumidor | Padrão | Descrição |
|---|---|---|---|
| `config` | `avaliacao` | **Conformista** | O motor de avaliação consome os Prompts e CamposExtraídos configurados exatamente como estão persistidos. |
| `avaliacao` | `relatorios` | **Anti-Corruption Layer** | O módulo de relatórios lê dados do contexto de avaliação através de queries/views dedicadas, sem acoplamento direto ao modelo interno. |
| `avaliacao` | API Externa | **Open Host Service** | O contexto de avaliação expõe uma API REST pública para integração com sistemas externos. |

---

## 4. Subdomínios

| Subdomínio | Tipo | Justificativa |
|---|---|---|
| Avaliação multi-dimensional por LLM | **Core** | Diferencial competitivo; lógica proprietária de prompts e grafo paralelo. |
| Extração de metadados por LLM | **Core** | Valor direto para o cliente; configurável e extensível. |
| Gestão de Prompts e Campos | **Supporting** | Necessário, mas sem diferenciação; pode evoluir para Generic se necessário. |
| Autenticação e multi-tenancy | **Generic** | Pode ser implementado com biblioteca/serviço padrão de mercado. |
| Relatórios e dashboards | **Supporting** | Agrega valor mas não é o diferencial do produto. |
| Ingestão em lote / mensageria | **Generic** | Padrão de mercado (RabbitMQ / fila). |
