# Módulo de Relatórios e Dashboards

> **Bounded Context:** `relatorios`  
> **Tipo:** Supporting Domain  
> **Status:** 🗓 Roadmap — não implementado

---

## Responsabilidade

Este módulo oferece ao Tenant (cliente contratante) uma visão analítica dos resultados de avaliação dos seus atendimentos. Permite identificar pontos de melhoria por **atendente**, por **cliente** e ao longo do **tempo**.

---

## Atores

| Ator | Descrição |
|---|---|
| **Administrador do Tenant** | Configuração do sistema, acesso a todos os relatórios, gestão de usuários |
| **Analista / Supervisor** | Acesso a relatórios de equipe e clientes |
| **Atendente** | Acesso restrito às suas próprias avaliações (opcional) |

---

## Funcionalidades

### 1. Dashboard Geral

- Visão consolidada de todos os chamados avaliados no período.
- Indicadores:
  - Total de chamados avaliados
  - Nota média geral
  - Nota mediana geral
  - Evolução temporal (gráfico de linha)
  - Distribuição de notas (histograma)

### 2. Relatório por Atendente

- Lista de atendentes com suas médias de avaliação.
- Por atendente, detalha:
  - Nota média geral e por Dimensão
  - Nota mediana
  - Total de chamados avaliados
  - Evolução temporal
  - Lista dos chamados individuais com acesso ao detalhe

**Caso de uso:** Identificar atendentes com baixo desempenho em Dimensões específicas para direcionamento de treinamento.

### 3. Relatório por Cliente

- Lista de clientes atendidos com suas médias de avaliação.
- Por cliente, detalha:
  - Nota média e mediana dos atendimentos
  - Atendentes que atenderam este cliente
  - Histórico de chamados

**Caso de uso:** Identificar clientes que recebem atendimento de menor qualidade de forma consistente.

### 4. Detalhe do Chamado

- Visualização completa da transcrição do chamado.
- Notas e justificativas por Dimensão.
- Metadados extraídos (atendente, categoria, protocolo, etc.).
- Status do processamento.

### 5. Filtros

| Filtro | Tipo |
|---|---|
| Período (de/até) | Date range |
| Atendente | Seleção múltipla |
| Cliente | Seleção múltipla |
| Dimensão de avaliação | Seleção múltipla |
| Faixa de nota | Range numérico |
| Status | Enum |

---

## Modelo de Dados

O módulo de relatórios **não possui tabelas próprias** — lê dados do contexto de Avaliação via queries dedicadas ou views materializadas, respeitando o padrão de Anti-Corruption Layer.

### Views / Queries Propostas

**`v_medias_por_atendente`** (view ou query):

```sql
SELECT
    m.metadado_valor              AS atendente,
    COUNT(DISTINCT a.id)          AS total_chamados,
    AVG(a.nota_media)             AS nota_media,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.nota_media) AS nota_mediana,
    a.cnpj
FROM avaliacoes a
-- JOIN com tabela de metadados quando implementada
GROUP BY atendente, a.cnpj;
```

**`v_medias_por_dimensao_atendente`**:

```sql
SELECT
    m.metadado_valor              AS atendente,
    d.criterio,
    AVG(d.nota)                   AS nota_media,
    a.cnpj
FROM detalhes_avaliacao d
JOIN avaliacoes a ON d.avaliacao_id = a.id
-- JOIN com tabela de metadados quando implementada
GROUP BY atendente, d.criterio, a.cnpj;
```

---

## Pré-requisitos Técnicos

Para este módulo funcionar corretamente, os seguintes itens devem estar implementados no Módulo de Avaliação:

1. **Extração de metadados** — o campo `atendente` e `cliente` devem ser extraídos e persistidos para agrupamento.
2. **Tabela de metadados por avaliação** — estrutura para armazenar os metadados extraídos vinculados ao `avaliacao_id`.

### Tabela Proposta: `metadados_avaliacao`

