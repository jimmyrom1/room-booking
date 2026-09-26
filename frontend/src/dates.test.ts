import { describe, expect, it } from 'vitest'

import {
  addDays,
  atTime,
  currentWorkWeek,
  dayOffsets,
  startOfWeek,
  timeOptions,
  toDateInput,
} from './dates'

describe('startOfWeek', () => {
  it('returns Monday 00:00 for any day of the week', () => {
    const sunday = new Date(2026, 9, 11, 18, 30) // domingo 11/10/2026
    const monday = startOfWeek(sunday)
    expect(toDateInput(monday)).toBe('2026-10-05')
    expect(monday.getHours()).toBe(0)
    expect(toDateInput(startOfWeek(new Date(2026, 9, 5, 9)))).toBe('2026-10-05')
  })
})

describe('dayOffsets', () => {
  const day = new Date(2026, 9, 5)

  it('places an event relative to opening time', () => {
    const offsets = dayOffsets(atTime(day, '10:30'), atTime(day, '12:00'), day)
    expect(offsets).toEqual({ top: 150, height: 90 })
  })

  it('clips events that cross opening or closing', () => {
    expect(dayOffsets(atTime(day, '07:00'), atTime(day, '09:00'), day)).toEqual({
      top: 0,
      height: 60,
    })
    expect(dayOffsets(atTime(day, '20:30'), atTime(addDays(day, 1), '01:00'), day)).toEqual({
      top: 750,
      height: 30,
    })
  })

  it('returns null for events on another day', () => {
    const tomorrow = addDays(day, 1)
    expect(dayOffsets(atTime(tomorrow, '10:00'), atTime(tomorrow, '11:00'), day)).toBeNull()
  })
})

describe('timeOptions', () => {
  it('generates 15-minute slots including both ends', () => {
    const options = timeOptions(8, 9)
    expect(options).toEqual(['08:00', '08:15', '08:30', '08:45', '09:00'])
  })
})

describe('currentWorkWeek', () => {
  it('jumps to next week on weekends', () => {
    expect(toDateInput(currentWorkWeek(new Date(2026, 8, 27)))).toBe('2026-09-28') // domingo
    expect(toDateInput(currentWorkWeek(new Date(2026, 8, 26)))).toBe('2026-09-28') // sábado
    expect(toDateInput(currentWorkWeek(new Date(2026, 8, 25)))).toBe('2026-09-21') // viernes
  })
})
