import Link from 'next/link'
import { ArrowRight, BarChart3, Shield, Zap, Globe, Check } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-primary" />
              <span className="font-display font-bold text-xl">Analytics</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login" className="text-sm font-medium text-foreground/80 hover:text-foreground">
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
      <section className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold tracking-tight">
            {/* CONTENT_SLOT: landing.hero.headline */}
            Simple analytics for
            <span className="text-gradient"> modern teams</span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-foreground/70 max-w-2xl mx-auto">
            {/* CONTENT_SLOT: landing.hero.subheadline */}
            Get the insights you need without the complexity. Privacy-friendly,
            lightweight, and beautiful analytics for your website.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup" className="btn-primary text-base px-8 py-3">
              {/* CONTENT_SLOT: landing.cta.primary */}
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link href="#demo" className="btn-secondary text-base px-8 py-3">
              View Demo
            </Link>
          </div>
          <p className="mt-4 text-sm text-foreground/50">
            No credit card required. 14-day free trial.
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-display font-bold">
              {/* CONTENT_SLOT: landing.features.title */}
              Everything you need, nothing you don&apos;t
            </h2>
            <p className="mt-4 text-lg text-foreground/70 max-w-2xl mx-auto">
              Built for simplicity and speed. Get meaningful insights in seconds.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[0].title */}
                Lightning Fast
              </h3>
              <p className="text-foreground/70">
                {/* CONTENT_SLOT: landing.features.items[0].description */}
                Our script is under 1KB. Your site stays fast while you get all the insights.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[1].title */}
                Privacy First
              </h3>
              <p className="text-foreground/70">
                {/* CONTENT_SLOT: landing.features.items[1].description */}
                No cookies, no personal data. GDPR, CCPA, and PECR compliant out of the box.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Globe className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {/* CONTENT_SLOT: landing.features.items[2].title */}
                Share Publicly
              </h3>
              <p className="text-foreground/70">
                {/* CONTENT_SLOT: landing.features.items[2].description */}
                Make your dashboard public with one click. Build trust with transparency.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20" id="pricing">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-display font-bold">Simple, transparent pricing</h2>
            <p className="mt-4 text-lg text-foreground/70">
              Pay based on your usage. No hidden fees.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Starter Plan */}
            <div className="card p-8">
              <h3 className="text-lg font-semibold">Starter</h3>
              <p className="text-foreground/70 text-sm mt-1">For personal projects</p>
              <div className="mt-4">
                <span className="text-4xl font-bold">$9</span>
                <span className="text-foreground/70">/month</span>
              </div>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Up to 1,000 events/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  7-day data retention
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Email support
                </li>
              </ul>
              <Link href="/signup?plan=starter" className="btn-secondary w-full mt-8">
                Get Started
              </Link>
            </div>

            {/* Pro Plan - Highlighted */}
            <div className="card p-8 border-primary border-2 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="badge bg-primary text-white px-3 py-1">Popular</span>
              </div>
              <h3 className="text-lg font-semibold">Pro</h3>
              <p className="text-foreground/70 text-sm mt-1">For growing teams</p>
              <div className="mt-4">
                <span className="text-4xl font-bold">$29</span>
                <span className="text-foreground/70">/month</span>
              </div>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Up to 50,000 events/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  1-year data retention
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Priority support
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Team members
                </li>
              </ul>
              <Link href="/signup?plan=pro" className="btn-primary w-full mt-8">
                Get Started
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="card p-8">
              <h3 className="text-lg font-semibold">Enterprise</h3>
              <p className="text-foreground/70 text-sm mt-1">For large organizations</p>
              <div className="mt-4">
                <span className="text-4xl font-bold">Custom</span>
              </div>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Unlimited events
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Unlimited retention
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Dedicated support
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-success" />
                  Custom integrations
                </li>
              </ul>
              <Link href="/contact" className="btn-secondary w-full mt-8">
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="font-display font-semibold">Analytics</span>
            </div>
            <p className="text-sm text-foreground/50">
              {new Date().getFullYear()} Analytics Dashboard. All rights reserved.
            </p>
            <div className="flex items-center gap-2 text-sm text-foreground/50">
              <Shield className="h-4 w-4" />
              Privacy Friendly | GDPR Compliant
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
