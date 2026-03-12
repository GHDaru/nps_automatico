import { useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5020'

function ScoreCard({ avaliacao }) {
  return (
    <div className="score-card">
      <div className="score-header">
        <span className="score-type">{avaliacao.tipo_avaliacao}</span>
        <span className="score-badge">{avaliacao.nota}/100</span>
      </div>
      <p className="score-justificativa">{avaliacao.justificativa}</p>
    </div>
  )
}

function App() {
  const [cnpj, setCnpj] = useState('')
  const [chat, setChat] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)
  const [rawJson, setRawJson] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResultado(null)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/chamados/avaliacao_individual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cnpj, chat }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || JSON.stringify(data, null, 2))
      } else {
        setResultado(data)
      }
    } catch (err) {
      setError(`Erro ao conectar com a API: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>NPS Automático</h1>
        <p>Avaliação de chamados com LangGraph + Gemini</p>
      </header>

      <main className="app-main">
        <section className="form-section">
          <h2>Avaliação Individual</h2>
          <form onSubmit={handleSubmit} className="eval-form">
            <div className="field">
              <label htmlFor="cnpj">CNPJ da empresa</label>
              <input
                id="cnpj"
                type="text"
                value={cnpj}
                onChange={(e) => setCnpj(e.target.value)}
                placeholder="Ex: 11222333000181"
                required
              />
            </div>

            <div className="field">
              <label htmlFor="chat">Chat / Chamado</label>
              <textarea
                id="chat"
                value={chat}
                onChange={(e) => setChat(e.target.value)}
                placeholder="Cole aqui o conteúdo completo do chat ou chamado..."
                rows={12}
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn-submit">
              {loading ? 'Avaliando...' : 'Avaliar Chat'}
            </button>
          </form>
        </section>

        {error && (
          <section className="result-section error-section">
            <h2>Erro</h2>
            <pre className="error-box">{error}</pre>
          </section>
        )}

        {resultado && (
          <section className="result-section">
            <div className="result-header">
              <h2>Resultado</h2>
              <button
                className="btn-toggle"
                onClick={() => setRawJson((v) => !v)}
              >
                {rawJson ? 'Ver formatado' : 'Ver JSON bruto'}
              </button>
            </div>

            {rawJson ? (
              <pre className="json-box">{JSON.stringify(resultado, null, 2)}</pre>
            ) : (
              <>
                <div className="summary-cards">
                  <div className="summary-card">
                    <span className="summary-label">Nota Média</span>
                    <span className="summary-value">{resultado.nota_media?.toFixed(1)}</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Nota Mediana</span>
                    <span className="summary-value">{resultado.nota_mediana?.toFixed(1)}</span>
                  </div>
                </div>

                <div className="avaliacoes-list">
                  {resultado.avaliacoes?.map((av, i) => (
                    <ScoreCard key={i} avaliacao={av} />
                  ))}
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
