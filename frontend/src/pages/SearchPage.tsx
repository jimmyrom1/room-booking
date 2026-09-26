import { useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '../api'
import { BookingDialog } from '../components/BookingDialog'
import { atTime, formatRange, fromDateInput, timeOptions, toDateInput } from '../dates'
import type { Booking, Room } from '../types'

function nextWorkday(): Date {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1)
  return d
}

export function SearchPage() {
  const times = timeOptions()
  const [date, setDate] = useState(toDateInput(nextWorkday()))
  const [start, setStart] = useState('10:00')
  const [end, setEnd] = useState('11:00')
  const [people, setPeople] = useState('4')
  const [results, setResults] = useState<Room[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [chosen, setChosen] = useState<Room | null>(null)
  const [booked, setBooked] = useState<Booking | null>(null)

  async function search(e?: React.FormEvent) {
    e?.preventDefault()
    setError(null)
    setBooked(null)
    const day = fromDateInput(date)
    try {
      setResults(
        await api.rooms({
          from: atTime(day, start).toISOString(),
          to: atTime(day, end).toISOString(),
          min_capacity: Number(people) || undefined,
        }),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo buscar.')
    }
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Buscar sala libre</h1>
          <p className="muted">Encuentra qué salas están disponibles en una franja.</p>
        </div>
      </header>

      <form className="card search-form" onSubmit={search}>
        <label>
          Día
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <label>
          Desde
          <select value={start} onChange={(e) => setStart(e.target.value)}>
            {times.slice(0, -1).map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <label>
          Hasta
          <select value={end} onChange={(e) => setEnd(e.target.value)}>
            {times.filter((t) => t > start).map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <label>
          Personas
          <input type="number" min={1} value={people} onChange={(e) => setPeople(e.target.value)} />
        </label>
        <button type="submit">Buscar</button>
      </form>

      {error && <p className="alert">{error}</p>}
      {booked && (
        <p className="success" role="status">
          ✓ Reservada <strong>{booked.room.name}</strong> · {formatRange(booked.starts_at, booked.ends_at)}.{' '}
          <Link to="/mine">Ver mis reservas</Link>
        </p>
      )}

      {results && results.length === 0 && (
        <div className="empty">No hay ninguna sala libre con esos requisitos. Prueba otra franja.</div>
      )}

      {results && results.length > 0 && (
        <ul className="room-grid">
          {results.map((room) => (
            <li key={room.id} className="card room-card">
              <div>
                <h3>{room.name}</h3>
                <p className="muted">
                  {room.capacity} personas{room.location && ` · ${room.location}`}
                </p>
                <p>
                  {room.amenities.map((a) => (
                    <span key={a} className="chip">
                      {a}
                    </span>
                  ))}
                </p>
              </div>
              <button type="button" onClick={() => setChosen(room)}>
                Reservar
              </button>
            </li>
          ))}
        </ul>
      )}

      {chosen && (
        <BookingDialog
          room={chosen}
          day={fromDateInput(date)}
          start={start}
          end={end}
          onClose={() => setChosen(null)}
          onBooked={(booking) => {
            setChosen(null)
            setBooked(booking)
            setResults((prev) => prev?.filter((r) => r.id !== booking.room.id) ?? null)
          }}
        />
      )}
    </>
  )
}
