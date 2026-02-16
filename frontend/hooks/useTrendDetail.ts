import { useQuery } from '@tanstack/react-query';
import type { Trend } from '@/types/database.types';

async function fetchTrendDetail(trendId: string): Promise<Trend> {
  const response = await fetch(`/api/trends/${trendId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch trend detail');
  }
  
  return response.json();
}

export function useTrendDetail(trendId: string) {
  return useQuery({
    queryKey: ['trend', trendId],
    queryFn: () => fetchTrendDetail(trendId),
    staleTime: 30000, // 30 seconds
    enabled: !!trendId, // Only run query if trendId exists
  });
}
