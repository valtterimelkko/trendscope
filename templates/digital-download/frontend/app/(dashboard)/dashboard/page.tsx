'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { FREE_UPLOAD_CAP_BYTES, FREE_UPLOAD_CAP_MB } from '@/constants/uploadLimits'

type DownloadStatus = 'queued' | 'processing' | 'ready' | 'expired' | 'failed'

export default function DownloadLockerPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploadState, setUploadState] = useState<DownloadStatus>('queued')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [lastFileName, setLastFileName] = useState<string>('Sample Pack.zip')

  const usage = { used: 12, total: 30 }

  const recentDownloads = useMemo(
    () => [
      { id: 1, name: 'Neon LUT Bundle.zip', status: 'ready' as DownloadStatus, size: '240 MB', expiresIn: '23h', mode: 'auto' },
      { id: 2, name: 'Poster Mockups.psd', status: 'processing' as DownloadStatus, size: '1.2 GB', expiresIn: '—', mode: 'manual' },
      { id: 3, name: 'Lo-fi Stems.wav', status: 'queued' as DownloadStatus, size: '480 MB', expiresIn: '—', mode: 'auto' },
      { id: 4, name: 'Template Kit.pdf', status: 'expired' as DownloadStatus, size: '35 MB', expiresIn: 'expired', mode: 'auto' },
    ],
    []
  )

  const history = useMemo(
    () => [
      { id: 'h1', name: 'Logo Pack v2.zip', result: 'Delivered', at: '3m ago', status: 'ready' as DownloadStatus },
      { id: 'h2', name: 'Product Shots.jpg', result: 'Retry available', at: '12m ago', status: 'failed' as DownloadStatus },
      { id: 'h3', name: 'Preset Vault.zip', result: 'Deleted after 24h', at: '1d ago', status: 'expired' as DownloadStatus },
    ],
    []
  )

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]
    setLastFileName(file.name)

    if (file.size > FREE_UPLOAD_CAP_BYTES) {
      setError(`File too large for free tier. Upgrade to upload files over ${Math.round(FREE_UPLOAD_CAP_MB)}MB.`)
      setUploadState('failed')
      setProgress(0)
      return
    }

    setError(null)
    setUploadState('processing')
    setProgress(18)

    // Simulate upload + processing states to demonstrate waiting UX
    setTimeout(() => setProgress(72), 600)
    setTimeout(() => {
      setProgress(100)
      setUploadState('ready')
    }, 1200)
  }

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
    handleFiles(event.dataTransfer.files)
  }

  return (
    <div className="p-6 space-y-8">
      {/* Top bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Download locker</h1>
          <p className="text-muted mt-1">Hero dropzone + transparent quotas, designed from the minimalist SaaS research.</p>
        </div>
        <Link
          href="/billing"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors"
        >
          Upgrade for HD
        </Link>
      </div>

      {/* Quota + paywall highlights */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="p-4 bg-surface border border-border rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">Downloads this month</span>
            <span className="text-foreground font-semibold">{usage.used} / {usage.total}</span>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden mt-2">
            <div className="h-full bg-primary rounded-full" style={{ width: `${(usage.used / usage.total) * 100}%` }} />
          </div>
          <p className="text-xs text-muted mt-2">Free tier: 3 files, then soft paywall prompts upgrade.</p>
        </div>
        <div className="p-4 bg-surface border border-border rounded-lg flex items-center gap-3">
          <ShieldIcon className="w-5 h-5 text-primary" />
          <div className="text-sm">
            <p className="text-foreground font-semibold">Signed URLs</p>
            <p className="text-muted">Auto-expire after 24h. Download history shows retention timers.</p>
          </div>
        </div>
        <div className="p-4 bg-surface border border-border rounded-lg flex items-center gap-3">
          <BoltIcon className="w-5 h-5 text-accent" />
          <div className="text-sm">
            <p className="text-foreground font-semibold">Auto-start uploads</p>
            <p className="text-muted">Drop a file to begin instantly. Configurable manual start for heavy exports.</p>
          </div>
        </div>
      </div>

      {/* Hero dropzone + guardrails */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
            className={`border-2 border-dashed rounded-2xl p-8 transition-all bg-background ${dragActive ? 'border-primary/70 bg-primary/5' : 'border-border'}`}
          >
            <div className="flex flex-col items-center text-center gap-3">
              <UploadIcon className="w-10 h-10 text-primary" />
              <p className="text-lg font-semibold text-foreground">
                Drop your pack to start delivery
              </p>
              <p className="text-sm text-muted">
                We validate size and type before upload. PNG, JPG, ZIP, WAV up to 500MB on free.
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-3">
                <label className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-primary-hover">
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => handleFiles(e.target.files)}
                    aria-label="Select a file (PNG, JPG, ZIP, WAV up to 500MB) to generate a secure download link"
                  />
                  Browse files
                </label>
                <span className="text-sm text-muted">Paste or drag from Drive/Dropbox.</span>
              </div>

              <div className="w-full max-w-xl bg-surface border border-border rounded-xl p-4 mt-4">
                <div className="flex items-center justify-between text-sm text-muted">
                  <span>{lastFileName}</span>
                  <StatusBadge status={uploadState} />
                </div>
                <div className="h-2 bg-surface-hover rounded-full overflow-hidden mt-3">
                  <div
                    className={`h-full rounded-full transition-all ${uploadState === 'failed' ? 'bg-red-400' : 'bg-primary'}`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-muted mt-2">
                  {uploadState === 'ready'
                    ? 'Signed download link ready. Expires in 24h.'
                    : uploadState === 'processing'
                      ? 'Uploading and compressing… we smooth the progress so it never freezes at 99%.'
                      : uploadState === 'failed'
                        ? error || 'Upload failed. Retry without losing context.'
                        : 'Auto-start is on. Turn it off if you need configuration-first jobs.'}
                </p>
              </div>
            </div>
          </div>
          {error && (
            <div className="mt-3 p-3 border border-red-200 bg-red-50 rounded-lg text-sm text-red-700 flex items-center gap-2">
              <AlertIcon className="w-4 h-4" />
              {error}
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="p-4 bg-surface border border-border rounded-xl">
            <p className="text-sm font-semibold text-foreground mb-1">Empty state education</p>
            <p className="text-sm text-muted">We show a sample pack and a short tour instead of a blank locker.</p>
          </div>
          <div className="p-4 bg-surface border border-border rounded-xl">
            <p className="text-sm font-semibold text-foreground mb-1">Permeable paywall</p>
            <p className="text-sm text-muted">First HD download is free. Gate bigger files with a friendly upsell instead of a hard error.</p>
          </div>
          <div className="p-4 bg-surface border border-border rounded-xl">
            <p className="text-sm font-semibold text-foreground mb-1">Retention clarity</p>
            <p className="text-sm text-muted">Each download shows time-to-expire so users trust the handling of their files.</p>
          </div>
        </div>
      </div>

      {/* Active downloads */}
      <div className="bg-surface border border-border rounded-xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <p className="text-sm font-semibold text-foreground">Active downloads</p>
          <span className="text-xs text-muted">Auto-start enabled • Showing latest</span>
        </div>
        <div className="divide-y divide-border">
          {recentDownloads.map((item) => (
            <div key={item.id} className="grid md:grid-cols-6 gap-4 p-4 items-center">
              <div className="md:col-span-2">
                <p className="text-sm font-semibold text-foreground truncate">{item.name}</p>
                <p className="text-xs text-muted mt-1">Mode: {item.mode === 'auto' ? 'Magic (auto-start)' : 'Manual start'}</p>
              </div>
              <div className="text-xs text-muted">{item.size}</div>
              <div className="flex items-center gap-2">
                <StatusBadge status={item.status} />
                {item.status === 'processing' && <span className="text-xs text-muted">Smoothing progress…</span>}
              </div>
              <div className="text-xs text-muted">{item.expiresIn}</div>
              <div className="flex gap-2 justify-end">
                <button className="text-xs text-muted hover:text-foreground">Download</button>
                <button className="text-xs text-muted hover:text-foreground">Redo</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* History / soft failures */}
      <div className="bg-surface border border-border rounded-xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <p className="text-sm font-semibold text-foreground">History</p>
          <span className="text-xs text-muted">We keep failed files for retry without reselecting.</span>
        </div>
        <div className="divide-y divide-border">
          {history.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-semibold text-foreground">{item.name}</p>
                <p className="text-xs text-muted">{item.result}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={item.status} />
                <span className="text-xs text-muted">{item.at}</span>
                {item.status === 'failed' && (
                  <button className="text-xs text-primary font-medium hover:underline">Retry</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: DownloadStatus }) {
  const variants: Record<DownloadStatus, string> = {
    queued: 'bg-gray-100 text-gray-700',
    processing: 'bg-amber-100 text-amber-800',
    ready: 'bg-green-100 text-green-800',
    expired: 'bg-slate-100 text-slate-700',
    failed: 'bg-red-100 text-red-700',
  }
  const labels: Record<DownloadStatus, string> = {
    queued: 'Queued',
    processing: 'Processing',
    ready: 'Ready',
    expired: 'Expired',
    failed: 'Failed',
  }
  return (
    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${variants[status]}`}>
      {labels[status]}
    </span>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  )
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  )
}

function BoltIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />
    </svg>
  )
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
    </svg>
  )
}
