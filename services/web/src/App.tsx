import { useState, type FormEvent } from 'react'
import './App.css'
import { ask, ingest, type AskResponse } from './api'

// Resalta las citas [n] dentro del texto de la respuesta.
function AnswerText({ text }: { text: string }) {
  const parts = text.split(/(\[\d+\])/g)
  return (
    <p className="answer">
      {parts.map((part, i) =>
        /^\[\d+\]$/.test(part) ? (
          <span key={i} className="cite">
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </p>
  )
}

function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AskResponse | null>(null)

  const [showIngest, setShowIngest] = useState(false)
  const [docId, setDocId] = useState('')
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [ingestMsg, setIngestMsg] = useState<string | null>(null)

  async function handleAsk(e: FormEvent) {
    e.preventDefault()
    if (!question.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await ask(question.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  async function handleIngest(e: FormEvent) {
    e.preventDefault()
    if (!docId.trim() || !title.trim() || !text.trim()) return
    setIngestMsg(null)
    try {
      const r = await ingest({
        doc_id: docId.trim(),
        title: title.trim(),
        text: text.trim(),
      })
      setIngestMsg(`Documento "${r.title}" cargado (${r.chunks} fragmento/s).`)
      setDocId('')
      setTitle('')
      setText('')
    } catch (err) {
      setIngestMsg(err instanceof Error ? err.message : 'Error al cargar')
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>omni-rag</h1>
        <p className="tagline">
          Preguntá y obtené respuestas basadas <strong>solo</strong> en tus
          documentos, con la fuente citada y sin invenciones.
        </p>
      </header>

      <form className="ask" onSubmit={handleAsk}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ej: ¿Cuántos días tengo para devolver un producto?"
          rows={3}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Consultando…' : 'Preguntar'}
        </button>
      </form>

      {error && <div className="error">⚠ {error}</div>}

      {result && (
        <section className="result">
          <AnswerText text={result.answer} />
          {result.sources.length > 0 && (
            <>
              <h2>Fuentes</h2>
              <ul className="sources">
                {result.sources.map((s) => (
                  <li key={s.n} className="source">
                    <div className="source-head">
                      <span className="badge">[{s.n}]</span>
                      <span className="source-title">{s.title}</span>
                      <span className="score">{Math.round(s.score * 100)}%</span>
                    </div>
                    <p className="excerpt">{s.excerpt}</p>
                  </li>
                ))}
              </ul>
            </>
          )}
          <p className="model">Generado con {result.model}</p>
        </section>
      )}

      <section className="ingest-toggle">
        <button
          type="button"
          className="link"
          onClick={() => setShowIngest((v) => !v)}
        >
          {showIngest ? '− Ocultar carga de documentos' : '+ Cargar un documento'}
        </button>
        {showIngest && (
          <form className="ingest" onSubmit={handleIngest}>
            <input
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
              placeholder="id (ej: garantia)"
            />
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Título del documento"
            />
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Pegá acá el texto del documento…"
              rows={4}
            />
            <button type="submit">Cargar documento</button>
            {ingestMsg && <p className="ingest-msg">{ingestMsg}</p>}
          </form>
        )}
      </section>

      <footer className="foot">
        Frontend en React + TypeScript · consume la API de omni-rag (FastAPI)
      </footer>
    </div>
  )
}

export default App
