import { useState } from "react"

export default function HotelDot({ hotel, onOpen }) {
  const [hovered, setHovered] = useState(false)
  const size = hovered ? 16 : 12

  return (
    <button
      type="button"
      className="absolute rounded-full bg-blue-600 ring-4 ring-white shadow-md transition-all"
      style={{
        left: `${hotel.x}%`,
        top: `${hotel.y}%`,
        width: size,
        height: size,
        transform: "translate(-50%, -50%)",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onOpen(hotel.id)}
      aria-label={hotel.name}
    >
      {hovered && (
        <span className="absolute left-1/2 -translate-x-1/2 -top-8 whitespace-nowrap bg-slate-900 text-white text-xs rounded-md px-2 py-1">
          {hotel.name}
        </span>
      )}
    </button>
  )
}
