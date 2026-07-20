import { createContext, useEffect, useState } from "react"

export const DashboardDataContext = createContext(null)

export function DashboardDataProvider({ token, children }) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  useEffect(() => {
    setState({ data: null, loading: true, error: null })
    fetch(`${import.meta.env.VITE_API_URL}/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`API ${res.status}`)
        return res.json()
      })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => setState({ data: null, loading: false, error }))
  }, [token])

  return <DashboardDataContext.Provider value={state}>{children}</DashboardDataContext.Provider>
}
