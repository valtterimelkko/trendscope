import React from 'react';
import { Composition, Folder, Still } from 'remotion';
import { TrendReportVideo } from './compositions/TrendReport';
import { MarketingHeroVideo } from './compositions/MarketingHero';
import { BloombergIntro } from './compositions/BloombergIntro';
import { BloombergIntroV2 } from './compositions/BloombergIntroV2';

// Default video dimensions
const WIDTH = 1920;
const HEIGHT = 1080;
const FPS = 30;

export const Root: React.FC = () => {
  return (
    <>
      <Folder name="marketing-videos">
        <Composition
          id="TrendscopeBloombergIntroV2"
          component={BloombergIntroV2}
          durationInFrames={540} // 18 seconds @ 30fps
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            logoUrl: 'assets/scene1/trendscope-logo-transparent.png',
            montageImages: [
              'assets/scene2/creator-filming.jpg',
              'assets/scene2/data-dashboard.jpg',
              'assets/scene2/viral-explosion.jpg',
              'assets/scene2/alert-phone.jpg',
            ],
            globeUrl: 'assets/scene3/digital-globe.jpg',
          }}
        />

        <Composition
          id="TrendscopeBloombergIntro"
          component={BloombergIntro}
          durationInFrames={450} // 15 seconds @ 30fps
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            logoUrl: 'assets/scene1/trendscope-logo-white.png',
            montageImages: [
              'assets/scene2/creator-filming.jpg',
              'assets/scene2/data-dashboard.jpg',
              'assets/scene2/viral-explosion.jpg',
              'assets/scene2/alert-phone.jpg',
            ],
            globeUrl: 'assets/scene3/digital-globe.jpg',
          }}
        />

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
