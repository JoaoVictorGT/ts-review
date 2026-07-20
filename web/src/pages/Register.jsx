import { useState, useEffect, useRef } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { Mail, Lock, User, Search } from "lucide-react"
import Logo from "../components/Logo"
import { useAuth } from "../hooks/useAuth"

export default function Register() {
  const [searchParams] = useSearchParams()
  const fromPricing = searchParams.get("from") === "pricing"
  const navigate = useNavigate()
  const { register } = useAuth()

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const [hotelQuery, setHotelQuery] = useState("")
  const [hotelResults, setHotelResults] = useState([])
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [newHotelName, setNewHotelName] = useState("")
  const debounceRef = useRef(null)

  useEffect(() => {
    if (!hotelQuery.trim() || selectedHotel) {
      setHotelResults([])
      return
    }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/hotels/search?q=${encodeURIComponent(hotelQuery)}`)
        if (res.ok) setHotelResults(await res.json())
      } catch {
        setHotelResults([])
      }
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [hotelQuery, selectedHotel])

  function pickHotel(hotel) {
    setSelectedHotel(hotel)
    setHotelQuery(hotel.hotel_name)
    setHotelResults([])
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)

    if (!selectedHotel && !notFound) {
      setError("Please select your hotel, or tell us it's not listed.")
      return
    }
    if (notFound && !newHotelName.trim()) {
      setError("Please enter your business name.")
      return
    }

    setSubmitting(true)
    try {
      await register({
        name,
        email,
        password,
        hotelSlug: selectedHotel?.hotel_slug,
        newHotelName: notFound ? newHotelName.trim() : undefined,
        plan: fromPricing ? "starter" : undefined,
      })
      navigate(fromPricing ? "/dashboard" : "/pricing")
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="min-h-[640px] grid md:grid-cols-2">
      <div className="relative bg-slate-900 hidden md:flex flex-col justify-between p-12 overflow-hidden">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, #38bdf8 0%, transparent 40%), radial-gradient(circle at 80% 70%, #2563eb 0%, transparent 45%)",
          }}
        />
        <div className="relative">
          <Logo light />
        </div>
        <div className="relative">
          <p className="text-2xl text-white leading-snug max-w-sm">
            Access the world's largest hotel intelligence platform.
          </p>
          <p className="text-sm text-blue-200 mt-4">Verified reviews. Trusted stays.</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-10">
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold text-slate-900 mb-1">Create your account</h1>
          <p className="text-sm text-slate-500 mb-8">
            {fromPricing ? "Starting on the free Starter plan." : "Set up your TrueStay account."}
          </p>
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm px-3 py-2">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="text-xs font-medium text-slate-600">
                Your name
              </label>
              <div className="mt-1 relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  required
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <div>
              <label htmlFor="email" className="text-xs font-medium text-slate-600">
                Corporate email
              </label>
              <div className="mt-1 relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="text-xs font-medium text-slate-600">
                Password
              </label>
              <div className="mt-1 relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  minLength={8}
                  required
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>

            {!notFound ? (
              <div>
                <label htmlFor="hotel" className="text-xs font-medium text-slate-600">
                  Your hotel
                </label>
                <div className="mt-1 relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="hotel"
                    type="text"
                    value={hotelQuery}
                    onChange={(e) => {
                      setHotelQuery(e.target.value)
                      setSelectedHotel(null)
                    }}
                    placeholder="Search by hotel name..."
                    className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                  />
                  {hotelResults.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-md max-h-48 overflow-y-auto">
                      {hotelResults.map((h) => (
                        <button
                          key={h.hotel_slug}
                          type="button"
                          onClick={() => pickHotel(h)}
                          className="block w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                        >
                          {h.hotel_name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setNotFound(true)
                    setSelectedHotel(null)
                    setHotelQuery("")
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800 mt-1.5"
                >
                  I can't find my hotel
                </button>
              </div>
            ) : (
              <div>
                <label htmlFor="newHotel" className="text-xs font-medium text-slate-600">
                  Business name
                </label>
                <input
                  id="newHotel"
                  type="text"
                  value={newHotelName}
                  onChange={(e) => setNewHotelName(e.target.value)}
                  placeholder="Your hotel's name"
                  className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
                <button
                  type="button"
                  onClick={() => setNotFound(false)}
                  className="text-xs text-blue-600 hover:text-blue-800 mt-1.5"
                >
                  Search existing hotels instead
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-gradient-to-r from-sky-400 to-blue-600 text-white text-sm font-medium rounded-lg py-2.5 shadow-sm hover:shadow-md transition-shadow disabled:opacity-50"
            >
              {submitting ? "Creating account..." : "Create account"}
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
