-- ============================================================
--  ENUMs
-- ============================================================

-- ENUM 'status': Define os possíveis estados de processamento para lotes e avaliações.
-- Valores:
--   'pending'    : Aguardando início do processamento.
--   'processing' : Em processamento ativo.
--   'done'       : Processamento concluído com sucesso.
--   'error'      : Processamento finalizado com erro.
CREATE TYPE status AS ENUM ('pending', 'processing', 'done', 'error');

-- ENUM 'criterio_avaliacao': Define os critérios de avaliação utilizados para analisar os chats.
-- Alinhado ao enum TipoAvaliacao no código Python.
-- Valores:
--   'ComunicacaoClareza'           : Avalia a clareza e eficácia da comunicação.
--   'ProfissionalismoConformidade' : Avalia o profissionalismo e a conformidade com regras.
--   'ResolucaoEficiencia'          : Avalia a eficiência e a qualidade da resolução.
CREATE TYPE criterio_avaliacao AS ENUM (
    'Comunicação e Clareza',
    'Profissionalismo e Conformidade',
    'Resolução e Eficiência'
);

-- ENUM 'nivel_log': Define os níveis de severidade para os registros de log.
-- Valores:
--   'info'    : Mensagens informativas sobre o fluxo normal da aplicação.
--   'warning' : Alertas sobre situações que podem indicar um problema, mas não são críticas.
--   'error'   : Erros que indicam falhas na execução e requerem atenção.
CREATE TYPE nivel_log AS ENUM ('info', 'warning', 'error');

-- ============================================================
--  TABLE: lotes
--  Armazena informações sobre os lotes de avaliações em massa.
--  Permite o acompanhamento do progresso e status de processamento de grupos de avaliações.
-- ============================================================
CREATE TABLE IF NOT EXISTS lotes (
    -- Identificador único do lote. Gerado automaticamente como UUID.
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    -- CNPJ da empresa solicitante do lote de avaliações.
    -- Armazenado como TEXT para suportar o padrão alfanumérico futuro.
    cnpj          TEXT          NOT NULL,

    -- Timestamp de quando o lote foi criado no sistema.
    criado_em     TIMESTAMPTZ   NOT NULL DEFAULT now(),

    -- Timestamp da última atualização do registro do lote.
    atualizado_em TIMESTAMPTZ   NOT NULL DEFAULT now(),

    -- Número total de itens (avaliações) contidos neste lote.
    -- Nota: deve ser atualizado conforme inserção das avaliações.
    total_itens   INT           NOT NULL,

    -- Número de itens (avaliações) que já foram processados com sucesso neste lote.
    -- Nota: deve ser atualizado conforme processamento avança.
    itens_prontos INT           NOT NULL,

    -- Status atual do lote, utilizando o ENUM 'status'.
    -- Valor padrão: 'pending'.
    status        status        NOT NULL DEFAULT 'pending'
);

-- ============================================================
--  TABLE: avaliacoes
--  Armazena os detalhes de cada avaliação individual de um chat.
--  Cada avaliação está sempre associada a um lote.
-- ============================================================
CREATE TABLE IF NOT EXISTS avaliacoes (
    -- Identificador único da avaliação individual. Gerado automaticamente como UUID.
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    -- CNPJ da empresa à qual esta avaliação pertence.
    -- Armazenado como TEXT para suportar o padrão alfanumérico futuro.
    cnpj          TEXT          NOT NULL,

    -- Chave estrangeira para a tabela 'lotes'.
    -- Indica a qual lote esta avaliação pertence (obrigatório).
    -- ON DELETE CASCADE: Se um lote for deletado, todas as avaliações associadas a ele também serão removidas.
    lote_id       UUID          REFERENCES lotes(id) ON DELETE CASCADE,

    -- Conteúdo completo do chat que foi avaliado.
    chat          TEXT          NOT NULL,

    -- Nota média calculada a partir dos critérios de avaliação.
    -- Pode ser NULL enquanto a avaliação está em processamento ou se não houver critérios avaliados.
    nota_media    DECIMAL(5, 2)  CHECK (nota_media BETWEEN 0 AND 10),

    -- Nota mediana calculada a partir dos critérios de avaliação.
    -- Pode ser NULL enquanto a avaliação está em processamento ou se não houver critérios avaliados.
    nota_mediana    DECIMAL(5, 2)  CHECK (nota_mediana BETWEEN 0 AND 10), -- CORRIGIDO 1

    -- Status atual da avaliação, utilizando o ENUM 'status'.
    -- Valor padrão: 'pending'.
    status        status        NOT NULL DEFAULT 'pending',

    -- Timestamp de quando a avaliação foi criada no sistema.
    criado_em     TIMESTAMPTZ   NOT NULL DEFAULT now(),

    -- Timestamp da última atualização do registro da avaliação.
    atualizado_em TIMESTAMPTZ   NOT NULL DEFAULT now() -- CORRIGIDO 2
); -- CORRIGIDO 2

