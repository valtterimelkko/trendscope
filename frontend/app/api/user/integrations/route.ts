import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

// GET - Fetch user's integrations
export async function GET() {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { data: integrations, error } = await supabase
      .from('alert_integrations')
      .select('id, user_id, type, name, config, is_active, last_tested_at, last_test_status, created_at, updated_at')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching integrations:', error);
      return NextResponse.json({ error: 'Failed to fetch integrations' }, { status: 500 });
    }

    // Mask sensitive data in config
    const maskedIntegrations = integrations?.map(integration => ({
      ...integration,
      config: {
        ...integration.config,
        webhook_url: integration.config?.webhook_url ? '••••••••' + integration.config.webhook_url.slice(-8) : undefined
      }
    })) || [];

    return NextResponse.json({ integrations: maskedIntegrations });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// POST - Create a new integration
export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { type, name, config } = body;

    // Validate required fields
    if (!type || !name || !config) {
      return NextResponse.json({ error: 'type, name, and config are required' }, { status: 400 });
    }

    // Validate type
    const validTypes = ['slack', 'webhook', 'discord'];
    if (!validTypes.includes(type)) {
      return NextResponse.json({ error: `Invalid type. Must be one of: ${validTypes.join(', ')}` }, { status: 400 });
    }

    // Validate webhook URL
    if (config.webhook_url) {
      try {
        new URL(config.webhook_url);
      } catch {
        return NextResponse.json({ error: 'Invalid webhook URL format' }, { status: 400 });
      }
    }

    // Create integration
    const { data: integration, error: insertError } = await supabase
      .from('alert_integrations')
      .insert({
        user_id: user.id,
        type,
        name,
        config: {
          webhook_url: config.webhook_url,
          channel: config.channel,
          format: config.format || 'detailed'
        },
        is_active: true
      })
      .select()
      .single();

    if (insertError) {
      console.error('Error creating integration:', insertError);
      return NextResponse.json({ error: 'Failed to create integration' }, { status: 500 });
    }

    // Mask webhook URL in response
    const maskedIntegration = {
      ...integration,
      config: {
        ...integration.config,
        webhook_url: '••••••••' + (config.webhook_url?.slice(-8) || '')
      }
    };

    return NextResponse.json(maskedIntegration, { status: 201 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE - Remove an integration
export async function DELETE(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({ error: 'id query parameter is required' }, { status: 400 });
    }

    // Delete integration (RLS ensures user owns it)
    const { error: deleteError } = await supabase
      .from('alert_integrations')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id);

    if (deleteError) {
      console.error('Error deleting integration:', deleteError);
      return NextResponse.json({ error: 'Failed to delete integration' }, { status: 500 });
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// PATCH - Update an integration
export async function PATCH(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { id, name, config, is_active } = body;

    if (!id) {
      return NextResponse.json({ error: 'id is required' }, { status: 400 });
    }

    const updates: Record<string, unknown> = {};
    if (name !== undefined) updates.name = name;
    if (is_active !== undefined) updates.is_active = is_active;
    if (config !== undefined) {
      updates.config = {
        webhook_url: config.webhook_url,
        channel: config.channel,
        format: config.format || 'detailed'
      };
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ error: 'No fields to update' }, { status: 400 });
    }

    const { data: updated, error: updateError } = await supabase
      .from('alert_integrations')
      .update(updates)
      .eq('id', id)
      .eq('user_id', user.id)
      .select()
      .single();

    if (updateError) {
      console.error('Error updating integration:', updateError);
      return NextResponse.json({ error: 'Failed to update integration' }, { status: 500 });
    }

    if (!updated) {
      return NextResponse.json({ error: 'Integration not found' }, { status: 404 });
    }

    // Mask webhook URL in response
    const maskedIntegration = {
      ...updated,
      config: {
        ...updated.config,
        webhook_url: updated.config?.webhook_url ? '••••••••' + updated.config.webhook_url.slice(-8) : undefined
      }
    };

    return NextResponse.json(maskedIntegration);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
