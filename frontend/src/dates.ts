/** Utilidades de fechas sin dependencias. Trabajan en la zona horaria del navegador. */

export const OPEN_HOUR = 8
export const CLOSE_HOUR = 21
export const SLOT_MINUTES = 15
export const MAX_BOOKING_MINUTES = 4 * 60

export function startOfWeek(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const offset = (d.getDay() + 6) % 7 // lunes = 0
  d.setDate(d.getDate() - offset)
  return d
}

/** Semana que tiene sentido mostrar por defecto: en fin de semana, la siguiente. */
export function currentWorkWeek(now: Date): Date {
  const weekend = now.getDay() === 0 || now.getDay() === 6
  return startOfWeek(weekend ? addDays(now, 2) : now)
}

export function addDays(date: Date, days: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

export function addMinutes(date: Date, minutes: number): Date {
  return new Date(date.getTime() + minutes * 60_000)
}

export function atTime(day: Date, hhmm: string): Date {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date(day)
  d.setHours(h, m, 0, 0)
  return d
}

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  )
}

/** "2026-10-05" en hora local (para <input type="date">). */
export function toDateInput(date: Date): string {
  return date.toLocaleDateString('sv-SE')
}

export function fromDateInput(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, m - 1, d)
}

const timeFmt = new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' })
const dayFmt = new Intl.DateTimeFormat('es-ES', { weekday: 'short', day: 'numeric' })
const longDayFmt = new Intl.DateTimeFormat('es-ES', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})
const monthFmt = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' })

export const formatTime = (d: Date | string) => timeFmt.format(new Date(d))
export const formatDay = (d: Date) => dayFmt.format(d)
export const formatLongDay = (d: Date | string) => longDayFmt.format(new Date(d))
export const formatMonth = (d: Date) => monthFmt.format(d)

export function formatRange(start: string, end: string): string {
  return `${formatLongDay(start)}, ${formatTime(start)}–${formatTime(end)}`
}

/** Posición vertical (en minutos desde la apertura) de un evento dentro de un día. */
export function dayOffsets(start: Date, end: Date, day: Date) {
  const opening = atTime(day, `${OPEN_HOUR}:00`)
  const closing = atTime(day, `${CLOSE_HOUR}:00`)
  const from = Math.max(start.getTime(), opening.getTime())
  const to = Math.min(end.getTime(), closing.getTime())
  if (to <= from) return null
  return {
    top: (from - opening.getTime()) / 60_000,
    height: (to - from) / 60_000,
  }
}

/** Opciones HH:MM cada 15 minutos entre apertura y cierre. */
export function timeOptions(from = OPEN_HOUR, to = CLOSE_HOUR): string[] {
  const options: string[] = []
  for (let minutes = from * 60; minutes <= to * 60; minutes += SLOT_MINUTES) {
    const h = String(Math.floor(minutes / 60)).padStart(2, '0')
    const m = String(minutes % 60).padStart(2, '0')
    options.push(`${h}:${m}`)
  }
  return options
}
