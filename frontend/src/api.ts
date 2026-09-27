import type { Booking, BookingInput, Occupancy, Room, RoomInput, User } from './types'

const BASE = import.meta.env.VITE_API_URL ?? '/api'
const TOKEN_KEY = 'room-booking-token'

export class ApiError extends Error {
  status: number
  details?: Record<string, string[]>

  constructor(status: number, message: string, details?: Record<string, string[]>) {
    super(message)
    this.status = status
    this.details = details
  }
}

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set: (token: string | null) => {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token)
      else localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* almacenamiento no disponible: la sesión solo dura mientras la pestaña esté abierta */
    }
  },
}

let onUnauthorized: () => void = () => {}
export const setUnauthorizedHandler = (handler: () => void) => {
  onUnauthorized = handler
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStore.get()
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized()
    const details = body.details as Record<string, string[]> | undefined
    const firstDetail = details ? Object.values(details).flat()[0] : undefined
    throw new ApiError(res.status, body.message ?? firstDetail ?? 'Error inesperado', details)
  }
  return body as T
}

/**
 * Descarga un archivo protegido por el token. Un <a href> normal no puede enviar la cabecera
 * Authorization, así que se pide con fetch y se entrega como blob.
 */
async function download(path: string, filename: string): Promise<void> {
  const token = tokenStore.get()
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized()
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.message ?? 'No se pudo descargar el archivo')
  }
  const url = URL.createObjectURL(await res.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const send = (method: string, data?: unknown): RequestInit => ({
  method,
  body: data === undefined ? undefined : JSON.stringify(data),
})

const qs = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  return search.toString()
}

interface AuthResponse {
  access_token: string
  user: User
}

export const api = {
  register: (data: { name: string; email: string; password: string }) =>
    request<AuthResponse>('/auth/register', send('POST', data)),
  login: (data: { email: string; password: string }) =>
    request<AuthResponse>('/auth/login', send('POST', data)),
  me: () => request<User>('/auth/me'),

  rooms: (params: { from?: string; to?: string; min_capacity?: number; include_inactive?: number } = {}) =>
    request<Room[]>(`/rooms?${qs(params)}`),
  createRoom: (data: RoomInput) => request<Room>('/rooms', send('POST', data)),
  updateRoom: (id: number, data: RoomInput) => request<Room>(`/rooms/${id}`, send('PUT', data)),
  deleteRoom: (id: number) => request<Room | undefined>(`/rooms/${id}`, send('DELETE')),

  calendar: (params: { from: string; to: string; room_id?: number }) =>
    request<Booking[]>(`/bookings?${qs(params)}`),
  myBookings: (scope: 'upcoming' | 'past') => request<Booking[]>(`/bookings/mine?scope=${scope}`),
  book: (data: BookingInput) => request<Booking>('/bookings', send('POST', data)),
  cancel: (id: number) => request<Booking>(`/bookings/${id}`, send('DELETE')),
  downloadMyBookingsIcs: () => download('/bookings/mine.ics', 'mis-reservas.ics'),
  downloadBookingIcs: (id: number) => download(`/bookings/${id}.ics`, `reserva-${id}.ics`),

  occupancy: (params: { from: string; to: string }) =>
    request<Occupancy>(`/stats/occupancy?${qs(params)}`),
}
