import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { CheckCircle2, TrendingUp, Zap, Target, Bell, Users, FileText } from 'lucide-react';

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b bg-white/95 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-primary">Trendscope</span>
          </div>
          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm font-medium hover:text-primary">Features</a>
            <a href="#pricing" className="text-sm font-medium hover:text-primary">Pricing</a>
            <a href="#faq" className="text-sm font-medium hover:text-primary">FAQ</a>
            <a href="/auth/login" className="text-sm font-medium hover:text-primary">Login</a>
            <Button asChild>
              <a href="/auth/signup">Get Started</a>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-24 text-center">
        <Badge className="mb-6" variant="secondary">
          The Bloomberg Terminal for Short-Form Video Trends
        </Badge>
        <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight md:text-6xl">
          Real-time trend intelligence.<br />
          Professional-grade detection.<br />
          <span className="text-primary">Alerts before the mainstream knows.</span>
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-xl text-muted-foreground">
          While you&apos;re sleeping, trends are born. By the time you check TikTok Creative Center, that sound already peaked. Trendscope detects trends at the micro-influencer layer—where viral content is born.
        </p>
        <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
          <Button size="lg" className="text-lg px-8" asChild>
            <a href="/auth/signup">Start Free →</a>
          </Button>
          <Button size="lg" variant="outline" className="text-lg px-8" asChild>
            <a href="#how-it-works">See How It Works ↓</a>
          </Button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          No credit card required. 14-day free trial.
        </p>
      </section>

      {/* Problem Section */}
      <section className="bg-gray-50 py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-4xl font-bold">
            You&apos;re Not Missing Trends. You&apos;re Just Finding Them Too Late.
          </h2>
          <p className="mx-auto mb-12 max-w-3xl text-center text-xl text-muted-foreground">
            The average creator spends 4 hours a day scrolling TikTok. That&apos;s not research. That&apos;s digital drift.
          </p>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                title: 'Trend Decay',
                description: 'By the time you spot a sound manually, 50,000 creators already used it',
              },
              {
                title: 'Creator Burnout',
                description: '62% of creators experience burnout from endless scrolling',
              },
              {
                title: 'Reactive Content',
                description: 'You&apos;re always chasing yesterday&apos;s news',
              },
              {
                title: 'Algorithm Bias',
                description: 'Your FYP shows you what you already like, not what&apos;s about to break',
              },
            ].map((problem) => (
              <Card key={problem.title}>
                <CardHeader>
                  <CardTitle className="text-lg">{problem.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{problem.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-12 rounded-lg border-2 border-yellow-500 bg-yellow-50 p-8 text-center">
            <p className="text-2xl font-bold text-yellow-900">
              You&apos;re paying with your time. And losing anyway.
            </p>
            <p className="mt-2 text-lg text-yellow-800">
              4 hours/day = $3,000/month in lost productivity (at $25/hour)
            </p>
          </div>
        </div>
      </section>

      {/* Agitate Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-4xl font-bold">
            The Trend Decay Dilemma: Why You&apos;re Always 24 Hours Behind
          </h2>
          <p className="mx-auto mb-12 max-w-3xl text-center text-xl text-muted-foreground">
            Here&apos;s the brutal truth about TikTok trends: They don&apos;t build slowly. They explode overnight.
          </p>

          <div className="mx-auto max-w-3xl">
            <Card className="border-2 border-red-500">
              <CardHeader>
                <CardTitle className="text-red-900">Your Current Workflow:</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {[
                  '9 AM: You wake up and start scrolling',
                  '11 AM: You finally find something "interesting"',
                  '12 PM: You brief your team / plan your content',
                  '3 PM: You film',
                  '5 PM: You edit',
                  '7 PM: You post',
                ].map((step, i) => (
                  <p key={i} className="text-muted-foreground">{step}</p>
                ))}
                <p className="pt-4 text-2xl font-bold text-red-600">
                  Meanwhile, the trend peaked at 2 PM.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="how-it-works" className="bg-primary py-24 text-white">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-4xl font-bold">
            Introducing Trendscope: Zero-Effort Trend Intelligence
          </h2>
          <p className="mx-auto mb-12 max-w-3xl text-center text-xl text-white/90">
            Set it up once. Get alerts forever.
          </p>

          <div className="grid gap-8 md:grid-cols-4">
            {[
              {
                step: '1',
                title: 'Select Your Niches',
                description: 'Beauty. Finance. Gaming. Fashion. 20+ categories.',
              },
              {
                step: '2',
                title: 'Connect Your Channels',
                description: 'Slack. Email. SMS (Agency+). We meet you where you are.',
              },
              {
                step: '3',
                title: 'Receive Real-Time Alerts',
                description: '🔥 TREND ALERT: Sound "soft glam" surging 340% in #beauty.',
              },
              {
                step: '4',
                title: 'Create While the Window Is Open',
                description: 'Velocity data. Saturation scores. Example videos. Everything you need.',
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-white text-2xl font-bold text-primary">
                  {item.step}
                </div>
                <h3 className="mb-2 text-xl font-bold">{item.title}</h3>
                <p className="text-white/80">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-4xl font-bold">What You Get</h2>
          <p className="mx-auto mb-12 max-w-3xl text-center text-xl text-muted-foreground">
            Professional-grade trend intelligence built for creators and agencies
          </p>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: <TrendingUp className="h-8 w-8" />,
                title: 'Velocity Detection',
                description: 'Track growth rate, not just volume. Catch trends while they&apos;re accelerating.',
              },
              {
                icon: <Users className="h-8 w-8" />,
                title: 'Micro-Influencer Signal',
                description: 'Monitor accounts with <10k followers—where trends are born, not where they die.',
              },
              {
                icon: <Bell className="h-8 w-8" />,
                title: 'Push-First Architecture',
                description: 'Alerts come to you. No dashboards to check. No apps to open.',
              },
              {
                icon: <Zap className="h-8 w-8" />,
                title: 'Multi-Channel Delivery',
                description: 'Slack, email, SMS. Your workflow, your way.',
              },
              {
                icon: <Target className="h-8 w-8" />,
                title: 'Saturation Scoring',
                description: 'Know exactly how much runway a trend has left.',
              },
              {
                icon: <FileText className="h-8 w-8" />,
                title: 'Agency White-Label',
                description: 'Branded reports that make you look like a research powerhouse.',
              },
            ].map((feature) => (
              <Card key={feature.title}>
                <CardHeader>
                  <div className="mb-4 text-primary">{feature.icon}</div>
                  <CardTitle>{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="bg-gray-50 py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-4xl font-bold">
            Trusted by Creators and Agencies Who Treat This Like a Business
          </h2>

          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                quote: 'I used to wake up at 6 AM to "get ahead" of trends. Now Trendscope does that while I sleep. I filmed a video at 7 AM based on a 6:30 AM alert. It hit 500K views by dinner.',
                author: 'Sarah K.',
                role: 'Beauty Creator, 180K followers',
              },
              {
                quote: 'We manage 12 client accounts. Before Trendscope, we had junior staff scrolling 3 hours a day. Now we get a Slack digest every morning with 3-5 viable trends.',
                author: 'Mark T.',
                role: 'Boutique Agency Founder',
              },
              {
                quote: 'The white-label reports are genius. I send clients "Market Intelligence" briefs with our branding. They think we have a research team. It&apos;s just Trendscope.',
                author: 'Jessica L.',
                role: 'Social Media Director',
              },
            ].map((testimonial, i) => (
              <Card key={i}>
                <CardContent className="pt-6">
                  <p className="mb-4 italic text-muted-foreground">&quot;{testimonial.quote}&quot;</p>
                  <div>
                    <p className="font-semibold">{testimonial.author}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-4xl font-bold">Simple Pricing. Serious Value.</h2>
          <p className="mx-auto mb-12 max-w-3xl text-center text-xl text-muted-foreground">
            Choose the plan that fits your needs
          </p>

          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                name: 'Free',
                price: '$0',
                period: '',
                description: 'For casual creators testing the water',
                features: [
                  'Weekly digest (7 trends max)',
                  '1 niche',
                  'Email delivery',
                  'Basic trend data',
                ],
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
              <Card key={tier.name} className={tier.highlighted ? 'border-2 border-primary' : ''}>
                <CardHeader>
                  <CardTitle className="text-2xl">{tier.name}</CardTitle>
                  <CardDescription>{tier.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">{tier.price}</span>
                    <span className="text-muted-foreground">{tier.period}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2">
                        <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full" variant={tier.highlighted ? 'default' : 'outline'} asChild>
                    <a href="/auth/signup">{tier.cta} →</a>
                  </Button>
                  <p className="text-center text-xs text-muted-foreground">
                    {tier.price === '$0' ? 'No credit card required' : 'Cancel anytime'}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="bg-gray-50 py-24">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-4xl font-bold">Questions? Answered.</h2>

          <Accordion type="single" collapsible className="mx-auto max-w-3xl">
            <AccordionItem value="item-1">
              <AccordionTrigger className="text-left">
                How is this different from TikTok Creative Center?
              </AccordionTrigger>
              <AccordionContent>
                Creative Center shows what *was* viral (24-48h delay). We show what&apos;s *about to be* viral (6-24h detection). Creative Center also filters out &quot;edgy&quot; content—the exact trends creators want to catch early.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-2">
              <AccordionTrigger className="text-left">
                Why should I trust your trend predictions?
              </AccordionTrigger>
              <AccordionContent>
                We don&apos;t predict—we detect. Our algorithm identifies sounds and formats already growing fast among micro-influencers. This isn&apos;t fortune-telling; it&apos;s pattern recognition backed by velocity data.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-3">
              <AccordionTrigger className="text-left">
                What if I get too many alerts?
              </AccordionTrigger>
              <AccordionContent>
                We use segmented alerting by niche. A beauty creator won&apos;t get gaming alerts. Set velocity thresholds—only alert when growth exceeds your custom percentage.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-4">
              <AccordionTrigger className="text-left">
                How quickly do I get alerts?
              </AccordionTrigger>
              <AccordionContent>
                Free tier: Weekly digest. Solo tier: 2-hour latency. Agency tier: 30-minute latency. Enterprise tier: Real-time.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-5">
              <AccordionTrigger className="text-left">
                Can I cancel anytime?
              </AccordionTrigger>
              <AccordionContent>
                Yes. No contracts. No cancellation fees. Cancel in Settings → Billing.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-primary py-24 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-6 text-4xl font-bold md:text-5xl">
            Stop Scrolling. Start Creating.
          </h2>
          <p className="mx-auto mb-8 max-w-2xl text-xl text-white/90">
            The creators who &quot;always seem to know&quot; aren&apos;t psychic. They&apos;re just using Trendscope.
            Join 2,000+ creators and agencies who get alerts 6-24 hours before the mainstream.
          </p>
          <Button size="lg" variant="secondary" className="text-lg px-8" asChild>
            <a href="/auth/signup">Start Your Free Trial →</a>
          </Button>
          <p className="mt-4 text-sm text-white/80">
            14 days free. No credit card required. Cancel anytime.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-gray-50 py-12">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 md:grid-cols-4">
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <span className="text-lg font-bold">Trendscope</span>
              </div>
              <p className="text-sm text-muted-foreground">
                The Bloomberg Terminal for Short-Form Video Trends
              </p>
            </div>

            <div>
              <h3 className="mb-4 font-semibold">Product</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#features" className="hover:text-primary">Features</a></li>
                <li><a href="#pricing" className="hover:text-primary">Pricing</a></li>
                <li><a href="/auth/signup" className="hover:text-primary">Sign Up</a></li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 font-semibold">Resources</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary">Blog</a></li>
                <li><a href="#faq" className="hover:text-primary">FAQ</a></li>
                <li><a href="#" className="hover:text-primary">Help Center</a></li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 font-semibold">Legal</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-primary">Terms of Service</a></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 border-t pt-8 text-center text-sm text-muted-foreground">
            <p>© 2026 Trendscope. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
