import { useEffect, useState } from 'react'

import { api } from '../api'
import { addDays, formatLongDay, startOfWeek } from '../dates'
import type { Occupancy } from '../types'

const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 0 })
const hours = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 })

export function StatsPage() {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()))
  const [data, setData] = useState<Occupancy | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .occupancy({ from: weekStart.toISOString(), to: addDays(weekStart, 7).toISOString() })
      .then(setData)
      .catch((e: Error) => setError(e.message))
  }, [weekStart])

  const total = data?.rooms.reduce((sum, r) => sum + r.booked_hours, 0) ?? 0

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Ocupación</h1>
          <p className="muted">
            Semana del {formatLongDay(weekStart)} · horario laboral de 08:00 a 21:00
          </p>
        </div>
        <div className="week-nav">
          <button type="button" className="secondary" onClick={() => setWeekStart(addDays(weekStart, -7))} aria-label="Semana anterior">
            ‹
          </button>
          <button type="button" className="secondary" onClick={() => setWeekStart(startOfWeek(new Date()))}>
            Esta semana
          </button>
          <button type="button" className="secondary" onClick={() => setWeekStart(addDays(weekStart, 7))} aria-label="Semana siguiente">
            ›
          </button>
        </div>
      </header>

      {error && <p className="alert">{error}</p>}

      {data && (
        <>
          <section className="stats">
            <div className="stat">
              <span className="stat-label">Horas reservadas</span>
              <strong className="stat-value">{hours.format(total)} h</strong>
            </div>
            <div className="stat">
              <span className="stat-label">Ocupación media</span>
              <strong className="stat-value">
                {percent.format(data.rooms.length ? total / (data.open_hours * data.rooms.length) : 0)}
              </strong>
            </div>
            <div className="stat">
              <span className="stat-label">Horas disponibles por sala</span>
              <strong className="stat-value">{hours.format(data.open_hours)} h</strong>
            </div>
          </section>

          <div className="card">
            <ul className="bars">
              {data.rooms.map((r) => (
                <li key={r.room_id}>
                  <span className="bar-label">
                    {r.name} <span className="muted">· {r.capacity} pers.</span>
                  </span>
                  <span
                    className="bar"
                    role="meter"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(r.occupancy * 100)}
                    aria-label={`Ocupación de ${r.name}`}
                  >
                    <span style={{ width: `${Math.min(r.occupancy, 1) * 100}%` }} />
                  </span>
                  <span className="bar-value">
                    {percent.format(r.occupancy)} <span className="muted">({hours.format(r.booked_hours)} h)</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </>
  )
}
