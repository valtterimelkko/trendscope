import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: 'Trendscope - The Bloomberg Terminal for Short-Form Video Trends',
  description:
    'Real-time TikTok trend detection. Find emerging trends before they peak with velocity tracking and instant alerts.',
  keywords: [
    'TikTok trends',
    'trend detection',
    'creator tools',
    'viral content',
    'social media analytics',
  ],
  authors: [{ name: 'Trendscope' }],
  openGraph: {
    title: 'Trendscope - Trend Intelligence, Delivered First',
    description:
      'Detect TikTok trends 6-24 hours before mainstream saturation. Professional-grade intelligence for creators and agencies.',
    url: 'https://trendscope.io',
    siteName: 'Trendscope',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Trendscope - Trend Intelligence, Delivered First',
    description:
      'Real-time TikTok trend detection for creators who move fast.',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.variable}>{children}</body>
    </html>
  );
}
