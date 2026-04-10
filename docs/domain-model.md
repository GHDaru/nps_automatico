# Modelo de Domínio

Este documento descreve os Agregados, Entidades, Objetos de Valor e Eventos de Domínio de cada Bounded Context.

---

## Contexto: Configuração de Avaliação (`config`)

### Agregado: `Prompt`

Representa uma **Dimensão de Avaliação** — uma instrução completa em Markdown que orienta o LLM sobre como analisar um determinado aspecto do atendimento.

| Atributo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | UUID | PK, gerado | Identificador único |
| `nome` | string | obrigatório, único | Nome da dimensão (ex.: *Comunicação e Clareza*) |
| `conteudo` | string (Markdown) | obrigatório | Instruções completas para o LLM: role, metodologia, rubrica e formato de saída |
| `ativo` | boolean | padrão `true` | Controla se esta dimensão participa do fluxo de avaliação |
| `criado_em` | datetime | auto | Timestamp de criação |
| `atualizado_em` | datetime | auto | Timestamp de última atualização |

**Invariantes:**
- `nome` deve ser único no escopo do Tenant.
- Apenas Prompts com `ativo = true` são utilizados pelo motor de avaliação.
- `conteudo` deve especificar o formato de saída esperado (JSON estruturado com `nota` e `justificativa`).

**Templates padrão incluídos:**
- `Comunicação e Clareza`
- `Profissionalismo e Conformidade`
- `Resolução e Eficiência`

---

### Agregado: `CampoExtraído`

Representa um **metadado** que o sistema deve identificar e extrair do texto de um Chamado.

| Atributo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | UUID | PK, gerado | Identificador único |
| `nome` | string | obrigatório, único | Chave do campo no JSON de saída (ex.: `atendente`, `categoria`) |
| `descricao` | string | obrigatório | Instrução para o LLM sobre como encontrar/inferir o campo e o que retornar quando ausente |
| `criado_em` | datetime | auto | Timestamp de criação |
| `atualizado_em` | datetime | auto | Timestamp de última atualização |

**Invariantes:**
- `nome` deve ser único (restrição de unicidade no banco).
- `descricao` deve incluir o comportamento esperado quando o campo não for encontrado (ex.: `null`, `"desconhecido"`).

---

## Contexto: Avaliação de Chamados (`avaliacao`)

### Agregado Raiz: `Lote`

Agrupa um conjunto de Chamados enviados para processamento assíncrono em massa.

| Atributo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | UUID | PK, gerado | Identificador único |
| `cnpj` | string | obrigatório | Chave do Tenant |
| `total_itens` | int | ≥ 0 | Quantidade de Chamados no lote |
| `itens_prontos` | int | ≥ 0, ≤ `total_itens` | Quantidade de Chamados já processados |
| `status` | enum | `pending`, `processing`, `done`, `error` | Estado de processamento do lote |
| `criado_em` | datetime | auto | Timestamp de criação |
| `atualizado_em` | datetime | auto | Timestamp de última atualização |

**Invariantes:**
- `itens_prontos` nunca pode exceder `total_itens`.
- Somente quando todos os itens forem processados o status pode ser `done`.

---

### Entidade: `Chamado`

Representa um atendimento individual submetido para avaliação. Pertence a um Lote ou pode ser processado de forma avulsa.

| Atributo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | UUID | PK, gerado | Identificador único |
| `cnpj` | string | obrigatório | Chave do Tenant |
| `lote_id` | UUID | FK → `Lote`, nullable | Lote ao qual pertence (null = chamado avulso) |
| `chat` | string | obrigatório | Transcrição completa do atendimento |
| `nota_media` | decimal(5,2) | 0–10, nullable | Média das notas das Dimensões avaliadas |
| `nota_mediana` | decimal(5,2) | 0–10, nullable | Mediana das notas das Dimensões avaliadas |
| `status` | enum | `pending`, `processing`, `done`, `error` | Estado do processamento |
| `criado_em` | datetime | auto | Timestamp de criação |
| `atualizado_em` | datetime | auto | Timestamp de última atualização |

---

### Entidade: `DetalheAvaliacao`

Armazena a nota e justificativa de uma Dimensão de Avaliação específica para um Chamado.

| Atributo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | UUID | PK, gerado | Identificador único |
| `avaliacao_id` | UUID | FK → `Chamado` | Chamado avaliado |
| `criterio` | string | enum de dimensões | Dimensão avaliada |
| `nota` | smallint | 0–10 | Nota atribuída pelo LLM |
| `justificativa` | string | obrigatório | Justificativa com evidências do chat |
| `criado_em` | datetime | auto | Timestamp de criação |

