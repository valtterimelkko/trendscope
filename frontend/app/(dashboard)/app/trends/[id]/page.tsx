'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ArrowLeft, Bookmark, Share2, ExternalLink } from 'lucide-react';
import { use } from 'react';
import Link from 'next/link';

// Mock velocity data for the chart
const velocityData = [
  { time: '-24h', velocity: 12 },
  { time: '-20h', velocity: 18 },
  { time: '-16h', velocity: 25 },
  { time: '-12h', velocity: 45 },
  { time: '-8h', velocity: 67 },
  { time: '-4h', velocity: 82 },
  { time: 'Now', velocity: 89 },
];

export default function TrendDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  // Mock trend data - replace with actual API call
  const trend = {
    id,
    name: 'Soft Glam Transformation',
    type: 'sound',
    niche: 'beauty',
    velocity: 89,
    saturation: 12,
    videoCount: 2891,
    previousCount: 847,
    growthRate: 340,
    timeWindow: '6-8 hours',
    status: 'emerging',
    detectedAt: '2 hours ago',
    source: 'Micro-influencer layer (<10k followers)',
    relatedTags: ['#makeup', '#transformation', '#grwm'],
    exampleVideos: [
      { id: '1', thumbnail: 'https://picsum.photos/200/300?random=1', views: '12.4K' },
      { id: '2', thumbnail: 'https://picsum.photos/200/300?random=2', views: '8.2K' },
      { id: '3', thumbnail: 'https://picsum.photos/200/300?random=3', views: '45.1K' },
    ],
  };

  const getSaturationColor = (percentage: number) => {
    if (percentage < 30) return 'text-green-600';
    if (percentage < 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'emerging':
        return 'bg-green-100 text-green-800';
      case 'peaking':
        return 'bg-yellow-100 text-yellow-800';
      case 'declining':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild>
        <Link href="/app/trends" className="flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Trends
        </Link>
      </Button>

      {/* Trend Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-heading-2">{trend.name}</h1>
            <Badge className={getStatusBadge(trend.status)}>{trend.status}</Badge>
            <Badge variant="outline">{trend.type}</Badge>
            <Badge variant="secondary">{trend.niche}</Badge>
          </div>
          <p className="text-body-sm text-muted-foreground">
            Detected {trend.detectedAt} • {trend.videoCount.toLocaleString()} videos
          </p>
        </div>
        <Button variant="outline" size="icon">
          <Bookmark className="h-4 w-4" />
        </Button>
      </div>

      {/* Velocity and Saturation Metrics */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Velocity Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold text-primary">{trend.velocity}</span>
                <span className="text-xl text-muted-foreground">/100</span>
              </div>
              <Progress value={trend.velocity} className="h-3" />
              <p className="text-sm text-muted-foreground">
                +{trend.growthRate}% in 3 hours
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Saturation Level</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-end gap-2">
                <span className={`text-4xl font-bold ${getSaturationColor(trend.saturation)}`}>
                  {trend.saturation}%
                </span>
              </div>
              <Progress value={trend.saturation} className="h-3" />
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Window remaining:</span>
                <span className="font-semibold text-green-600">{trend.timeWindow}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Velocity Graph */}
      <Card>
        <CardHeader>
          <CardTitle>24-Hour Velocity Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer config={{ velocity: { label: 'Velocity', color: 'hsl(var(--primary))' } }} className="h-[300px]">
            <LineChart data={velocityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line type="monotone" dataKey="velocity" stroke="hsl(var(--primary))" strokeWidth={2} />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Trend Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Growth</dt>
              <dd className="mt-1 text-2xl font-semibold text-green-600">
                +{trend.growthRate}%
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Videos</dt>
              <dd className="mt-1 text-2xl font-semibold">
                {trend.previousCount.toLocaleString()} → {trend.videoCount.toLocaleString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Source</dt>
              <dd className="mt-1 text-sm">{trend.source}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Detected</dt>
              <dd className="mt-1 text-sm">{trend.detectedAt}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Example Videos */}
      <Card>
        <CardHeader>
          <CardTitle>Example Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            {trend.exampleVideos.map((video) => (
              <a
                key={video.id}
                href={`https://tiktok.com/@example/video/${video.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative overflow-hidden rounded-lg border transition-transform hover:scale-105"
              >
                <img
                  src={video.thumbnail}
                  alt="Example video"
                  className="h-[300px] w-full object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                  <div className="flex items-center justify-between text-white">
                    <span className="text-sm font-semibold">{video.views} views</span>
                    <ExternalLink className="h-4 w-4" />
                  </div>
                </div>
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Related Tags */}
      <Card>
        <CardHeader>
          <CardTitle>Related</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {trend.relatedTags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button size="lg" className="flex-1">
          <ExternalLink className="mr-2 h-4 w-4" />
          Create Video
        </Button>
        <Button size="lg" variant="outline">
          Dismiss
        </Button>
        <Button size="lg" variant="outline">
          <Share2 className="mr-2 h-4 w-4" />
          Share
        </Button>
      </div>
    </div>
  );
}
