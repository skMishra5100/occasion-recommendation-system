// App.jsx - the one page of the app. It owns the state and decides what to show.
//
//   What the user sees, top to bottom:
//     1. Headline + occasion input + "Find gifts" button + suggestion chips   (OccasionSearch)
//     2. Below it, ONE of:  loading skeletons | error | empty message | product grid
//
//   How a search is triggered (3 ways):  press the button / Enter, click a chip, or just stop typing
//   for a moment (that last one is the "real-time" search, using a small delay called a debounce).
import { useCallback, useEffect, useState } from "react";
import { fetchOccasions } from "./api";
import { useDebounce } from "./hooks/useDebounce";
import { useRecommendations } from "./hooks/useRecommendations";
import OccasionSearch from "./components/OccasionSearch";
import ResultsHeader from "./components/ResultsHeader";
import ProductGrid, { SkeletonGrid } from "./components/ProductGrid";
import EmptyState from "./components/EmptyState";
import ErrorState from "./components/ErrorState";

const PAGE_SIZE = 12; // how many products to show at first, and how many more each "Show more" adds
const MIN_LIVE_CHARS = 2; // real-time search starts after this many characters
const FALLBACK_CHIPS = ["Birthday", "Wedding", "Diwali", "Valentine's Day", "Anniversary", "Office Party"];

// If the page is opened as /?occasion=Diwali, start with that occasion already searched.
const occasionFromUrl = () => new URLSearchParams(window.location.search).get("occasion") ?? "";

export default function App() {
  // What is currently typed in the box (changes on every keystroke).
  const [typed, setTyped] = useState(occasionFromUrl);
  // What we actually searched for (changes only when a search is triggered).
  const [search, setSearch] = useState({ query: occasionFromUrl(), limit: PAGE_SIZE });
  // The suggestion chips under the input.
  const [chips, setChips] = useState(FALLBACK_CHIPS);

  // Ask the backend for products whenever `search` changes. status = idle | loading | success | error
  const { status, data, error, retry } = useRecommendations(search);

  // On first load, get the chip names from the backend (keep the fallback list if it is not reachable).
  useEffect(() => {
    const controller = new AbortController();
    fetchOccasions(controller.signal)
      .then(({ occasions }) => {
        const featured = occasions.filter((o) => o.featured).map((o) => o.name);
        if (featured.length) setChips(featured);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  // Start a brand-new search (always back to the first page).
  const runSearch = useCallback((text) => setSearch({ query: text.trim(), limit: PAGE_SIZE }), []);

  // Real-time search: wait until the user pauses typing for 0.45s, then search.
  const pausedText = useDebounce(typed, 450);
  useEffect(() => {
    const text = pausedText.trim();
    if (text.length >= MIN_LIVE_CHARS) runSearch(text);
    else if (text === "") runSearch(""); // box was cleared
  }, [pausedText, runSearch]);

  // Keep the address bar in sync (/?occasion=Diwali) so a reload or shared link shows the same results.
  useEffect(() => {
    const url = new URL(window.location.href);
    if (search.query) url.searchParams.set("occasion", search.query);
    else url.searchParams.delete("occasion");
    window.history.replaceState(null, "", url);
  }, [search.query]);

  // Clicking a chip fills the box and searches right away.
  const pickOccasion = (name) => {
    setTyped(name);
    runSearch(name);
  };

  const loading = status === "loading";
  const hasResults = data && data.results.length > 0;

  return (
    <main className="mx-auto max-w-7xl px-5 pb-24 sm:px-8">
      <OccasionSearch
        value={typed}
        onChange={setTyped}
        onSubmit={() => runSearch(typed)}
        suggestions={chips}
        onPick={pickOccasion}
        busy={loading}
      />

      {/* Results appear right below the input, on the same page. */}
      <section className="mt-12 sm:mt-16" aria-label="Recommendations">
        {/* Nothing searched yet: show a hint. */}
        {!search.query && (
          <p className="max-w-xl text-muted">
            It understands aliases and typos too: try &ldquo;bday&rdquo;, &ldquo;diwai&rdquo; or &ldquo;my
            sister&rsquo;s engagement&rdquo;.
          </p>
        )}

        {/* The request failed. */}
        {search.query && status === "error" && <ErrorState message={error} onRetry={retry} />}

        {search.query && status !== "error" && (
          <>
            {/* We have products: show them (slightly faded while a newer search is loading). */}
            {hasResults && (
              <div className="space-y-6">
                <ResultsHeader data={data} />
                <ProductGrid products={data.results} dimmed={loading} />
                {data.returned < data.total && (
                  <div className="pt-4 text-center">
                    <button
                      type="button"
                      onClick={() => setSearch((s) => ({ ...s, limit: s.limit + PAGE_SIZE }))}
                      disabled={loading}
                      className="rounded-2xl border-2 border-ink px-7 py-3 font-semibold hover:bg-ink hover:text-white disabled:opacity-50"
                    >
                      Show more gifts
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Waiting for the first answer. */}
            {!hasResults && loading && <SkeletonGrid />}

            {/* The answer came back with zero products: the "empty state". */}
            {!hasResults && !loading && data && (
              <EmptyState query={data.query} suggestions={chips} onPick={pickOccasion} />
            )}
          </>
        )}
      </section>
    </main>
  );
}