**Invariantes:**
- Cada combinação (`avaliacao_id`, `criterio`) deve ser única.

---

### Objeto de Valor: `ResultadoAvaliacao`

Representa o resultado consolidado de um Chamado retornado pela API. É imutável e não persiste diretamente (é computado a partir dos `DetalheAvaliacao`).

```json
{
  "avaliacoes": [
    {
      "tipo_avaliacao": "Comunicação e Clareza",
      "nota": 8,
      "justificativa": "O atendente demonstrou cordialidade..."
    }
  ],
  "nota_media": 7.67,
  "nota_mediana": 8.0,
  "metadados": {
    "atendente": "João Silva",
    "categoria": "Suporte Técnico"
  }
}
```

---

### Objeto de Valor: `EstadoGeral` (interno ao LangGraph)

Estado compartilhado entre os nós do grafo de avaliação durante a execução.

| Campo | Tipo | Descrição |
|---|---|---|
| `chat_avaliado` | string | Transcrição do Chamado sendo avaliado |
| `avaliacoes` | list[ResultadoAvaliacao] | Acumulador de resultados parciais (operação `add`) |
| `erros` | list[string] | Erros ocorridos durante o processamento (operação `add`) |
| `tipo_avaliacao` | TipoAvaliacao | Dimensão sendo avaliada pelo nó atual |

---

## Eventos de Domínio

Eventos que representam mudanças de estado relevantes no domínio. São candidatos a publicação em mensageria (ex.: RabbitMQ).

| Evento | Contexto | Trigger | Payload |
|---|---|---|---|
| `ChamadoRecebido` | avaliacao | Chamado submetido via API | `{ id, cnpj, timestamp }` |
| `AvaliacaoIniciada` | avaliacao | Processamento inicia (status → `processing`) | `{ id, cnpj, lote_id }` |
| `AvaliacaoConcluida` | avaliacao | Grafo retorna resultado com sucesso | `{ id, cnpj, nota_media, nota_mediana }` |
| `AvaliacaoFalhou` | avaliacao | Erro durante o processamento | `{ id, cnpj, erro }` |
| `LoteCriado` | avaliacao | Lote submetido via API | `{ lote_id, cnpj, total_itens }` |
| `LoteConcluido` | avaliacao | Todos os itens do lote processados | `{ lote_id, cnpj, total_itens, erros }` |
| `PromptAtualizado` | config | Prompt editado por administrador | `{ prompt_id, nome, ativo }` |
| `CampoExtraidoCriado` | config | Novo campo cadastrado | `{ campo_id, nome }` |

---

## Diagrama de Classes de Domínio

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTEXTO: config                                 │
│                                                                      │
│  ┌────────────────────┐    ┌──────────────────────────┐             │
│  │     Prompt         │    │      CampoExtraído        │             │
│  ├────────────────────┤    ├──────────────────────────┤             │
│  │ + id: UUID         │    │ + id: UUID                │             │
│  │ + nome: str        │    │ + nome: str               │             │
│  │ + conteudo: str    │    │ + descricao: str          │             │
│  │ + ativo: bool      │    │ + criado_em: datetime     │             │
│  │ + criado_em        │    │ + atualizado_em: datetime │             │
│  │ + atualizado_em    │    └──────────────────────────┘             │
│  └────────────────────┘                                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ usa (downstream)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTEXTO: avaliacao                              │
│                                                                      │
│  ┌───────────────────────────────┐                                  │
│  │            Lote               │                                  │
│  ├───────────────────────────────┤                                  │
│  │ + id: UUID                    │                                  │
│  │ + cnpj: str                   │                                  │
│  │ + total_itens: int            │                                  │
│  │ + itens_prontos: int          │                                  │
│  │ + status: Status              │                                  │
│  └──────────────┬────────────────┘                                  │
│                 │ 1..*                                               │
│  ┌──────────────▼────────────────┐                                  │
│  │           Chamado             │                                  │
│  ├───────────────────────────────┤                                  │
│  │ + id: UUID                    │                                  │
│  │ + cnpj: str                   │                                  │
│  │ + chat: str                   │                                  │
│  │ + nota_media: decimal         │                                  │
│  │ + nota_mediana: decimal       │                                  │
│  │ + status: Status              │                                  │
│  └──────────────┬────────────────┘                                  │
│                 │ 1..*                                               │
│  ┌──────────────▼────────────────┐                                  │
│  │       DetalheAvaliacao        │                                  │
│  ├───────────────────────────────┤                                  │
│  │ + id: UUID                    │                                  │
│  │ + criterio: str               │                                  │
│  │ + nota: int (0–10)            │                                  │
│  │ + justificativa: str          │                                  │
│  └───────────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```
