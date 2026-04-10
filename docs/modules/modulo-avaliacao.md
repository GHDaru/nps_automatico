# Módulo de Avaliação de Chamados

> **Bounded Context:** `avaliacao`  
> **Tipo:** Core Domain  
> **Status:** Em desenvolvimento

---

## Responsabilidade

Este módulo é o coração do sistema. Recebe transcrições de atendimentos (chamados) e coordena:

1. A **avaliação multi-dimensional** via LLM, onde cada dimensão é analisada em paralelo.
2. A **extração de metadados** configuráveis do texto do chamado.
3. O **armazenamento** dos resultados JSON vinculados ao CNPJ do Tenant.
4. O **rastreamento do status** de processamento individual e por lote.

---

## Modalidades de Entrada

### Entrada Passiva (Push)

O chamado é enviado ao sistema por um usuário ou integração externa.

| Modalidade | Endpoint | Processamento |
|---|---|---|
| Individual | `POST /chamados/avaliacao_individual` | Síncrono — resposta imediata |
| Em lote | `POST /chamados/lotes` _(roadmap)_ | Assíncrono — via fila RabbitMQ |

### Entrada Ativa (Pull) _(Roadmap)_

O sistema busca chamados em plataformas externas (CRMs, sistemas de atendimento como Zendesk, Freshdesk, etc.).

- Configurado por Tenant: URL do endpoint externo, credenciais, frequência de coleta.
- Um job agendado (ou webhook) dispara a coleta e envia os chamados para a fila de processamento.

---

## Motor de Avaliação (LangGraph)

O motor utiliza um **grafo de estado** (LangGraph) que distribui a avaliação em paralelo entre os nós de avaliação.

### Grafo de Execução

```
START
  │
  ▼
[entrada]  ←── nó fan-out
  │   Distribui via Send para cada Dimensão ativa
  ├──► [avaliar] (Comunicação e Clareza)
  ├──► [avaliar] (Profissionalismo e Conformidade)
  └──► [avaliar] (Resolução e Eficiência)
            │  (execução paralela)
            ▼
           END  ←── estado agregado com todas as avaliações
```

### Nó `entrada`

- Lê as Dimensões ativas (atualmente hardcoded no enum `TipoAvaliacao`; roadmap: carregar do banco).
- Dispara um `Send("avaliar", ...)` para cada Dimensão, habilitando paralelismo.

### Nó `avaliar`

- Recebe o `chat` e o `tipo_avaliacao`.
- Carrega o system prompt correspondente (do disco ou do banco).
- Invoca o LLM (Gemini 2.0 Flash) com `structured_output` → `ResultadoAnalise { nota, justificativa }`.
- Retorna o resultado acumulado na chave `avaliacoes` do estado.

### Estado Compartilhado (`EstadoGeral`)

```python
class EstadoGeral(TypedDict):
    chat_avaliado: str                           # entrada
    avaliacoes: Annotated[list[...], op.add]     # acumulador (paralelo-safe)
    erros: Annotated[list[str], op.add]          # erros parciais
    tipo_avaliacao: TipoAvaliacao                # contexto do nó
```

O uso de `Annotated[list, op.add]` garante que resultados de nós paralelos são corretamente mesclados.

---

## Extração de Metadados

### Situação Atual

A tabela `campos_extraidos` e a rota `/campos` já estão implementadas, mas **o nó de extração no grafo ainda não existe**.

### Proposta de Implementação

Adicionar um nó `extrair_metadados` ao grafo, executado **após** a avaliação:

```
START → entrada → avaliar (×N, paralelo) → extrair_metadados → END
```

**Comportamento do nó:**

1. Consulta a lista de `CamposExtraídos` ativos no banco.
2. Monta um prompt dinâmico:
   ```
   Extraia os seguintes campos do chamado abaixo.
   Para cada campo, siga a instrução fornecida.
   
   Campos:
   - atendente: Nome completo do atendente. Se não encontrado, retornar null.
   - categoria: Categoria do problema. Se não identificado, retornar "Não identificado".
   
   Retorne um JSON com exatamente as chaves acima.
   ```
3. Invoca o LLM com `structured_output` dinâmico ou extrai via parsing.
4. Adiciona o objeto `metadados` ao `ResultadoFinal`.