-- ============================================================
--  TABLE: detalhes_avaliacao
--  Armazena as notas e justificativas para cada critério de avaliação de um chat.
--  Cada avaliação pode ter múltiplos detalhes (um para cada critério).
--  Restrição UNIQUE garante que cada critério só pode aparecer uma vez por avaliação.
-- ============================================================
CREATE TABLE IF NOT EXISTS detalhes_avaliacao (
    -- Identificador único do detalhe da avaliação. Gerado automaticamente como UUID.
    id            UUID               PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Chave estrangeira para a tabela 'avaliacoes'.
    -- Indica a qual avaliação este detalhe pertence.
    -- ON DELETE CASCADE: Se uma avaliação for deletada, seus detalhes também serão removidos.
    avaliacao_id  UUID               NOT NULL REFERENCES avaliacoes(id) ON DELETE CASCADE,

    -- O critério específico que foi avaliado, utilizando o ENUM 'criterio_avaliacao'.
    criterio      criterio_avaliacao NOT NULL,

    -- A nota atribuída para este critério (geralmente entre deve ser entre 0 e 100).
    nota          SMALLINT                NOT NULL CHECK (nota BETWEEN 0 AND 10),

    -- A justificativa textual para a nota atribuída a este critério.
    justificativa TEXT               NOT NULL,

    -- Timestamp de quando este detalhe de avaliação foi criado.
    criado_em     TIMESTAMPTZ        NOT NULL DEFAULT now(),

    -- Restrição: Garante que não haverá duplicidade de critérios para a mesma avaliação.
    UNIQUE (avaliacao_id, criterio)
);

-- ============================================================
--  TABLE: logs
--  Armazena registros de eventos, erros e alertas do sistema para auditoria e depuração.
--  Utiliza BIGSERIAL para id por simplicidade, performance e ordenação temporal.
-- ============================================================
CREATE TABLE IF NOT EXISTS logs (
    -- Identificador único do registro de log. Gerado automaticamente como um número sequencial (BIGSERIAL).
    id        BIGSERIAL    PRIMARY KEY,

    -- Timestamp de quando o log foi registrado.
    criado_em TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- Nível de severidade do log, utilizando o ENUM 'nivel_log'.
    nivel     nivel_log    NOT NULL,

    -- Origem do log (ex: nome do módulo, função, worker, etc.).
    origem    TEXT         NOT NULL,

    -- Mensagem descritiva do evento ou erro.
    mensagem  TEXT         NOT NULL,

    -- Dados adicionais em formato JSONB para contexto extra (ex: stacktrace, parâmetros).
    -- Campo opcional (pode ser NULL). Exemplos: { "stacktrace": "...", "params": {...} }
    contexto  JSONB
);

-- ============================================================
-- Observações para manutenção futura:
-- - Se desejar permitir avaliações avulsas (fora de lote), altere 'lote_id' em 'avaliacoes' para permitir NULL e ajuste os comentários.
-- - Para adicionar novos status ou critérios, altere os ENUMs com migração controlada.
-- - Sempre alinhe comentários e restrições ao comportamento real do banco.
-- - Atualize esta documentação sempre que houver mudanças estruturais.
-- ============================================================

