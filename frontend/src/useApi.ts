import { useEffect, useState } from "react";

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Tiny data-fetching hook to avoid pulling in a query library this early.
export function useApi<T>(fetcher: () => Promise<T>): State<T> {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    fetcher()
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch(
        (e) =>
          active &&
          setState({ data: null, loading: false, error: String(e.message ?? e) })
      );
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return state;
}
