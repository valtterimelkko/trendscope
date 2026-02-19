/**
 * CSRF Protection Utilities
 * 
 * Provides CSRF token generation and validation for state-changing operations.
 * Uses double-submit cookie pattern with token stored in session.
 */

import { cookies } from 'next/headers';
import { NextRequest } from 'next/server';
import crypto from 'crypto';

const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'x-csrf-token';

/**
 * Generate a cryptographically secure CSRF token
 */
export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Get or create CSRF token for the current session
 * Server-side only
 */
export async function getCsrfToken(): Promise<string> {
  const cookieStore = await cookies();
  const existingToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  
  if (existingToken) {
    return existingToken;
  }
  
  // Generate new token
  const newToken = generateCsrfToken();
  
  // Set cookie with security options
  cookieStore.set(CSRF_COOKIE_NAME, newToken, {
    httpOnly: false, // Must be accessible by JavaScript for double-submit
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 60 * 60 * 24, // 24 hours
    path: '/',
  });
  
  return newToken;
}

/**
 * Validate CSRF token from request
 * Server-side only
 */
export async function validateCsrfToken(request: NextRequest): Promise<boolean> {
  const cookieStore = await cookies();
  const cookieToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  
  // Get token from header
  const headerToken = request.headers.get(CSRF_HEADER_NAME);
  
  // Validate both tokens exist and match
  if (!cookieToken || !headerToken) {
    return false;
  }
  
  // Use timing-safe comparison
  try {
    return crypto.timingSafeEqual(
      Buffer.from(cookieToken, 'hex'),
      Buffer.from(headerToken, 'hex')
    );
  } catch {
    // Length mismatch or invalid hex
    return false;
  }
}

/**
 * Middleware to enforce CSRF protection on state-changing methods
 * Use in API routes that modify data
 */
export async function requireCsrfToken(request: NextRequest): Promise<{ valid: boolean; error?: string }> {
  // Only enforce CSRF for state-changing methods
  const stateChangingMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
  
  if (!stateChangingMethods.includes(request.method)) {
    return { valid: true };
  }
  
  const isValid = await validateCsrfToken(request);
  
  if (!isValid) {
    return { 
      valid: false, 
      error: 'Invalid or missing CSRF token' 
    };
  }
  
  return { valid: true };
}

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
