import Link from 'next/link'
import { ArrowRight, Zap, Command, Layers, Users, Check, Keyboard } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center gap-2">
              <Layers className="h-7 w-7 text-primary" />
              <span className="font-display font-semibold text-lg">Productivity</span>
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
            <Keyboard className="h-4 w-4" />
            Keyboard-first design
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-semibold tracking-tight">
            {/* CONTENT_SLOT: landing.hero.headline */}
            Build products at the
            <span className="text-primary"> speed of thought</span>
          </h1>
          <p className="mt-6 text-lg text-text-secondary max-w-2xl mx-auto">
            {/* CONTENT_SLOT: landing.hero.subheadline */}
            The issue tracker designed for high-performance teams. Keyboard shortcuts,
            instant search, and real-time collaboration.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/signup" className="btn-primary text-sm px-6 py-2.5">
              {/* CONTENT_SLOT: landing.cta.primary */}
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <span>Press</span>
              <kbd>⌘</kbd>
              <kbd>K</kbd>
              <span>to try it</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-display font-semibold">
              {/* CONTENT_SLOT: landing.features.title */}
              Built for speed
            </h2>
            <p className="mt-4 text-text-secondary max-w-2xl mx-auto">
              Every interaction is optimized for keyboard power users.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Command className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                {/* CONTENT_SLOT: landing.features.items[0].title */}
                Command Palette
                <span className="keyboard-hint"><kbd>⌘K</kbd></span>
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[0].description */}
                Access any action instantly. Create issues, change status, assign teammates—all from the keyboard.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[1].title */}
                Real-time Sync
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[1].description */}
                See changes as they happen. No refresh needed. Your team stays in sync automatically.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card p-6 group">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[2].title */}
                Team Collaboration
              </h3>
              <p className="text-sm text-text-secondary">
                {/* CONTENT_SLOT: landing.features.items[2].description */}
                Assign, comment, and track progress together. Built for teams that ship fast.
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
              Simple per-seat pricing
            </h2>
            <p className="mt-4 text-text-secondary">
              Pay for what you use. Add or remove seats anytime.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {/* Starter */}
            <div className="card p-6">
              <h3 className="font-semibold">Starter</h3>
              <p className="text-text-muted text-sm mt-1">For small teams</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">$8</span>
                <span className="text-text-secondary">/seat/month</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Up to 5 seats
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Unlimited issues
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Basic integrations
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
              <p className="text-text-muted text-sm mt-1">For growing teams</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">$12</span>
                <span className="text-text-secondary">/seat/month</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Up to 20 seats
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Advanced analytics
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Priority support
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  API access
                </li>
              </ul>
              <Link href="/signup?plan=pro" className="btn-primary w-full mt-6">
                Get Started
              </Link>
            </div>

            {/* Enterprise */}
            <div className="card p-6">
              <h3 className="font-semibold">Enterprise</h3>
              <p className="text-text-muted text-sm mt-1">For large organizations</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">Custom</span>
              </div>
              <ul className="mt-6 space-y-2">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Unlimited seats
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  SSO & SAML
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Dedicated support
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  SLA guarantee
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
              <Layers className="h-5 w-5 text-primary" />
              <span className="font-display font-medium">Productivity</span>
            </div>
            <p className="text-xs text-text-muted">
              {new Date().getFullYear()} Productivity Tool. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
