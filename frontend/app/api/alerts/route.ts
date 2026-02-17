import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function GET(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Parse query parameters
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');
    const dismissed = searchParams.get('dismissed');
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);
    const offset = parseInt(searchParams.get('offset') || '0');

    // Build query
    let query = supabase
      .from('alerts')
      .select(`
        id,
        user_id,
        trend_id,
        channel,
        status,
        sent_at,
        opened_at,
        clicked_at,
        dismissed,
        confidence_score,
        created_at,
        trends (
          id,
          name,
          type,
          velocity_score,
          saturation_percent,
          status
        )
      `)
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    // Apply status filter
    if (status) {
      query = query.eq('status', status);
    }

    // Apply dismissed filter
    if (dismissed !== null) {
      query = query.eq('dismissed', dismissed === 'true');
    }

    const { data: alerts, error } = await query;

    if (error) {
      console.error('Error fetching alerts:', error);
      return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 });
    }

    // Get total count
    let countQuery = supabase
      .from('alerts')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id);

    if (status) {
      countQuery = countQuery.eq('status', status);
    }

    if (dismissed !== null) {
      countQuery = countQuery.eq('dismissed', dismissed === 'true');
    }

    const { count } = await countQuery;

    // Transform data to match frontend types
    const transformedAlerts = alerts?.map(alert => ({
      id: alert.id,
      user_id: alert.user_id,
      trend_id: alert.trend_id,
      delivered_at: alert.sent_at,
      channel: alert.channel,
      status: alert.status === 'delivered' ? 'sent' : alert.status,
      created_at: alert.created_at,
      trend: alert.trends
    })) || [];

    return NextResponse.json({
      alerts: transformedAlerts,
      total: count || 0
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
