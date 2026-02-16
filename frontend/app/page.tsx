export default function Home() {
  return (
    <main className="min-h-screen bg-(--color-background)">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-heading-1 mb-6">
            The Bloomberg Terminal for Short-Form Video Trends
          </h1>
          
          <p className="text-body-lg mb-8 text-(--color-foreground-muted)">
            Real-time trend intelligence. Professional-grade detection. Alerts before the mainstream knows.
          </p>
          
          <div className="flex gap-4 justify-center">
            <button className="btn-primary">
              Get Started
            </button>
            <button className="px-6 py-3 border-2 border-(--color-primary) text-(--color-primary) rounded-lg font-semibold hover:bg-(--color-primary) hover:text-white transition-all">
              View Demo
            </button>
          </div>
          
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-heading-4 mb-2">Fast Detection</h3>
              <p className="text-body-sm text-(--color-foreground-muted)">
                Alerts within 6-24 hours of trend emergence
              </p>
            </div>
            
            <div className="card">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-heading-4 mb-2">Velocity Tracking</h3>
              <p className="text-body-sm text-(--color-foreground-muted)">
                Monitor growth rate, not just volume
              </p>
            </div>
            
            <div className="card">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-heading-4 mb-2">Niche Focused</h3>
              <p className="text-body-sm text-(--color-foreground-muted)">
                Filter trends by your specific niches
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
