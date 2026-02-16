'use client'

import { useMemo, useState } from 'react'
import { FREE_UPLOAD_CAP_BYTES, FREE_UPLOAD_CAP_MB } from '@/constants/uploadLimits'

type JobStatus = 'queued' | 'config' | 'processing' | 'done' | 'failed'

export default function DashboardPage() {
  const [dragActive, setDragActive] = useState(false)
  const [jobStatus, setJobStatus] = useState<JobStatus>('queued')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'auto' | 'manual'>('auto')
  const [lastFile, setLastFile] = useState('Sample-input.pdf')

  const usage = { used: 14, limit: 40 }

  const activeJobs = useMemo(
    () => [
      { id: '1', name: 'Press-kit.png', status: 'processing' as JobStatus, start: 'Auto', size: '240MB', eta: '35s' },
      { id: '2', name: 'Invoice.pdf', status: 'config' as JobStatus, start: 'Manual', size: '12MB', eta: 'Awaiting start' },
      { id: '3', name: 'Clip.mov', status: 'queued' as JobStatus, start: 'Auto', size: '1.1GB', eta: '—' },
    ],
    []
  )

  const history = useMemo(
    () => [
      { id: 'h1', name: 'Archive.zip', status: 'done' as JobStatus, time: '2m ago', note: 'Deleted in 24h' },
      { id: 'h2', name: 'Screenshot.png', status: 'failed' as JobStatus, time: '9m ago', note: 'Network drop – retry saved' },
    ],
    []
  )

  const handleFile = (file: File) => {
    setLastFile(file.name)

    if (file.size > FREE_UPLOAD_CAP_BYTES) {
      setError(`File too large for free tier (${Math.round(FREE_UPLOAD_CAP_MB)}MB). Upgrade for higher caps or process a smaller file.`)
      setJobStatus('failed')
      setProgress(0)
      return
    }

    setError(null)
    if (mode === 'manual') {
      setJobStatus('config')
      setProgress(0)
      return
    }

    setJobStatus('processing')
    setProgress(20)
    setTimeout(() => setProgress(68), 500)
    setTimeout(() => {
      setProgress(100)
      setJobStatus('done')
    }, 1200)
  }

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
    const file = event.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Process files fast</h1>
          <p className="text-muted mt-1">Hero dropzone, waiting UX, and quota meter are included from the minimalist SaaS research.</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={() => setMode(mode === 'auto' ? 'manual' : 'auto')}
            className="px-3 py-2 border border-border rounded-lg hover:bg-surface"
          >
            Mode: <span className="font-semibold ml-1">{mode === 'auto' ? 'Auto-start' : 'Manual start'}</span>
          </button>
          <span className="text-muted hidden sm:inline">Toggle between magic and control.</span>
        </div>
      </div>

      {/* Quota meter + guardrails */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="p-4 bg-surface border border-border rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">Jobs this month</span>
            <span className="font-semibold text-foreground">{usage.used} / {usage.limit}</span>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden mt-2">
            <div className="h-full bg-primary rounded-full" style={{ width: `${(usage.used / usage.limit) * 100}%` }} />
          </div>
          <p className="text-xs text-muted mt-2">Show limits first; upsell gently when the meter turns amber.</p>
        </div>
        <div className="p-4 bg-surface border border-border rounded-lg flex items-center gap-3">
          <ShieldIcon className="w-5 h-5 text-primary" />
          <div className="text-sm">
            <p className="font-semibold text-foreground">Deterministic progress</p>
            <p className="text-muted">Separate upload vs processing phases so users know why they are waiting.</p>
          </div>
        </div>
        <div className="p-4 bg-surface border border-border rounded-lg flex items-center gap-3">
          <GaugeIcon className="w-5 h-5 text-primary" />
          <div className="text-sm">
            <p className="font-semibold text-foreground">Soft failures</p>
            <p className="text-muted">Failed uploads stay in the list with Retry so users never re-select files.</p>
          </div>
        </div>
      </div>

      {/* Hero dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-2xl p-6 transition-all bg-background ${dragActive ? 'border-primary/70 bg-primary/5' : 'border-border'}`}
      >
        <div className="flex flex-col lg:flex-row items-start gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <UploadIcon className="w-8 h-8 text-primary" />
              <div>
                <p className="text-lg font-semibold text-foreground">Drop a file to auto-start</p>
                <p className="text-sm text-muted">PNG, JPG, PDF, MOV up to 500MB on free. We validate on drag so errors show early.</p>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <label className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-primary-hover">
                <input
                  type="file"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) handleFile(file)
                  }}
                  aria-label="Select a file (PNG/JPG/PDF/MOV up to 500MB) to process and download"
                />
                Browse files
              </label>
              <span className="text-xs text-muted">Paste images with ⌘+V. Cloud pickers slot here.</span>
            </div>

            <div className="mt-6 bg-surface border border-border rounded-xl p-4">
              <div className="flex items-center justify-between text-sm text-muted">
                <span>{lastFile}</span>
                <StatusBadge status={jobStatus} />
              </div>
              <div className="h-2 bg-surface-hover rounded-full overflow-hidden mt-3">
                <div
                  className={`h-full rounded-full transition-all ${jobStatus === 'failed' ? 'bg-red-400' : 'bg-primary'}`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-muted mt-2">
                {jobStatus === 'done'
                  ? 'Processed. Download link ready. We keep it for 24h.'
                  : jobStatus === 'processing'
                    ? 'Upload + processing running. ETA displayed; progress is smoothed to avoid 99% stalls.'
                    : jobStatus === 'config'
                      ? 'Manual mode: review options before starting.'
                      : jobStatus === 'failed'
                        ? error || 'Upload failed. Retry without losing context.'
                        : 'Auto-start is enabled. Switch to manual to queue first.'}
              </p>
            </div>

            {error && (
              <div className="mt-3 p-3 border border-red-200 bg-red-50 rounded-lg text-sm text-red-700 flex items-center gap-2">
                <AlertIcon className="w-4 h-4" />
                {error}
              </div>
            )}
          </div>

          <div className="w-full lg:w-72 bg-surface border border-border rounded-xl p-4 space-y-3">
            <p className="text-sm font-semibold text-foreground">Usage guidance</p>
            <ul className="space-y-2 text-xs text-muted">
              <li>• Permeable paywall: first 3 jobs free, then upsell.</li>
              <li>• Manual start for heavy conversions; auto-start for quick wins.</li>
              <li>• Show ETA and phase (upload vs process) to reduce anxiety.</li>
              <li>• Failed jobs persist with retry.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Active jobs */}
      <div className="bg-surface border border-border rounded-xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <p className="text-sm font-semibold text-foreground">Active jobs</p>
          <span className="text-xs text-muted">Auto vs manual start reflected in each row.</span>
        </div>
        <div className="divide-y divide-border">
          {activeJobs.map((job) => (
            <div key={job.id} className="grid md:grid-cols-5 gap-4 p-4 items-center">
              <div className="md:col-span-2">
                <p className="text-sm font-semibold text-foreground">{job.name}</p>
                <p className="text-xs text-muted">Start mode: {job.start}</p>
              </div>
              <div className="text-xs text-muted">{job.size}</div>
              <div className="flex items-center gap-2">
                <StatusBadge status={job.status} />
                {job.status === 'processing' && <span className="text-xs text-muted">ETA {job.eta}</span>}
              </div>
              <div className="flex gap-2 justify-end">
                <button className="text-xs text-muted hover:text-foreground">Download</button>
                <button className="text-xs text-muted hover:text-foreground">Redo</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* History */}
      <div className="bg-surface border border-border rounded-xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <p className="text-sm font-semibold text-foreground">History</p>
          <span className="text-xs text-muted">We keep failed items for one-click retry.</span>
        </div>
        <div className="divide-y divide-border">
          {history.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-semibold text-foreground">{item.name}</p>
                <p className="text-xs text-muted">{item.note}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={item.status} />
                <span className="text-xs text-muted">{item.time}</span>
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

function StatusBadge({ status }: { status: JobStatus }) {
  const styles: Record<JobStatus, string> = {
    queued: 'bg-gray-100 text-gray-700',
    config: 'bg-blue-100 text-blue-800',
    processing: 'bg-amber-100 text-amber-800',
    done: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-700',
  }
  const labels: Record<JobStatus, string> = {
    queued: 'Queued',
    config: 'Config',
    processing: 'Processing',
    done: 'Done',
    failed: 'Failed',
  }
  return (
    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${styles[status]}`}>
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

function GaugeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 13l3-3m-3 3l-3-3m3 3v6m8-3a9 9 0 10-16 0" />
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