```sql
CREATE TABLE metadados_avaliacao (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    avaliacao_id  UUID        NOT NULL REFERENCES avaliacoes(id) ON DELETE CASCADE,
    campo         TEXT        NOT NULL,  -- nome do campo (ex: "atendente")
    valor         TEXT,                  -- valor extraído (null se não encontrado)
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (avaliacao_id, campo)
);
```

---

## Endpoints Propostos

Ver [api-specification.md](../api-specification.md#módulo-relatórios-roadmap) para detalhe dos contratos.

| Endpoint | Descrição |
|---|---|
| `GET /relatorios/atendentes` | Médias por atendente (filtros: cnpj, de, até, dimensão) |
| `GET /relatorios/atendentes/{atendente_id}` | Detalhe de um atendente com histórico de chamados |
| `GET /relatorios/clientes` | Médias por cliente (filtros: cnpj, de, até) |
| `GET /relatorios/clientes/{cliente_id}` | Detalhe de um cliente com histórico de chamados |
| `GET /relatorios/chamados/{avaliacao_id}` | Detalhe completo de um chamado avaliado |
| `GET /relatorios/dashboard` | Indicadores gerais do Tenant no período |

---

## Frontend — Telas Propostas

### Tela: Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Período: [01/04/2025] a [10/04/2025]  [Atualizar]       │
│                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │  Total     │ │ Nota Média │ │  Nota Mediana       │   │
│  │  148 chats │ │   7.8 / 10 │ │      8.0 / 10       │   │
│  └────────────┘ └────────────┘ └────────────────────┘   │
│                                                           │
│  [Gráfico: Evolução da nota média ao longo do tempo]     │
│                                                           │
│  [Gráfico: Distribuição de notas — histograma]           │
└──────────────────────────────────────────────────────────┘
```

### Tela: Relatório por Atendente

```
┌──────────────────────────────────────────────────────────┐
│  Atendentes                         [Filtros ▼]          │
│                                                           │
│  ┌──────────────┬──────────┬──────────┬───────────────┐  │
│  │ Atendente    │ Chamados │ Nota Med │ Ver Detalhes   │  │
│  ├──────────────┼──────────┼──────────┼───────────────┤  │
│  │ João Silva   │ 42       │ 8.1      │ [→ Detalhe]   │  │
│  │ Maria Santos │ 38       │ 7.4      │ [→ Detalhe]   │  │
│  │ Pedro Lima   │ 15       │ 6.9      │ [→ Detalhe]   │  │
│  └──────────────┴──────────┴──────────┴───────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Tela: Detalhe do Chamado

```
┌──────────────────────────────────────────────────────────┐
│  Chamado #UUID — 10/04/2025 14:30                        │
│  Atendente: João Silva | Categoria: Suporte Técnico      │
│  Nota Média: 8.0 | Nota Mediana: 8.0                     │
│                                                           │
│  Transcrição:                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ ATENDENTE: Olá, como posso ajudar?                 │  │
│  │ CLIENTE: Preciso de suporte...                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  Avaliações por Dimensão:                                │
│  • Comunicação e Clareza: 8/10                           │
│    "O atendente cumprimentou cordialmente..."            │
│  • Profissionalismo e Conformidade: 9/10                 │
│    "Postura profissional mantida..."                     │
│  • Resolução e Eficiência: 7/10                          │
│    "O problema foi resolvido com alguma demora..."       │
└──────────────────────────────────────────────────────────┘
```

---

## Roadmap de Implementação

| Fase | Entregável |
|---|---|
| **Fase 1** | Implementar extração de metadados (atendente, cliente) no módulo de Avaliação |
| **Fase 2** | Criar tabela `metadados_avaliacao` e persistir metadados extraídos |
| **Fase 3** | Implementar endpoints `GET /relatorios/atendentes` e `/clientes` |
| **Fase 4** | Criar telas de relatório no frontend (Dashboard, Atendentes, Clientes) |
| **Fase 5** | Implementar autenticação e controle de acesso por Tenant (CNPJ) |
| **Fase 6** | Tela de detalhe do chamado com transcrição e notas por Dimensão |
| **Fase 7** | Filtros avançados e exportação (CSV/PDF) |
