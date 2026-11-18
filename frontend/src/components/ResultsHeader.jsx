// ResultsHeader - the line above the grid. It tells the user how we understood what they typed,
// and how many products matched.

// The sentence depends on how the backend matched the text (resolved_occasion.match_type):
//   "keyword" -> it contained a known occasion name or alias   ("bday" -> Birthday)
//   "typo"    -> it looked like a misspelling of one            ("diwai" -> Diwali)
//   "meaning" -> it was close in meaning to one                 ("festival of colours" -> Holi)
//   no occasion found -> we searched the catalog for the raw words
function Understood({ data }) {
  const { query, resolved_occasion: occasion } = data;

  if (!occasion) {
    return (
      <>
        Searching the catalog for <strong className="font-semibold">&ldquo;{query}&rdquo;</strong>.
      </>
    );
  }

  const name = <strong className="font-semibold">{occasion.name}</strong>;

  if (occasion.match_type === "meaning") {
    return (
      <>
        Showing gifts for {name}, the closest occasion we know to &ldquo;{query}&rdquo;.
      </>
    );
  }

  // They typed exactly the occasion name: keep it short. Otherwise say how we read it.
  const typedExactly = query.trim().toLowerCase() === occasion.name.toLowerCase();
  return typedExactly ? (
    <>Gifts for {name}.</>
  ) : (
    <>
      Gifts for {name}. We read &ldquo;{query}&rdquo; as {occasion.name}.
    </>
  );
}

export default function ResultsHeader({ data }) {
  return (
    <div className="flex flex-col gap-1 border-b border-line pb-5 sm:flex-row sm:items-baseline sm:justify-between">
      <h2 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
        <Understood data={data} />
      </h2>
      <p className="text-muted" aria-live="polite">
        {data.total} {data.total === 1 ? "match" : "matches"}, showing {data.returned}
      </p>
    </div>
  );
}
