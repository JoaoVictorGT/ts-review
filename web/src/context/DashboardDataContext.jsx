import { createContext, useEffect, useState } from "react"

export const DashboardDataContext = createContext(null)

export function DashboardDataProvider({ hotelSlug, children }) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  useEffect(() => {
    const url = `${import.meta.env.VITE_API_URL}/dashboard?hotel=${encodeURIComponent(hotelSlug)}`
    setState({ data: null, loading: true, error: null })
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`API ${res.status}`)
        return res.json()
      })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => setState({ data: null, loading: false, error }))
  }, [hotelSlug])

  return <DashboardDataContext.Provider value={state}>{children}</DashboardDataContext.Provider>
}
