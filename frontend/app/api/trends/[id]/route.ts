import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const { id } = await params;

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Fetch trend with niche info
    const { data: trend, error } = await supabase
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
        video_count_start,
        video_count_current,
        growth_rate,
        metadata,
        created_at,
        updated_at,
        niches (
          id,
          name,
          display_name
        )
      `)
      .eq('id', id)
      .single();

    if (error || !trend) {
      return NextResponse.json({ error: 'Trend not found' }, { status: 404 });
    }

    // Fetch velocity history for the trend (last 24 data points)
    const { data: velocityHistory } = await supabase
      .from('trend_velocity_history')
      .select('timestamp, video_count, velocity_score, growth_rate, saturation_percent')
      .eq('trend_id', id)
      .order('timestamp', { ascending: false })
      .limit(24);

    // Transform data to match frontend types
    const transformedTrend = {
      id: trend.id,
      type: trend.type,
      identifier: trend.platform_id,
      display_name: trend.name,
      niche_id: trend.niche_id,
      velocity_score: trend.velocity_score || 0,
      saturation_percentage: trend.saturation_percent || 0,
      video_count: trend.video_count_current || 0,
      video_count_start: trend.video_count_start,
      video_count_current: trend.video_count_current,
      growth_rate: trend.growth_rate || 0,
      detection_timestamp: trend.first_detected_at,
      peak_timestamp: trend.peak_detected_at,
      status: trend.status,
      example_videos: trend.metadata?.example_videos || [],
      related_tags: trend.metadata?.related_hashtags || [],
      created_at: trend.created_at,
      updated_at: trend.updated_at,
      niche: trend.niches,
      velocity_history: velocityHistory?.map(v => ({
        timestamp: v.timestamp,
        video_count: v.video_count,
        velocity_score: v.velocity_score,
        growth_rate: v.growth_rate,
        saturation_percent: v.saturation_percent
      })) || []
    };

    return NextResponse.json(transformedTrend);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
