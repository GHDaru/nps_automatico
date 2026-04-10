# Esquema do Banco de Dados

**SGBD:** PostgreSQL 14+  
**Arquivo DDL:** `backend/bd/database.sql`

---

## Diagrama Entidade-Relacionamento

```
                        ┌──────────────────────────┐
                        │          lotes            │
                        ├──────────────────────────┤
                        │ id (PK)       UUID        │
                        │ cnpj          TEXT        │
                        │ total_itens   INT         │
                        │ itens_prontos INT         │
                        │ status        status      │
                        │ criado_em     TIMESTAMPTZ │
                        │ atualizado_em TIMESTAMPTZ │
                        └────────────┬─────────────┘
                                     │ 1:N
                        ┌────────────▼─────────────┐
                        │        avaliacoes         │
                        ├──────────────────────────┤
                        │ id (PK)       UUID        │
                        │ cnpj          TEXT        │
                        │ lote_id (FK)  UUID        │
                        │ chat          TEXT        │
                        │ nota_media    DECIMAL(5,2)│
                        │ nota_mediana  DECIMAL(5,2)│
                        │ status        status      │
                        │ criado_em     TIMESTAMPTZ │
                        │ atualizado_em TIMESTAMPTZ │
                        └────────────┬─────────────┘
                                     │ 1:N
                        ┌────────────▼─────────────┐
                        │    detalhes_avaliacao     │
                        ├──────────────────────────┤
                        │ id (PK)       UUID        │
                        │ avaliacao_id (FK) UUID    │
                        │ criterio  criterio_av..   │
                        │ nota          SMALLINT    │
                        │ justificativa TEXT        │
                        │ criado_em     TIMESTAMPTZ │
                        │ UNIQUE(avaliacao_id,      │
                        │        criterio)          │
                        └──────────────────────────┘

┌──────────────────────────┐   ┌──────────────────────────┐
│         prompts          │   │     campos_extraidos      │
├──────────────────────────┤   ├──────────────────────────┤
│ id (PK)       UUID       │   │ id (PK)       UUID       │
│ nome          TEXT       │   │ nome          TEXT UNIQUE│
│ conteudo      TEXT       │   │ descricao     TEXT       │
│ ativo         BOOLEAN    │   │ criado_em     TIMESTAMPTZ│
│ criado_em     TIMESTAMPTZ│   │ atualizado_em TIMESTAMPTZ│
│ atualizado_em TIMESTAMPTZ│   └──────────────────────────┘
└──────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                           logs                            │
├──────────────────────────────────────────────────────────┤
│ id (PK)   BIGSERIAL                                       │
│ criado_em TIMESTAMPTZ                                     │
│ nivel     nivel_log  (info | warning | error)            │
│ origem    TEXT                                            │
│ mensagem  TEXT                                            │
│ contexto  JSONB                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Tabelas

### `lotes`

Agrupa chamados enviados em massa para processamento assíncrono.

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Identificador único do lote |
| `cnpj` | TEXT | NOT NULL | CNPJ do Tenant |
| `total_itens` | INT | NOT NULL | Total de chamados no lote |
| `itens_prontos` | INT | NOT NULL | Chamados já processados |
| `status` | `status` | NOT NULL, default `'pending'` | Estado atual do lote |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp de criação |
| `atualizado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Atualizado por trigger |

**Índices:** `cnpj`, `status WHERE pending`, `criado_em`, `(cnpj, status)`

---

### `avaliacoes`

Cada linha representa um chamado individual avaliado ou em avaliação.

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Identificador único da avaliação |
| `cnpj` | TEXT | NOT NULL | CNPJ do Tenant |
| `lote_id` | UUID | FK → `lotes(id)` ON DELETE CASCADE, nullable | Lote pai (null = avulso) |
| `chat` | TEXT | NOT NULL | Transcrição completa do chamado |
| `nota_media` | DECIMAL(5,2) | CHECK 0–10, nullable | Média das notas das dimensões |
| `nota_mediana` | DECIMAL(5,2) | CHECK 0–10, nullable | Mediana das notas das dimensões |
| `status` | `status` | NOT NULL, default `'pending'` | Estado do processamento |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp de criação |
| `atualizado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Atualizado por trigger |

**Índices:** `lote_id`, `cnpj`, `status WHERE pending`, `criado_em`, `(lote_id, status)`

---

### `detalhes_avaliacao`

Armazena nota e justificativa por dimensão de avaliação para cada chamado.

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Identificador único |
| `avaliacao_id` | UUID | NOT NULL, FK → `avaliacoes(id)` ON DELETE CASCADE | Chamado avaliado |
| `criterio` | `criterio_avaliacao` | NOT NULL | Dimensão avaliada |
| `nota` | SMALLINT | NOT NULL, CHECK 0–10 | Nota atribuída pelo LLM |
| `justificativa` | TEXT | NOT NULL | Justificativa com evidências |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp de criação |

**Constraint:** `UNIQUE(avaliacao_id, criterio)` — cada dimensão aparece uma única vez por avaliação.  
**Índice:** `avaliacao_id`

---

### `prompts`

Armazena os prompts de avaliação configurados (uma linha = uma Dimensão de Avaliação).

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Identificador único |
| `nome` | TEXT | NOT NULL | Nome da dimensão |
| `conteudo` | TEXT | NOT NULL | Instruções Markdown para o LLM |
| `ativo` | BOOLEAN | NOT NULL, default `true` | Controla participação no fluxo |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp de criação |
| `atualizado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Atualizado por trigger |

