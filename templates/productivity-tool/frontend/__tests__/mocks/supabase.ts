/**
 * Supabase Mock Utilities
 *
 * Provides mock implementations for Supabase client operations.
 * Use these in tests to simulate database interactions without
 * connecting to a real Supabase instance.
 */

// Type definitions for mock responses
export interface MockQueryResult<T> {
  data: T | null;
  error: Error | null;
  count?: number;
}

// Mock user for auth tests
export const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  user_metadata: {
    full_name: 'Test User',
    avatar_url: 'https://example.com/avatar.jpg',
  },
  app_metadata: {},
  aud: 'authenticated',
  created_at: new Date().toISOString(),
};

// Mock session for auth tests
export const mockSession = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  token_type: 'bearer',
  user: mockUser,
};

// Mock profile record
export const mockProfile = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  avatar_url: 'https://example.com/avatar.jpg',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

// Mock customer record
export const mockCustomer = {
  id: 'customer-123',
  user_id: 'user-123',
  stripe_customer_id: 'cus_mock123',
  email: 'test@example.com',
  created_at: new Date().toISOString(),
};

// Mock lead record
export const mockLead = {
  id: 'lead-123',
  email: 'lead@example.com',
  source: 'lead-magnet',
  lead_magnet_id: 'pdf-guide',
  created_at: new Date().toISOString(),
  converted_at: null,
};

// Mock purchase record
export const mockPurchase = {
  id: 'purchase-123',
  user_id: 'user-123',
  stripe_checkout_session_id: 'cs_test_mock',
  stripe_customer_id: 'cus_mock123',
  product_id: 'prod_mock',
  amount: 7900, // cents
  currency: 'usd',
  status: 'completed',
  created_at: new Date().toISOString(),
};

/**
 * Create a mock Supabase client
 *
 * Usage:
 * ```typescript
 * const mockClient = createMockSupabaseClient();
 * mockClient.from.mockReturnValue({
 *   select: jest.fn().mockReturnValue({
 *     eq: jest.fn().mockResolvedValue({ data: [mockProfile], error: null })
 *   })
 * });
 * ```
 */
export function createMockSupabaseClient() {
  const mockFrom = jest.fn();
  const mockAuth = {
    getSession: jest.fn().mockResolvedValue({ data: { session: mockSession }, error: null }),
    getUser: jest.fn().mockResolvedValue({ data: { user: mockUser }, error: null }),
    signInWithOAuth: jest.fn().mockResolvedValue({ data: {}, error: null }),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    onAuthStateChange: jest.fn().mockReturnValue({
      data: { subscription: { unsubscribe: jest.fn() } },
    }),
  };

  return {
    from: mockFrom,
    auth: mockAuth,
    rpc: jest.fn(),
    storage: {
      from: jest.fn().mockReturnValue({
        upload: jest.fn().mockResolvedValue({ data: { path: 'test/file.pdf' }, error: null }),
        getPublicUrl: jest.fn().mockReturnValue({ data: { publicUrl: 'https://example.com/file.pdf' } }),
        createSignedUrl: jest.fn().mockResolvedValue({ data: { signedUrl: 'https://example.com/signed' }, error: null }),
      }),
    },
  };
}

/**
 * Helper to create a mock query chain
 *
 * Usage:
 * ```typescript
 * const queryChain = createMockQueryChain({ data: [mockProfile], error: null });
 * mockClient.from.mockReturnValue(queryChain);
 * ```
 */
export function createMockQueryChain<T>(result: MockQueryResult<T>) {
  const chain: Record<string, jest.Mock> = {};

  const methods = ['select', 'insert', 'update', 'delete', 'upsert', 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'is', 'in', 'contains', 'containedBy', 'range', 'textSearch', 'match', 'not', 'or', 'filter', 'order', 'limit', 'single', 'maybeSingle'];

  methods.forEach(method => {
    chain[method] = jest.fn().mockReturnValue(chain);
  });

  // Terminal methods that return the result
  chain['single'] = jest.fn().mockResolvedValue(result);
  chain['maybeSingle'] = jest.fn().mockResolvedValue(result);

  // For queries without single/maybeSingle, the chain itself resolves
  Object.defineProperty(chain, 'then', {
    value: (resolve: (value: MockQueryResult<T>) => void) => Promise.resolve(result).then(resolve),
  });

  return chain;
}

/**
 * Mock for successful database operations
 */
export const mockSuccessResponse = <T>(data: T): MockQueryResult<T> => ({
  data,
  error: null,
});

/**
 * Mock for failed database operations
 */
export const mockErrorResponse = (message: string, code?: string): MockQueryResult<null> => ({
  data: null,
  error: {
    message,
    name: 'PostgrestError',
    code: code || 'PGRST000',
  } as Error,
});
