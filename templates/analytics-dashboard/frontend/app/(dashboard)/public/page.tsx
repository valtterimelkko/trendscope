'use client'

import { useState } from 'react'
import { Globe, Copy, Check, Eye, EyeOff } from 'lucide-react'

export default function PublicDashboardPage() {
  const [isPublic, setIsPublic] = useState(false)
  const [copied, setCopied] = useState(false)

  const publicUrl = 'https://analytics.example.com/share/abc123xyz'

  const handleCopy = async () => {
    await navigator.clipboard.writeText(publicUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">Public Dashboard</h1>
        <p className="text-foreground/70 mt-1">
          Share your analytics publicly to build trust with your audience.
        </p>
      </div>

      {/* Toggle Card */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isPublic ? 'bg-success/10' : 'bg-surface'
            }`}>
              {isPublic ? (
                <Eye className="h-5 w-5 text-success" />
              ) : (
                <EyeOff className="h-5 w-5 text-foreground/40" />
              )}
            </div>
            <div>
              <p className="font-semibold">Public Stats Page</p>
              <p className="text-sm text-foreground/60">
                {isPublic
                  ? 'Anyone with the link can view your stats'
                  : 'Your stats are private'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsPublic(!isPublic)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isPublic ? 'bg-success' : 'bg-gray-300 dark:bg-slate-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isPublic ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Public URL */}
      {isPublic && (
        <div className="card p-6 mb-6 animate-fade-in">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary" />
            Your Public URL
          </h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={publicUrl}
              readOnly
              className="input flex-1 bg-surface"
            />
            <button
              onClick={handleCopy}
              className="btn-secondary flex items-center gap-2"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 text-success" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy
                </>
              )}
            </button>
          </div>
          <p className="text-sm text-foreground/60 mt-3">
            Share this link anywhere. Perfect for &quot;Build in Public&quot; transparency.
          </p>
        </div>
      )}

      {/* Preview Card */}
      <div className="card p-6">
        <h2 className="font-semibold mb-4">What&apos;s Visible Publicly</h2>
        <ul className="space-y-3 text-sm">
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-success" />
            Total visitors and pageviews
          </li>
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-success" />
            Traffic sources breakdown
          </li>
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-success" />
            Top pages
          </li>
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-success" />
            Geographic distribution
          </li>
          <li className="flex items-center gap-2 text-foreground/50">
            <EyeOff className="h-4 w-4" />
            Individual user sessions (never shared)
          </li>
          <li className="flex items-center gap-2 text-foreground/50">
            <EyeOff className="h-4 w-4" />
            Billing information (never shared)
          </li>
        </ul>
      </div>
    </div>
  )
}
