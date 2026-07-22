import { Outlet, useLocation } from "react-router-dom"
import { useEffect } from "react"
import Header from "./Header"
import Footer from "./Footer"
import ChatWidget from "./ChatWidget"
import { useAuth } from "../hooks/useAuth"

const CHAT_WIDGET_PATHS = ["/", "/dashboard"]

export default function Layout() {
  const { pathname } = useLocation()
  const { session } = useAuth()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="bg-slate-50 text-slate-900 min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      {session && CHAT_WIDGET_PATHS.includes(pathname) && <ChatWidget />}
    </div>
  )
}
