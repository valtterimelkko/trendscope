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
    const niches = searchParams.get('niches')?.split(',').filter(Boolean);
    const status = searchParams.get('status');
    const minVelocity = searchParams.get('minVelocity');
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);
    const offset = parseInt(searchParams.get('offset') || '0');

    // Build query
    let query = supabase
      .from('trends')
      .select(`
        id,
        type,
        name,
        platform_id,
        niche_id,
        first_detected_at,
        peak_detected_at,
        status,
        velocity_score,
        saturation_percent,
        video_count_current,
        growth_rate,
        metadata,
        created_at,
        niches (
          id,
          name,
          display_name
        )
      `)
      .order('velocity_score', { ascending: false })
      .range(offset, offset + limit - 1);

    // Apply filters
    if (niches && niches.length > 0) {
      query = query.in('niche_id', niches);
    }

    if (status) {
      query = query.eq('status', status);
    }

    if (minVelocity) {
      query = query.gte('velocity_score', parseInt(minVelocity));
    }

    const { data: trends, error } = await query;

    if (error) {
      console.error('Error fetching trends:', error);
      return NextResponse.json({ error: 'Failed to fetch trends' }, { status: 500 });
    }

    // Get total count for pagination
    let countQuery = supabase
      .from('trends')
      .select('*', { count: 'exact', head: true });

    if (niches && niches.length > 0) {
      countQuery = countQuery.in('niche_id', niches);
    }
    if (status) {
      countQuery = countQuery.eq('status', status);
    }
    if (minVelocity) {
      countQuery = countQuery.gte('velocity_score', parseInt(minVelocity));
    }

    const { count } = await countQuery;

    // Transform data to match frontend types
    const transformedTrends = trends?.map(trend => ({
      id: trend.id,
      type: trend.type,
      identifier: trend.platform_id,
      display_name: trend.name,
      niche_id: trend.niche_id,
      velocity_score: trend.velocity_score || 0,
      saturation_percentage: trend.saturation_percent || 0,
      video_count: trend.video_count_current || 0,
      growth_rate: trend.growth_rate || 0,
      detection_timestamp: trend.first_detected_at,
      peak_timestamp: trend.peak_detected_at,
      status: trend.status,
      example_videos: trend.metadata?.example_videos || [],
      related_tags: trend.metadata?.related_hashtags || [],
      created_at: trend.created_at,
      updated_at: trend.created_at,
      niche: trend.niches
    })) || [];

    return NextResponse.json({
      trends: transformedTrends,
      total: count || 0,
      limit,
      offset
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
