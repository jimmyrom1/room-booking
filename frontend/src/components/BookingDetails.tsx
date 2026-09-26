import { useState } from 'react'

import { ApiError, api } from '../api'
import { formatRange } from '../dates'
import type { Booking, User } from '../types'
import { Modal } from './Modal'

interface Props {
  booking: Booking
  user: User
  onClose: () => void
  onCancelled: () => void
}

export function BookingDetails({ booking, user, onClose, onCancelled }: Props) {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const canCancel =
    (booking.user.id === user.id || user.is_admin) && new Date(booking.starts_at) > new Date()

  async function cancel() {
    setBusy(true)
    try {
      await api.cancel(booking.id)
      onCancelled()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo cancelar.')
      setBusy(false)
    }
  }

  return (
    <Modal title={booking.title} onClose={onClose}>
      <dl className="details">
        <dt>Sala</dt>
        <dd>{booking.room.name}</dd>
        <dt>Cuándo</dt>
        <dd>{formatRange(booking.starts_at, booking.ends_at)}</dd>
        <dt>Reservada por</dt>
        <dd>{booking.user.id === user.id ? 'Ti' : booking.user.name}</dd>
      </dl>
      {error && <p className="alert">{error}</p>}
      <div className="actions">
        <button type="button" className="secondary" onClick={onClose}>
          Cerrar
        </button>
        {canCancel && (
          <button type="button" className="danger" onClick={cancel} disabled={busy}>
            {busy ? 'Cancelando…' : 'Cancelar reserva'}
          </button>
        )}
      </div>
    </Modal>
  )
}
