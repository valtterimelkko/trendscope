-- Sample trends data for testing
-- Run this to populate the trends table with example data

BEGIN;

-- Insert sample trends
INSERT INTO public.trends (
    type,
    name,
    platform_id,
    niche_id,
    first_detected_at,
    peak_detected_at,
    status,
    velocity_score,
    saturation_percent,
    video_count_start,
    video_count_current,
    growth_rate,
    metadata
) VALUES
-- Beauty trends
('sound', 'Glow Up Transition', 'music_001', (SELECT id FROM niches WHERE name = 'beauty'), NOW() - INTERVAL '2 days', NULL, 'emerging', 85, 25, 1000, 15000, 45.5, '{"example_videos": ["https://tiktok.com/@user1/video/1", "https://tiktok.com/@user2/video/2"], "related_hashtags": ["#glowup", "#transformation", "#beautytips"]}'),
('hashtag', '#LipstickChallenge', 'hashtag_001', (SELECT id FROM niches WHERE name = 'beauty'), NOW() - INTERVAL '5 days', NOW() - INTERVAL '1 day', 'peaking', 92, 65, 5000, 125000, 32.1, '{"example_videos": ["https://tiktok.com/@user3/video/3"], "related_hashtags": ["#lipstick", "#makeupchallenge", "#beautyhacks"]}'),

-- Fitness trends
('sound', 'Workout Motivation Beat', 'music_002', (SELECT id FROM niches WHERE name = 'fitness'), NOW() - INTERVAL '1 day', NULL, 'emerging', 78, 15, 500, 8500, 55.2, '{"example_videos": ["https://tiktok.com/@user4/video/4"], "related_hashtags": ["#fitness", "#workout", "#motivation"]}'),
('format', 'Before After Fitness', 'format_001', (SELECT id FROM niches WHERE name = 'fitness'), NOW() - INTERVAL '7 days', NOW() - INTERVAL '2 days', 'saturated', 65, 80, 10000, 250000, 12.5, '{"example_videos": ["https://tiktok.com/@user5/video/5"], "related_hashtags": ["#transformation", "#fitnessjourney", "#gym"]}'),

-- Finance trends
('hashtag', '#MoneyTips2024', 'hashtag_002', (SELECT id FROM niches WHERE name = 'finance'), NOW() - INTERVAL '3 days', NULL, 'emerging', 88, 30, 2000, 35000, 42.8, '{"example_videos": ["https://tiktok.com/@user6/video/6"], "related_hashtags": ["#finance", "#money", "#investing"]}'),
('sound', 'Cash Register Sound', 'music_003', (SELECT id FROM niches WHERE name = 'finance'), NOW() - INTERVAL '10 days', NOW() - INTERVAL '3 days', 'saturated', 55, 75, 8000, 180000, 8.3, '{"example_videos": ["https://tiktok.com/@user7/video/7"], "related_hashtags": ["#money", "#rich", "#success"]}'),

-- Gaming trends
('hashtag', '#GamingClips', 'hashtag_003', (SELECT id FROM niches WHERE name = 'gaming'), NOW() - INTERVAL '4 days', NULL, 'emerging', 72, 20, 3000, 42000, 28.9, '{"example_videos": ["https://tiktok.com/@user8/video/8"], "related_hashtags": ["#gaming", "#gamer", "#twitch"]}'),

-- Cooking trends
('sound', 'Satisfying Cooking ASMR', 'music_004', (SELECT id FROM niches WHERE name = 'cooking'), NOW() - INTERVAL '2 days', NULL, 'emerging', 90, 35, 1500, 28000, 48.7, '{"example_videos": ["https://tiktok.com/@user9/video/9"], "related_hashtags": ["#cooking", "#foodtiktok", "#recipe"]}'),
('format', 'Recipe in 60 Seconds', 'format_002', (SELECT id FROM niches WHERE name = 'cooking'), NOW() - INTERVAL '6 days', NOW() - INTERVAL '1 day', 'peaking', 82, 55, 4000, 95000, 25.3, '{"example_videos": ["https://tiktok.com/@user10/video/10"], "related_hashtags": ["#quickrecipe", "#easycooking", "#food"]}'),

-- Comedy trends
('sound', 'Funny Sound Effect #47', 'music_005', (SELECT id FROM niches WHERE name = 'comedy'), NOW() - INTERVAL '1 day', NULL, 'emerging', 95, 10, 200, 5200, 68.5, '{"example_videos": ["https://tiktok.com/@user11/video/11"], "related_hashtags": ["#funny", "#comedy", "#lol"]}'),

-- Music trends
('hashtag', '#DanceChallenge', 'hashtag_004', (SELECT id FROM niches WHERE name = 'music'), NOW() - INTERVAL '8 days', NOW() - INTERVAL '4 days', 'saturated', 60, 85, 15000, 320000, 5.2, '{"example_videos": ["https://tiktok.com/@user12/video/12"], "related_hashtags": ["#dance", "#challenge", "#viral"]}'),

-- Tech trends
('format', 'Tech Review Format', 'format_003', (SELECT id FROM niches WHERE name = 'tech'), NOW() - INTERVAL '3 days', NULL, 'emerging', 75, 25, 800, 12500, 35.6, '{"example_videos": ["https://tiktok.com/@user13/video/13"], "related_hashtags": ["#tech", "#review", "#gadgets"]}')

ON CONFLICT (type, platform_id) DO NOTHING;

-- Insert sample velocity history for the first trend
INSERT INTO public.trend_velocity_history (trend_id, timestamp, video_count, velocity_score, growth_rate, saturation_percent)
SELECT
    t.id,
    NOW() - (i * INTERVAL '1 hour'),
    1000 + (i * 500),
    50 + (i * 2),
    30 + (i * 1.5),
    10 + (i * 1)
FROM public.trends t
CROSS JOIN generate_series(0, 23) AS i
WHERE t.platform_id = 'music_001'
ON CONFLICT DO NOTHING;

COMMIT;
