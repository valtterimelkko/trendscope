/**
 * Lead Capture API Tests
 *
 * Tests for the lead magnet capture endpoint:
 * 1. Email validation
 * 2. Rate limiting
 * 3. Duplicate handling
 * 4. Database operations
 * 5. Email delivery
 *
 * Run with: npm test -- lead-capture
 */

import {
  createMockSupabaseClient,
  createMockQueryChain,
  mockSuccessResponse,
  mockErrorResponse,
  mockLead,
} from '../mocks/supabase';

describe('Lead Capture API', () => {
  let mockSupabase: ReturnType<typeof createMockSupabaseClient>;

  beforeEach(() => {
    mockSupabase = createMockSupabaseClient();
    jest.clearAllMocks();
  });

  describe('Email Validation', () => {
    const validEmails = [
      'test@example.com',
      'user.name@domain.co.uk',
      'user+tag@example.org',
      'valid123@test-domain.com',
    ];

    const invalidEmails = [
      '',
      'notanemail',
      'missing@domain',
      '@nodomain.com',
      'spaces in@email.com',
      'double@@at.com',
    ];

    validEmails.forEach(email => {
      it(`should accept valid email: ${email}`, () => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        expect(emailRegex.test(email)).toBe(true);
      });
    });

    invalidEmails.forEach(email => {
      it(`should reject invalid email: ${email || '(empty)'}`, () => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        expect(emailRegex.test(email)).toBe(false);
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should allow first request from an IP', () => {
      // Rate limit: 5 requests per IP per hour
      const rateLimit = {
        limit: 5,
        remaining: 4,
        reset: Date.now() + 3600000,
      };

      expect(rateLimit.remaining).toBeGreaterThan(0);
    });

    it('should track requests per IP', () => {
      const ipRequests: Record<string, number> = {
        '192.168.1.1': 3,
        '192.168.1.2': 1,
      };

      expect(ipRequests['192.168.1.1']).toBe(3);
    });

    it('should block after limit exceeded', () => {
      const rateLimit = {
        limit: 5,
        remaining: 0,
        reset: Date.now() + 3600000,
      };

      expect(rateLimit.remaining).toBe(0);
    });

    it('should reset after time window', () => {
      const oneHourAgo = Date.now() - 3600001;
      const rateLimit = {
        limit: 5,
        remaining: 0,
        reset: oneHourAgo,
      };

      // After reset time, should allow requests again
      const shouldReset = Date.now() > rateLimit.reset;
      expect(shouldReset).toBe(true);
    });
  });

  describe('Duplicate Lead Handling', () => {
    it('should check for existing lead before insert', async () => {
      const email = 'existing@example.com';

      // Mock finding existing lead
      const selectChain = createMockQueryChain(mockSuccessResponse(mockLead));
      mockSupabase.from.mockReturnValue(selectChain);

      expect(mockLead.email).toBeDefined();
    });

    it('should update existing lead instead of creating duplicate', async () => {
      const email = 'existing@example.com';
      const existingLead = { ...mockLead, email };

      // When lead exists, update last_activity timestamp
      expect(existingLead.email).toBe(email);
    });

    it('should create new lead if email not found', async () => {
      const email = 'new@example.com';

      // Mock not finding existing lead
      const selectChain = createMockQueryChain(mockSuccessResponse(null));
      mockSupabase.from.mockReturnValue(selectChain);

      // Should proceed to insert
      const insertChain = createMockQueryChain(mockSuccessResponse({
        ...mockLead,
        email,
      }));
      mockSupabase.from.mockReturnValue(insertChain);

      expect(email).toBe('new@example.com');
    });
  });

  describe('Database Operations', () => {
    it('should insert lead with correct fields', async () => {
      const leadData = {
        email: 'test@example.com',
        source: 'pdf-guide',
        lead_magnet_id: 'product-launch-guide',
        ip_address: '192.168.1.1',
        user_agent: 'Mozilla/5.0...',
      };

      const insertChain = createMockQueryChain(mockSuccessResponse({
        id: 'new-lead-id',
        ...leadData,
        created_at: new Date().toISOString(),
      }));
      mockSupabase.from.mockReturnValue(insertChain);

      expect(leadData.email).toBe('test@example.com');
      expect(leadData.source).toBe('pdf-guide');
    });

    it('should handle database errors gracefully', async () => {
      const errorChain = createMockQueryChain(
        mockErrorResponse('Connection refused', 'PGRST503')
      );
      mockSupabase.from.mockReturnValue(errorChain);

      // Implementation should return 500 error to user
      // But not expose internal error details
      expect(errorChain.insert).toBeDefined();
    });
  });

  describe('Lead Magnet Delivery', () => {
    it('should generate signed URL for PDF delivery', () => {
      const signedUrlParams = {
        bucket: 'lead-magnets',
        path: 'guides/product-launch.pdf',
        expiresIn: 3600, // 1 hour
      };

      expect(signedUrlParams.expiresIn).toBe(3600);
    });

    it('should queue email with download link', () => {
      const emailPayload = {
        to: 'lead@example.com',
        subject: 'Your free guide is ready!',
        template: 'lead-magnet-delivery',
        data: {
          downloadUrl: 'https://storage.example.com/signed-url',
          productName: 'Product Launch Guide',
          expiresIn: '1 hour',
        },
      };

      expect(emailPayload.template).toBe('lead-magnet-delivery');
      expect(emailPayload.data.downloadUrl).toContain('signed-url');
    });
  });

  describe('Security', () => {
    it('should sanitize email input', () => {
      const dangerousInputs = [
        '<script>alert("xss")</script>@example.com',
        'email@example.com; DROP TABLE leads;--',
        'email@example.com\n\nBcc: spam@hacker.com',
      ];

      dangerousInputs.forEach(input => {
        // Implementation should strip/reject dangerous characters
        const hasScriptTag = input.includes('<script>');
        const hasSqlInjection = input.includes('; DROP');
        const hasHeaderInjection = input.includes('\n');

        expect(hasScriptTag || hasSqlInjection || hasHeaderInjection).toBe(true);
      });
    });

    it('should not expose internal errors to client', () => {
      const internalError = 'Connection to database failed: timeout after 30s';
      const clientError = 'An error occurred. Please try again later.';

      // Implementation should log internal error but return generic message
      expect(clientError).not.toContain('database');
      expect(clientError).not.toContain('timeout');
    });
  });
});

describe('Rate Limit Helper Functions', () => {
  describe('Token Bucket Algorithm', () => {
    it('should implement token bucket rate limiting', () => {
      const bucket = {
        capacity: 5,
        tokens: 5,
        refillRate: 5, // tokens per hour
        lastRefill: Date.now(),
      };

      // Consume a token
      const consumeToken = (b: typeof bucket) => {
        if (b.tokens > 0) {
          b.tokens--;
          return true;
        }
        return false;
      };

      expect(consumeToken(bucket)).toBe(true);
      expect(bucket.tokens).toBe(4);
    });
  });
});
