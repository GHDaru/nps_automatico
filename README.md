# NPS Automático

Projeto de análise e avaliação de chamados utilizando **LangGraph** + **Google Gemini** (via `langchain-google-genai`).

A aplicação é dividida em:
- **Backend** – API FastAPI que recebe dados e devolve um JSON com a avaliação do chamado.
- **Frontend** – Interface React (Vite) para envio e visualização dos resultados.

---

## Arquitetura

```
frontend/        ← React + Vite
src/app/
  api/           ← Rotas FastAPI
  controllers/   ← Lógica de orquestração
  domain/        ← Grafo LangGraph, modelos Pydantic
  infrastructure/
    nodes.py     ← Nós do grafo (LLM Gemini)
    db/          ← Pool PostgreSQL
    messenger/   ← RabbitMQ (processamento em lote)
  prompts/system/← System prompts de avaliação
  utils/
worker.py        ← Worker RabbitMQ (processamento assíncrono)
```

---

## Pré-requisitos

| Ferramenta       | Versão mínima |
|------------------|---------------|
| Python           | 3.13          |
| [uv](https://github.com/astral-sh/uv) | qualquer |
| Node.js          | 18+           |
| npm              | 9+            |
| PostgreSQL       | 14+           |
| RabbitMQ         | 3.x           |
| Docker + Compose | opcional      |

---

## Configuração do ambiente

### 1. Obter uma API Key do Google Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Crie ou selecione um projeto e gere uma chave de API.
3. Guarde a chave — ela será usada como `GOOGLE_API_KEY`.

### 2. Criar o arquivo `.env`

Copie o exemplo e preencha as variáveis:

```bash
cp .env.example .env
```

`.env`:

```env
# Obrigatório: chave do Google Gemini
GOOGLE_API_KEY="sua-chave-aqui"

# Opcional: observabilidade com Langfuse (https://langfuse.com)
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""
LANGFUSE_BASE_URL="http://localhost:3000"
LANGFUSE_TRACING_ENVIRONMENT="development"

# Banco de dados PostgreSQL
PG_USER="postgres"
PG_PASSWORD="postgres"
PG_HOST="localhost"
PG_PORT="5432"
PG_DB="nps_automatico"
```

> **Nota:** As variáveis do Langfuse são opcionais. Se não preenchidas, o sistema funciona normalmente sem rastreamento.

### 3. Banco de dados

Execute o script SQL para criar as tabelas:

```bash
psql -U $PG_USER -d $PG_DB -f bd/database.sql
```

---

## Rodando localmente

### Backend

```bash
# Instalar dependências
uv sync

# Iniciar a API (porta 5020)
uv run main.py
```

A API estará disponível em `http://localhost:5020`.

Documentação interativa (Swagger): `http://localhost:5020/docs`

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# (Opcional) configurar URL da API
cp .env.example .env
# edite VITE_API_URL se o backend estiver em outra porta/host

# Iniciar servidor de desenvolvimento (porta 5173)
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

---

## Rodando com Docker Compose

```bash
# Copiar e preencher variáveis de ambiente
cp .env.example .env
# edite .env com suas credenciais

# Subir todos os serviços
docker compose up --build
```

Serviços expostos:

| Serviço   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:3001        |
| Backend   | http://localhost:5020        |
| RabbitMQ  | http://localhost:15672 (mgmt)|

---

## Endpoints da API

### `POST /chamados/avaliacao_individual`

Avalia um único chat e retorna as pontuações.

**Request body:**
```json
{
  "cnpj": "11222333000181",
  "chat": "ATENDENTE: Olá, como posso ajudar?\nCLIENTE: Preciso de suporte..."
}
```

**Response:**
```json
{
  "avaliacoes": [
    {
      "nota": 85,
      "justificativa": "O atendente demonstrou clareza...",
      "tipo_avaliacao": "Comunicação e Clareza"
    },
    {
      "nota": 90,
      "justificativa": "Postura profissional mantida...",
      "tipo_avaliacao": "Profissionalismo e Conformidade"
    },
    {
      "nota": 78,
      "justificativa": "O problema foi resolvido...",
      "tipo_avaliacao": "Resolução e Eficiência"
    }
  ],
  "nota_media": 84.3,
  "nota_mediana": 85.0
}
```

### `POST /chamados/lotes`

Cria um lote de avaliações assíncronas.

**Request body:**
```json
{
  "cnpj": "11222333000181",
  "chats": ["chat 1...", "chat 2...", "chat 3..."]
}
```

---

## Critérios de avaliação

O grafo LangGraph avalia cada chat em paralelo em 3 dimensões (0–100 pontos cada):

| Critério                         | Descrição                                              |
|----------------------------------|--------------------------------------------------------|
| **Comunicação e Clareza**        | Objetividade, linguagem adequada, organização          |
| **Profissionalismo e Conformidade** | Postura, respeito às normas, ética                  |
| **Resolução e Eficiência**       | Velocidade, qualidade da solução, satisfação do cliente|

---

## Estrutura do grafo (LangGraph)

```
START → entrada → avaliar (×3, paralelo) → retornar_resultado → END
```

- `entrada`: distribui o chat para 3 nós paralelos via `Send`
- `avaliar`: invoca o Gemini com structured output para cada critério
- `retornar_resultado`: agrega os resultados

---

## Variáveis de ambiente — referência completa

| Variável                     | Obrigatório | Descrição                              |
|------------------------------|-------------|----------------------------------------|
| `GOOGLE_API_KEY`             | ✅ Sim      | Chave da API Google Gemini             |
| `PG_USER`                    | ✅ Sim      | Usuário PostgreSQL                     |
| `PG_PASSWORD`                | ✅ Sim      | Senha PostgreSQL                       |
| `PG_HOST`                    | ✅ Sim      | Host PostgreSQL                        |
| `PG_PORT`                    | ✅ Sim      | Porta PostgreSQL (padrão: 5432)        |
| `PG_DB`                      | ✅ Sim      | Nome do banco PostgreSQL               |
| `LANGFUSE_PUBLIC_KEY`        | ❌ Opcional | Chave pública Langfuse                 |
| `LANGFUSE_SECRET_KEY`        | ❌ Opcional | Chave secreta Langfuse                 |
| `LANGFUSE_BASE_URL`          | ❌ Opcional | URL do servidor Langfuse               |
| `LANGFUSE_TRACING_ENVIRONMENT` | ❌ Opcional | Ambiente de rastreamento             |
