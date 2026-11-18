import { useEffect, useState } from "react";

// useDebounce("Diw", 450) keeps returning the OLD value until the input has stopped changing for 450ms.
// We use it so we don't call the backend on every single keystroke.
export function useDebounce(value, delay = 450) {
  const [settled, setSettled] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay);
    return () => clearTimeout(timer); // typing again cancels the pending update
  }, [value, delay]);

  return settled;
}
