import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5020'

const emptyForm = { nome: '', conteudo: '', ativo: true }

export default function PromptManager() {
  const [prompts, setPrompts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)

  async function fetchPrompts() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/prompts`)
      if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`)
      setPrompts(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPrompts()
  }, [])

  function openNew() {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
  }

  function openEdit(p) {
    setForm({ nome: p.nome, conteudo: p.conteudo, ativo: p.ativo })
    setEditingId(p.id)
    setShowForm(true)
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const url = editingId ? `${API_BASE}/prompts/${editingId}` : `${API_BASE}/prompts`
      const method = editingId ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || JSON.stringify(data))
      }
      cancelForm()
      await fetchPrompts()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id) {
    if (!confirm('Deseja excluir este prompt?')) return
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/prompts/${id}`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) {
        const data = await res.json()
        throw new Error(data.detail || JSON.stringify(data))
      }
      await fetchPrompts()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleToggleAtivo(p) {
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/prompts/${p.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ativo: !p.ativo }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || JSON.stringify(data))
      }
      await fetchPrompts()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>Gerenciamento de Prompts</h2>
        <button className="btn-submit" onClick={openNew}>
          + Novo Prompt
        </button>
      </div>

      {error && <div className="inline-error">{error}</div>}

      {showForm && (
        <section className="form-section">
          <h3>{editingId ? 'Editar Prompt' : 'Novo Prompt'}</h3>
          <form onSubmit={handleSave} className="eval-form">
            <div className="field">
              <label>Nome da dimensão de análise</label>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                placeholder="Ex: Comunicação e Clareza"
                required
              />
            </div>
            <div className="field">
              <label>Conteúdo do prompt (instruções para o LLM)</label>
              <textarea
                value={form.conteudo}
                onChange={(e) => setForm((f) => ({ ...f, conteudo: e.target.value }))}
                placeholder="Descreva as instruções para avaliação desta dimensão..."
                rows={10}
                required
              />
            </div>
            <div className="field-row field-row--align-center">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.ativo}
                  onChange={(e) => setForm((f) => ({ ...f, ativo: e.target.checked }))}
                />
                Ativo no fluxo de avaliação
              </label>
            </div>
            <div className="field-row">
              <button type="submit" className="btn-submit" disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button type="button" className="btn-upload" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="result-section">
        {loading ? (
          <p className="loading-text">Carregando prompts...</p>
        ) : prompts.length === 0 ? (
          <p className="empty-text">Nenhum prompt cadastrado ainda.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Ativo</th>
                <th>Criado em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {prompts.map((p) => (
                <tr key={p.id}>
                  <td>{p.nome}</td>
                  <td>
                    <button
                      className={`badge ${p.ativo ? 'badge--green' : 'badge--gray'}`}
                      onClick={() => handleToggleAtivo(p)}
                      title={p.ativo ? 'Clique para desativar' : 'Clique para ativar'}
                    >
                      {p.ativo ? 'Ativo' : 'Inativo'}
                    </button>
                  </td>
                  <td>{new Date(p.criado_em).toLocaleDateString('pt-BR')}</td>
                  <td className="actions-cell">
                    <button className="btn-action" onClick={() => openEdit(p)}>
                      ✏️ Editar
                    </button>
                    <button
                      className="btn-action btn-action--danger"
                      onClick={() => handleDelete(p.id)}
                    >
                      🗑️ Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
