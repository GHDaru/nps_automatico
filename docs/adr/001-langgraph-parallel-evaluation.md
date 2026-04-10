# ADR 001 — Avaliação Paralela com LangGraph

| Campo | Valor |
|---|---|
| **Status** | Aceito |
| **Data** | 2025-04 |
| **Contexto** | Motor de IA do Módulo de Avaliação de Chamados |

---

## Contexto

O sistema precisa avaliar cada chamado em múltiplas **Dimensões de Avaliação** (ex.: Comunicação e Clareza, Profissionalismo e Conformidade, Resolução e Eficiência).

Cada Dimensão requer uma chamada independente ao LLM com seu próprio system prompt. As avaliações de diferentes Dimensões não dependem umas das outras — são totalmente independentes.

O desafio é como orquestrar múltiplas chamadas ao LLM de forma **eficiente**, **extensível** e **resiliente**.

---

## Opções Consideradas

### Opção A: Chamadas Sequenciais Simples

Invocar o LLM N vezes em sequência, acumulando os resultados em uma lista.

**Prós:**
- Simples de implementar
- Fácil de depurar

**Contras:**
- Latência proporcional a N (3 chamadas sequenciais = 3× o tempo de uma chamada)
- Não aproveita o paralelismo natural das tarefas independentes

---

### Opção B: `asyncio.gather` com LangChain

Usar `asyncio.gather` para disparar as N chamadas ao LLM em paralelo diretamente.

**Prós:**
- Paralelismo efetivo
- Relativamente simples

**Contras:**
- Gestão manual de estado, erros e retentativas
- Sem rastreabilidade estruturada por nó
- Dificulta extensão do fluxo (ex.: adicionar etapa de extração após avaliação)
- Sem suporte nativo a checkpoints, human-in-the-loop ou streaming

---

### Opção C: LangGraph com `Send` (escolhida) ✅

Usar **LangGraph** para modelar o fluxo de avaliação como um grafo de estado, com paralelismo via o mecanismo `Send`.

**Prós:**
- Paralelismo nativo e declarativo com `Send`
- Estado compartilhado tipado (`TypedDict`) com acumuladores thread-safe (`Annotated[list, op.add]`)
- Extensível: novos nós (extrator, validador, persistência) adicionados sem refatorar o core
- Integração nativa com LangChain callbacks → Langfuse (observabilidade)
- Suporte futuro a checkpoints, streaming de resultados, human-in-the-loop
- Grafo compilado e reutilizável entre requisições

**Contras:**
- Curva de aprendizado do modelo de grafo
- Abstração adicional sobre chamadas LLM diretas
- Dependência da biblioteca LangGraph

---

## Decisão

**Adotamos LangGraph com o mecanismo `Send` para orquestração paralela das avaliações.**

O grafo é definido em `infrastructure/nodes.py` e compilado uma única vez na inicialização da aplicação (em `config.py`). O estado é tipado via `TypedDict` (`EstadoGeral`) com a chave `avaliacoes` usando `Annotated[list, op.add]` para merge seguro de resultados paralelos.

---

## Implementação Atual

```python
# Nó de entrada: fan-out para cada Dimensão ativa
def entrada(state: EstadoGeral):
    return [
        Send("avaliar", {"chat": state["chat_avaliado"], "tipo_avaliacao": i})
        for i in [
            TipoAvaliacao.ComunicacaoClareza,
            TipoAvaliacao.ProfissionalismoConformidade,
            TipoAvaliacao.ResolucaoEficiencia,
        ]
    ]

# Nó de avaliação: uma chamada LLM por Dimensão
def avaliar(state: Avaliacao):
    system_prompt = abrir_system_prompt(state["tipo_avaliacao"].value)
    structured_llm = llm.with_structured_output(ResultadoAnalise)
    response = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": state["chat"]},
    ])
    return {"avaliacoes": [{"nota": response.nota, "justificativa": response.justificativa, ...}]}

# Montagem do grafo
grafo = StateGraph(EstadoGeral)
grafo.add_node("entrada", entrada)
grafo.add_node("avaliar", avaliar)
grafo.add_conditional_edges(START, entrada, ["avaliar"])
grafo.add_edge("avaliar", END)
compiled = grafo.compile()
```

---

## Consequências

### Positivas

- Latência de avaliação equivale à latência de **uma única** chamada ao LLM (as N chamadas rodam em paralelo).
- O fluxo é extensível: adicionar um nó `extrair_metadados` após o fan-in de avaliação requer apenas `grafo.add_node(...)` e `grafo.add_edge("avaliar", "extrair_metadados")`.
- Observabilidade completa via Langfuse com rastreamento por nó.

### Negativas / Trade-offs

- O enum `TipoAvaliacao` e a lista no nó `entrada` são atualmente hardcoded. Quando as Dimensões forem 100% dinâmicas (carregadas do banco), o nó `entrada` precisará ser atualizado para consultar o banco, e o grafo precisará ser recompilado ou o `Send` ser gerado dinamicamente.
- LangGraph adiciona ~30ms de overhead de inicialização na primeira execução por processo.

---

## Evolução Futura

1. **Dimensões Dinâmicas:** Carregar a lista de Dimensões ativas da tabela `prompts` no nó `entrada`, eliminando o enum hardcoded.
2. **Nó Extrator:** Adicionar `extrair_metadados` como nó sequencial após o fan-in de avaliações.
3. **Streaming:** Usar `grafo.astream()` para retornar resultados parciais ao cliente conforme cada Dimensão é avaliada.
4. **Retentativas:** Configurar retry policy por nó para lidar com erros transientes do LLM.
5. **Checkpoints:** Persistir o estado do grafo no banco para auditoria e reprocessamento.
