import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Profile, UserTier } from '@/types/database.types';

interface AuthState {
  user: Profile | null;
  tier: UserTier;
  isLoading: boolean;
  setUser: (user: Profile | null) => void;
  setTier: (tier: UserTier) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tier: 'free',
      isLoading: true,
      setUser: (user) => set({ user, tier: user?.tier || 'free' }),
      setTier: (tier) => set({ tier }),
      setLoading: (loading) => set({ isLoading: loading }),
      logout: () => set({ user: null, tier: 'free' }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
