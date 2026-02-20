'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { VelocityChart } from '@/components/dashboard/VelocityChart';
import { TrendingUp, BookmarkIcon, Bell, Video, Eye, TrendingDown } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';

// Mock data
const mockTrendDetail = {
  id: 'soft-glam',
  name: 'Soft Glam Transformation',
  niche: 'beauty',
  velocity: 89,
  detectionTime: '2 hours ago',
  timeWindow: '6 hours',
  stats: {
    totalVideos: 2891,
    totalViews: '45.2M',
    engagementRate: 87,
    avgViewsPerVideo: '156K',
  },
  insights: [
    { title: 'Peak Activity', description: 'Most videos posted between 6-10 PM EST' },
    {
      title: 'Creator Demographics',
      description: '78% female creators, ages 18-34',
    },
    { title: 'Top Sounds', description: '"Calm Vibes" audio (45% of videos)' },
  ],
};

const velocityData = [
  { time: '12 AM', velocity: 35 },
  { time: '4 AM', velocity: 42 },
  { time: '8 AM', velocity: 48 },
  { time: '12 PM', velocity: 65 },
  { time: '4 PM', velocity: 78 },
  { time: '8 PM', velocity: 89 },
];

export default function TrendDetailPage() {
  const router = useRouter();
  const params = useParams();

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex gap-2 text-sm text-muted-foreground">
        <button onClick={() => router.push('/app/trends')} className="hover:text-foreground">
          Trends
        </button>
        <span>→</span>
        <button onClick={() => router.push(`/app/trends?niche=beauty`)} className="hover:text-foreground">
          Beauty
        </button>
        <span>→</span>
        <span className="text-foreground font-medium">{mockTrendDetail.name}</span>
      </div>

      {/* Trend Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div className="flex-1">
          <h1 className="text-heading-2 mb-3">{mockTrendDetail.name}</h1>
          <div className="flex flex-wrap items-center gap-3 text-body-sm">
            <Badge variant="outline">{mockTrendDetail.niche}</Badge>
            <span className="text-muted-foreground">
              ⏰ Detected {mockTrendDetail.detectionTime}
            </span>
            <span className="text-muted-foreground">
              • {mockTrendDetail.timeWindow} detection window
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-3 w-full sm:w-auto">
          <div className="text-center">
            <div className="text-5xl font-bold text-primary">+{mockTrendDetail.velocity}%</div>
            <p className="text-caption">Velocity</p>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button variant="outline" size="sm" className="flex-1 sm:flex-auto">
              <BookmarkIcon className="h-4 w-4 mr-2" />
              Bookmark
            </Button>
            <Button size="sm" className="flex-1 sm:flex-auto">
              <Bell className="h-4 w-4 mr-2" />
              Create Alert
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption">Total Videos</p>
                <p className="text-stat-value">{mockTrendDetail.stats.totalVideos.toLocaleString()}</p>
              </div>
              <Video className="h-6 w-6 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption">Total Views</p>
                <p className="text-stat-value">{mockTrendDetail.stats.totalViews}</p>
              </div>
              <Eye className="h-6 w-6 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption">Engagement Rate</p>
                <p className="text-stat-value">{mockTrendDetail.stats.engagementRate}%</p>
              </div>
              <TrendingUp className="h-6 w-6 text-success" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption">Avg Views/Video</p>
                <p className="text-stat-value">{mockTrendDetail.stats.avgViewsPerVideo}</p>
              </div>
              <TrendingDown className="h-6 w-6 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Velocity Chart */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-heading-4 mb-4">📈 Velocity Over Time</h3>
          <VelocityChart data={velocityData} height={300} />
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Top Videos */}
        <div className="lg:col-span-2">
          <h3 className="text-heading-4 mb-4">🎬 Top Performing Videos</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="aspect-video bg-surface border border-border rounded-lg flex items-center justify-center cursor-pointer hover:border-primary transition-colors"
              >
                <div className="text-center">
                  <div className="text-3xl mb-2">🎬</div>
                  <p className="text-caption">Video {i}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <Button variant="outline">View All Videos →</Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Key Insights */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-heading-4 mb-4">💡 Key Insights</h3>
              <div className="space-y-3">
                {mockTrendDetail.insights.map((insight, idx) => (
                  <div key={idx} className="p-3 border border-dashed border-border rounded-lg">
                    <div className="font-medium text-sm mb-1">{insight.title}</div>
                    <div className="text-caption">{insight.description}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Related Trends */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-heading-4 mb-4">🔗 Related Trends</h3>
              <div className="space-y-2">
                {[
                  { name: '#CleanGirlAesthetic', velocity: 65 },
                  { name: 'Makeup Tutorial', velocity: 54 },
                  { name: 'Natural Beauty', velocity: 48 },
                ].map((trend, idx) => (
                  <div
                    key={idx}
                    className="p-3 border border-border rounded-lg hover:border-primary cursor-pointer transition-colors"
                  >
                    <div className="font-medium text-sm">{trend.name}</div>
                    <div className="text-caption text-success">+{trend.velocity}% velocity</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
