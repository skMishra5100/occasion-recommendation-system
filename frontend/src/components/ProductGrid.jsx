// ProductGrid - lays the product cards out in a responsive grid (1 column on phones, up to 4 on wide screens).
// SkeletonGrid is the grey placeholder grid shown while the first results are loading.
import ProductCard from "./ProductCard";

const grid = "grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4";

export function SkeletonGrid() {
  return (
    <ul className={grid} aria-hidden="true">
      {Array.from({ length: 8 }, (_, i) => (
        <li key={i} className="animate-pulse overflow-hidden rounded-2xl border border-line bg-white">
          <div className="aspect-[4/3] bg-wash" />
          <div className="space-y-3 p-5">
            <div className="h-3 w-1/3 rounded bg-wash" />
            <div className="h-5 w-3/4 rounded bg-wash" />
            <div className="h-3 w-full rounded bg-wash" />
            <div className="h-3 w-5/6 rounded bg-wash" />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function ProductGrid({ products, dimmed }) {
  return (
    <ul className={`${grid} transition-opacity ${dimmed ? "opacity-50" : ""}`} aria-busy={dimmed}>
      {products.map((p) => (
        <li key={p.product_id}>
          <ProductCard product={p} />
        </li>
      ))}
    </ul>
  );
}
