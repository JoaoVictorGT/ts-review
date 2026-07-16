import { Outlet, useLocation } from "react-router-dom"
import { useEffect } from "react"
import Header from "./Header"

export default function Layout() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="bg-slate-50 text-slate-900 min-h-screen">
      <Header />
      <main>
        <Outlet />
      </main>
    </div>
  )
}
