// Decodes a JWT's payload client-side (base64url + JSON) — no signature
// verification here, that's the backend's job on every protected request.
// This is only used to read claims (hotel name, expiry) for UI purposes.
export function decodeJwtPayload(token) {
  try {
    const payload = token.split(".")[1]
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/")
    const json = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join(""),
    )
    return JSON.parse(json)
  } catch {
    return null
  }
}

export function isTokenExpired(token) {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true
  return Date.now() >= payload.exp * 1000
}
