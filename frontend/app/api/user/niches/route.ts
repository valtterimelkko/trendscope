import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// GET - Fetch user's niche preferences
export async function GET() {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get user's tier to determine max niches
    const { data: profile } = await supabase
      .from('profiles')
      .select('tier')
      .eq('id', user.id)
      .single();

    const tierLimits: Record<string, number> = {
      free: 1,
      solo: 5,
      agency: 10,
      enterprise: 20
    };

    const maxAllowed = tierLimits[profile?.tier || 'free'] || 1;

    // Fetch all available niches
    const { data: allNiches, error: nichesError } = await supabase
      .from('niches')
      .select('id, name, display_name, description, is_active')
      .eq('is_active', true)
      .order('display_name');

    if (nichesError) {
      console.error('Error fetching niches:', nichesError);
      return NextResponse.json({ error: 'Failed to fetch niches' }, { status: 500 });
    }

    // Fetch user's selected niches
    const { data: userNiches, error: userNichesError } = await supabase
      .from('user_niches')
      .select('id, niche_id, alert_enabled, velocity_threshold, created_at')
      .eq('user_id', user.id);

    if (userNichesError) {
      console.error('Error fetching user niches:', userNichesError);
      return NextResponse.json({ error: 'Failed to fetch user preferences' }, { status: 500 });
    }

    // Create a map of user's selected niches
    const selectedMap = new Map(
      userNiches?.map(un => [un.niche_id, un])
    );

    // Combine data
    const niches = allNiches?.map(niche => ({
      id: niche.id,
      name: niche.name,
      display_name: niche.display_name,
      description: niche.description,
      is_selected: selectedMap.has(niche.id),
      alert_enabled: selectedMap.get(niche.id)?.alert_enabled ?? true,
      velocity_threshold: selectedMap.get(niche.id)?.velocity_threshold ?? 50,
      user_niche_id: selectedMap.get(niche.id)?.id
    })) || [];

    return NextResponse.json({
      niches,
      max_allowed: maxAllowed,
      current_count: userNiches?.length || 0
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST - Add a niche to user's preferences
export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { niche_id } = body;

    if (!niche_id) {
      return NextResponse.json({ error: 'niche_id is required' }, { status: 400 });
    }

    // Get user's tier and current count
    const { data: profile } = await supabase
      .from('profiles')
      .select('tier')
      .eq('id', user.id)
      .single();

    const { count } = await supabase
      .from('user_niches')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id);

    const tierLimits: Record<string, number> = {
      free: 1,
      solo: 5,
      agency: 10,
      enterprise: 20
    };

    const maxAllowed = tierLimits[profile?.tier || 'free'] || 1;

    if ((count || 0) >= maxAllowed) {
      return NextResponse.json({
        error: `Maximum niches reached for your tier (${maxAllowed}). Please upgrade to add more.`
      }, { status: 400 });
    }

    // Check if niche exists and is active
    const { data: niche, error: nicheError } = await supabase
      .from('niches')
      .select('id, name')
      .eq('id', niche_id)
      .eq('is_active', true)
      .single();

    if (nicheError || !niche) {
      return NextResponse.json({ error: 'Niche not found' }, { status: 404 });
    }

    // Add niche to user's preferences
    const { data: userNiche, error: insertError } = await supabase
      .from('user_niches')
      .insert({
        user_id: user.id,
        niche_id,
        alert_enabled: true,
        velocity_threshold: 50
      })
      .select()
      .single();

    if (insertError) {
      if (insertError.code === '23505') {
        return NextResponse.json({ error: 'Niche already selected' }, { status: 409 });
      }
      console.error('Error adding niche:', insertError);
      return NextResponse.json({ error: 'Failed to add niche' }, { status: 500 });
    }

    return NextResponse.json({
      id: userNiche.id,
      user_id: userNiche.user_id,
      niche_id: userNiche.niche_id,
      alert_enabled: userNiche.alert_enabled,
      velocity_threshold: userNiche.velocity_threshold,
      niche: niche
    }, { status: 201 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE - Remove a niche from user's preferences
export async function DELETE(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const niche_id = searchParams.get('niche_id');

    if (!niche_id) {
      return NextResponse.json({ error: 'niche_id query parameter is required' }, { status: 400 });
    }

    // Delete user's niche preference
    const { error: deleteError } = await supabase
      .from('user_niches')
      .delete()
      .eq('user_id', user.id)
      .eq('niche_id', niche_id);

    if (deleteError) {
      console.error('Error removing niche:', deleteError);
      return NextResponse.json({ error: 'Failed to remove niche' }, { status: 500 });
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// PATCH - Update niche preferences (alert_enabled, velocity_threshold)
export async function PATCH(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { niche_id, alert_enabled, velocity_threshold } = body;

    if (!niche_id) {
      return NextResponse.json({ error: 'niche_id is required' }, { status: 400 });
    }

    const updates: Record<string, unknown> = {};
    if (alert_enabled !== undefined) updates.alert_enabled = alert_enabled;
    if (velocity_threshold !== undefined) updates.velocity_threshold = velocity_threshold;

    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ error: 'No fields to update' }, { status: 400 });
    }

    const { data: updated, error: updateError } = await supabase
      .from('user_niches')
      .update(updates)
      .eq('user_id', user.id)
      .eq('niche_id', niche_id)
      .select()
      .single();

    if (updateError) {
      console.error('Error updating niche:', updateError);
      return NextResponse.json({ error: 'Failed to update niche' }, { status: 500 });
    }

    if (!updated) {
      return NextResponse.json({ error: 'Niche not found in preferences' }, { status: 404 });
    }

    return NextResponse.json(updated);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
