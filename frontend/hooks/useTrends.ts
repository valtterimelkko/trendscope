import { useQuery } from '@tanstack/react-query';
import type { Trend } from '@/types/database.types';

interface TrendFilters {
  niches?: string[];
  status?: 'emerging' | 'peaking' | 'declining' | 'expired';
  minVelocity?: number;
}

async function fetchTrends(filters: TrendFilters): Promise<Trend[]> {
  const params = new URLSearchParams();
  
  if (filters.niches?.length) {
    params.append('niches', filters.niches.join(','));
  }
  if (filters.status) {
    params.append('status', filters.status);
  }
  if (filters.minVelocity) {
    params.append('minVelocity', filters.minVelocity.toString());
  }

  const response = await fetch(`/api/trends?${params.toString()}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch trends');
  }
  
  return response.json();
}

export function useTrends(filters: TrendFilters = {}) {
  return useQuery({
    queryKey: ['trends', filters],
    queryFn: () => fetchTrends(filters),
    refetchInterval: 60000, // Refetch every 60 seconds
    staleTime: 30000, // Consider data stale after 30 seconds
  });
}
