// api.js - the only file that talks to the backend. Everything else just calls these two functions.
// In development Vite forwards "/api/..." to FastAPI on port 8000 (see vite.config.js).
// For a production build, set VITE_API_BASE to the backend URL.
const BASE = import.meta.env.VITE_API_BASE || "";

async function getJson(path, params, signal) {
  const qs = params ? "?" + new URLSearchParams(params) : "";
  let res;
  try {
    res = await fetch(`${BASE}${path}${qs}`, { signal });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new Error("Can't reach the recommendation service.");
  }
  if (!res.ok) throw new Error(`The recommendation service returned an error (${res.status}).`);
  return res.json();
}

export const fetchRecommendations = (occasion, limit, signal) =>
  getJson("/api/recommendations", { occasion, limit }, signal);

export const fetchOccasions = (signal) => getJson("/api/occasions", null, signal);
