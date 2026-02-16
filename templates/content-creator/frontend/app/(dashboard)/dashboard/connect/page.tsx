import { createClient } from '@/lib/supabase/server'

export default async function ConnectPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch connected accounts
  const { data: connections } = await supabase
    .from('social_connections')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .order('created_at', { ascending: false })

  // Available platforms for connection
  const platforms = [
    {
      id: 'twitter',
      name: 'X (Twitter)',
      icon: TwitterIcon,
      description: 'Post tweets and threads to your X account',
      color: '#000000',
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: LinkedInIcon,
      description: 'Share updates with your professional network',
      color: '#0A66C2',
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: FacebookIcon,
      description: 'Post to your Facebook page or profile',
      color: '#1877F2',
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: InstagramIcon,
      description: 'Schedule posts to your Instagram feed',
      color: '#E4405F',
    },
    {
      id: 'threads',
      name: 'Threads',
      icon: ThreadsIcon,
      description: 'Share text posts on Threads',
      color: '#000000',
    },
    {
      id: 'bluesky',
      name: 'Bluesky',
      icon: BlueskyIcon,
      description: 'Post to your Bluesky account',
      color: '#0085FF',
    },
  ]

  // Check which platforms are connected
  const connectedPlatformIds = connections?.map((c) => c.platform) || []

  return (
    <div className="p-6 max-w-4xl">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">
          {/* CONTENT_SLOT: connect.title */}
          Connect Your Accounts
        </h1>
        <p className="text-muted mt-1">
          {/* CONTENT_SLOT: connect.subtitle */}
          Link your social media accounts to publish content directly from your dashboard.
        </p>
      </div>

      {/* Connected accounts */}
      {connections && connections.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-4">Connected Accounts</h2>
          <div className="space-y-3">
            {connections.map((connection) => {
              const platform = platforms.find((p) => p.id === connection.platform)
              if (!platform) return null

              return (
                <div
                  key={connection.id}
                  className="flex items-center justify-between p-4 bg-surface border border-border rounded-xl"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${platform.color}15` }}
                    >
                      <platform.icon className="w-5 h-5" style={{ color: platform.color }} />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{platform.name}</p>
                      <p className="text-sm text-muted">@{connection.username || connection.account_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 text-sm text-green-600">
                      <CheckCircleIcon className="w-4 h-4" />
                      Connected
                    </span>
                    <button className="text-sm text-muted hover:text-red-500 transition-colors">
                      Disconnect
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Available platforms */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4">
          {connections && connections.length > 0 ? 'Add More Accounts' : 'Available Platforms'}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {platforms
            .filter((p) => !connectedPlatformIds.includes(p.id))
            .map((platform) => (
              <button
                key={platform.id}
                className="flex items-start gap-4 p-4 bg-surface border border-border rounded-xl hover:border-primary hover:shadow-sm transition-all text-left group"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform"
                  style={{ backgroundColor: `${platform.color}15` }}
                >
                  <platform.icon className="w-6 h-6" style={{ color: platform.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground group-hover:text-primary transition-colors">
                    {platform.name}
                  </p>
                  <p className="text-sm text-muted mt-0.5">{platform.description}</p>
                </div>
                <div className="flex-shrink-0 mt-1">
                  <PlusCircleIcon className="w-5 h-5 text-muted group-hover:text-primary transition-colors" />
                </div>
              </button>
            ))}
        </div>
      </div>

      {/* Connection info */}
      <div className="mt-8 p-4 bg-surface-hover rounded-xl">
        <div className="flex items-start gap-3">
          <InfoIcon className="w-5 h-5 text-muted flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-foreground">Secure OAuth Connection</p>
            <p className="text-sm text-muted mt-0.5">
              {/* CONTENT_SLOT: connect.security_note */}
              We use OAuth to securely connect your accounts. We never store your passwords and you can revoke access at any time.
            </p>
          </div>
        </div>
      </div>

      {/* Plan limits notice */}
      {connections && connections.length >= 3 && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Channel limit reached</p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-0.5">
                Your current plan allows 3 connected accounts.{' '}
                <a href="/dashboard/settings/billing" className="font-medium underline">
                  Upgrade
                </a>{' '}
                to connect more platforms.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Platform Icons
function TwitterIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  )
}

function LinkedInIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  )
}

function FacebookIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  )
}

function InstagramIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
    </svg>
  )
}

function ThreadsIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.96-.065-1.182.408-2.256 1.332-3.023.85-.706 2.017-1.12 3.377-1.197 1.03-.059 1.988.034 2.861.273-.075-.96-.398-1.667-.96-2.104-.636-.494-1.6-.768-2.874-.768h-.09c-1.022.018-1.848.27-2.453.746l-1.274-1.615c.966-.762 2.2-1.163 3.673-1.194h.12c1.773 0 3.216.434 4.285 1.29 1.098.879 1.72 2.144 1.852 3.768.442.122.86.28 1.25.474 1.168.583 2.08 1.463 2.637 2.545.74 1.438.834 3.96-1.18 5.934-1.79 1.753-4.022 2.542-7.029 2.564zm-.063-7.008c-.063 0-.126.002-.188.005-.821.047-1.458.263-1.844.627-.328.31-.49.692-.456 1.107.036.472.327.887.821 1.167.549.312 1.262.45 2.065.396 1.027-.056 1.785-.401 2.317-1.054.377-.463.613-1.065.72-1.835-.687-.18-1.455-.322-2.296-.366a11.83 11.83 0 00-1.14-.047z" />
    </svg>
  )
}

function BlueskyIcon({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364.136-.02.275-.039.415-.056-.138.022-.276.04-.415.056-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078a8.741 8.741 0 01-.415-.056c.14.017.279.036.415.056 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8z" />
    </svg>
  )
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function PlusCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  )
}
