import { useState, useRef } from 'react'
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

function buildResultadoText(resultado) {
  const lines = []
  lines.push(`Nota Média: ${resultado.nota_media?.toFixed(1)}`)
  lines.push(`Nota Mediana: ${resultado.nota_mediana?.toFixed(1)}`)
  lines.push('')
  resultado.avaliacoes?.forEach((av) => {
    lines.push(`--- ${av.tipo_avaliacao} ---`)
    lines.push(`Nota: ${av.nota}/100`)
    lines.push(`Justificativa: ${av.justificativa}`)
    lines.push('')
  })
  return lines.join('\n')
}

function App() {
  const [chat, setChat] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)
  const [rawJson, setRawJson] = useState(false)
  const fileInputRef = useRef(null)

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => setChat(ev.target.result || '')
    reader.onerror = () => setError('Erro ao ler o arquivo. Verifique se é um arquivo de texto válido.')
    reader.readAsText(file, 'UTF-8')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResultado(null)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/chamados/avaliacao_individual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat }),
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

  function handleDownload() {
    if (!resultado) return
    const content = buildResultadoText(resultado)
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'resultado_avaliacao.txt'
    a.click()
    URL.revokeObjectURL(url)
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

            <div className="field-row">
              <button
                type="button"
                className="btn-upload"
                onClick={() => fileInputRef.current?.click()}
              >
                📂 Carregar arquivo .txt
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,text/plain"
                style={{ display: 'none' }}
                onChange={handleFileChange}
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
              <div className="result-actions">
                <button
                  className="btn-toggle"
                  onClick={() => setRawJson((v) => !v)}
                >
                  {rawJson ? 'Ver formatado' : 'Ver JSON bruto'}
                </button>
                <button className="btn-download" onClick={handleDownload}>
                  ⬇ Baixar resultado
                </button>
              </div>
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
