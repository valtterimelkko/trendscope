import Link from 'next/link'
import { ArrowRight, Check, Cloud, Gauge, Shield, Zap } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center gap-2">
              <Cloud className="h-7 w-7 text-primary" />
              <span className="font-display font-semibold text-lg">Utility Processor</span>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                Log in
              </Link>
              <Link href="/signup" className="btn-primary text-sm">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-primary/10 text-primary text-sm font-medium">
            Upload → Process → Download
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-semibold tracking-tight">
            {/* CONTENT_SLOT: landing.hero.headline */}
            One-screen utility with a
            <span className="text-primary"> hero dropzone</span>
          </h1>
          <p className="mt-6 text-lg text-text-secondary max-w-3xl mx-auto">
            {/* CONTENT_SLOT: landing.hero.subheadline */}
            Auto-start uploads for simple jobs, or pause and configure first. Determinate progress, retries, and usage meters are built in.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/signup" className="btn-primary text-sm px-6 py-2.5">
              {/* CONTENT_SLOT: landing.cta.primary */}
              Try a sample conversion
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link href="#features" className="btn-secondary text-sm px-6 py-2.5">
              {/* CONTENT_SLOT: landing.cta.secondary */}
              View patterns
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-display font-semibold">
              {/* CONTENT_SLOT: landing.features.title */}
              Research-backed UX for utility SaaS
            </h2>
            <p className="mt-4 text-text-secondary max-w-2xl mx-auto">
              Patterns from TinyPNG, CloudConvert, and remove.bg are already wired in.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Cloud className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[0].title */}
                Hero dropzone
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[0].description */}
                Above-the-fold uploader with drag-over states and pre-validation for size/type before you waste time.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[1].title */}
                Waiting UX that reassures
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[1].description */}
                Determinate progress for upload vs processing, smoothed so it never hangs at 99%, plus soft-failure retries.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Gauge className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[2].title */}
                Quotas + paywall clarity
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[2].description */}
                Usage meters, free-first downloads, and gentle upsells replace surprise errors and blocked flows.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 border-t border-border" id="pricing">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-display font-semibold">
              Usage-aware pricing
            </h2>
            <p className="mt-4 text-text-secondary">
              Bill on credits or minutes. Let them try before you prompt an upgrade.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {/* Starter */}
            <div className="card p-6">
              <h3 className="font-semibold">Free</h3>
              <p className="text-text-muted text-sm mt-1">First 3 jobs on us</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">$0</span>
                <span className="text-text-secondary">/month</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Auto-start uploads
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  500MB cap per file
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Determinate progress
                </li>
              </ul>
              <Link href="/signup?plan=starter" className="btn-secondary w-full mt-6">
                Get Started
              </Link>
            </div>

            {/* Pro - Highlighted */}
            <div className="card p-6 border-primary border-2 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="px-2 py-1 bg-primary text-white text-xs font-medium rounded">
                  Popular
                </span>
              </div>
              <h3 className="font-semibold">Pro</h3>
              <p className="text-text-muted text-sm mt-1">For active pipelines</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">$24</span>
                <span className="text-text-secondary">/month</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  50 credits / month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Manual start mode
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Retry failed jobs
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Webhook receipts
                </li>
              </ul>
              <Link href="/signup?plan=pro" className="btn-primary w-full mt-6">
                Get Started
              </Link>
            </div>

            {/* Enterprise */}
            <div className="card p-6">
              <h3 className="font-semibold">Enterprise</h3>
              <p className="text-text-muted text-sm mt-1">High-volume & API</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">Custom</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Unlimited jobs
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Priority processing
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  SSO + audit logs
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Dedicated support
                </li>
              </ul>
              <Link href="/contact" className="btn-secondary w-full mt-6">
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-primary" />
              <span className="font-display font-medium">Utility Processor</span>
            </div>
            <p className="text-xs text-text-muted">
              {new Date().getFullYear()} Utility Processor. Built with minimalist SaaS patterns.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
