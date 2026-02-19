import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { requireCsrfToken } from '@/lib/csrf';

// GET - List user's bookmarked trends
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
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);
    const offset = parseInt(searchParams.get('offset') || '0');

    // Fetch bookmarks with trend data
    const { data: bookmarks, error } = await supabase
      .from('bookmarks')
      .select(`
        id,
        user_id,
        trend_id,
        notes,
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

    if (error) {
      console.error('Error fetching bookmarks:', error);
      return NextResponse.json({ error: 'Failed to fetch bookmarks' }, { status: 500 });
    }

    // Get total count
    const { count } = await supabase
      .from('bookmarks')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id);

    return NextResponse.json({
      bookmarks: bookmarks || [],
      total: count || 0
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST - Bookmark a trend
export async function POST(request: NextRequest) {
  try {
    // Validate CSRF token for state-changing operation
    const csrfCheck = await requireCsrfToken(request);
    if (!csrfCheck.valid) {
      return NextResponse.json(
        { error: csrfCheck.error || 'Invalid CSRF token' },
        { status: 403 }
      );
    }

    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { trend_id, notes } = body;

    if (!trend_id) {
      return NextResponse.json({ error: 'trend_id is required' }, { status: 400 });
    }

    // Validate notes length
    if (notes && notes.length > 500) {
      return NextResponse.json({ error: 'Notes must be 500 characters or less' }, { status: 400 });
    }

    // Check if trend exists
    const { data: trend, error: trendError } = await supabase
      .from('trends')
      .select('id, name')
      .eq('id', trend_id)
      .single();

    if (trendError || !trend) {
      return NextResponse.json({ error: 'Trend not found' }, { status: 404 });
    }

    // Create bookmark
    const { data: bookmark, error: insertError } = await supabase
      .from('bookmarks')
      .insert({
        user_id: user.id,
        trend_id,
        notes: notes || null
      })
      .select()
      .single();

    if (insertError) {
      if (insertError.code === '23505') {
        return NextResponse.json({ error: 'Trend already bookmarked' }, { status: 409 });
      }
      console.error('Error creating bookmark:', insertError);
      return NextResponse.json({ error: 'Failed to create bookmark' }, { status: 500 });
    }

    return NextResponse.json(bookmark, { status: 201 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