**Índice:** `ativo`

---

### `campos_extraidos`

Metadados que o sistema deve extrair dos chamados.

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Identificador único |
| `nome` | TEXT | NOT NULL, UNIQUE | Chave no JSON de saída |
| `descricao` | TEXT | NOT NULL | Instrução para o LLM e comportamento quando ausente |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp de criação |
| `atualizado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Atualizado por trigger |

---

### `logs`

Registro de eventos do sistema para auditoria e depuração.

| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| `id` | BIGSERIAL | PK | Sequencial para ordenação temporal |
| `criado_em` | TIMESTAMPTZ | NOT NULL, default `now()` | Timestamp do evento |
| `nivel` | `nivel_log` | NOT NULL | `info` / `warning` / `error` |
| `origem` | TEXT | NOT NULL | Módulo ou função que gerou o log |
| `mensagem` | TEXT | NOT NULL | Descrição do evento |
| `contexto` | JSONB | nullable | Dados adicionais (stacktrace, parâmetros) |

**Índices:** `nivel`, `origem`, `criado_em`, GIN em `contexto`, BRIN em `criado_em`

---

## ENUMs

| Enum | Valores | Uso |
|---|---|---|
| `status` | `pending`, `processing`, `done`, `error` | Estado de `lotes` e `avaliacoes` |
| `criterio_avaliacao` | `Comunicação e Clareza`, `Profissionalismo e Conformidade`, `Resolução e Eficiência` | Dimensão em `detalhes_avaliacao` |
| `nivel_log` | `info`, `warning`, `error` | Severidade em `logs` |

---

## Funções PL/pgSQL

### `inserir_avaliacao_completa(p_cnpj, p_chat, p_detalhes, p_lote_id?)`

Insere atomicamente uma avaliação completa (registro em `avaliacoes` + N registros em `detalhes_avaliacao`) e retorna um JSONB com o resultado consolidado.

**Parâmetros:**
- `p_cnpj TEXT` — CNPJ do Tenant
- `p_chat TEXT` — Transcrição do chamado
- `p_detalhes JSONB` — Array de `{ tipo_avaliacao, nota, justificativa }`
- `p_lote_id UUID` (opcional) — ID do lote pai

**Retorno:** `JSONB { avaliacao_id, nota_media, nota_mediana, detalhes[] }`

---

### `criar_lote(p_cnpj, p_total_itens, p_itens_prontos)`

Cria um novo lote e retorna o UUID gerado.

---

## Triggers

| Trigger | Tabela | Evento | Ação |
|---|---|---|---|
| `lotes_atualizado_em` | `lotes` | BEFORE UPDATE | Atualiza `atualizado_em` para `NOW()` |
| `avaliacoes_atualizado_em` | `avaliacoes` | BEFORE UPDATE | Atualiza `atualizado_em` para `NOW()` |
| `prompts_atualizado_em` | `prompts` | BEFORE UPDATE | Atualiza `atualizado_em` para `NOW()` |
| `campos_extraidos_atualizado_em` | `campos_extraidos` | BEFORE UPDATE | Atualiza `atualizado_em` para `NOW()` |

---

## Notas de Evolução

- Para suportar **multi-tenancy com isolamento por schema**, substituir a coluna `cnpj` por um schema PostgreSQL por tenant. Requer migração.
- O campo `lote_id` em `avaliacoes` é nullable para permitir chamados avulsos (fora de lote).
- O ENUM `criterio_avaliacao` é estático no banco. Quando os prompts forem 100% dinâmicos (carregados do banco), esta restrição deve ser removida e `criterio` passar a ser `TEXT` referenciando `prompts.nome`.
- A tabela `campos_extraidos` não possui FK para `avaliacoes` — os metadados extraídos são retornados diretamente no JSON do resultado, não persistidos em coluna separada (considerar tabela `metadados_avaliacao` futuramente).
