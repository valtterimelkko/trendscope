import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { validateUuid } from '@/lib/utils';

// Tier limits for client management
const TIER_CLIENT_LIMITS: Record<string, number> = {
  free: 0,
  solo: 0,
  agency: 5,
  enterprise: 20
};

// Helper to check if user can manage clients
async function canManageClients(supabase: Awaited<ReturnType<typeof createClient>>, userId: string): Promise<boolean> {
  const { data: profile } = await supabase
    .from('profiles')
    .select('tier')
    .eq('id', userId)
    .single();

  const tier = profile?.tier || 'free';
  return (TIER_CLIENT_LIMITS[tier] || 0) > 0;
}

// GET - Get client workspace details
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check tier access
    const hasAccess = await canManageClients(supabase, user.id);
    if (!hasAccess) {
      return NextResponse.json({
        error: 'Client management requires Agency tier or higher'
      }, { status: 403 });
    }

    const { id } = await params;

    // Validate UUID format
    const uuidCheck = validateUuid(id, 'Client ID');
    if (!uuidCheck.valid) {
      return NextResponse.json({ error: uuidCheck.error }, { status: 400 });
    }

    // Fetch client (RLS ensures agency owns it)
    const { data: client, error } = await supabase
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
      .eq('id', id)
      .eq('agency_id', user.id)
      .single();

    if (error || !client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }

    // Fetch client's alert integrations through client_alerts
    const { data: clientAlerts } = await supabase
      .from('client_alerts')
      .select(`
        id,
        niche_filter,
        alert_integrations (
          id,
          type,
          name,
          is_active
        )
      `)
      .eq('client_id', id);

    // Get recent trends for client's niches
    const clientNiches = client.config?.niches || [];
    let recentTrends: Array<{ id: string; name: string; velocity_score: number }> = [];

    if (clientNiches.length > 0) {
      const { data: trends } = await supabase
        .from('trends')
        .select('id, name, velocity_score')
        .in('niche_id', clientNiches)
        .order('velocity_score', { ascending: false })
        .limit(5);

      recentTrends = trends || [];
    }

    // Type for the joined alert_integrations data
    type AlertIntegration = { id: string; type: string; name: string; is_active: boolean };

    return NextResponse.json({
      ...client,
      alert_integrations: clientAlerts?.map(ca => {
        // alert_integrations could be an object or array, normalize
        const integration = ca.alert_integrations as AlertIntegration | AlertIntegration[] | null;
        const int = Array.isArray(integration) ? integration[0] : integration;
        return {
          id: int?.id,
          type: int?.type,
          name: int?.name,
          is_active: int?.is_active
        };
      }) || [],
      recent_trends: recentTrends
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// PUT - Update client workspace
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check tier access
    const hasAccess = await canManageClients(supabase, user.id);
    if (!hasAccess) {
      return NextResponse.json({
        error: 'Client management requires Agency tier or higher'
      }, { status: 403 });
    }

    const { id } = await params;

    // Validate UUID format
    const uuidCheck = validateUuid(id, 'Client ID');
    if (!uuidCheck.valid) {
      return NextResponse.json({ error: uuidCheck.error }, { status: 400 });
    }

    const body = await request.json();
    const { name, logo_url, config, is_active } = body;

    // Build updates object
    const updates: Record<string, unknown> = {};
    if (name !== undefined) {
      if (typeof name !== 'string' || name.trim().length === 0) {
        return NextResponse.json({ error: 'name must be a non-empty string' }, { status: 400 });
      }
      if (name.length > 100) {
        return NextResponse.json({ error: 'name must be 100 characters or less' }, { status: 400 });
      }
      updates.name = name.trim();
    }
    if (logo_url !== undefined) {
      if (logo_url) {
        try {
          new URL(logo_url);
        } catch {
          return NextResponse.json({ error: 'Invalid logo_url format' }, { status: 400 });
        }
      }
      updates.logo_url = logo_url;
    }
    if (config !== undefined) {
      updates.config = config;
    }
    if (is_active !== undefined) {
      updates.is_active = is_active;
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ error: 'No fields to update' }, { status: 400 });
    }

    // Update client (RLS ensures agency owns it)
    const { data: client, error } = await supabase
      .from('clients')
      .update(updates)
      .eq('id', id)
      .eq('agency_id', user.id)
      .select()
      .single();

    if (error) {
      console.error('Error updating client:', error);
      return NextResponse.json({ error: 'Failed to update client' }, { status: 500 });
    }

    if (!client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 });
    }

    return NextResponse.json(client);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE - Delete client workspace
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check tier access
    const hasAccess = await canManageClients(supabase, user.id);
    if (!hasAccess) {
      return NextResponse.json({
        error: 'Client management requires Agency tier or higher'
      }, { status: 403 });
    }

    const { id } = await params;

    // Validate UUID format
    const uuidCheck = validateUuid(id, 'Client ID');
    if (!uuidCheck.valid) {
      return NextResponse.json({ error: uuidCheck.error }, { status: 400 });
    }

    // Delete client (cascades to client_alerts, RLS ensures agency owns it)
    const { error } = await supabase
      .from('clients')
      .delete()
      .eq('id', id)
      .eq('agency_id', user.id);

    if (error) {
      console.error('Error deleting client:', error);
      return NextResponse.json({ error: 'Failed to delete client' }, { status: 500 });
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
