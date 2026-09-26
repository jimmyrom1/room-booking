import { useMemo, useState } from 'react'

import { ApiError, api } from '../api'
import { atTime, formatLongDay, MAX_BOOKING_MINUTES, timeOptions } from '../dates'
import type { Booking, Room } from '../types'
import { Modal } from './Modal'

interface Props {
  room: Pick<Room, 'id' | 'name'>
  day: Date
  start: string
  end?: string
  onClose: () => void
  onBooked: (booking: Booking) => void
}

const toMinutes = (hhmm: string) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

export function BookingDialog({ room, day, start: initialStart, end: initialEnd, onClose, onBooked }: Props) {
  const all = useMemo(() => timeOptions(), [])
  const [title, setTitle] = useState('')
  const [start, setStart] = useState(initialStart)
  const [end, setEnd] = useState(
    initialEnd ?? all[Math.min(all.indexOf(initialStart) + 4, all.length - 1)],
  )
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const startOptions = all.slice(0, -1)
  const endOptions = all.filter((t) => {
    const diff = toMinutes(t) - toMinutes(start)
    return diff > 0 && diff <= MAX_BOOKING_MINUTES
  })

  function changeStart(value: string) {
    setStart(value)
    const duration = toMinutes(end) - toMinutes(start)
    const shifted = all.find((t) => toMinutes(t) === toMinutes(value) + duration)
    setEnd(shifted ?? all[Math.min(all.indexOf(value) + 4, all.length - 1)])
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const booking = await api.book({
        room_id: room.id,
        title: title.trim(),
        starts_at: atTime(day, start).toISOString(),
        ends_at: atTime(day, end).toISOString(),
      })
      onBooked(booking)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={`Reservar ${room.name}`} onClose={onClose}>
      <form onSubmit={submit} className="stack">
        <p className="muted">{formatLongDay(day)}</p>
        <label>
          Motivo
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ej.: Reunión de equipo"
            maxLength={120}
            required
          />
        </label>
        <div className="row">
          <label>
            Desde
            <select value={start} onChange={(e) => changeStart(e.target.value)}>
              {startOptions.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label>
            Hasta
            <select value={end} onChange={(e) => setEnd(e.target.value)}>
              {endOptions.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
        </div>
        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}
        <div className="actions">
          <button type="button" className="secondary" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" disabled={saving || !title.trim() || !endOptions.includes(end)}>
            {saving ? 'Reservando…' : 'Reservar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
