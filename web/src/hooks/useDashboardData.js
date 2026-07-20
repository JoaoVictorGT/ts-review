import { useContext } from "react"
import { DashboardDataContext } from "../context/DashboardDataContext"

export function useDashboardData() {
  const ctx = useContext(DashboardDataContext)
  if (!ctx) throw new Error("useDashboardData must be used within DashboardDataProvider")
  return ctx
}
