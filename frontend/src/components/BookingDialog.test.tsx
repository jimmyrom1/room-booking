import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { BookingDialog } from './BookingDialog'

const room = { id: 7, name: 'Atlántico' }
const day = new Date(2026, 9, 5) // lunes 5 de octubre

// Se simula fetch (no el módulo api) para probar también el cliente HTTP real.
const fetchMock = vi.fn<typeof fetch>()
const respond = (status: number, body: unknown) =>
  fetchMock.mockResolvedValueOnce(
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  )

function setup(props: Partial<Parameters<typeof BookingDialog>[0]> = {}) {
  const onBooked = vi.fn()
  const onClose = vi.fn()
  render(
    <BookingDialog room={room} day={day} start="10:00" onBooked={onBooked} onClose={onClose} {...props} />,
  )
  return { onBooked, onClose, user: userEvent.setup() }
}

describe('BookingDialog', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  it('defaults to one hour and never offers more than four', () => {
    setup()
    const end = screen.getByLabelText('Hasta') as HTMLSelectElement
    expect(end.value).toBe('11:00')
    const options = Array.from(end.options).map((o) => o.value)
    expect(options[0]).toBe('10:15')
    expect(options.at(-1)).toBe('14:00')
  })

  it('keeps the duration when the start time changes', async () => {
    const { user } = setup({ end: '11:30' })
    await user.selectOptions(screen.getByLabelText('Desde'), '12:00')
    expect((screen.getByLabelText('Hasta') as HTMLSelectElement).value).toBe('13:30')
  })

  it('sends the booking in UTC and reports success', async () => {
    respond(201, { id: 1 })
    const { user, onBooked } = setup()

    const submit = screen.getByRole('button', { name: 'Reservar' })
    expect(submit).toBeDisabled() // falta el motivo
    await user.type(screen.getByLabelText('Motivo'), 'Daily')
    await user.click(submit)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/bookings')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({
      room_id: 7,
      title: 'Daily',
      starts_at: new Date(2026, 9, 5, 10, 0).toISOString(),
      ends_at: new Date(2026, 9, 5, 11, 0).toISOString(),
    })
    expect(onBooked).toHaveBeenCalledWith({ id: 1 })
  })

  it('shows the server error when the slot is taken', async () => {
    respond(409, { error: 'slot_taken', message: 'La sala ya está reservada en ese horario.' })
    const { user, onBooked } = setup()
    await user.type(screen.getByLabelText('Motivo'), 'Daily')
    await user.click(screen.getByRole('button', { name: 'Reservar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('ya está reservada')
    expect(onBooked).not.toHaveBeenCalled()
  })
})
