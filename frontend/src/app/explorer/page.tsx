"use client"

import { useState } from 'react'

export default function ApiExplorerPage() {
  const [path, setPath] = useState<string>('/api/')
  const [method, setMethod] = useState<string>('GET')
  const [body, setBody] = useState<string>('')
  const [response, setResponse] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  const sendRequest = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const url = `${BACKEND_URL}${path}`
      const options: RequestInit = { method }
      if (method !== 'GET' && body) {
        options.headers = { 'Content-Type': 'application/json' }
        options.body = body
      }
      const res = await fetch(url, options)
      const text = await res.text()
      try {
        setResponse(JSON.parse(text))
      } catch {
        setResponse(text)
      }
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">API Explorer</h1>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="px-2 py-1 border rounded"
          >
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>PATCH</option>
            <option>DELETE</option>
          </select>
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/api/your/endpoint"
            className="flex-1 px-2 py-1 border rounded"
          />
          <button
            onClick={sendRequest}
            disabled={loading}
            className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Send'}
          </button>
        </div>
        {(method !== 'GET') && (
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder='Request body as JSON'
            rows={6}
            className="w-full px-2 py-1 border rounded font-mono text-sm"
          />
        )}
        {error && (
          <div className="p-2 bg-red-100 text-red-700 rounded">
            Error: {error}
          </div>
        )}
        {response !== null && (
          <div className="p-2 bg-gray-50 border rounded font-mono text-sm whitespace-pre-wrap">
            {typeof response === 'string'
              ? response
              : JSON.stringify(response, null, 2)
            }
          </div>
        )}
      </div>
    </div>
