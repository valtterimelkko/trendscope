import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

/**
 * Add security headers to response
 */
function addSecurityHeaders(response: NextResponse): NextResponse {
  // Prevent clickjacking
  response.headers.set('X-Frame-Options', 'DENY');
  // Prevent MIME type sniffing
  response.headers.set('X-Content-Type-Options', 'nosniff');
  // Enable XSS filter in browsers
  response.headers.set('X-XSS-Protection', '1; mode=block');
  // Control referrer information
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  // Strict CSP - removes unsafe-inline and unsafe-eval for better security
  // Note: If Next.js requires these for development, they can be added conditionally
  const isDev = process.env.NODE_ENV === 'development';
  const scriptSrc = isDev 
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval'" 
    : "script-src 'self'";
  
  response.headers.set(
    'Content-Security-Policy',
    `default-src 'self'; ${scriptSrc}; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.supabase.co https://api.stripe.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self';`
  );
  // Prevent sending referrer to other origins
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  return response;
}

export async function middleware(request: NextRequest) {
  // TEMPORARY: Allow all access without authentication for preview/demo
  // This bypasses Supabase auth checks since backend is not yet set up
  const bypassAuth = !process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  if (bypassAuth) {
    const response = NextResponse.next();
    return addSecurityHeaders(response);
  }

  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: { name: string; value: string; options?: any }[]) {
          cookiesToSet.forEach(({ name, value }) => {
            request.cookies.set(name, value);
          });
          supabaseResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Protect /app routes
  if (request.nextUrl.pathname.startsWith('/app') && !session) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = '/auth/login';
    redirectUrl.searchParams.set('redirectTo', request.nextUrl.pathname);
    return addSecurityHeaders(NextResponse.redirect(redirectUrl));
  }

  // Redirect to dashboard if already logged in and trying to access auth pages
  if (
    (request.nextUrl.pathname.startsWith('/auth/login') ||
      request.nextUrl.pathname.startsWith('/auth/signup')) &&
    session
  ) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = '/app';
    return addSecurityHeaders(NextResponse.redirect(redirectUrl));
  }

  return addSecurityHeaders(supabaseResponse);
}

export const config = {
  matcher: ['/app/:path*', '/auth/:path*'],
};
