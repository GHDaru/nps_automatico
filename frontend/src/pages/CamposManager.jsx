import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5020'

const emptyForm = { nome: '', descricao: '' }

export default function CamposManager() {
  const [campos, setCampos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)

  async function fetchCampos() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/campos`)
      if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`)
      setCampos(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCampos()
  }, [])

  function openNew() {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
  }

  function openEdit(c) {
    setForm({ nome: c.nome, descricao: c.descricao })
    setEditingId(c.id)
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
      const url = editingId ? `${API_BASE}/campos/${editingId}` : `${API_BASE}/campos`
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
      await fetchCampos()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id) {
    if (!confirm('Deseja excluir este campo?')) return
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/campos/${id}`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) {
        const data = await res.json()
        throw new Error(data.detail || JSON.stringify(data))
      }
      await fetchCampos()
    } catch (err) {
      setError(err.message)
    }
  }

  function handleExportJson() {
    const json = JSON.stringify(
      campos.map((c) => ({ nome: c.nome, descricao: c.descricao })),
      null,
      2
    )
    const blob = new Blob([json], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'campos_extraidos.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>Campos Extraídos</h2>
        <div className="field-row">
          {campos.length > 0 && (
            <button className="btn-upload" onClick={handleExportJson}>
              ⬇ Exportar JSON
            </button>
          )}
          <button className="btn-submit" onClick={openNew}>
            + Novo Campo
          </button>
        </div>
      </div>

      {error && <div className="inline-error">{error}</div>}

      {showForm && (
        <section className="form-section">
          <h3>{editingId ? 'Editar Campo' : 'Novo Campo'}</h3>
          <form onSubmit={handleSave} className="eval-form">
            <div className="field">
              <label>Nome do campo</label>
              <input
                type="text"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                placeholder="Ex: cliente, atendente, categoria_chamado"
                required
              />
            </div>
            <div className="field">
              <label>Descrição (exibida no JSON exportado)</label>
              <textarea
                value={form.descricao}
                onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
                placeholder="Descreva o que este campo representa e como deve ser extraído..."
                rows={4}
                required
              />
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
          <p className="loading-text">Carregando campos...</p>
        ) : campos.length === 0 ? (
          <p className="empty-text">Nenhum campo cadastrado ainda.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Descrição</th>
                <th>Criado em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {campos.map((c) => (
                <tr key={c.id}>
                  <td>
                    <code className="field-name">{c.nome}</code>
                  </td>
                  <td>{c.descricao}</td>
                  <td>{new Date(c.criado_em).toLocaleDateString('pt-BR')}</td>
                  <td className="actions-cell">
                    <button className="btn-action" onClick={() => openEdit(c)}>
                      ✏️ Editar
                    </button>
                    <button
                      className="btn-action btn-action--danger"
                      onClick={() => handleDelete(c.id)}
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
