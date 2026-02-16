import { TrendingUp } from 'lucide-react';

export function Logo({ className }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className || ''}`}>
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
        <TrendingUp className="h-5 w-5 text-white" />
      </div>
      <span className="text-xl font-bold text-primary">Trendscope</span>
    </div>
  );
}
