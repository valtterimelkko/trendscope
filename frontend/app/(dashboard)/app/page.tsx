import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Bell, Activity } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-heading-2 mb-2">Welcome back, Sarah</h1>
        <p className="text-body text-muted-foreground">
          Here&apos;s what&apos;s happening with your trends today.
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard
          title="Active Trends"
          value="12"
          description="Trending in your niches"
          icon={<TrendingUp className="h-4 w-4 text-primary" />}
        />
        <StatsCard
          title="Detected Today"
          value="3"
          description="New trends found"
          icon={<Activity className="h-4 w-4 text-success" />}
        />
        <StatsCard
          title="Alerts This Week"
          value="28"
          description="Sent to your channels"
          icon={<Bell className="h-4 w-4 text-accent" />}
        />
      </div>

      {/* Hot Trends */}
      <div>
        <h2 className="text-heading-3 mb-4">🔥 Hot Trends</h2>
        <div className="space-y-3">
          <TrendCard
            name="Soft Glam Transformation"
            niche="beauty"
            velocity={89}
            videoCount="2,891"
            timeWindow="6 hours"
          />
          <TrendCard
            name="#QuietLuxury"
            niche="fashion"
            velocity={78}
            videoCount="1,234"
            timeWindow="12 hours"
          />
          <TrendCard
            name="Finance Advice Format"
            niche="finance"
            velocity={65}
            videoCount="847"
            timeWindow="18 hours"
          />
        </div>
      </div>

      {/* Recent Alerts */}
      <div>
        <h2 className="text-heading-3 mb-4">Recent Alerts</h2>
        <div className="space-y-2">
          <AlertItem
            time="2 hours ago"
            message="Sound alert in #beauty"
            trend="Soft Glam Transformation"
          />
          <AlertItem
            time="5 hours ago"
            message="Hashtag alert in #finance"
            trend="#MoneyTips"
          />
          <AlertItem
            time="8 hours ago"
            message="Format alert in #fashion"
            trend="Get Ready With Me"
          />
        </div>
      </div>
    </div>
  );
}

function StatsCard({
  title,
  value,
  description,
  icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function TrendCard({
  name,
  niche,
  velocity,
  videoCount,
  timeWindow,
}: {
  name: string;
  niche: string;
  velocity: number;
  videoCount: string;
  timeWindow: string;
}) {
  const getVelocityColor = (score: number) => {
    if (score >= 70) return 'bg-green-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold mb-1">{name}</h3>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline" className="text-xs">
                {niche}
              </Badge>
              <span>•</span>
              <span>{videoCount} videos</span>
              <span>•</span>
              <span>⏰ {timeWindow} window</span>
            </div>
          </div>
          <div className="flex flex-col items-end">
            <div className="text-2xl font-bold text-primary">+{velocity}%</div>
            <div className={`h-1 w-16 rounded-full ${getVelocityColor(velocity)}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AlertItem({
  time,
  message,
  trend,
}: {
  time: string;
  message: string;
  trend: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border p-3 hover:bg-accent/5">
      <Bell className="h-4 w-4 text-accent" />
      <div className="flex-1">
        <p className="text-sm">{message}</p>
        <p className="text-xs text-muted-foreground">{trend}</p>
      </div>
      <span className="text-xs text-muted-foreground">{time}</span>
    </div>
  );
}