-- =============================================================================
-- FUNÇÃO: inserir_avaliacao_completa
-- Versão corrigida — bug no bloco EXCEPTION resolvido (SQLSTATE 42703)
-- =============================================================================

CREATE OR REPLACE FUNCTION inserir_avaliacao_completa(
    p_cnpj     TEXT,
    p_chat     TEXT,
    p_detalhes JSONB,
    p_lote_id  UUID DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, pg_catalog
AS $$
DECLARE
    v_avaliacao_id  UUID;
    v_nota_media    NUMERIC(5,2);
    v_nota_mediana  NUMERIC(5,2);
    v_notas         NUMERIC[];
    v_count         INT;
    v_detalhe       JSONB;
    v_criterio      criterio_avaliacao;
    v_nota          NUMERIC;
    v_justificativa TEXT;
    -- [FIX] variável local para capturar o contexto da exceção via
    --       GET STACKED DIAGNOSTICS; necessária porque PG_EXCEPTION_CONTEXT
    --       não pode ser referenciado diretamente em RAISE ... USING DETAIL
    --       (causava SQLSTATE 42703 — coluna inexistente).
    v_ctx           TEXT;
BEGIN
    -- -------------------------------------------------------------------------
    -- Validação dos parâmetros de entrada
    -- -------------------------------------------------------------------------
    IF p_cnpj IS NULL OR trim(p_cnpj) = '' THEN
        RAISE EXCEPTION 'CNPJ não pode ser vazio';
    END IF;

    IF p_chat IS NULL OR trim(p_chat) = '' THEN
        RAISE EXCEPTION 'Chat não pode ser vazio';
    END IF;

    IF p_detalhes IS NULL OR jsonb_array_length(p_detalhes) = 0 THEN
        RAISE EXCEPTION 'É obrigatório informar ao menos um detalhe de avaliação';
    END IF;

    -- Verifica existência do lote, quando informado
    IF p_lote_id IS NOT NULL THEN
        PERFORM 1 FROM lotes WHERE id = p_lote_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Lote de avaliação % não existe', p_lote_id;
        END IF;
    END IF;

    -- -------------------------------------------------------------------------
    -- Coleta e validação prévia das notas
    -- -------------------------------------------------------------------------
    v_notas := ARRAY(
        SELECT (d->>'nota')::NUMERIC
        FROM jsonb_array_elements(p_detalhes) AS d
    );

    v_count := array_length(v_notas, 1);
    IF v_count IS NULL OR v_count = 0 THEN
        RAISE EXCEPTION 'Nenhuma nota informada nos detalhes';
    END IF;

    FOREACH v_nota IN ARRAY v_notas LOOP
        IF v_nota < 0 OR v_nota > 10 THEN
            RAISE EXCEPTION 'Nota fora do intervalo permitido (0-10): %', v_nota
                USING HINT = 'Verifique os dados enviados';
        END IF;
    END LOOP;

    -- -------------------------------------------------------------------------
    -- Cálculo de média e mediana
    -- -------------------------------------------------------------------------
    SELECT avg(n), percentile_cont(0.5) WITHIN GROUP (ORDER BY n)
      INTO v_nota_media, v_nota_mediana
      FROM unnest(v_notas) AS n;

    -- -------------------------------------------------------------------------
    -- Inserção do registro principal de avaliação
    -- -------------------------------------------------------------------------
    INSERT INTO avaliacoes (
        cnpj, lote_id, chat, nota_media, nota_mediana, status, criado_em, atualizado_em
    ) VALUES (
        p_cnpj, p_lote_id, p_chat,
        v_nota_media::SMALLINT, v_nota_mediana::SMALLINT,
        'pending', now(), now()
    )
    RETURNING id INTO v_avaliacao_id;

    -- -------------------------------------------------------------------------
    -- Inserção dos detalhes (critérios individuais)
    -- -------------------------------------------------------------------------
    FOR v_detalhe IN SELECT * FROM jsonb_array_elements(p_detalhes) LOOP

        v_criterio      := (v_detalhe->>'tipo_avaliacao')::criterio_avaliacao;
        v_nota          := (v_detalhe->>'nota')::NUMERIC;
        v_justificativa := v_detalhe->>'justificativa';

        IF v_criterio IS NULL THEN
            RAISE EXCEPTION 'Critério de avaliação não informado ou inválido';
        END IF;

        IF v_nota IS NULL OR v_nota < 0 OR v_nota > 10 THEN
            RAISE EXCEPTION 'Nota fora do intervalo permitido (0-10): %', v_nota;
        END IF;

        IF v_justificativa IS NULL OR trim(v_justificativa) = '' THEN
            RAISE EXCEPTION 'Justificativa não pode ser vazia para o critério %', v_criterio;
        END IF;

        INSERT INTO detalhes_avaliacao (
            avaliacao_id, criterio, nota, justificativa, criado_em
        ) VALUES (
            v_avaliacao_id, v_criterio, v_nota, v_justificativa, now()
        );

    END LOOP;

    -- -------------------------------------------------------------------------
    -- Retorno do objeto JSON com o resultado consolidado
    -- -------------------------------------------------------------------------
    RETURN jsonb_build_object(
        'avaliacao_id',  v_avaliacao_id,
        'nota_media',    v_nota_media,
        'nota_mediana',  v_nota_mediana,
        'detalhes', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'tipo_avaliacao', d->>'criterio',
                    'nota',           d->>'nota',
                    'justificativa',  d->>'justificativa'
                )
            )
            FROM jsonb_array_elements(p_detalhes) AS d
        )
    );

