// EmptyState - shown when the backend finds no matching products. Suggests occasions to try instead.
export default function EmptyState({ query, suggestions, onPick }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-white px-6 py-12 text-center sm:py-16" role="status">
      <h2 className="font-display text-2xl font-semibold sm:text-3xl">
        Nothing in the catalog fits &ldquo;{query}&rdquo;
      </h2>
      <p className="mx-auto mt-3 max-w-md text-muted">
        Check the spelling, or try a more common occasion such as one of these.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {suggestions.slice(0, 6).map((name) => (
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
    </div>
  );
}
