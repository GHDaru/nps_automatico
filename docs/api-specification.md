# Especificação de API

## Visão Geral

**Base URL:** `http://localhost:5020`  
**Documentação interativa (Swagger):** `http://localhost:5020/docs`  
**Content-Type:** `application/json`

---

## Módulo: Avaliação de Chamados (`/chamados`)

### `POST /chamados/avaliacao_individual`

Avalia um único chamado de forma **síncrona** e retorna o resultado completo.

**Request Body:**

```json
{
  "chat": "ATENDENTE: Olá, como posso ajudar?\nCLIENTE: Preciso de suporte com meu pedido."
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `chat` | string | ✅ | Transcrição completa do atendimento, ordenada cronologicamente, identificando ATENDENTE e CLIENTE |

**Response — `200 OK`:**

```json
{
  "avaliacoes": [
    {
      "tipo_avaliacao": "Comunicação e Clareza",
      "nota": 8,
      "justificativa": "O atendente cumprimentou cordialmente..."
    },
    {
      "tipo_avaliacao": "Profissionalismo e Conformidade",
      "nota": 9,
      "justificativa": "Postura profissional mantida ao longo do atendimento..."
    },
    {
      "tipo_avaliacao": "Resolução e Eficiência",
      "nota": 7,
      "justificativa": "O problema foi resolvido, mas com alguma demora..."
    }
  ],
  "nota_media": 8.0,
  "nota_mediana": 8.0
}
```

**Erros:**

| Status | Descrição |
|---|---|
| `422 Unprocessable Entity` | Corpo inválido (Pydantic validation error) |
| `502 Bad Gateway` | Erro interno no motor de IA ou na comunicação com o LLM |

---

### `POST /chamados/lotes` _(Roadmap)_

Cria um **lote** de chamados para processamento **assíncrono**.

**Request Body:**

```json
{
  "cnpj": "11222333000181",
  "chats": [
    "ATENDENTE: Olá...\nCLIENTE: ...",
    "ATENDENTE: Bom dia...\nCLIENTE: ..."
  ]
}
```

**Response — `202 Accepted`:**

```json
{
  "lote_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_itens": 2,
  "status": "pending"
}
```

---

### `GET /chamados/lotes/{lote_id}` _(Roadmap)_

Consulta o status e o progresso de um lote.

**Response — `200 OK`:**

```json
{
  "lote_id": "550e8400-e29b-41d4-a716-446655440000",
  "cnpj": "11222333000181",
  "total_itens": 10,
  "itens_prontos": 7,
  "status": "processing",
  "criado_em": "2025-04-10T10:00:00Z",
  "atualizado_em": "2025-04-10T10:02:30Z"
}
```

---

## Módulo: Configuração de Prompts (`/prompts`)

### `GET /prompts`

Retorna todos os prompts cadastrados, ordenados por nome.

**Response — `200 OK`:**

```json
[
  {
    "id": "uuid",
    "nome": "Comunicação e Clareza",
    "conteudo": "# Role\nVocê é o Agente Avaliador...",
    "ativo": true,
    "criado_em": "2025-01-01T00:00:00Z",
    "atualizado_em": "2025-01-01T00:00:00Z"
  }
]
```

---

### `POST /prompts`

Cria um novo prompt (nova Dimensão de Avaliação).

**Request Body:**

```json
{
  "nome": "Empatia e Acolhimento",
  "conteudo": "# Role\nVocê é especialista em empatia...",
  "ativo": true
}
```

**Response — `201 Created`:** objeto `Prompt` completo.

---

### `GET /prompts/{prompt_id}`

Retorna um prompt específico pelo ID.

**Response — `200 OK`:** objeto `Prompt` completo.  
**Erros:** `404 Not Found` se não existir.

---

### `PUT /prompts/{prompt_id}`

Atualiza parcialmente um prompt existente.

**Request Body** (todos os campos opcionais):

```json
{
  "nome": "Novo Nome",
  "conteudo": "# Role\nConteúdo atualizado...",
  "ativo": false
}
```

**Response — `200 OK`:** objeto `Prompt` atualizado.  
**Erros:** `404 Not Found`, `422` se nenhum campo fornecido.

---

### `DELETE /prompts/{prompt_id}`

Remove um prompt pelo ID.

**Response — `204 No Content`.**  
**Erros:** `404 Not Found`.

---

## Módulo: Configuração de Campos Extraídos (`/campos`)

### `GET /campos`

Retorna todos os campos extraídos cadastrados, ordenados por nome.

**Response — `200 OK`:**

```json
[
  {
    "id": "uuid",
    "nome": "atendente",
    "descricao": "Nome completo do atendente. Se não encontrado, retornar null.",
    "criado_em": "2025-01-01T00:00:00Z",
    "atualizado_em": "2025-01-01T00:00:00Z"
  }
]
```

---

### `POST /campos`

Cria um novo campo a ser extraído.

**Request Body:**

```json
{
  "nome": "categoria",
  "descricao": "Categoria do chamado (ex: Financeiro, Técnico, Comercial). Se não identificado, retornar 'Não identificado'."
}
```

**Response — `201 Created`:** objeto `CampoExtraído` completo.  
**Erros:** `409 Conflict` se já existir campo com o mesmo nome.

---

### `GET /campos/{campo_id}`

Retorna um campo específico pelo ID.

**Response — `200 OK`:** objeto `CampoExtraído` completo.  
**Erros:** `404 Not Found`.

---

### `PUT /campos/{campo_id}`

Atualiza parcialmente um campo existente.

**Request Body** (todos os campos opcionais):

```json
{
  "nome": "categoria_atendimento",
  "descricao": "Descrição atualizada do campo."
}
```

**Response — `200 OK`:** objeto `CampoExtraído` atualizado.  
**Erros:** `404 Not Found`, `409 Conflict` (nome duplicado), `422` se nenhum campo fornecido.

---

### `DELETE /campos/{campo_id}`

Remove um campo pelo ID.

**Response — `204 No Content`.**  
**Erros:** `404 Not Found`.

---

## Módulo: Extração de Metadados (Proposto)

### `POST /chamados/extrair` _(Roadmap)_

Extrai metadados de um chamado com base nos campos configurados.

**Request Body:**

```json
{
  "chat": "ATENDENTE: João Silva\nCLIENTE: Preciso resolver..."
}
```

**Response — `200 OK`:**

```json
{
  "atendente": "João Silva",
  "categoria": "Suporte Técnico",
  "protocolo": null
}
```

---

## Módulo: Relatórios (Roadmap)

### `GET /relatorios/atendentes`

Retorna médias de avaliação agrupadas por atendente.

**Query Parameters:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `cnpj` | string | CNPJ do Tenant |
| `de` | date | Data inicial (ISO 8601) |
| `ate` | date | Data final (ISO 8601) |

**Response — `200 OK`:**

```json
[
  {
    "atendente": "João Silva",
    "total_chamados": 42,
    "nota_media": 7.8,
    "nota_mediana": 8.0,
    "por_dimensao": {
      "Comunicação e Clareza": 8.1,
      "Profissionalismo e Conformidade": 7.9,
      "Resolução e Eficiência": 7.4
    }
  }
]
```

---

### `GET /relatorios/clientes`

Retorna médias de avaliação agrupadas por cliente do Tenant.

**Response — `200 OK`:** estrutura similar a `/relatorios/atendentes`.

---

## Códigos de Erro Globais

| Status | Descrição |
|---|---|
| `400 Bad Request` | Parâmetros inválidos |
| `404 Not Found` | Recurso não encontrado |
| `409 Conflict` | Conflito (ex.: nome duplicado) |
| `422 Unprocessable Entity` | Falha de validação do corpo da requisição |
| `500 Internal Server Error` | Erro interno inesperado |
| `502 Bad Gateway` | Erro no motor de IA |
| `503 Service Unavailable` | Banco de dados indisponível |