EXCEPTION WHEN OTHERS THEN
    -- -------------------------------------------------------------------------
    -- [FIX] Captura o contexto da exceção em v_ctx via GET STACKED DIAGNOSTICS.
    --
    -- PROBLEMA ORIGINAL:
    --   RAISE EXCEPTION '...' USING DETAIL = PG_EXCEPTION_CONTEXT;
    --   → O PostgreSQL avalia PG_EXCEPTION_CONTEXT como nome de coluna dentro
    --     da cláusula USING, levantando SQLSTATE 42703 (coluna inexistente)
    --     em vez de propagar o erro original.
    --
    -- SOLUÇÃO:
    --   Usar GET STACKED DIAGNOSTICS para ler a variável especial e armazená-la
    --   em v_ctx, que então pode ser referenciada normalmente na cláusula USING.
    -- -------------------------------------------------------------------------
    GET STACKED DIAGNOSTICS v_ctx = PG_EXCEPTION_CONTEXT;

    RAISE EXCEPTION 'Erro ao inserir avaliação: %', SQLERRM
        USING DETAIL = v_ctx;

END;
$$;


CREATE OR REPLACE FUNCTION criar_lote(
    p_cnpj TEXT,
    p_total_itens INT,
    p_itens_prontos INT
) RETURNS UUID
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public, pg_catalog
AS $$
DECLARE
    v_lote_id UUID;
BEGIN
    -- Validação dos parâmetros
    IF p_cnpj IS NULL OR trim(p_cnpj) = '' THEN
        RAISE EXCEPTION 'CNPJ não pode ser vazio ou nulo';
    END IF;
    IF p_total_itens IS NULL OR p_total_itens < 0 THEN
        RAISE EXCEPTION 'total_itens deve ser informado e não pode ser negativo';
    END IF;
    IF p_itens_prontos IS NULL OR p_itens_prontos < 0 THEN
        RAISE EXCEPTION 'itens_prontos deve ser informado e não pode ser negativo';
    END IF;
    IF p_itens_prontos > p_total_itens THEN
        RAISE EXCEPTION 'itens_prontos não pode ser maior que total_itens';
    END IF;

    -- Inserção e captura do UUID gerado
    INSERT INTO lotes (
        cnpj, total_itens, itens_prontos, status, criado_em, atualizado_em
    ) VALUES (
        p_cnpj, p_total_itens, p_itens_prontos, 'pending', now(), now()
    )
    RETURNING id INTO v_lote_id;

    RETURN v_lote_id;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Erro ao criar lote: %', SQLERRM
        USING DETAIL = PG_EXCEPTION_CONTEXT;
