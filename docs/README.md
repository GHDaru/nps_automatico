# Documentação — NPS Automático

Bem-vindo à documentação de arquitetura e domínio do projeto **NPS Automático**.  
Este diretório reúne todos os artefatos de design orientado ao domínio (DDD), especificações técnicas e decisões arquiteturais.

---

## Índice

| Documento | Descrição |
|---|---|
| [ddd-overview.md](./ddd-overview.md) | Linguagem ubíqua, Bounded Contexts e Context Map |
| [domain-model.md](./domain-model.md) | Agregados, Entidades, Objetos de Valor e Eventos de Domínio |
| [architecture.md](./architecture.md) | Arquitetura técnica em camadas, componentes e integrações |
| [api-specification.md](./api-specification.md) | Contratos de API — endpoints atuais e propostos |
| [database-schema.md](./database-schema.md) | Esquema do banco de dados relacional |
| [modules/modulo-avaliacao.md](./modules/modulo-avaliacao.md) | Módulo de Avaliação de Chamados (Core Domain) |
| [modules/modulo-relatorios.md](./modules/modulo-relatorios.md) | Módulo de Relatórios e Dashboards (Supporting Domain — roadmap) |
| [adr/001-langgraph-parallel-evaluation.md](./adr/001-langgraph-parallel-evaluation.md) | ADR 001: Avaliação paralela com LangGraph |

---

## Visão Geral do Sistema

O **NPS Automático** é uma plataforma SaaS multi-tenant para avaliação automatizada de atendimentos por Inteligência Artificial.  
O sistema recebe transcrições de chamados (de forma ativa ou passiva, individual ou em lote), executa avaliações multi-dimensionais via LLM e extrai metadados configuráveis, retornando resultados em JSON.

### Fluxo de Alto Nível

```
Fontes de Chamados                 Motor de IA                  Armazenamento / Saída
─────────────────                 ──────────────               ──────────────────────
  API REST (passivo)  ──►                                      ┌──────────────────────┐
  Integração Ativo    ──►  Avaliação Multi-Dimensão (LLM)  ──► │  JSON c/ chave CNPJ  │
  Upload em lote      ──►  Extração de Metadados    (LLM)  ──► │  PostgreSQL          │
                                                               └──────────────────────┘
```

### Módulos

| # | Módulo | Status |
|---|--------|--------|
| 1 | **Avaliação de Chamados** — recebimento, avaliação por IA, extração de metadados | ✅ Em desenvolvimento |
| 2 | **Relatórios e Dashboards** — visão por cliente e por atendente | 🗓 Roadmap |

---

## Princípios de Design

- **Domain-Driven Design (DDD)** — modelo de domínio rico, linguagem ubíqua compartilhada entre negócio e tecnologia.
- **Separação de responsabilidades em camadas** — API → Controller → Domain → Infrastructure.
- **Multi-tenancy por CNPJ** — cada cliente é isolado pela chave `cnpj`.
- **Configurabilidade** — prompts de avaliação e campos de extração são gerenciados pelo cliente, sem deploy.
- **Observabilidade** — rastreamento opcional via Langfuse.
