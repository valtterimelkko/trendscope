import Link from 'next/link'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-background/80 backdrop-blur-sm border-b border-border z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <BoxIcon className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold text-foreground">Download Vault</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-sm font-medium text-muted hover:text-foreground transition-colors"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover transition-colors"
              >
                Start free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-light rounded-full mb-6">
            <SparklesIcon className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">Upload → Deliver → Download</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6">
            Ship digital packs with a
            <span className="text-primary"> hero dropzone</span>
          </h1>

          <p className="text-xl text-muted max-w-3xl mx-auto mb-8">
            Let customers drag a file, auto-start delivery, and grab their download link in seconds.
            Clear quotas, waiting UX, and a gated locker are baked in.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup"
              className="w-full sm:w-auto px-8 py-4 bg-primary text-white text-lg font-medium rounded-xl hover:bg-primary-hover transition-colors shadow-lg"
            >
              Try a sample download
            </Link>
            <Link
              href="#features"
              className="w-full sm:w-auto px-8 py-4 border border-border text-foreground text-lg font-medium rounded-xl hover:bg-surface-hover transition-colors"
            >
              See the flow
            </Link>
          </div>
        </div>
      </section>

      {/* Instant preview */}
      <section className="px-4 pb-20">
        <div className="max-w-5xl mx-auto">
          <div className="aspect-video bg-surface border border-border rounded-2xl shadow-xl overflow-hidden">
            <div className="h-12 bg-surface-hover border-b border-border flex items-center px-4 gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span className="text-xs text-muted ml-3">Hero dropzone + quota meter</span>
            </div>
            <div className="p-8 grid md:grid-cols-3 gap-6 h-[calc(100%-48px)]">
              <div className="md:col-span-2 rounded-xl border border-dashed border-primary/40 bg-primary/5 p-6 flex flex-col justify-center text-center">
                <UploadIcon className="w-10 h-10 text-primary mx-auto mb-3" />
                <p className="font-semibold text-foreground">Drop your pack to auto-start delivery</p>
                <p className="text-sm text-muted mt-2">Idle → Uploading → Processing → Ready with signed link</p>
              </div>
              <div className="rounded-xl border border-border p-6 bg-background flex flex-col gap-4">
                <div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted">Downloads this month</span>
                    <span className="font-semibold text-foreground">12 / 30</span>
                  </div>
                  <div className="h-2 bg-surface-hover rounded-full overflow-hidden mt-2">
                    <div className="h-full bg-primary rounded-full" style={{ width: '40%' }} />
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm text-muted">
                  <ShieldIcon className="w-4 h-4 text-primary" />
                  Signed URLs expire in 24h for safety.
                </div>
                <div className="flex items-center gap-3 text-sm text-muted">
                  <BoltIcon className="w-4 h-4 text-accent" />
                  Permeable paywall: first download is free, no account needed.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 bg-surface">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Minimalist patterns baked in</h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              The template follows the research playbook: action-first UI, clear limits, and trustworthy delivery.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <CloudIcon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Hero dropzone</h3>
              <p className="text-muted">
                The upload area owns the above-the-fold space with drag-over states, size validation, and auto-start delivery.
              </p>
            </div>

            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-secondary/30 rounded-xl flex items-center justify-center mb-4">
                <GaugeIcon className="w-6 h-6 text-secondary-hover" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Quota meter</h3>
              <p className="text-muted">
                Show remaining downloads and limits up-front. Nudge upgrades instead of surprising users at checkout.
              </p>
            </div>

            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-accent/20 rounded-xl flex items-center justify-center mb-4">
                <LockIcon className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Gated locker</h3>
              <p className="text-muted">
                Deliver signed URLs with retention timers, error recovery, and a soft paywall for HD or additional assets.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Usage-based pricing that matches intent</h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Let people download before committing. Gate HD, extra seats, or higher limits when they see value.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {/* Starter */}
            <div className="p-6 bg-surface border border-border rounded-2xl">
              <h3 className="text-lg font-semibold text-foreground mb-1">Sampler</h3>
              <p className="text-sm text-muted mb-4">Try 3 downloads free</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$0</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  3 free downloads
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Signed URLs (24h)
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Email receipts
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center border border-border rounded-lg text-foreground hover:bg-surface-hover transition-colors"
              >
                Start free
              </Link>
            </div>

            {/* Creator */}
            <div className="p-6 bg-surface border-2 border-primary rounded-2xl relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-white text-xs font-medium rounded-full">
                Popular
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-1">Creator</h3>
              <p className="text-sm text-muted mb-4">For active sellers</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$19</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  50 downloads / mo
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  HD + ZIP bundles
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Custom license keys
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
              >
                Start free trial
              </Link>
            </div>

            {/* Studio */}
            <div className="p-6 bg-surface border border-border rounded-2xl">
              <h3 className="text-lg font-semibold text-foreground mb-1">Studio</h3>
              <p className="text-sm text-muted mb-4">For large catalogs</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$59</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Unlimited downloads
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Team seats & API
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Priority webhooks
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center border border-border rounded-lg text-foreground hover:bg-surface-hover transition-colors"
              >
                Talk to us
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-primary">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Let people download before they bounce</h2>
          <p className="text-lg text-white/80 mb-8">
            Deliver value in one click, then invite them to create an account for HD, history, and receipts.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-4 bg-white text-primary text-lg font-medium rounded-xl hover:bg-gray-100 transition-colors"
          >
            Launch the download locker
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <BoxIcon className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm text-muted">© 2024 Download Vault</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted">
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
            <a href="#" className="hover:text-foreground transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Icons
function BoxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7l9 4 9-4M3 7l9-4 9 4M3 7v10l9 4 9-4V7" />
    </svg>
  )
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  )
}

function CloudIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v8" />
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

function LockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c1.104 0 2 .896 2 2v3a2 2 0 11-4 0v-3c0-1.104.896-2 2-2zM8 11V7a4 4 0 118 0v4m-9 2h10a2 2 0 012 2v4a2 2 0 01-2 2H7a2 2 0 01-2-2v-4a2 2 0 012-2z" />
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

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  )
}