END;
$$;



-- Índices para lotes
CREATE INDEX idx_lotes_cnpj ON lotes(cnpj);
CREATE INDEX idx_lotes_status_pending ON lotes(status) WHERE status = 'pending';
CREATE INDEX idx_lotes_criado_em ON lotes(criado_em);
CREATE INDEX idx_lotes_cnpj_status ON lotes(cnpj, status);

-- Índices para avaliacoes
CREATE INDEX idx_avaliacoes_lote_id ON avaliacoes(lote_id);
CREATE INDEX idx_avaliacoes_cnpj ON avaliacoes(cnpj);
CREATE INDEX idx_avaliacoes_status_pending ON avaliacoes(status) WHERE status = 'pending';
CREATE INDEX idx_avaliacoes_criado_em ON avaliacoes(criado_em);
CREATE INDEX idx_avaliacoes_lote_id_status ON avaliacoes(lote_id, status);

-- Índices para detalhes_avaliacao
CREATE INDEX idx_detalhes_avaliacao_avaliacao_id ON detalhes_avaliacao(avaliacao_id);

-- Índices para logs
CREATE INDEX idx_logs_nivel ON logs(nivel);
CREATE INDEX idx_logs_origem ON logs(origem);
CREATE INDEX idx_logs_criado_em ON logs(criado_em);
CREATE INDEX idx_logs_contexto_gin ON logs USING gin(contexto);
CREATE INDEX idx_logs_criado_em_brin ON logs USING brin(criado_em);


-- TRIGGERS
-- 1. Função trigger genérica para atualizar o campo 'atualizado_em'
CREATE OR REPLACE FUNCTION atualiza_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger para a tabela 'lotes'
CREATE TRIGGER lotes_atualizado_em
BEFORE UPDATE ON lotes
FOR EACH ROW
EXECUTE FUNCTION atualiza_atualizado_em();

-- 3. Trigger para a tabela 'avaliacoes'
CREATE TRIGGER avaliacoes_atualizado_em
BEFORE UPDATE ON avaliacoes
FOR EACH ROW
EXECUTE FUNCTION atualiza_atualizado_em();

-- ============================================================
--  TABLE: prompts
--  Armazena os prompts de avaliação gerenciados pelo administrador.
--  Cada prompt representa uma dimensão de análise (ex: Comunicação e Clareza).
-- ============================================================
CREATE TABLE IF NOT EXISTS prompts (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Nome da dimensão de análise (ex: "Comunicação e Clareza")
    nome          TEXT        NOT NULL,

    -- Conteúdo completo do prompt (instruções para o LLM)
    conteudo      TEXT        NOT NULL,

    -- Indica se o prompt está ativo para o fluxo de avaliação
    ativo         BOOLEAN     NOT NULL DEFAULT true,

    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prompts_ativo ON prompts(ativo);

CREATE TRIGGER prompts_atualizado_em
BEFORE UPDATE ON prompts
FOR EACH ROW
EXECUTE FUNCTION atualiza_atualizado_em();

-- ============================================================
--  TABLE: campos_extraidos
--  Armazena os campos globais que devem ser extraídos das mensagens/chats.
--  Exemplos: cliente, atendente, categoria do chamado.
-- ============================================================
CREATE TABLE IF NOT EXISTS campos_extraidos (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Nome do campo (ex: "cliente", "atendente", "categoria_chamado")
    nome          TEXT        NOT NULL UNIQUE,

    -- Descrição do campo para ser exportada no JSON
    descricao     TEXT        NOT NULL,

    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER campos_extraidos_atualizado_em
BEFORE UPDATE ON campos_extraidos
FOR EACH ROW
EXECUTE FUNCTION atualiza_atualizado_em();
