import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'

import { AuthProvider, useAuth } from './auth'
import { AdminRoomsPage } from './pages/AdminRoomsPage'
import { CalendarPage } from './pages/CalendarPage'
import { LoginPage } from './pages/LoginPage'
import { MyBookingsPage } from './pages/MyBookingsPage'
import { SearchPage } from './pages/SearchPage'
import { StatsPage } from './pages/StatsPage'

function RequireAuth({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <p className="loading">Cargando…</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  if (admin && !user.is_admin) return <Navigate to="/" replace />
  return <>{children}</>
}

function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  return (
    <>
      <nav className="topbar">
        <span className="brand">◫ Reserva de Salas</span>
        <div className="nav-links">
          <NavLink to="/" end>
            Calendario
          </NavLink>
          <NavLink to="/search">Buscar sala</NavLink>
          <NavLink to="/mine">Mis reservas</NavLink>
          {user?.is_admin && (
            <>
              <NavLink to="/admin/rooms">Salas</NavLink>
              <NavLink to="/admin/stats">Ocupación</NavLink>
            </>
          )}
        </div>
        <div className="user-menu">
          <span>
            {user?.name}
            {user?.is_admin && <span className="chip">admin</span>}
          </span>
          <button type="button" className="link" onClick={logout}>
            Salir
          </button>
        </div>
      </nav>
      <main className="container">{children}</main>
    </>
  )
}

const page = (element: ReactNode, admin = false) => (
  <RequireAuth admin={admin}>
    <Layout>{element}</Layout>
  </RequireAuth>
)

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={page(<CalendarPage />)} />
          <Route path="/search" element={page(<SearchPage />)} />
          <Route path="/mine" element={page(<MyBookingsPage />)} />
          <Route path="/admin/rooms" element={page(<AdminRoomsPage />, true)} />
          <Route path="/admin/stats" element={page(<StatsPage />, true)} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
