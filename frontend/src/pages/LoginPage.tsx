import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { ApiError } from '../api'
import { useAuth } from '../auth'

export function LoginPage() {
  const { user, login, register } = useAuth()
  const location = useLocation()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [details, setDetails] = useState<Record<string, string[]>>({})
  const [busy, setBusy] = useState(false)

  if (user) {
    const from = (location.state as { from?: string } | null)?.from ?? '/'
    return <Navigate to={from} replace />
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setDetails({})
    try {
      if (mode === 'login') await login(email, password)
      else await register(name, email, password)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setDetails(err.details ?? {})
      } else setError('No se pudo conectar con el servidor.')
    } finally {
      setBusy(false)
    }
  }

  const fieldError = (field: string) =>
    details[field] && <span className="field-error">{details[field].join(' ')}</span>

  return (
    <div className="auth-page">
      <form className="card auth-card stack" onSubmit={submit} noValidate>
        <div className="brand-lg">◫ Reserva de Salas</div>
        <div className="segmented" role="tablist">
          <button type="button" role="tab" aria-selected={mode === 'login'} onClick={() => setMode('login')}>
            Entrar
          </button>
          <button type="button" role="tab" aria-selected={mode === 'register'} onClick={() => setMode('register')}>
            Crear cuenta
          </button>
        </div>

        {mode === 'register' && (
          <label>
            Nombre
            <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" aria-invalid={!!details.name} />
            {fieldError('name')}
          </label>
        )}
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" aria-invalid={!!details.email} />
          {fieldError('email')}
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            aria-invalid={!!details.password}
          />
          {mode === 'register' && <span className="hint">Mínimo 8 caracteres.</span>}
          {fieldError('password')}
        </label>

        {error && <p className="alert" role="alert">{error}</p>}

        <button type="submit" disabled={busy}>
          {busy ? 'Un momento…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
        </button>
        <p className="hint center">
          Demo: <code>ana@demo.local</code> / <code>demo1234</code>
        </p>
      </form>
    </div>
  )
}
