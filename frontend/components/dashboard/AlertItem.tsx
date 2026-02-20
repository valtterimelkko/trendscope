import { Bell, Music, Tag, Film } from 'lucide-react';

interface AlertItemProps {
  time: string;
  message: string;
  trend: string;
  type?: 'sound' | 'hashtag' | 'format';
}

const alertTypeIcons = {
  sound: <Music className="h-4 w-4 text-accent" />,
  hashtag: <Tag className="h-4 w-4 text-accent" />,
  format: <Film className="h-4 w-4 text-accent" />,
};

export function AlertItem({ time, message, trend, type = 'sound' }: AlertItemProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg border p-3 hover:bg-accent/5 transition-colors">
      {alertTypeIcons[type] || <Bell className="h-4 w-4 text-accent" />}
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
        <p className="text-caption">{trend}</p>
      </div>
      <span className="text-caption whitespace-nowrap">{time}</span>
    </div>
  );
}
