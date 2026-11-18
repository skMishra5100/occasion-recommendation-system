// ErrorState - shown when the request to the backend fails (e.g. the server is not running).
export default function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-2xl border border-berry/30 bg-white px-6 py-10 text-center" role="alert">
      <h2 className="font-display text-2xl font-semibold">We couldn&rsquo;t load recommendations</h2>
      <p className="mx-auto mt-3 max-w-md text-muted">
        {message} Check that the backend is running on port 8000, then try again.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-6 rounded-2xl bg-berry px-6 py-3 font-semibold text-white hover:bg-berry-deep"
      >
        Try again
      </button>
    </div>
  );
}
