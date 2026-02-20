import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand Palette from Trendscope
        'brand-primary': '#0066FF',
        'brand-secondary': '#1A1A1A',
        'brand-accent': '#00D9FF',
        'brand-success': '#00C853',
        'brand-warning': '#FFC107',
        'brand-danger': '#FF3B30',
        'brand-background': '#FFFFFF',
        'brand-surface': '#F5F5F5',
        'brand-border': '#E0E0E0',
        'brand-muted': '#6B7280',
        'brand-foreground': '#1A1A1A',
        'brand-foreground-muted': '#6B7280',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Clash Display', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      spacing: {
        'xs': '8px',
        'sm': '12px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
        '3xl': '64px',
      },
      borderRadius: {
        'xs': '4px',
        'sm': '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
};

export default config;
