'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { getClientCsrfToken } from '@/lib/csrf';

interface CsrfContextType {
  token: string | null;
  isReady: boolean;
}

const CsrfContext = createContext<CsrfContextType>({
  token: null,
  isReady: false,
});

export function useCsrf() {
  return useContext(CsrfContext);
}

/**
 * CSRF Provider Component
 * 
 * Ensures CSRF token is available for all child components.
 * Fetches token from cookie on mount.
 */
export function CsrfProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Get token from cookie
    const csrfToken = getClientCsrfToken();
    setToken(csrfToken);
    setIsReady(true);
  }, []);

  return (
    <CsrfContext.Provider value={{ token, isReady }}>
      {children}
    </CsrfContext.Provider>
  );
}

/**
 * Hook for making CSRF-protected requests
 */
export function useCsrfFetch() {
  const { token, isReady } = useCsrf();

  const csrfFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
    if (!isReady || !token) {
      throw new Error('CSRF token not available');
    }

    const headers = new Headers(options.headers);
    headers.set('x-csrf-token', token);

    return fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin',
    });
  };

  return { csrfFetch, isReady, token };
}
