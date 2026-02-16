import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserPreferencesState {
  selectedNiches: string[];
  alertThreshold: number;
  emailNotifications: boolean;
  updateNiches: (niches: string[]) => void;
  addNiche: (niche: string) => void;
  removeNiche: (niche: string) => void;
  updateThreshold: (threshold: number) => void;
  toggleEmailNotifications: () => void;
}

export const useUserPreferencesStore = create<UserPreferencesState>()(
  persist(
    (set) => ({
      selectedNiches: [],
      alertThreshold: 50,
      emailNotifications: true,
      updateNiches: (niches) => set({ selectedNiches: niches }),
      addNiche: (niche) =>
        set((state) => ({
          selectedNiches: [...state.selectedNiches, niche],
        })),
      removeNiche: (niche) =>
        set((state) => ({
          selectedNiches: state.selectedNiches.filter((n) => n !== niche),
        })),
      updateThreshold: (threshold) => set({ alertThreshold: threshold }),
      toggleEmailNotifications: () =>
        set((state) => ({
          emailNotifications: !state.emailNotifications,
        })),
    }),
    {
      name: 'user-preferences-storage',
    }
  )
);
