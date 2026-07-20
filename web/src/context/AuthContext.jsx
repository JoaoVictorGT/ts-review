import { createContext, useState } from "react"
import { isTokenExpired } from "../utils/jwt"

export const AuthContext = createContext(null)
const STORAGE_KEY = "truestay_auth"

function loadStoredSession() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  const stored = JSON.parse(raw)
  if (!stored?.token || isTokenExpired(stored.token)) {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
  return stored
}

async function parseErrorMessage(res) {
  try {
    const body = await res.json()
    return body.detail || `API ${res.status}`
  } catch {
    return `API ${res.status}`
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadStoredSession)

  function storeSession(data) {
    const next = {
      token: data.token,
      email: data.email,
      hotelSlug: data.hotel_slug,
      hotelName: data.hotel_name,
      name: data.name,
      plan: data.plan,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setSession(next)
    return next
  }

  async function login(email, password) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Invalid email or password" : await parseErrorMessage(res))
    }
    return storeSession(await res.json())
  }

  async function register({ name, email, password, hotelSlug, newHotelName, plan }) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        password,
        hotel_slug: hotelSlug || null,
        new_hotel_name: newHotelName || null,
        plan: plan || null,
      }),
    })
    if (!res.ok) {
      throw new Error(res.status === 409 ? "This email is already registered" : await parseErrorMessage(res))
    }
    return storeSession(await res.json())
  }

  async function setPlan(plan) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/me/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.token}` },
      body: JSON.stringify({ plan }),
    })
    if (!res.ok) throw new Error(await parseErrorMessage(res))
    const next = { ...session, plan }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setSession(next)
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY)
    setSession(null)
  }

  return (
    <AuthContext.Provider value={{ session, login, register, setPlan, logout }}>{children}</AuthContext.Provider>
  )
}
