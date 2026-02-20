import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

interface TrendCardProps {
  name: string;
  niche: string;
  velocity: number;
  videoCount: string;
  timeWindow: string;
  onViewDetails?: () => void;
  onBookmark?: () => void;
  onCreateAlert?: () => void;
}

export function TrendCard({
  name,
  niche,
  velocity,
  videoCount,
  timeWindow,
  onViewDetails,
  onBookmark,
  onCreateAlert,
}: TrendCardProps) {
  const getVelocityColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getVelocityBgColor = (score: number) => {
    if (score >= 70) return 'bg-green-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <Card className="trend-card">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="font-semibold mb-2">{name}</h3>
            <div className="flex items-center gap-2 text-body-sm text-muted-foreground flex-wrap">
              <Badge variant="outline" className="text-xs">
                {niche}
              </Badge>
              <span>•</span>
              <span>{videoCount} videos</span>
              <span>•</span>
              <span>⏰ {timeWindow}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className={`text-2xl font-bold ${getVelocityColor(velocity)}`}>
              +{velocity}%
            </div>
            <div className={`h-1 w-16 rounded-full ${getVelocityBgColor(velocity)}`} />
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={onViewDetails}>
            View Details <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
          {onBookmark && (
            <Button variant="ghost" size="sm" onClick={onBookmark}>
              ⭐
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