---

## Gerenciamento de Prompts

### Situação Atual

- **3 templates** estão presentes como arquivos Markdown em `src/app/prompts/system/`.
- A rota `/prompts` (CRUD) e a tabela `prompts` estão implementadas.
- **Gap:** O nó `avaliar` ainda carrega prompts do disco (`abrir_system_prompt()`), não do banco.

### Evolução Proposta

1. **Fase 1 (imediata):** Popular a tabela `prompts` com os 3 templates na inicialização do sistema (seed/migration).
2. **Fase 2:** Modificar o nó `avaliar` para buscar o prompt pelo nome da Dimensão na tabela `prompts`, com cache em memória com TTL.
3. **Fase 3:** Tornar o enum `TipoAvaliacao` dinâmico — carregar as Dimensões ativas do banco em tempo de execução, eliminando o código hardcoded.

---

## Armazenamento dos Resultados

### Atual

- Tabelas `avaliacoes` e `detalhes_avaliacao` no PostgreSQL.
- A função `inserir_avaliacao_completa()` realiza a inserção atomicamente.
- O resultado também é retornado diretamente na resposta da API.

### Proposta — Banco Não Estruturado

Para casos de uso analítico e consulta rápida por CNPJ, o JSON completo do resultado (incluindo metadados extraídos) deve ser armazenado em um banco de dados orientado a documentos (ex.: MongoDB, CouchDB, ou JSONB no PostgreSQL).

**Estrutura do documento:**

```json
{
  "_id": "uuid-da-avaliacao",
  "cnpj": "11222333000181",
  "lote_id": "uuid-do-lote",
  "chat": "ATENDENTE: ...",
  "criado_em": "2025-04-10T10:00:00Z",
  "avaliacoes": [
    {
      "tipo_avaliacao": "Comunicação e Clareza",
      "nota": 8,
      "justificativa": "..."
    }
  ],
  "nota_media": 8.0,
  "nota_mediana": 8.0,
  "metadados": {
    "atendente": "João Silva",
    "categoria": "Suporte Técnico"
  }
}
```

**Índices recomendados:** `cnpj`, `lote_id`, `criado_em`, `nota_media`

---

## Gestão de Erros

| Cenário | Comportamento |
|---|---|
| LLM retorna resposta malformada | Nó registra erro em `erros` do estado; avaliação da Dimensão é omitida do resultado |
| Todas as Dimensões falham | API retorna `502 Bad Gateway` com detalhe do erro |
| Lote com item com erro | Item recebe `status = error`; lote continua processando os demais |
| Banco indisponível | API retorna `503 Service Unavailable` |

---

## Observabilidade

- **Langfuse** (opcional): rastreia cada invocação do LLM com prompt, resposta, tokens e latência.
- **Tabela `logs`**: registra eventos internos do sistema (erros, avisos, informações de fluxo).
- **Status de Lote**: permite acompanhamento do progresso via `GET /chamados/lotes/{lote_id}`.

---

## O que Aproveitar do Código Atual

| Componente | Status | Observação |
|---|---|---|
| Grafo LangGraph paralelo (`nodes.py`) | ✅ Pronto | Base sólida; adicionar nó extrator |
| CRUD de Prompts (`/prompts`) | ✅ Pronto | Falta conectar ao grafo |
| CRUD de Campos Extraídos (`/campos`) | ✅ Pronto | Falta o nó extrator no grafo |
| Endpoint avaliação individual | ✅ Pronto | Funcional |
| Templates de system prompts (3 Markdown) | ✅ Prontos | Fazer seed na tabela `prompts` |
| Schema PostgreSQL | ✅ Pronto | Sólido; adicionar tabela de metadados |
| Frontend Prompt/Campos Manager | ✅ Pronto | Funcional |
| Processamento em lote (RabbitMQ) | 🗓 Roadmap | Estrutura DB pronta |
| Nó extrator de metadados | 🗓 Roadmap | Campos já configuráveis |
| Prompts dinâmicos no grafo | 🗓 Roadmap | Ler do banco em vez do disco |
| Entrada ativa (pull externo) | 🗓 Roadmap | Novo componente |
