import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { validateUuid } from '@/lib/utils';

// PATCH - Update bookmark notes
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

    // Validate UUID format
    const uuidCheck = validateUuid(id, 'Bookmark ID');
    if (!uuidCheck.valid) {
      return NextResponse.json({ error: uuidCheck.error }, { status: 400 });
    }

    const body = await request.json();
    const { notes } = body;

    // Validate notes length
    if (notes && notes.length > 500) {
      return NextResponse.json({ error: 'Notes must be 500 characters or less' }, { status: 400 });
    }

    // Update bookmark (RLS ensures user owns it)
    const { data: bookmark, error } = await supabase
      .from('bookmarks')
      .update({ notes: notes || null })
      .eq('id', id)
      .eq('user_id', user.id)
      .select()
      .single();

    if (error) {
      console.error('Error updating bookmark:', error);
      return NextResponse.json({ error: 'Failed to update bookmark' }, { status: 500 });
    }

    if (!bookmark) {
      return NextResponse.json({ error: 'Bookmark not found' }, { status: 404 });
    }

    return NextResponse.json(bookmark);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE - Remove a bookmark
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

    const { id } = await params;

    // Validate UUID format
    const uuidCheck = validateUuid(id, 'Bookmark ID');
    if (!uuidCheck.valid) {
      return NextResponse.json({ error: uuidCheck.error }, { status: 400 });
    }

    // Delete bookmark (RLS ensures user owns it)
    const { error, count } = await supabase
      .from('bookmarks')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id);

    if (error) {
      console.error('Error deleting bookmark:', error);
      return NextResponse.json({ error: 'Failed to delete bookmark' }, { status: 500 });
    }

    // Return 204 regardless - don't leak whether bookmark existed
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
