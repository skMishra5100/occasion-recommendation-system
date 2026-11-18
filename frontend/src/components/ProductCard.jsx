// ProductCard - one product in the results grid: image, category, title, description snippet,
// "why it matched" chips, price, and a match-strength bar.
import { useState } from "react";

// Formats 3499 as "₹3,499" (Indian number style).
const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

// The product picture. If it is missing or fails to load, show a coloured block with the first letter instead.
function Image({ src, alt }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div
        className="flex aspect-[4/3] w-full items-center justify-center bg-wash font-display text-6xl font-bold text-berry/40"
        role="img"
        aria-label={`${alt} (no image available)`}
      >
        {alt.charAt(0).toUpperCase()}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className="aspect-[4/3] w-full bg-wash object-cover"
    />
  );
}

// Shows the price; if there is a discount, also the old price (struck through) and "x% off".
function Price({ price, finalPrice, discount }) {
  if (price == null) return null;
  const discounted = finalPrice != null && finalPrice < price;
  return (
    <p className="flex items-baseline gap-2">
      <span className="font-display text-xl font-semibold">{inr.format(discounted ? finalPrice : price)}</span>
      {discounted && (
        <>
          <span className="text-sm text-muted line-through">{inr.format(price)}</span>
          <span className="text-sm font-semibold text-berry">{Math.round(discount)}% off</span>
        </>
      )}
    </p>
  );
}

export default function ProductCard({ product: p }) {
  // relevance is 0..1 compared with the best result; show it as a percentage.
  const pct = Math.round(p.relevance * 100);
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-white">
      <Image src={p.image} alt={p.title} />

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div>
          {p.vendor_category_desc && <p className="text-sm text-muted">{p.vendor_category_desc}</p>}
          <h3 className="mt-0.5 font-display text-xl font-semibold leading-snug">{p.title}</h3>
        </div>

        <p className="line-clamp-3 text-[0.95rem] leading-relaxed text-ink/80">
          {p.snippet || "No description provided."}
        </p>

        {p.reasons.length > 0 && (
          <ul className="flex flex-wrap gap-1.5" aria-label="Why this was recommended">
            {p.reasons.slice(0, 2).map((r) => (
              <li key={r} className="rounded-full bg-wash px-2.5 py-1 text-xs font-medium">
                {r}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-auto flex flex-col gap-3 pt-2">
          <Price price={p.price} finalPrice={p.final_price} discount={p.discount_percentage} />
          <div className="flex items-center gap-3">
            <div
              className="h-2 flex-1 overflow-hidden rounded-full bg-wash"
              role="meter"
              aria-label="Match strength"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={pct}
            >
              <div className="h-full rounded-full bg-marigold" style={{ width: `${pct}%` }} />
            </div>
            <span className="w-16 text-right text-sm font-semibold tabular-nums">{pct}% match</span>
          </div>
        </div>
      </div>
    </article>
  );
}
