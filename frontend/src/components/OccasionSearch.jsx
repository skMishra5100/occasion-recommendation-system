// OccasionSearch - the top of the page: headline, the labelled occasion input, the "Find gifts"
// button, and one-click suggestion chips. It holds no state of its own; App.jsx controls it.
export default function OccasionSearch({ value, onChange, onSubmit, suggestions, onPick, busy }) {
  return (
    <section aria-labelledby="page-title" className="pt-12 sm:pt-20">
      <h1
        id="page-title"
        className="font-display text-[2.6rem] leading-[1.02] font-bold tracking-tight sm:text-6xl lg:text-7xl"
      >
        What are you
        <br />
        celebrating?
      </h1>
      <p className="mt-5 max-w-xl text-lg text-muted">
        Tell us the occasion and we&rsquo;ll rank the gifts in the catalog by how well they fit.
      </p>

      <form
        role="search"
        className="mt-9 max-w-3xl"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <label htmlFor="occasion" className="mb-2 block text-base font-semibold">
          Occasion
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            id="occasion"
            name="occasion"
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Birthday, Diwali, office party…"
            autoComplete="off"
            maxLength={200}
            className="h-14 min-w-0 flex-1 rounded-2xl border-2 border-line bg-white px-5 text-lg placeholder:text-muted/70 focus:border-berry focus:outline-none sm:text-xl"
          />
          <button
            type="submit"
            className="h-14 rounded-2xl bg-berry px-8 text-lg font-semibold text-white hover:bg-berry-deep"
          >
            {busy ? "Finding…" : "Find gifts"}
          </button>
        </div>
      </form>

      {suggestions.length > 0 && (
        <div className="mt-5 flex max-w-3xl flex-wrap gap-2" role="group" aria-label="Popular occasions">
          {suggestions.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => onPick(name)}
              className="rounded-full bg-wash px-4 py-1.5 text-[0.95rem] font-medium hover:bg-berry hover:text-white"
            >
              {name}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
