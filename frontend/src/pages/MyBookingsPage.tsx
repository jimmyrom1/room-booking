import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import { formatLongDay, formatTime } from '../dates'
import type { Booking } from '../types'

export function MyBookingsPage() {
  const [scope, setScope] = useState<'upcoming' | 'past'>('upcoming')
  const [bookings, setBookings] = useState<Booking[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    api
      .myBookings(scope)
      .then(setBookings)
      .catch((e: Error) => setError(e.message))
  }, [scope])

  useEffect(load, [load])

  async function cancel(b: Booking) {
    if (!window.confirm(`¿Cancelar «${b.title}» en ${b.room.name}?`)) return
    try {
      await api.cancel(b.id)
      load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function exportIcs(b?: Booking) {
    try {
      await (b ? api.downloadBookingIcs(b.id) : api.downloadMyBookingsIcs())
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const hasUpcoming = scope === 'upcoming' && bookings?.some((b) => !b.is_cancelled)

  return (
    <>
      <header className="page-header">
        <h1>Mis reservas</h1>
        {hasUpcoming && (
          <button
            type="button"
            className="secondary"
            onClick={() => exportIcs()}
            title="Descarga un .ics para Google Calendar, Outlook o Apple Calendar"
          >
            Añadir todas al calendario
          </button>
        )}
        <div className="segmented" role="tablist">
          <button type="button" role="tab" aria-selected={scope === 'upcoming'} onClick={() => setScope('upcoming')}>
            Próximas
          </button>
          <button type="button" role="tab" aria-selected={scope === 'past'} onClick={() => setScope('past')}>
            Anteriores
          </button>
        </div>
      </header>

      {error && <p className="alert">{error}</p>}

      {bookings?.length === 0 && (
        <div className="empty">
          {scope === 'upcoming' ? (
            <>
              No tienes reservas próximas. <Link to="/search">Busca una sala libre</Link>.
            </>
          ) : (
            'Todavía no hay reservas pasadas.'
          )}
        </div>
      )}

      <ul className="booking-list">
        {bookings?.map((b) => (
          <li key={b.id} className={`card booking-item ${b.is_cancelled ? 'cancelled' : ''}`}>
            <div className="when">
              <strong>{formatTime(b.starts_at)}</strong>
              <span>{formatTime(b.ends_at)}</span>
            </div>
            <div className="what">
              <strong>{b.title}</strong>
              <span className="muted">
                {formatLongDay(b.starts_at)} · {b.room.name}
                {b.room.location && ` · ${b.room.location}`}
              </span>
            </div>
            {b.is_cancelled ? (
              <span className="chip">Cancelada</span>
            ) : (
              scope === 'upcoming' && (
                <div className="actions">
                  <button type="button" className="link" onClick={() => exportIcs(b)}>
                    .ics
                  </button>
                  {new Date(b.starts_at) > new Date() && (
                    <button type="button" className="link danger" onClick={() => cancel(b)}>
                      Cancelar
                    </button>
                  )}
                </div>
              )
            )}
          </li>
        ))}
      </ul>
    </>
  )
}
