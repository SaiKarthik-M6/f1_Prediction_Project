import { API_BASE } from "./config"

// Reads the error message out of an API response that is not OK
async function apiError(res) {
  try {
    const body = await res.json()
    return body.detail || body.error || `Request failed (${res.status})`
  } catch {
    return `Prediction service returned ${res.status}`
  }
}

async function request(path, options) {
  let res
  try {
    res = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new Error("Failed to reach prediction service.")
  }
  if (!res.ok) throw new Error(await apiError(res))
  return res.json()
}

const post = (path, body = {}) =>
  request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

// Next race, expected lineup, and how current the data is
export const getNextRace = () => request("/race/next")

// Ask the server to check for new results now
export const refreshData = () => post("/refresh")

// Predictions are always for the next race. Qualifying data is used
// automatically once it is available.
export const predictRaceOrder = () => post("/predict/race-order")
export const predictDriver = (driverRef) => post("/predict/winner", { driver: driverRef })
