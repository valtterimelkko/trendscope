import { createClient } from '@/lib/supabase/server'

export default async function InboxPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch notifications/inbox items
  const { data: notifications } = await supabase
    .from('notifications')
    .select(`
      *,
      issue:issues(id, title, identifier, status),
      actor:profiles!actor_id(id, display_name, avatar_url)
    `)
    .eq('user_id', user?.id)
    .order('created_at', { ascending: false })
    .limit(50)

  // Group by read/unread
  const unreadNotifications = notifications?.filter((n) => !n.read_at) || []
  const readNotifications = notifications?.filter((n) => n.read_at) || []

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            {/* CONTENT_SLOT: inbox.title */}
            Inbox
          </h2>
          <p className="text-sm text-muted">
            {unreadNotifications.length} unread notification{unreadNotifications.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-sm text-primary hover:underline">
            Mark all as read
          </button>
          <button className="p-2 hover:bg-surface-hover rounded-lg transition-colors">
            <SettingsIcon className="w-4 h-4 text-muted" />
          </button>
        </div>
      </div>

      {/* Keyboard hints */}
      <div className="px-4 py-2 bg-surface border-b border-border">
        <div className="flex items-center gap-4 text-xs text-muted">
          <span><kbd className="kbd">J/K</kbd> Navigate</span>
          <span><kbd className="kbd">↵</kbd> Open issue</span>
          <span><kbd className="kbd">E</kbd> Mark read</span>
          <span><kbd className="kbd">A</kbd> Archive</span>
        </div>
      </div>

      {/* Notification list */}
      <div className="flex-1 overflow-auto">
        {notifications && notifications.length > 0 ? (
          <div className="divide-y divide-border">
            {/* Unread section */}
            {unreadNotifications.length > 0 && (
              <>
                <div className="px-4 py-2 bg-surface-hover sticky top-0">
                  <span className="text-xs font-semibold text-muted uppercase tracking-wide">
                    Unread
                  </span>
                </div>
                {unreadNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    isUnread
                  />
                ))}
              </>
            )}

            {/* Read section */}
            {readNotifications.length > 0 && (
              <>
                <div className="px-4 py-2 bg-surface-hover sticky top-0">
                  <span className="text-xs font-semibold text-muted uppercase tracking-wide">
                    Earlier
                  </span>
                </div>
                {readNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    isUnread={false}
                  />
                ))}
              </>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="w-16 h-16 bg-surface-hover rounded-full flex items-center justify-center mb-4">
              <InboxEmptyIcon className="w-8 h-8 text-muted" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {/* CONTENT_SLOT: inbox.empty.title */}
              All caught up!
            </h3>
            <p className="text-muted max-w-md">
              {/* CONTENT_SLOT: inbox.empty.description */}
              You have no notifications. When someone mentions you, assigns you an issue, or comments on your work, you&apos;ll see it here.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// Notification Item Component
function NotificationItem({
  notification,
  isUnread,
}: {
  notification: any
  isUnread: boolean
}) {
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'assigned':
        return <UserIcon className="w-4 h-4 text-primary" />
      case 'mentioned':
        return <AtSymbolIcon className="w-4 h-4 text-warning" />
      case 'commented':
        return <ChatIcon className="w-4 h-4 text-success" />
      case 'status_changed':
        return <StatusIcon className="w-4 h-4 text-muted" />
      default:
        return <BellIcon className="w-4 h-4 text-muted" />
    }
  }

  const getNotificationText = (type: string, actorName: string) => {
    switch (type) {
      case 'assigned':
        return `${actorName} assigned you to an issue`
      case 'mentioned':
        return `${actorName} mentioned you`
      case 'commented':
        return `${actorName} commented on an issue`
      case 'status_changed':
        return `Issue status was updated`
      default:
        return `New notification`
    }
  }

  return (
    <div
      className={`px-4 py-3 hover:bg-surface-hover transition-colors cursor-pointer group ${
        isUnread ? 'bg-primary/5' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Unread indicator */}
        {isUnread && (
          <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0 mt-2" />
        )}
        {!isUnread && <div className="w-2 flex-shrink-0" />}

        {/* Icon */}
        <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center flex-shrink-0">
          {getNotificationIcon(notification.type)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={`text-sm ${isUnread ? 'font-medium text-foreground' : 'text-muted'}`}>
              {getNotificationText(notification.type, notification.actor?.display_name || 'Someone')}
            </p>
            <span className="text-xs text-muted">
              {formatRelativeTime(notification.created_at)}
            </span>
          </div>
          {notification.issue && (
            <div className="mt-1 flex items-center gap-2">
              <span className="text-xs font-mono text-muted">{notification.issue.identifier}</span>
              <span className="text-sm text-foreground truncate">{notification.issue.title}</span>
            </div>
          )}
          {notification.preview && (
            <p className="text-sm text-muted mt-1 line-clamp-2">{notification.preview}</p>
          )}
        </div>

        {/* Actions (shown on hover) */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 hover:bg-surface rounded transition-colors" title="Mark as read">
            <CheckIcon className="w-4 h-4 text-muted" />
          </button>
          <button className="p-1.5 hover:bg-surface rounded transition-colors" title="Archive">
            <ArchiveIcon className="w-4 h-4 text-muted" />
          </button>
        </div>
      </div>
    </div>
  )
}

// Helper function
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`
  return date.toLocaleDateString()
}

// Icons
function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}

function InboxEmptyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
  )
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  )
}

function AtSymbolIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
    </svg>
  )
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  )
}

function StatusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}

function ArchiveIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
    </svg>
  )
}
