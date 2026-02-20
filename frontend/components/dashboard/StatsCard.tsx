import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import React from 'react';

interface StatsCardProps {
  title: string;
  value: string;
  description: string;
  icon: React.ReactNode;
  isClickable?: boolean;
  onClick?: () => void;
}

export function StatsCard({
  title,
  value,
  description,
  icon,
  isClickable = false,
  onClick,
}: StatsCardProps) {
  const className = isClickable ? 'cursor-pointer hover:shadow-lg transition-all' : '';

  return (
    <Card className={className} onClick={onClick}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-stat-value">{value}</div>
        <p className="text-caption">{description}</p>
      </CardContent>
    </Card>
  );
}
