'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

interface VelocityDataPoint {
  time: string;
  velocity: number;
}

interface VelocityChartProps {
  data: VelocityDataPoint[];
  height?: number;
}

const chartConfig = {
  velocity: {
    label: 'Velocity',
    color: 'var(--color-primary)',
  },
};

export function VelocityChart({ data, height = 300 }: VelocityChartProps) {
  return (
    <ChartContainer config={chartConfig} className="w-full">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="time"
            stroke="var(--color-muted)"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="var(--color-muted)"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            content={<ChartTooltipContent />}
          />
          <Line
            type="monotone"
            dataKey="velocity"
            stroke="var(--color-primary)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-primary)', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
