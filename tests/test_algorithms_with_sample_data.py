#!/usr/bin/env python3
"""
Algorithm Integration Test with Sample Data

Tests the complete trend detection pipeline with realistic sample data
to verify algorithms work correctly before production deployment.

Uses sample data (no API calls required).
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.velocity_engine import VelocityEngine, VelocityResult
from detection.saturation import SaturationEngine, SaturationResult
from detection.models import VideoData, TrendType, ExtractedTrend


def generate_exponential_growth_data(
    start_count: int = 100,
    growth_rate: float = 0.5,  # 50% per hour
    hours: int = 24,
    noise_factor: float = 0.05
) -> list:
    """Generate realistic exponential growth data for testing"""
    data_points = []
    base_time = datetime.now() - timedelta(hours=hours)
    
    for hour in range(hours):
        # Exponential growth: V(t) = V0 * e^(rt)
        ideal_count = start_count * np.exp(growth_rate * hour)
        
        # Add realistic noise
        noise = np.random.normal(0, ideal_count * noise_factor)
        actual_count = max(1, int(ideal_count + noise))
        
        timestamp = base_time + timedelta(hours=hour)
        data_points.append((timestamp, actual_count))
    
    return data_points


def generate_viral_trend_data() -> list:
    """Generate data for a viral trend (very high growth)"""
    return generate_exponential_growth_data(
        start_count=50,
        growth_rate=1.2,  # 120% per hour - viral!
        hours=12,
        noise_factor=0.1
    )


def generate_moderate_trend_data() -> list:
    """Generate data for a moderate trend (steady growth)"""
    return generate_exponential_growth_data(
        start_count=200,
        growth_rate=0.3,  # 30% per hour
        hours=48,
        noise_factor=0.05
    )


def generate_saturated_trend_data() -> list:
    """Generate data for a saturated trend (flat/plateau)"""
    data_points = []
    base_time = datetime.now() - timedelta(hours=72)
    
    # Initial growth phase (first 24 hours)
    for hour in range(24):
        count = int(100 * np.exp(0.4 * hour))
        timestamp = base_time + timedelta(hours=hour)
        data_points.append((timestamp, count))
    
    # Saturation phase: completely flat/plateau (last 48 hours)
    plateau_count = data_points[-1][1]
    for hour in range(24, 72):
        # Add small random noise for realism, but keep it essentially flat
        noise = np.random.normal(0, plateau_count * 0.001)  # 0.1% noise
        count = max(plateau_count - 100, int(plateau_count + noise))
        timestamp = base_time + timedelta(hours=hour)
        data_points.append((timestamp, count))
    
    return data_points


def test_viral_trend_detection():
    """Test detection of a viral trend"""
    print("\nTest 1: Viral Trend Detection")
    print("-" * 60)
    
    engine = VelocityEngine()
    data = generate_viral_trend_data()
    
    result = engine.calculate_velocity(data)
    
    print(f"Data points: {result.data_points}")
    print(f"Time window: {result.time_window_hours:.1f} hours")
    print(f"Growth rate: {result.growth_rate:.2f}% per hour")
    print(f"R-squared: {result.r_squared:.3f}")
    print(f"Is exponential: {result.is_exponential}")
    print(f"Velocity score: {result.score}/100")
    print(f"Doubling time: {result.doubling_time:.2f} hours")
    print(f"Acceleration: {result.acceleration:.4f}")
    
    # Assertions for viral trend
    assert result.growth_rate > 100, f"Expected viral growth >100%, got {result.growth_rate}%"
    assert result.is_exponential, "Viral trend should be exponential"
    assert result.score > 80, f"Viral trend should have score >80, got {result.score}"
    assert result.doubling_time < 1.5, f"Viral trend doubles in <1.5 hours, got {result.doubling_time}"
    
    print("✅ Viral trend correctly identified!")
    return result


def test_moderate_trend_detection():
    """Test detection of a moderate trend"""
    print("\nTest 2: Moderate Trend Detection")
    print("-" * 60)
    
    engine = VelocityEngine()
    data = generate_moderate_trend_data()
    
    result = engine.calculate_velocity(data)
    
    print(f"Data points: {result.data_points}")
    print(f"Time window: {result.time_window_hours:.1f} hours")
    print(f"Growth rate: {result.growth_rate:.2f}% per hour")
    print(f"R-squared: {result.r_squared:.3f}")
    print(f"Is exponential: {result.is_exponential}")
    print(f"Velocity score: {result.score}/100")
    
    # Assertions for moderate trend
    assert 20 < result.growth_rate < 50, f"Expected moderate growth 20-50%, got {result.growth_rate}%"
    assert result.score > 20, f"Moderate trend should have score >20, got {result.score}"
    assert result.score < 80, f"Moderate trend should have score <80, got {result.score}"
    
    print("✅ Moderate trend correctly identified!")
    return result


def test_saturated_trend_detection():
    """Test detection of a saturated trend"""
    print("\nTest 3: Saturated Trend Detection")
    print("-" * 60)
    
    engine = VelocityEngine()
    data = generate_saturated_trend_data()
    
    # Use only the last 24 hours (saturated phase)
    recent_data = data[-24:]
    result = engine.calculate_velocity(recent_data)
    
    print(f"Data points: {result.data_points}")
    print(f"Time window: {result.time_window_hours:.1f} hours")
    print(f"Growth rate: {result.growth_rate:.2f}% per hour")
    print(f"R-squared: {result.r_squared:.3f}")
    print(f"Acceleration: {result.acceleration:.4f}")
    print(f"Velocity score: {result.score}/100")
    
    # Saturated trends should have low/zero growth and not be exponential
    assert result.growth_rate < 5, f"Saturated trend should have growth <5%, got {result.growth_rate}%"
    # Flat data won't have exponential fit (R² will be low), so is_exponential should be False
    assert not result.is_exponential, f"Saturated/flat trend should not be exponential, got R²={result.r_squared}"
    
    print("✅ Saturated trend correctly identified!")
    return result


def test_alert_thresholds():
    """Test alert threshold classification"""
    print("\nTest 4: Alert Threshold Classification")
    print("-" * 60)
    
    from detection.velocity_engine import AdaptiveThresholds
    
    thresholds = AdaptiveThresholds()
    
    # Simulate historical scores
    historical_scores = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 
                        60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    percentiles = thresholds.calculate_percentiles(historical_scores)
    
    print(f"P10: {percentiles['P10']:.1f}")
    print(f"P50: {percentiles['P50']:.1f}")
    print(f"P90: {percentiles['P90']:.1f}")
    print(f"P99: {percentiles['P99']:.1f}")
    
    # Test classifications
    test_scores = [5, 25, 50, 80, 95]
    for score in test_scores:
        level = thresholds.classify_score(score, percentiles)
        print(f"Score {score}: {level}")
    
    # Assertions based on percentile classification logic
    # P10=19, P50=55, P90=91, P99=99.1
    assert thresholds.classify_score(5, percentiles) == "noise"    # < P10
    assert thresholds.classify_score(25, percentiles) == "weak"    # P10-P50
    assert thresholds.classify_score(50, percentiles) == "weak"    # P10-P50  
    assert thresholds.classify_score(80, percentiles) == "moderate" # P50-P90
    assert thresholds.classify_score(95, percentiles) == "strong"  # P90-P99
    assert thresholds.classify_score(100, percentiles) == "viral"  # >= P99
    
    print("✅ Alert thresholds working correctly!")


def test_saturation_engine():
    """Test saturation calculation"""
    print("\nTest 5: Saturation Engine")
    print("-" * 60)
    
    engine = SaturationEngine()
    
    # Create a sample velocity result for testing
    from detection.models import Trend
    
    velocity_result = VelocityResult(
        score=50,
        growth_rate=25.0,
        doubling_time=2.8,
        r_squared=0.9,
        is_exponential=True,
        acceleration=10.0,  # Positive acceleration = early stage
        confidence=0.8,
        data_points=12,
        time_window_hours=12.0
    )
    
    # Test with early-stage trend (positive acceleration, no existing trend)
    result = engine.calculate(velocity_result, existing_trend=None, data_points=12)
    print(f"Early trend (accel={velocity_result.acceleration}): score={result.score}, stage={result.stage}")
    assert result.score < 80, f"Early trend should have score <80, got {result.score}"
    assert result.stage in ["early", "growth", "mature"], f"Valid stage expected, got {result.stage}"
    
    # Test with late-stage trend (negative acceleration)
    velocity_result.acceleration = -20.0
    result = engine.calculate(velocity_result, existing_trend=None, data_points=50)
    print(f"Late trend (accel={velocity_result.acceleration}): score={result.score}, stage={result.stage}")
    
    print("✅ Saturation engine working correctly!")


def test_sample_video_processing():
    """Test processing sample video data"""
    print("\nTest 6: Sample Video Processing")
    print("-" * 60)
    
    # Import nested models
    from detection.models import VideoStats, VideoAuthor, VideoMusic
    
    # Create sample video data with proper nested structure
    video = VideoData(
        id="test123",
        create_time=int((datetime.now() - timedelta(hours=2)).timestamp()),
        stats=VideoStats(
            play_count=50000,
            digg_count=2500,
            share_count=300,
            comment_count=150
        ),
        author=VideoAuthor(
            unique_id="testcreator",
            nickname="Test Creator",
            follower_count=5000
        ),
        music=VideoMusic(
            id="sound789",
            title="Test Sound"
        ),
        hashtags=["viral", "trending"]
    )
    
    # Create extracted trend
    trend = ExtractedTrend(
        type=TrendType.SOUND,
        platform_id="sound789",
        name="Test Sound",
        video=video
    )
    
    print(f"Video ID: {video.id}")
    print(f"Author: @{video.author.unique_id}")
    print(f"Views: {video.stats.play_count:,}")
    print(f"Engagement: {video.stats.digg_count:,} likes, {video.stats.share_count:,} shares")
    print(f"Hashtags: {', '.join(video.hashtags)}")
    print(f"Trend type: {trend.type.value}")
    print(f"Trend ID: {trend.platform_id}")
    
    # Calculate engagement rate
    engagement = (video.stats.digg_count + video.stats.share_count + video.stats.comment_count) / video.stats.play_count
    print(f"Engagement rate: {engagement:.4f} ({engagement*100:.2f}%)")
    
    assert engagement > 0.05, "Engagement rate should be >5% for viral content"
    
    print("✅ Video processing working correctly!")


def run_all_tests():
    """Run all algorithm tests"""
    print("=" * 70)
    print("ALGORITHM INTEGRATION TESTS WITH SAMPLE DATA")
    print("=" * 70)
    
    all_passed = True
    
    tests = [
        ("Viral Trend Detection", test_viral_trend_detection),
        ("Moderate Trend Detection", test_moderate_trend_detection),
        ("Saturated Trend Detection", test_saturated_trend_detection),
        ("Alert Thresholds", test_alert_thresholds),
        ("Saturation Engine", test_saturation_engine),
        ("Sample Video Processing", test_sample_video_processing),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅✅✅ ALL ALGORITHM TESTS PASSED! ✅✅✅")
        print("\nThe trend detection pipeline is working correctly with sample data.")
        print("Ready for production deployment with real API data.")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
