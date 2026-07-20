import { createContext, useState } from "react"

export const AuthContext = createContext(null)
const STORAGE_KEY = "truestay_auth"

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  })

  async function login(email, password) {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      throw new Error(res.status === 401 ? "Invalid email or password" : `API ${res.status}`)
    }
    const { hotel_slug, hotel_name } = await res.json()
    const next = { email, hotelSlug: hotel_slug, hotelName: hotel_name }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setSession(next)
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY)
    setSession(null)
  }

  return <AuthContext.Provider value={{ session, login, logout }}>{children}</AuthContext.Provider>
}
