import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from '../api'
import { useAuth } from '../auth'
import { BookingDetails } from '../components/BookingDetails'
import { BookingDialog } from '../components/BookingDialog'
import { WeekCalendar } from '../components/WeekCalendar'
import { addDays, currentWorkWeek, formatMonth, fromDateInput, startOfWeek, toDateInput } from '../dates'
import type { Booking, Room } from '../types'

export function CalendarPage() {
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const [rooms, setRooms] = useState<Room[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<{ day: Date; start: string } | null>(null)
  const [selected, setSelected] = useState<Booking | null>(null)
  const [now, setNow] = useState(() => new Date())

  const weekStart = params.get('week') ? startOfWeek(fromDateInput(params.get('week')!)) : currentWorkWeek(now)
  const weekKey = toDateInput(weekStart)
  const roomId = Number(params.get('room')) || rooms[0]?.id
  const room = rooms.find((r) => r.id === roomId)

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    next.set(key, value)
    setParams(next, { replace: true })
  }

  useEffect(() => {
    api.rooms().then(setRooms).catch((e: Error) => setError(e.message))
    const timer = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(timer)
  }, [])

  const load = useCallback(() => {
    if (!roomId) return
    const from = fromDateInput(weekKey)
    api
      .calendar({ room_id: roomId, from: from.toISOString(), to: addDays(from, 7).toISOString() })
      .then((res) => {
        setBookings(res)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
  }, [roomId, weekKey])

  useEffect(load, [load])

  if (!user) return null

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Calendario</h1>
          <p className="muted">Haz clic en un hueco libre para reservar.</p>
        </div>
        <div className="toolbar">
          <label className="inline">
            <span className="sr-only">Sala</span>
            <select value={roomId ?? ''} onChange={(e) => update('room', e.target.value)}>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} · {r.capacity} pers.
                </option>
              ))}
            </select>
          </label>
          <div className="week-nav">
            <button type="button" className="secondary" onClick={() => update('week', toDateInput(addDays(weekStart, -7)))} aria-label="Semana anterior">
              ‹
            </button>
            <button type="button" className="secondary" onClick={() => update('week', toDateInput(currentWorkWeek(new Date())))}>
              Hoy
            </button>
            <button type="button" className="secondary" onClick={() => update('week', toDateInput(addDays(weekStart, 7)))} aria-label="Semana siguiente">
              ›
            </button>
          </div>
        </div>
      </header>

      {room && (
        <p className="room-summary">
          <strong>{formatMonth(weekStart)}</strong>
          {room.location && <span>{room.location}</span>}
          {room.amenities.map((a) => (
            <span key={a} className="chip">
              {a}
            </span>
          ))}
        </p>
      )}

      {error && <p className="alert">{error}</p>}

      <WeekCalendar
        weekStart={weekStart}
        bookings={bookings}
        currentUserId={user.id}
        now={now}
        onSlotClick={(day, start) => setDraft({ day, start })}
        onBookingClick={setSelected}
      />

      {draft && room && (
        <BookingDialog
          room={room}
          day={draft.day}
          start={draft.start}
          onClose={() => setDraft(null)}
          onBooked={() => {
            setDraft(null)
            load()
          }}
        />
      )}

      {selected && (
        <BookingDetails
          booking={selected}
          user={user}
          onClose={() => setSelected(null)}
          onCancelled={() => {
            setSelected(null)
            load()
          }}
        />
      )}
    </>
  )
}
