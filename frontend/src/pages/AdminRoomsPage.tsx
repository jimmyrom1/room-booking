import { useCallback, useEffect, useState } from 'react'

import { ApiError, api } from '../api'
import type { Room, RoomInput } from '../types'

interface FormState {
  name: string
  capacity: string
  location: string
  amenities: string
  is_active: boolean
}

const blank: FormState = { name: '', capacity: '4', location: '', amenities: '', is_active: true }

const toInput = (form: FormState): RoomInput => ({
  name: form.name.trim(),
  capacity: Number(form.capacity),
  location: form.location.trim() || null,
  amenities: form.amenities
    .split(',')
    .map((a) => a.trim().toLowerCase())
    .filter(Boolean),
  is_active: form.is_active,
})

export function AdminRoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [form, setForm] = useState<FormState>(blank)
  const [editing, setEditing] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [details, setDetails] = useState<Record<string, string[]>>({})

  const load = useCallback(() => {
    api.rooms({ include_inactive: 1 }).then(setRooms).catch((e: Error) => setError(e.message))
  }, [])
  useEffect(load, [load])

  const reset = () => {
    setForm(blank)
    setEditing(null)
    setDetails({})
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setDetails({})
    try {
      if (editing) await api.updateRoom(editing, toInput(form))
      else await api.createRoom(toInput(form))
      reset()
      load()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setDetails(err.details ?? {})
      }
    }
  }

  async function remove(room: Room) {
    if (!window.confirm(`¿Eliminar ${room.name}? Si tiene historial de reservas se desactivará.`)) return
    try {
      await api.deleteRoom(room.id)
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const input = (field: 'name' | 'capacity' | 'location' | 'amenities', label: string, extra = {}) => (
    <label>
      {label}
      <input
        value={form[field]}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
        aria-invalid={!!details[field]}
        {...extra}
      />
      {details[field] && <span className="field-error">{details[field].join(' ')}</span>}
    </label>
  )

  return (
    <>
      <header className="page-header">
        <h1>Gestionar salas</h1>
      </header>

      {error && <p className="alert">{error}</p>}

      <form className="card grid" onSubmit={submit} noValidate>
        <h2 className="span-all">{editing ? 'Editar sala' : 'Nueva sala'}</h2>
        {input('name', 'Nombre')}
        {input('capacity', 'Capacidad', { type: 'number', min: 1 })}
        {input('location', 'Ubicación', { placeholder: 'Planta 1' })}
        {input('amenities', 'Equipamiento', { placeholder: 'proyector, pizarra' })}
        <label className="checkbox span-all">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          Disponible para reservar
        </label>
        <div className="actions span-all">
          {editing && (
            <button type="button" className="secondary" onClick={reset}>
              Cancelar
            </button>
          )}
          <button type="submit">{editing ? 'Guardar cambios' : 'Añadir sala'}</button>
        </div>
      </form>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Sala</th>
              <th className="num">Capacidad</th>
              <th>Ubicación</th>
              <th>Equipamiento</th>
              <th>Estado</th>
              <th aria-label="Acciones" />
            </tr>
          </thead>
          <tbody>
            {rooms.map((room) => (
              <tr key={room.id}>
                <td>
                  <strong>{room.name}</strong>
                </td>
                <td className="num">{room.capacity}</td>
                <td>{room.location ?? '—'}</td>
                <td>
                  {room.amenities.map((a) => (
                    <span key={a} className="chip">
                      {a}
                    </span>
                  ))}
                </td>
                <td>{room.is_active ? 'Activa' : <span className="muted">Inactiva</span>}</td>
                <td className="row-actions">
                  <button
                    type="button"
                    className="link"
                    onClick={() => {
                      setEditing(room.id)
                      setForm({
                        name: room.name,
                        capacity: String(room.capacity),
                        location: room.location ?? '',
                        amenities: room.amenities.join(', '),
                        is_active: room.is_active,
                      })
                      window.scrollTo({ top: 0, behavior: 'smooth' })
                    }}
                  >
                    Editar
                  </button>
                  <button type="button" className="link danger" onClick={() => remove(room)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
