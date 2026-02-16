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
                <PenIcon className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold text-foreground">Content Studio</span>
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
                Start creating
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          {/* Decorative element */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-light rounded-full mb-8">
            <SparklesIcon className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">Built for creators</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6">
            Where great content
            <span className="text-primary"> comes to life</span>
          </h1>

          <p className="text-xl text-muted max-w-2xl mx-auto mb-10">
            The all-in-one platform for writers, creators, and media teams to draft,
            collaborate, and publish beautiful content.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup"
              className="w-full sm:w-auto px-8 py-4 bg-primary text-white text-lg font-medium rounded-xl hover:bg-primary-hover transition-colors shadow-lg"
            >
              Start for free
            </Link>
            <Link
              href="#features"
              className="w-full sm:w-auto px-8 py-4 border border-border text-foreground text-lg font-medium rounded-xl hover:bg-surface-hover transition-colors"
            >
              See how it works
            </Link>
          </div>
        </div>
      </section>

      {/* Preview image */}
      <section className="px-4 pb-20">
        <div className="max-w-5xl mx-auto">
          <div className="aspect-video bg-surface border border-border rounded-2xl shadow-xl overflow-hidden">
            <div className="h-10 bg-surface-hover border-b border-border flex items-center px-4 gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
            </div>
            <div className="p-8 flex items-center justify-center h-[calc(100%-40px)]">
              <div className="text-center text-muted">
                <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Product screenshot placeholder</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 bg-surface">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Everything you need to create</h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              From first draft to final publish, Content Studio has the tools you need.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <EditIcon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Rich text editor</h3>
              <p className="text-muted">
                A beautiful writing experience with markdown support, embeds, and real-time collaboration.
              </p>
            </div>

            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-secondary/30 rounded-xl flex items-center justify-center mb-4">
                <ImageIcon className="w-6 h-6 text-secondary-hover" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Media library</h3>
              <p className="text-muted">
                Organize images, videos, and files in one place. Drag and drop into any post.
              </p>
            </div>

            <div className="p-6 bg-background rounded-2xl border border-border">
              <div className="w-12 h-12 bg-accent/20 rounded-xl flex items-center justify-center mb-4">
                <CalendarIcon className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Content calendar</h3>
              <p className="text-muted">
                Plan and schedule your content with a visual calendar. Never miss a publish date.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Simple, transparent pricing</h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              Start for free, upgrade when you need more.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {/* Starter */}
            <div className="p-6 bg-surface border border-border rounded-2xl">
              <h3 className="text-lg font-semibold text-foreground mb-1">Starter</h3>
              <p className="text-sm text-muted mb-4">For individual creators</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$0</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  10 posts
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  500MB media storage
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  5 scheduled posts
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center border border-border rounded-lg text-foreground hover:bg-surface-hover transition-colors"
              >
                Get started
              </Link>
            </div>

            {/* Creator */}
            <div className="p-6 bg-surface border-2 border-primary rounded-2xl relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-white text-xs font-medium rounded-full">
                Popular
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-1">Creator</h3>
              <p className="text-sm text-muted mb-4">For growing creators</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$15</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  100 posts
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  10GB media storage
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  50 scheduled posts
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  3 team members
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
              <p className="text-sm text-muted mb-4">For teams & agencies</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-foreground">$39</span>
                <span className="text-muted">/month</span>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Unlimited posts
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  100GB media storage
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  Unlimited scheduling
                </li>
                <li className="flex items-center gap-2 text-sm text-muted">
                  <CheckIcon className="w-4 h-4 text-accent" />
                  10 team members
                </li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center border border-border rounded-lg text-foreground hover:bg-surface-hover transition-colors"
              >
                Contact sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-primary">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to start creating?</h2>
          <p className="text-lg text-white/80 mb-8">
            Join thousands of creators who trust Content Studio for their publishing needs.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-4 bg-white text-primary text-lg font-medium rounded-xl hover:bg-gray-100 transition-colors"
          >
            Start your free trial
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <PenIcon className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm text-muted">© 2024 Content Studio</span>
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
function PenIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
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

function EditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  )
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
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
