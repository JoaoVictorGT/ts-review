import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

export default function RequireGuest() {
  const { session } = useAuth()
  return session ? <Navigate to="/dashboard" replace /> : <Outlet />
}
