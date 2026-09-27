import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { tokenStore } from '../api'
import { MyBookingsPage } from './MyBookingsPage'

const fetchMock = vi.fn<typeof fetch>()
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const upcoming = {
  id: 42,
  title: 'Revisión de sprint',
  starts_at: '2099-10-05T08:00:00Z',
  ends_at: '2099-10-05T09:00:00Z',
  is_cancelled: false,
  room: { id: 1, name: 'Atlántico', location: 'Planta 2' },
  user: { id: 2, name: 'Ana' },
}

describe('MyBookingsPage', () => {
  const clicks: string[] = []

  beforeEach(() => {
    fetchMock.mockReset()
    clicks.length = 0
    vi.stubGlobal('fetch', fetchMock)
    tokenStore.set('token-de-prueba')
    // jsdom no implementa blobs como URL ni la descarga al hacer clic en un enlace.
    URL.createObjectURL = vi.fn(() => 'blob:ics')
    URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      clicks.push(this.download)
    })
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    tokenStore.set(null)
  })

  async function renderPage() {
    fetchMock.mockResolvedValueOnce(json([upcoming]))
    render(
      <MemoryRouter>
        <MyBookingsPage />
      </MemoryRouter>,
    )
    await screen.findByText('Revisión de sprint')
    return userEvent.setup()
  }

  it('downloads all upcoming bookings as .ics with the auth header', async () => {
    const user = await renderPage()
    fetchMock.mockResolvedValueOnce(new Response('BEGIN:VCALENDAR\r\n', { headers: { 'Content-Type': 'text/calendar' } }))

    await user.click(screen.getByRole('button', { name: 'Añadir todas al calendario' }))

    const [url, init] = fetchMock.mock.calls[1] ?? []
    expect(url).toBe('/api/bookings/mine.ics')
    expect((init?.headers as Record<string, string> | undefined)?.Authorization).toBe('Bearer token-de-prueba')
    expect(clicks).toEqual(['mis-reservas.ics'])
  })

  it('downloads a single booking', async () => {
    const user = await renderPage()
    fetchMock.mockResolvedValueOnce(new Response('BEGIN:VCALENDAR\r\n'))

    await user.click(screen.getByRole('button', { name: '.ics' }))

    expect(fetchMock.mock.calls[1][0]).toBe('/api/bookings/42.ics')
    expect(clicks).toEqual(['reserva-42.ics'])
  })

  it('shows the API error if the download fails', async () => {
    const user = await renderPage()
    fetchMock.mockResolvedValueOnce(json({ message: 'Reserva no encontrada.' }, 404))

    await user.click(screen.getByRole('button', { name: '.ics' }))

    expect(await screen.findByText('Reserva no encontrada.')).toBeInTheDocument()
    expect(clicks).toEqual([])
  })
})
