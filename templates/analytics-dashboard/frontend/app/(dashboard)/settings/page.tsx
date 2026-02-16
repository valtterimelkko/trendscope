import { createClient } from '@/lib/supabase/server'
import { SettingsForm } from '@/components/settings/SettingsForm'

export default async function SettingsPage() {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user?.id)
    .single()

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">General Settings</h1>
        <p className="text-foreground/70 mt-1">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="card p-6">
        <SettingsForm profile={profile} />
      </div>
    </div>
  )
}
