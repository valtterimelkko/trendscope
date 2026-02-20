import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface TrendFilterBarProps {
  onSearchChange?: (search: string) => void;
  onNicheChange?: (niche: string) => void;
  onVelocityChange?: (velocity: string) => void;
  searchValue?: string;
  nicheValue?: string;
  velocityValue?: string;
}

const niches = [
  { value: 'all', label: 'All Niches' },
  { value: 'beauty', label: 'Beauty' },
  { value: 'fashion', label: 'Fashion' },
  { value: 'finance', label: 'Finance' },
  { value: 'tech', label: 'Tech' },
  { value: 'lifestyle', label: 'Lifestyle' },
];

const velocityOptions = [
  { value: 'all', label: 'All Velocities' },
  { value: 'high', label: 'High (>70%)' },
  { value: 'medium', label: 'Medium (40-70%)' },
  { value: 'low', label: 'Low (<40%)' },
];

export function TrendFilterBar({
  onSearchChange,
  onNicheChange,
  onVelocityChange,
  searchValue = '',
  nicheValue = 'all',
  velocityValue = 'all',
}: TrendFilterBarProps) {
  return (
    <div className="flex gap-3 mb-4 flex-col sm:flex-row">
      <Input
        placeholder="🔍 Search trends..."
        className="flex-1"
        value={searchValue}
        onChange={(e) => onSearchChange?.(e.target.value)}
      />
      <Select value={nicheValue} onValueChange={onNicheChange}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="All Niches" />
        </SelectTrigger>
        <SelectContent>
          {niches.map((niche) => (
            <SelectItem key={niche.value} value={niche.value}>
              {niche.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={velocityValue} onValueChange={onVelocityChange}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="All Velocities" />
        </SelectTrigger>
        <SelectContent>
          {velocityOptions.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
