'use client'

import { useState } from 'react'
import { Copy, Check, Code } from 'lucide-react'

export default function SnippetPage() {
  const [copied, setCopied] = useState(false)

  const trackingCode = `<script defer data-domain="yoursite.com" src="https://analytics.example.com/script.js"></script>`

  const handleCopy = async () => {
    await navigator.clipboard.writeText(trackingCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-bold">Tracking Code</h1>
        <p className="text-foreground/70 mt-1">
          Add this snippet to your website to start tracking visitors.
        </p>
      </div>

      {/* Snippet Card */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Code className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">JavaScript Snippet</h2>
          </div>
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

        <pre className="bg-slate-900 text-slate-50 p-4 rounded-lg overflow-x-auto text-sm font-mono">
          <code>{trackingCode}</code>
        </pre>

        <div className="mt-4 text-sm text-foreground/70 space-y-2">
          <p>
            <strong>Where to add it:</strong> Paste this snippet in the{' '}
            <code className="bg-surface px-1 rounded">&lt;head&gt;</code> section of your HTML.
          </p>
          <p>
            <strong>Note:</strong> Replace <code className="bg-surface px-1 rounded">yoursite.com</code> with your actual domain.
          </p>
        </div>
      </div>

      {/* Framework Guides */}
      <div className="card p-6">
        <h2 className="font-semibold mb-4">Framework Guides</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            { name: 'Next.js', icon: '▲' },
            { name: 'React', icon: '⚛️' },
            { name: 'Vue', icon: '💚' },
            { name: 'WordPress', icon: '📝' },
          ].map((framework) => (
            <button
              key={framework.name}
              className="flex items-center gap-3 p-4 border border-border rounded-lg hover:bg-surface transition-colors text-left"
            >
              <span className="text-2xl">{framework.icon}</span>
              <span className="font-medium">{framework.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Verification Status */}
      <div className="card p-6 mt-6">
        <h2 className="font-semibold mb-4">Installation Status</h2>
        <div className="flex items-center gap-3 p-4 bg-warning/10 rounded-lg">
          <div className="w-3 h-3 rounded-full bg-warning animate-pulse" />
          <div>
            <p className="font-medium text-warning">Waiting for first event</p>
            <p className="text-sm text-foreground/60 mt-0.5">
              Add the tracking code to your site, then refresh this page.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
