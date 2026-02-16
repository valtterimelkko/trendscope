import { createClient } from '@/lib/supabase/server'
import { formatFileSize, formatRelativeDate } from '@/lib/utils'

export default async function MediaPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Fetch user's workspace
  const { data: workspaces } = await supabase
    .from('workspaces')
    .select('*, workspace_members!inner(*)')
    .eq('workspace_members.user_id', user?.id)
    .limit(1)

  const currentWorkspace = workspaces?.[0]

  // Fetch media files
  const { data: media } = await supabase
    .from('media')
    .select('*')
    .eq('workspace_id', currentWorkspace?.id)
    .order('created_at', { ascending: false })

  // Calculate storage usage
  const totalStorage = media?.reduce((sum, file) => sum + (file.size_bytes || 0), 0) || 0
  const storageLimit = 500 * 1024 * 1024 // 500MB for starter
  const storagePercent = (totalStorage / storageLimit) * 100

  return (
    <div className="p-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Media Library</h1>
          <p className="text-muted mt-1">Upload and manage your images and files</p>
        </div>
        <button className="px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors">
          Upload Media
        </button>
      </div>

      {/* Storage usage */}
      <div className="bg-surface border border-border rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted">Storage used</span>
          <span className="text-sm font-medium text-foreground">
            {formatFileSize(totalStorage)} / {formatFileSize(storageLimit)}
          </span>
        </div>
        <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              storagePercent >= 90 ? 'bg-red-500' : storagePercent >= 70 ? 'bg-yellow-500' : 'bg-primary'
            }`}
            style={{ width: `${Math.min(storagePercent, 100)}%` }}
          />
        </div>
        {storagePercent >= 80 && (
          <p className="text-xs text-yellow-600 mt-2">
            Running low on storage.{' '}
            <a href="/dashboard/settings/billing" className="text-primary hover:underline">
              Upgrade for more
            </a>
          </p>
        )}
      </div>

      {/* Media grid */}
      {media && media.length > 0 ? (
        <div className="media-grid">
          {media.map((file) => (
            <div key={file.id} className="media-item group">
              {file.type?.startsWith('image/') ? (
                <img
                  src={file.url}
                  alt={file.name}
                  className="w-full h-full object-cover"
                />
              ) : file.type?.startsWith('video/') ? (
                <video
                  src={file.url}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-surface-hover">
                  <FileIcon className="w-10 h-10 text-muted" />
                </div>
              )}

              {/* Overlay */}
              <div className="media-item-overlay">
                <button className="p-2 bg-white/90 rounded-lg hover:bg-white transition-colors">
                  <EyeIcon className="w-4 h-4 text-foreground" />
                </button>
                <button className="p-2 bg-white/90 rounded-lg hover:bg-white transition-colors">
                  <CopyIcon className="w-4 h-4 text-foreground" />
                </button>
                <button className="p-2 bg-white/90 rounded-lg hover:bg-white transition-colors">
                  <TrashIcon className="w-4 h-4 text-red-500" />
                </button>
              </div>

              {/* File info */}
              <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent">
                <p className="text-xs text-white truncate">{file.name}</p>
                <p className="text-xs text-white/70">{formatFileSize(file.size_bytes)}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl p-12 text-center">
          <ImageIcon className="w-16 h-16 text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No media yet</h3>
          <p className="text-sm text-muted mb-6 max-w-sm mx-auto">
            Upload images and files to use in your posts. Drag & drop or click to upload.
          </p>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary-hover transition-colors">
            <UploadIcon className="w-4 h-4" />
            Upload your first file
          </button>
        </div>
      )}
    </div>
  )
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  )
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  )
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  )
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  )
}
