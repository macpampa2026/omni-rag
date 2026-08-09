// Cliente de la API de omni-rag. En dev, las rutas relativas se reenvían al
// backend vía el proxy de Vite; en producción se puede fijar VITE_API_URL.
const env = import.meta.env as Record<string, string | undefined>
const BASE = env.VITE_API_URL ?? ''

export interface Source {
  n: number
  doc_id: string
  title: string
  page: number | null
  score: number
  excerpt: string
}

export interface AskResponse {
  question: string
  answer: string
  sources: Source[]
  model: string
}

export interface IngestResponse {
  doc_id: string
  title: string
  chunks: number
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const data = (await res.json().catch(() => null)) as { detail?: string } | null
    throw new Error(data?.detail ?? `Error ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function ask(question: string): Promise<AskResponse> {
  return post<AskResponse>('/ask', { question })
}

export function ingest(doc: {
  doc_id: string
  title: string
  text: string
}): Promise<IngestResponse> {
  return post<IngestResponse>('/documents', doc)
}
