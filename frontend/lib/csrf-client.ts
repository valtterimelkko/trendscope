/**
 * CSRF Protection Utilities - Client Side
 * 
 * Client-side helpers for CSRF token handling
 */

const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'x-csrf-token';

/**
 * Client-side helper to get CSRF token from cookie
 */
export function getClientCsrfToken(): string | null {
  if (typeof document === 'undefined') {
    return null;
  }
  
  const match = document.cookie.match(new RegExp(`(^| )${CSRF_COOKIE_NAME}=([^;]+)`));
  return match ? match[2] : null;
}

/**
 * Client-side helper to make authenticated requests with CSRF token
 */
export async function fetchWithCsrf(
  url: string, 
  options: RequestInit = {}
): Promise<Response> {
  const csrfToken = getClientCsrfToken();
  
  const headers = new Headers(options.headers);
  
  if (csrfToken) {
    headers.set(CSRF_HEADER_NAME, csrfToken);
  }
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });
}

export { CSRF_COOKIE_NAME, CSRF_HEADER_NAME };
