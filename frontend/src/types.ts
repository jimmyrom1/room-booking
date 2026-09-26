export interface User {
  id: number
  name: string
  email: string
  is_admin: boolean
}

export interface Room {
  id: number
  name: string
  capacity: number
  location: string | null
  amenities: string[]
  is_active: boolean
}

export type RoomInput = Omit<Room, 'id'>

export interface Booking {
  id: number
  title: string
  starts_at: string
  ends_at: string
  is_cancelled: boolean
  room: Pick<Room, 'id' | 'name' | 'location'>
  user: Pick<User, 'id' | 'name'>
}

export interface BookingInput {
  room_id: number
  title: string
  starts_at: string
  ends_at: string
}

export interface Occupancy {
  open_hours: number
  rooms: Array<{
    room_id: number
    name: string
    capacity: number
    booked_hours: number
    occupancy: number
  }>
}
