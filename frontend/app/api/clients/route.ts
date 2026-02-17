import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// Tier limits for client management
const TIER_CLIENT_LIMITS: Record<string, number> = {
  free: 0,
  solo: 0,
  agency: 5,
  enterprise: 20
};

// Helper to check if user can manage clients
async function canManageClients(supabase: Awaited<ReturnType<typeof createClient>>, userId: string): Promise<{ allowed: boolean; maxAllowed: number; tier: string }> {
  const { data: profile } = await supabase
    .from('profiles')
    .select('tier')
    .eq('id', userId)
    .single();

  const tier = profile?.tier || 'free';
  const maxAllowed = TIER_CLIENT_LIMITS[tier] || 0;

  return { allowed: maxAllowed > 0, maxAllowed, tier };
}

// GET - List agency's client workspaces
export async function GET(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check tier access
    const { allowed, maxAllowed } = await canManageClients(supabase, user.id);

    if (!allowed) {
      return NextResponse.json({
        error: 'Client management requires Agency tier or higher'
      }, { status: 403 });
    }

    // Parse query parameters
    const { searchParams } = new URL(request.url);
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);
    const offset = parseInt(searchParams.get('offset') || '0');
    const isActive = searchParams.get('is_active');

    // Build query
    let query = supabase
      .from('clients')
      .select(`
        id,
        agency_id,
        name,
        logo_url,
        config,
        is_active,
        created_at,
        updated_at
      `)
      .eq('agency_id', user.id)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (isActive !== null) {
      query = query.eq('is_active', isActive === 'true');
    }

    const { data: clients, error } = await query;

    if (error) {
      console.error('Error fetching clients:', error);
      return NextResponse.json({ error: 'Failed to fetch clients' }, { status: 500 });
    }

    // Get total count
    let countQuery = supabase
      .from('clients')
      .select('*', { count: 'exact', head: true })
      .eq('agency_id', user.id);

    if (isActive !== null) {
      countQuery = countQuery.eq('is_active', isActive === 'true');
    }

    const { count } = await countQuery;

    return NextResponse.json({
      clients: clients || [],
      total: count || 0,
      max_allowed: maxAllowed
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST - Create a client workspace
export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check tier access
    const { allowed, maxAllowed } = await canManageClients(supabase, user.id);

    if (!allowed) {
      return NextResponse.json({
        error: 'Client management requires Agency tier or higher'
      }, { status: 403 });
    }

    const body = await request.json();
    const { name, logo_url, config } = body;

    // Validate required fields
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return NextResponse.json({ error: 'name is required' }, { status: 400 });
    }

    if (name.length > 100) {
      return NextResponse.json({ error: 'name must be 100 characters or less' }, { status: 400 });
    }

    // Validate logo_url if provided
    if (logo_url) {
      try {
        new URL(logo_url);
      } catch {
        return NextResponse.json({ error: 'Invalid logo_url format' }, { status: 400 });
      }
    }

    // Check current client count
    const { count } = await supabase
      .from('clients')
      .select('*', { count: 'exact', head: true })
      .eq('agency_id', user.id);

    if ((count || 0) >= maxAllowed) {
      return NextResponse.json({
        error: `Maximum clients reached for your tier (${maxAllowed}). Please upgrade to add more.`
      }, { status: 400 });
    }

    // Create client
    const { data: client, error: insertError } = await supabase
      .from('clients')
      .insert({
        agency_id: user.id,
        name: name.trim(),
        logo_url: logo_url || null,
        config: config || {},
        is_active: true
      })
      .select()
      .single();

    if (insertError) {
      console.error('Error creating client:', insertError);
      return NextResponse.json({ error: 'Failed to create client' }, { status: 500 });
    }

    return NextResponse.json(client, { status: 201 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
