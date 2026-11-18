import { useCallback, useEffect, useState } from "react";
import { fetchRecommendations } from "../api";

// useRecommendations({ query, limit }) calls the backend whenever the query or limit changes.
// It returns:  status ("idle" | "loading" | "success" | "error"), data, error, retry()
export function useRecommendations({ query, limit }) {
  const [state, setState] = useState({ status: "idle", data: null, error: null });
  const [attempt, setAttempt] = useState(0); // bumping this re-runs the request (used by "Try again")

  useEffect(() => {
    const text = query.trim();
    if (!text) {
      setState({ status: "idle", data: null, error: null });
      return;
    }

    // If the user searches again before this request finishes, we cancel it, so an old slow
    // answer can never overwrite a newer one.
    const controller = new AbortController();

    // Keep the previous data on screen while loading (so the page doesn't flash empty).
    setState((old) => ({ ...old, status: "loading", error: null }));

    fetchRecommendations(text, limit, controller.signal)
      .then((data) => setState({ status: "success", data, error: null }))
      .catch((err) => {
        if (err.name === "AbortError") return; // we cancelled it on purpose, not a real error
        setState((old) => ({ ...old, status: "error", error: err.message }));
      });

    return () => controller.abort();
  }, [query, limit, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, retry };
}
