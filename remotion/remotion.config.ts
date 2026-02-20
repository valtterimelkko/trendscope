import { Config } from '@remotion/cli/config';

/**
 * Remotion Configuration for Trendscope
 * 
 * This file configures Remotion for video generation in the Trendscope project.
 * 
 * IMPORTANT: React Version Compatibility
 * - Remotion uses React 18 (in remotion/package.json)
 * - Frontend uses React 19 (in frontend/package.json)
 * - These are kept separate to avoid version conflicts
 * 
 * Video Output:
 * - Default output: ../frontend/public/videos/
 * - This makes videos available as static assets in the Next.js app
 */

const config: Config = {
  // Logging
  logLevel: 'info',
  
  // Preview server - different port from frontend to avoid conflicts
  // Access the Remotion Studio at http://localhost:3003
  setPort: 3003,
};

export default config;
