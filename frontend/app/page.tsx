import { Button } from '@/components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { CheckCircle2, TrendingUp, Zap, Target, Bell, Users, FileText } from 'lucide-react';
import { Logo } from '@/components/common/Logo';

/* ─── Small reusable pieces ───────────────────────────────────────────── */

function CategoryLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs font-semibold tracking-widest uppercase text-[#00D9FF] mb-3 block">
      {children}
    </span>
  );
}

function DarkCard({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[#111111] border border-white/[0.07] rounded-2xl p-6 ${className}`}>
      {children}
    </div>
  );
}

function AlertCard({
  icon,
  text,
  className = '',
}: {
  icon: React.ReactNode;
  text: string;
  className?: string;
}) {
  return (
    <div
      className={`bg-[#111111] border border-white/[0.08] rounded-2xl px-5 py-3 flex items-center gap-3 text-sm text-white/70 w-fit ${className}`}
    >
      {icon}
      <span>{text}</span>
    </div>
  );
}

/* ─── Page ────────────────────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div className="dark">
      <main className="min-h-screen bg-[#080808] text-white antialiased">

        {/* ── Navigation ─────────────────────────────────────────────── */}
        <nav className="fixed top-0 z-50 w-full">
          <div className="container mx-auto flex h-20 items-center justify-between px-6">
            {/* Logo */}
            <Logo width={260} height={72} showText={false} />

            {/* Nav links */}
            <div className="hidden md:flex items-center gap-7">
              <a href="#features" className="text-sm text-white/50 hover:text-white transition-colors">Features</a>
              <a href="#pricing"  className="text-sm text-white/50 hover:text-white transition-colors">Pricing</a>
              <a href="#faq"      className="text-sm text-white/50 hover:text-white transition-colors">FAQ</a>
              <a href="/auth/login" className="text-sm text-white/50 hover:text-white transition-colors">Login</a>
              <Button
                asChild
                size="sm"
                className="rounded-full border border-white/20 bg-transparent text-white hover:bg-white/10 text-xs px-5"
              >
                <a href="/auth/signup">Get started</a>
              </Button>
            </div>
          </div>
        </nav>

        {/* ── Hero ────────────────────────────────────────────────────── */}
        <section className="relative min-h-screen overflow-hidden pt-40 bg-gradient-to-b from-[#080808] to-[#050505]">

          {/* Video background — faded, right-aligned */}
          <video
            aria-hidden
            autoPlay
            muted
            loop
            playsInline
            className="pointer-events-none absolute inset-0 w-full h-full object-contain -mt-8"
            style={{ opacity: 0.35 }}
          >
            <source src="/videos/trendscope-intro-semicomplex-final.mp4" type="video/mp4" />
          </video>

          {/* Overlay fade — gradient from dark on left to transparent on right */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background: 'linear-gradient(to right, rgba(8,8,8,0.95) 0%, rgba(8,8,8,0.7) 40%, transparent 80%)',
            }}
          />

          {/* Subtle cyan glow over video */}
          <div
            aria-hidden
            className="pointer-events-none absolute right-[25%] top-1/2 -translate-y-1/2 w-[480px] h-[480px] rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(0,217,255,0.07) 0%, transparent 70%)' }}
          />

          {/* Left text — upper-left, Gitness-style */}
          <div className="container mx-auto px-6 relative z-10">
             <div className="max-w-[280px] pt-4 pb-8">
               <h1 className="text-2xl font-bold leading-[1.1] tracking-tight mb-3 md:text-3xl">
                Real-time trend&nbsp;intelligence.<br />
                Professional-grade&nbsp;detection.<br />
                <span className="text-[#00D9FF]">Alerts before the mainstream&nbsp;knows.</span>
              </h1>
               <p className="text-white/50 text-sm leading-relaxed mb-4 max-w-xs">
                 While you&apos;re sleeping, trends are born. Trendscope detects trends at the
                   micro-influencer layer—where viral content is born.
               </p>
               <div className="flex flex-col gap-2 sm:flex-row">
                 <Button
                   size="sm"
                   asChild
                   className="rounded-full bg-white text-[#080808] hover:bg-white/90 font-semibold px-6"
                 >
                   <a href="/auth/signup">Start Free →</a>
                 </Button>
                 <Button
                   size="sm"
                   asChild
                   className="rounded-full border border-white/20 bg-transparent text-white hover:bg-white/10 px-6"
                >
                  <a href="#how-it-works">See How It Works ↓</a>
                </Button>
              </div>
               <p className="mt-2 text-xs text-white/30">No credit card required. 14-day free trial.</p>

               {/* Trust bar */}
               <div className="mt-6">
                 <p className="text-xs text-white/30 mb-2">
                   Trusted by creators and agencies who treat content like a business
                 </p>
                 <div className="flex items-center gap-4 text-white/25 text-xs font-semibold tracking-wide">
                   <span>CREATORS</span>
                   <span>AGENCIES</span>
                   <span>BRANDS</span>
                   <span>STUDIOS</span>
                 </div>
               </div>
            </div>
          </div>

          {/* Alert cards — floating over the video, right side */}
          <div className="absolute hidden lg:flex flex-col gap-5 z-10 top-[22%] right-[8%]">
            <AlertCard
              className="animate-float-a"
              icon={<span className="text-[#00C853] text-base">✓</span>}
              text="trend alert delivered"
            />
            <AlertCard
              className="ml-16 animate-float-b"
              icon={
                <img
                  src="https://i.pravatar.cc/20?u=sarah-k"
                  className="w-5 h-5 rounded-full"
                  alt="creator avatar"
                />
              }
              text="sarah caught trend +340%"
            />
            <AlertCard
              className="ml-6 animate-float-c"
              icon={<Zap className="w-4 h-4 text-[#FFC107]" />}
              text="velocity surge detected"
            />
          </div>

        </section>

        {/* ── Trend Intelligence feature section ─────────────────────── */}
        <section id="how-it-works" className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">

            {/* Section header — Gitness-style */}
            <div className="flex flex-col md:flex-row md:items-end md:justify-between mb-14 gap-6">
              <div>
                <CategoryLabel>Trend Intelligence</CategoryLabel>
                <h2 className="text-4xl font-bold tracking-tight md:text-5xl">
                  Detect. Alert. Create.
                </h2>
              </div>
              <Button
                asChild
                className="rounded-full border border-white/20 bg-transparent text-white hover:bg-white/10 w-fit"
              >
                <a href="/auth/signup">Get started →</a>
              </Button>
            </div>

            {/* Mock trend-alert UI */}
            <DarkCard className="overflow-hidden">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔥</span>
                  <div>
                    <p className="font-semibold text-white">TREND ALERT</p>
                    <p className="text-xs text-white/40">Detected 2 hours ago · Beauty niche</p>
                  </div>
                </div>
                <span className="text-xs bg-[#00C853]/15 text-[#00C853] border border-[#00C853]/20 rounded-full px-3 py-1">
                  Low saturation
                </span>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-[#080808] rounded-xl p-4">
                  <p className="text-xs text-white/40 mb-1">Sound</p>
                  <p className="font-semibold text-white">&quot;soft glam&quot;</p>
                  <p className="text-[#00D9FF] text-2xl font-bold mt-2">+340%</p>
                  <p className="text-xs text-white/40">velocity in #beauty</p>
                </div>
                <div className="bg-[#080808] rounded-xl p-4">
                  <p className="text-xs text-white/40 mb-1">Creators using it</p>
                  <p className="font-semibold text-white text-2xl">2.3K</p>
                  <p className="text-xs text-white/40 mt-1">micro-influencer layer</p>
                </div>
                <div className="bg-[#080808] rounded-xl p-4">
                  <p className="text-xs text-white/40 mb-1">Window open</p>
                  <p className="font-semibold text-white text-2xl">~18h</p>
                  <p className="text-xs text-white/40 mt-1">before mainstream saturation</p>
                </div>
              </div>

              <div className="mt-6 text-4xl font-bold tracking-tight">
                <span className="text-[#00D9FF]">Detect.</span>{' '}
                <span className="text-white/60">Alert.</span>{' '}
                <span className="text-white/30">Create.</span>
              </div>
            </DarkCard>
          </div>
        </section>

        {/* ── Problem Section ─────────────────────────────────────────── */}
        <section className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="mb-14">
              <CategoryLabel>The Problem</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-5xl max-w-2xl">
                You&apos;re Not Missing Trends.<br />You&apos;re Just Finding Them Too Late.
              </h2>
              <p className="mt-4 text-white/50 text-lg max-w-xl">
                The average creator spends 4 hours a day scrolling TikTok. That&apos;s not research.
                That&apos;s digital drift.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
              {[
                {
                  title: 'Trend Decay',
                  description: 'By the time you spot a sound manually, 50,000 creators already used it.',
                },
                {
                  title: 'Creator Burnout',
                  description: '62% of creators experience burnout from endless scrolling.',
                },
                {
                  title: 'Reactive Content',
                  description: "You're always chasing yesterday's news.",
                },
                {
                  title: 'Algorithm Bias',
                  description: "Your FYP shows you what you already like, not what's about to break.",
                },
              ].map((p) => (
                <DarkCard key={p.title}>
                  <h3 className="font-semibold text-white mb-2">{p.title}</h3>
                  <p className="text-sm text-white/50 leading-relaxed">{p.description}</p>
                </DarkCard>
              ))}
            </div>

            <DarkCard className="border-[#FFC107]/20 bg-[#FFC107]/5">
              <p className="text-xl font-bold text-[#FFC107]">
                You&apos;re paying with your time. And losing anyway.
              </p>
              <p className="mt-1 text-white/60">
                4 hours/day = $3,000/month in lost productivity (at $25/hour)
              </p>
            </DarkCard>
          </div>
        </section>

        {/* ── Trend Decay Dilemma ─────────────────────────────────────── */}
        <section className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="grid lg:grid-cols-2 gap-16 items-start">
              <div>
                <CategoryLabel>Why It Happens</CategoryLabel>
                <h2 className="text-4xl font-bold tracking-tight md:text-5xl">
                  The Trend Decay Dilemma: Why You&apos;re Always 24 Hours Behind
                </h2>
                <p className="mt-4 text-white/50 text-lg">
                  Here&apos;s the brutal truth about TikTok trends: They don&apos;t build slowly.
                  They explode overnight.
                </p>
              </div>

              <DarkCard className="border-[#FF3B30]/20">
                <p className="text-sm font-semibold text-[#FF3B30] mb-4">Your Current Workflow:</p>
                <div className="space-y-3">
                  {[
                    ['9 AM', 'You wake up and start scrolling'],
                    ['11 AM', 'You finally find something "interesting"'],
                    ['12 PM', 'You brief your team / plan your content'],
                    ['3 PM', 'You film'],
                    ['5 PM', 'You edit'],
                    ['7 PM', 'You post'],
                  ].map(([time, action]) => (
                    <div key={time} className="flex gap-4 text-sm">
                      <span className="text-white/30 w-12 shrink-0">{time}</span>
                      <span className="text-white/60">{action}</span>
                    </div>
                  ))}
                  <div className="pt-4 border-t border-white/[0.07]">
                    <p className="text-[#FF3B30] font-bold text-lg">
                      Meanwhile, the trend peaked at 2 PM.
                    </p>
                  </div>
                </div>
              </DarkCard>
            </div>
          </div>
        </section>

        {/* ── How It Works ────────────────────────────────────────────── */}
        <section className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between mb-14 gap-6">
              <div>
                <CategoryLabel>Zero-Effort Setup</CategoryLabel>
                <h2 className="text-4xl font-bold tracking-tight md:text-5xl">
                  Introducing Trendscope:<br />Set it once. Get alerts forever.
                </h2>
              </div>
              <Button
                asChild
                className="rounded-full border border-white/20 bg-transparent text-white hover:bg-white/10 w-fit"
              >
                <a href="/auth/signup">Start free →</a>
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  step: '01',
                  title: 'Select Your Niches',
                  description: 'Beauty. Finance. Gaming. Fashion. 20+ categories.',
                },
                {
                  step: '02',
                  title: 'Connect Your Channels',
                  description: 'Slack. Email. SMS (Agency+). We meet you where you are.',
                },
                {
                  step: '03',
                  title: 'Receive Real-Time Alerts',
                  description: '🔥 TREND ALERT: Sound "soft glam" surging 340% in #beauty.',
                },
                {
                  step: '04',
                  title: 'Create While the Window Is Open',
                  description:
                    'Velocity data. Saturation scores. Example videos. Everything you need.',
                },
              ].map((item) => (
                <DarkCard key={item.step}>
                  <p className="text-4xl font-bold text-white/10 mb-4">{item.step}</p>
                  <h3 className="font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-white/50 leading-relaxed">{item.description}</p>
                </DarkCard>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ────────────────────────────────────────────────── */}
        <section id="features" className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="mb-14">
              <CategoryLabel>What You Get</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-5xl max-w-xl">
                Professional-grade tools built for creators and agencies
              </h2>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: <TrendingUp className="h-6 w-6" />,
                  title: 'Velocity Detection',
                  description:
                    "Track growth rate, not just volume. Catch trends while they're accelerating.",
                },
                {
                  icon: <Users className="h-6 w-6" />,
                  title: 'Micro-Influencer Signal',
                  description:
                    'Monitor accounts with <10k followers—where trends are born, not where they die.',
                },
                {
                  icon: <Bell className="h-6 w-6" />,
                  title: 'Push-First Architecture',
                  description:
                    'Alerts come to you. No dashboards to check. No apps to open.',
                },
                {
                  icon: <Zap className="h-6 w-6" />,
                  title: 'Multi-Channel Delivery',
                  description: 'Slack, email, SMS. Your workflow, your way.',
                },
                {
                  icon: <Target className="h-6 w-6" />,
                  title: 'Saturation Scoring',
                  description: 'Know exactly how much runway a trend has left.',
                },
                {
                  icon: <FileText className="h-6 w-6" />,
                  title: 'Agency White-Label',
                  description: 'Branded reports that make you look like a research powerhouse.',
                },
              ].map((feature) => (
                <DarkCard key={feature.title} className="group hover:border-white/15 transition-colors">
                  <div className="mb-4 text-[#00D9FF]">{feature.icon}</div>
                  <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-sm text-white/50 leading-relaxed">{feature.description}</p>
                </DarkCard>
              ))}
            </div>
          </div>
        </section>

        {/* ── Social Proof ────────────────────────────────────────────── */}
        <section className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="mb-14">
              <CategoryLabel>Testimonials</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-5xl max-w-2xl">
                Trusted by Creators and Agencies Who Treat This Like a Business
              </h2>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {[
                {
                  quote:
                    'I used to wake up at 6 AM to "get ahead" of trends. Now Trendscope does that while I sleep. I filmed a video at 7 AM based on a 6:30 AM alert. It hit 500K views by dinner.',
                  author: 'Sarah K.',
                  role: 'Beauty Creator, 180K followers',
                },
                {
                  quote:
                    'We manage 12 client accounts. Before Trendscope, we had junior staff scrolling 3 hours a day. Now we get a Slack digest every morning with 3-5 viable trends.',
                  author: 'Mark T.',
                  role: 'Boutique Agency Founder',
                },
                {
                  quote:
                    'The white-label reports are genius. I send clients "Market Intelligence" briefs with our branding. They think we have a research team. It\'s just Trendscope.',
                  author: 'Jessica L.',
                  role: 'Social Media Director',
                },
              ].map((t, i) => (
                <DarkCard key={i}>
                  <p className="text-white/60 italic leading-relaxed mb-6 text-sm">
                    &ldquo;{t.quote}&rdquo;
                  </p>
                  <div className="flex items-center gap-3">
                    <img
                      src={`https://i.pravatar.cc/36?u=${t.author}`}
                      className="w-9 h-9 rounded-full"
                      alt={t.author}
                    />
                    <div>
                      <p className="text-sm font-semibold text-white">{t.author}</p>
                      <p className="text-xs text-white/40">{t.role}</p>
                    </div>
                  </div>
                </DarkCard>
              ))}
            </div>
          </div>
        </section>

        {/* ── Pricing ─────────────────────────────────────────────────── */}
        <section id="pricing" className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="mb-14">
              <CategoryLabel>Pricing</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-5xl">
                Simple Pricing. Serious Value.
              </h2>
              <p className="mt-3 text-white/50 text-lg">Choose the plan that fits your needs</p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {[
                {
                  name: 'Free',
                  price: '$0',
                  period: '',
                  description: 'For casual creators testing the water',
                  features: ['Weekly digest (7 trends max)', '1 niche', 'Email delivery', 'Basic trend data'],
                  cta: 'Start Free',
                  highlighted: false,
                },
                {
                  name: 'Solo',
                  price: '$29',
                  period: '/month',
                  description: 'For serious creators who treat TikTok like a business',
                  features: [
                    '2-hour alert latency',
                    'Unlimited niches',
                    'Slack integration',
                    'Saturation tracking',
                    'Velocity scores',
                    'Unlimited alerts',
                  ],
                  cta: 'Start 14-Day Free Trial',
                  highlighted: true,
                },
                {
                  name: 'Agency',
                  price: '$199',
                  period: '/month',
                  description: 'For SMMAs and brand teams managing multiple clients',
                  features: [
                    '30-minute alert latency',
                    '5 client workspaces',
                    'White-label reports',
                    '12 monitored niches',
                    'API access',
                    'Priority support',
                  ],
                  cta: 'Start Agency Trial',
                  highlighted: false,
                },
              ].map((tier) => (
                <div
                  key={tier.name}
                  className={`bg-[#111111] rounded-2xl p-6 flex flex-col border ${
                    tier.highlighted
                      ? 'border-[#00D9FF]/40'
                      : 'border-white/[0.07]'
                  }`}
                >
                  {tier.highlighted && (
                    <span className="text-xs font-semibold tracking-widest uppercase text-[#00D9FF] mb-4 block">
                      Most Popular
                    </span>
                  )}
                  <p className="text-sm text-white/40 mb-1">{tier.name}</p>
                  <div className="mb-2">
                    <span className="text-4xl font-bold text-white">{tier.price}</span>
                    <span className="text-white/40 text-sm">{tier.period}</span>
                  </div>
                  <p className="text-sm text-white/50 mb-6">{tier.description}</p>

                  <ul className="space-y-2 mb-8 flex-1">
                    {tier.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm text-white/60">
                        <CheckCircle2 className="h-4 w-4 text-[#00C853] shrink-0 mt-0.5" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <Button
                    asChild
                    className={
                      tier.highlighted
                        ? 'rounded-full bg-white text-[#080808] hover:bg-white/90 font-semibold'
                        : 'rounded-full border border-white/20 bg-transparent text-white hover:bg-white/10'
                    }
                  >
                    <a href="/auth/signup">{tier.cta} →</a>
                  </Button>
                  <p className="text-center text-xs text-white/30 mt-3">
                    {tier.price === '$0' ? 'No credit card required' : 'Cancel anytime'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── FAQ ─────────────────────────────────────────────────────── */}
        <section id="faq" className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div className="mb-14">
              <CategoryLabel>FAQ</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-5xl">Questions? Answered.</h2>
            </div>

            <Accordion type="single" collapsible className="mx-auto max-w-3xl space-y-2">
              {[
                {
                  q: 'How is this different from TikTok Creative Center?',
                  a: 'Creative Center shows what *was* viral (24-48h delay). We show what\'s *about to be* viral (6-24h detection). Creative Center also filters out "edgy" content—the exact trends creators want to catch early.',
                },
                {
                  q: 'Why should I trust your trend predictions?',
                  a: "We don't predict—we detect. Our algorithm identifies sounds and formats already growing fast among micro-influencers. This isn't fortune-telling; it's pattern recognition backed by velocity data.",
                },
                {
                  q: 'What if I get too many alerts?',
                  a: "We use segmented alerting by niche. A beauty creator won't get gaming alerts. Set velocity thresholds—only alert when growth exceeds your custom percentage.",
                },
                {
                  q: 'How quickly do I get alerts?',
                  a: 'Free tier: Weekly digest. Solo tier: 2-hour latency. Agency tier: 30-minute latency. Enterprise tier: Real-time.',
                },
                {
                  q: 'Can I cancel anytime?',
                  a: 'Yes. No contracts. No cancellation fees. Cancel in Settings → Billing.',
                },
              ].map((item, i) => (
                <AccordionItem
                  key={i}
                  value={`item-${i}`}
                  className="bg-[#111111] border border-white/[0.07] rounded-2xl px-6 data-[state=open]:border-white/[0.12]"
                >
                  <AccordionTrigger className="text-left text-white hover:no-underline py-5 text-sm font-semibold">
                    {item.q}
                  </AccordionTrigger>
                  <AccordionContent className="text-white/50 text-sm leading-relaxed pb-5">
                    {item.a}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </section>

        {/* ── Final CTA ───────────────────────────────────────────────── */}
        <section className="py-28 border-t border-white/[0.05]">
          <div className="container mx-auto px-6">
            <div
              className="rounded-3xl p-16 text-center"
              style={{
                background:
                  'radial-gradient(ellipse at 50% 0%, rgba(0,217,255,0.12) 0%, transparent 70%), #111111',
                border: '1px solid rgba(0,217,255,0.15)',
              }}
            >
              <CategoryLabel>Get Started Today</CategoryLabel>
              <h2 className="text-4xl font-bold tracking-tight md:text-6xl mb-4">
                Stop Scrolling.<br />Start Creating.
              </h2>
              <p className="text-white/50 text-lg max-w-2xl mx-auto mb-8">
                The creators who &quot;always seem to know&quot; aren&apos;t psychic. They&apos;re
                just using Trendscope. Join 2,000+ creators and agencies who get alerts 6-24 hours
                before the mainstream.
              </p>
              <Button
                size="lg"
                asChild
                className="rounded-full bg-white text-[#080808] hover:bg-white/90 font-semibold px-10"
              >
                <a href="/auth/signup">Start Your Free Trial →</a>
              </Button>
              <p className="mt-4 text-xs text-white/30">
                14 days free. No credit card required. Cancel anytime.
              </p>
            </div>
          </div>
        </section>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <footer className="border-t border-white/[0.05] py-14">
          <div className="container mx-auto px-6">
            <div className="grid gap-10 md:grid-cols-4 mb-12">
              <div>
                <Logo width={260} height={72} showText={false} className="mb-4" />
                <p className="text-sm text-white/40 leading-relaxed">
                  The Bloomberg Terminal for Short-Form Video Trends
                </p>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
                <ul className="space-y-2 text-sm text-white/40">
                  <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                  <li><a href="#pricing"  className="hover:text-white transition-colors">Pricing</a></li>
                  <li><a href="/auth/signup" className="hover:text-white transition-colors">Sign Up</a></li>
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white mb-4">Resources</h4>
                <ul className="space-y-2 text-sm text-white/40">
                  <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                  <li><a href="#faq" className="hover:text-white transition-colors">FAQ</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-white mb-4">Legal</h4>
                <ul className="space-y-2 text-sm text-white/40">
                  <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-white/[0.05] pt-8 text-center text-xs text-white/30">
              <p>© 2026 Trendscope. All rights reserved.</p>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
}
