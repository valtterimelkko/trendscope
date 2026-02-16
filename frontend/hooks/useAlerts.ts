import { useQuery } from '@tanstack/react-query';
import type { Alert } from '@/types/database.types';

async function fetchUserAlerts(): Promise<Alert[]> {
  const response = await fetch('/api/alerts');
  
  if (!response.ok) {
    throw new Error('Failed to fetch alerts');
  }
  
  return response.json();
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: fetchUserAlerts,
    refetchInterval: 120000, // Refetch every 2 minutes
    staleTime: 60000, // 1 minute
  });
}
