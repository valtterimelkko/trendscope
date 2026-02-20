import React from 'react';
import { Composition, Folder, Still } from 'remotion';
import { TrendReportVideo } from './compositions/TrendReport';
import { MarketingHeroVideo } from './compositions/MarketingHero';

// Default video dimensions
const WIDTH = 1920;
const HEIGHT = 1080;
const FPS = 30;

export const Root: React.FC = () => {
  return (
    <>
      <Folder name="marketing-videos">
        <Composition
          id="TrendReport"
          component={TrendReportVideo}
          durationInFrames={30 * 10} // 10 seconds
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            title: 'TikTok Trend Report',
            subtitle: 'Weekly insights for your niche',
            trends: [
              { name: '#ViralDance', growth: '+245%', views: '2.4M' },
              { name: '#CookingHacks', growth: '+189%', views: '1.8M' },
              { name: '#FitnessTips', growth: '+156%', views: '1.2M' },
            ],
          }}
        />
        
        <Composition
          id="MarketingHero"
          component={MarketingHeroVideo}
          durationInFrames={30 * 15} // 15 seconds
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            headline: 'Never Miss a Trend Again',
            subheadline: 'AI-powered TikTok trend detection for creators',
            cta: 'Start Free Trial',
          }}
        />
      </Folder>

      <Folder name="social-media">
        <Composition
          id="InstagramStory"
          component={TrendReportVideo}
          durationInFrames={30 * 15}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            title: 'Trend Alert',
            subtitle: 'New viral opportunity detected',
            trends: [
              { name: '#ViralDance', growth: '+245%', views: '2.4M' },
            ],
          }}
        />
      </Folder>
    </>
  );
};
