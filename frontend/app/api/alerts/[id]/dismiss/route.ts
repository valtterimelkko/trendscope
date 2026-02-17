import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// PATCH - Dismiss an alert
export async function PATCH(
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

    const { id } = await params;

    // Update alert to dismissed (RLS ensures user owns it)
    const { data: alert, error } = await supabase
      .from('alerts')
      .update({ dismissed: true })
      .eq('id', id)
      .eq('user_id', user.id)
      .select('id, dismissed')
      .single();

    if (error) {
      console.error('Error dismissing alert:', error);
      return NextResponse.json({ error: 'Failed to dismiss alert' }, { status: 500 });
    }

    if (!alert) {
      return NextResponse.json({ error: 'Alert not found' }, { status: 404 });
    }

    return NextResponse.json({
      id: alert.id,
      dismissed: alert.dismissed
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
