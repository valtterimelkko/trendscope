import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// GET - Get alert statistics for the current user
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
    const period = searchParams.get('period') || 'week';

    // Calculate date ranges
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Get total alerts this week
    const { count: totalThisWeek } = await supabase
      .from('alerts')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .gte('created_at', weekAgo.toISOString());

    // Get total alerts this month
    const { count: totalThisMonth } = await supabase
      .from('alerts')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .gte('created_at', monthAgo.toISOString());

    // Get alerts by niche (through trends)
    const { data: alertsByNiche } = await supabase
      .from('alerts')
      .select(`
        trend_id,
        trends (
          niche_id,
          niches (
            id,
            name
          )
        )
      `)
      .eq('user_id', user.id)
      .gte('created_at', (period === 'week' ? weekAgo : monthAgo).toISOString());

    // Aggregate by niche
    const nicheCounts = new Map<string, { niche_id: string; niche_name: string; count: number }>();
    for (const alert of alertsByNiche || []) {
      // trends is an object with a niches property that could be an object or array
      const trend = alert.trends as unknown as { niche_id: string; niches: { id: string; name: string } | { id: string; name: string }[] } | null;
      if (trend?.niches) {
        // niches could be an array or single object, normalize to array
        const nichesArr = Array.isArray(trend.niches) ? trend.niches : [trend.niches];
        for (const niche of nichesArr) {
          const existing = nicheCounts.get(niche.id);
          if (existing) {
            existing.count++;
          } else {
            nicheCounts.set(niche.id, {
              niche_id: niche.id,
              niche_name: niche.name,
              count: 1
            });
          }
        }
      }
    }

    // Get alerts by status
    const { data: alertsByStatus } = await supabase
      .from('alerts')
      .select('status')
      .eq('user_id', user.id)
      .gte('created_at', (period === 'week' ? weekAgo : monthAgo).toISOString());

    const statusCounts = {
      pending: 0,
      sent: 0,
      delivered: 0,
      failed: 0
    };

    for (const alert of alertsByStatus || []) {
      if (alert.status in statusCounts) {
        statusCounts[alert.status as keyof typeof statusCounts]++;
      }
    }

    // Calculate action rate (clicked or opened / total)
    const { data: actionedAlerts } = await supabase
      .from('alerts')
      .select('id')
      .eq('user_id', user.id)
      .gte('created_at', (period === 'week' ? weekAgo : monthAgo).toISOString())
      .or('opened_at.not.is.null,clicked_at.not.is.null');

    const totalAlerts = (period === 'week' ? totalThisWeek : totalThisMonth) || 0;
    const actionRate = totalAlerts > 0 ? (actionedAlerts?.length || 0) / totalAlerts : 0;

    // Calculate bookmark rate (bookmarked alerts / total)
    // We need to join with bookmarks through trends
    const { data: bookmarkedAlerts } = await supabase
      .from('bookmarks')
      .select('trend_id')
      .eq('user_id', user.id)
      .gte('created_at', (period === 'week' ? weekAgo : monthAgo).toISOString());

    const bookmarkedTrendIds = new Set(bookmarkedAlerts?.map(b => b.trend_id) || []);

    const { data: alertsWithBookmarks } = await supabase
      .from('alerts')
      .select('trend_id')
      .eq('user_id', user.id)
      .gte('created_at', (period === 'week' ? weekAgo : monthAgo).toISOString());

    const bookmarkedCount = (alertsWithBookmarks || []).filter(a => bookmarkedTrendIds.has(a.trend_id)).length;
    const bookmarkRate = totalAlerts > 0 ? bookmarkedCount / totalAlerts : 0;

    return NextResponse.json({
      total_this_week: totalThisWeek || 0,
      total_this_month: totalThisMonth || 0,
      by_niche: Array.from(nicheCounts.values()),
      by_status: statusCounts,
      action_rate: Math.round(actionRate * 100) / 100,
      bookmark_rate: Math.round(bookmarkRate * 100) / 100
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
