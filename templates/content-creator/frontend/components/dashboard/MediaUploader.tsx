'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { createClient } from '@/lib/supabase/client'
import { formatFileSize } from '@/lib/utils'

interface MediaUploaderProps {
  workspaceId: string
  onUpload: (url: string, file: File) => void
  maxSize?: number // in bytes
}

export function MediaUploader({ workspaceId, onUpload, maxSize = 10 * 1024 * 1024 }: MediaUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const supabase = createClient()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (file.size > maxSize) {
      setError(`File too large. Maximum size is ${formatFileSize(maxSize)}`)
      return
    }

    setUploading(true)
    setProgress(0)
    setError(null)

    try {
      const fileExt = file.name.split('.').pop()
      const fileName = `${workspaceId}/${Date.now()}-${Math.random().toString(36).substring(7)}.${fileExt}`

      const { data, error: uploadError } = await supabase.storage
        .from('media')
        .upload(fileName, file, {
          cacheControl: '3600',
          upsert: false,
        })

      if (uploadError) throw uploadError

      const { data: urlData } = supabase.storage
        .from('media')
        .getPublicUrl(data.path)

      onUpload(urlData.publicUrl, file)
      setProgress(100)
    } catch (err: any) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [workspaceId, maxSize, supabase.storage, onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'video/*': ['.mp4', '.webm', '.mov'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <UploadIcon className="w-10 h-10 text-muted mb-3" />
        {isDragActive ? (
          <p className="text-foreground font-medium">Drop the file here...</p>
        ) : (
          <>
            <p className="text-foreground font-medium">
              Drag & drop or click to upload
            </p>
            <p className="text-sm text-muted mt-1">
              PNG, JPG, GIF, WebP, MP4 up to {formatFileSize(maxSize)}
            </p>
          </>
        )}
      </div>

      {uploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">Uploading...</span>
            <span className="text-foreground font-medium">{progress}%</span>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  )
}
