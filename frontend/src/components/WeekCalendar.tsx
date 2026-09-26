import { addDays, addMinutes, CLOSE_HOUR, dayOffsets, formatDay, formatTime, isSameDay, OPEN_HOUR } from '../dates'
import type { Booking } from '../types'

interface Props {
  weekStart: Date
  bookings: Booking[]
  currentUserId: number
  now: Date
  onSlotClick: (day: Date, hhmm: string) => void
  onBookingClick: (booking: Booking) => void
}

const DAYS = 5
const SLOT = 30 // minutos por celda clicable
const HOURS = Array.from({ length: CLOSE_HOUR - OPEN_HOUR }, (_, i) => OPEN_HOUR + i)
const SLOTS = Array.from({ length: ((CLOSE_HOUR - OPEN_HOUR) * 60) / SLOT }, (_, i) => i * SLOT)

export function WeekCalendar({ weekStart, bookings, currentUserId, now, onSlotClick, onBookingClick }: Props) {
  const days = Array.from({ length: DAYS }, (_, i) => addDays(weekStart, i))

  return (
    <div className="calendar" style={{ '--minutes': (CLOSE_HOUR - OPEN_HOUR) * 60 } as React.CSSProperties}>
      <div className="calendar-head">
        <div />
        {days.map((day) => (
          <div key={day.toISOString()} className={isSameDay(day, now) ? 'today' : undefined}>
            {formatDay(day)}
          </div>
        ))}
      </div>

      <div className="calendar-body">
        <div className="hours" aria-hidden="true">
          {HOURS.map((h) => (
            <span key={h} style={{ top: `calc(${(h - OPEN_HOUR) * 60} * var(--px))` }}>
              {String(h).padStart(2, '0')}:00
            </span>
          ))}
        </div>

        {days.map((day) => {
          const opening = new Date(day)
          opening.setHours(OPEN_HOUR, 0, 0, 0)
          return (
            <div key={day.toISOString()} className="day" role="group" aria-label={formatDay(day)}>
              {SLOTS.map((offset) => {
                const slotStart = addMinutes(opening, offset)
                const past = slotStart < now
                const hhmm = formatTime(slotStart)
                return (
                  <button
                    key={offset}
                    type="button"
                    className="slot"
                    disabled={past}
                    style={{ top: `calc(${offset} * var(--px))`, height: `calc(${SLOT} * var(--px))` }}
                    onClick={() => onSlotClick(day, hhmm)}
                    aria-label={`Reservar ${formatDay(day)} a las ${hhmm}`}
                  />
                )
              })}

              {bookings.map((b) => {
                const pos = dayOffsets(new Date(b.starts_at), new Date(b.ends_at), day)
                if (!pos) return null
                const mine = b.user.id === currentUserId
                return (
                  <button
                    key={b.id}
                    type="button"
                    className={`event ${mine ? 'event-mine' : ''}`}
                    style={{ top: `calc(${pos.top} * var(--px))`, height: `calc(${pos.height} * var(--px))` }}
                    onClick={() => onBookingClick(b)}
                    title={`${b.title} · ${b.user.name}`}
                  >
                    <strong>{b.title}</strong>
                    <span>
                      {formatTime(b.starts_at)}–{formatTime(b.ends_at)} · {mine ? 'Tú' : b.user.name}
                    </span>
                  </button>
                )
              })}

              {isSameDay(day, now) && dayOffsets(now, addMinutes(now, 1), day) && (
                <div
                  className="now-line"
                  style={{ top: `calc(${dayOffsets(now, addMinutes(now, 1), day)!.top} * var(--px))` }}
                  aria-hidden="true"
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
