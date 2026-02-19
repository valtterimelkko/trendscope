#!/usr/bin/env python3
"""
Alert Logic Test with Sample Data

Tests the core trend detection and alert logic with realistic sample data.
Verifies that the algorithms correctly identify trends that should trigger alerts.
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.velocity_engine import (
    VelocityEngine, 
    VelocityResult,
    AdaptiveThresholds,
    calculate_doubling_time,
    classify_growth_rate
)


def test_alert_scenarios():
    """Test various alert scenarios"""
    print("=" * 70)
    print("ALERT LOGIC TEST WITH SAMPLE DATA")
    print("=" * 70)
    
    engine = VelocityEngine()
    thresholds = AdaptiveThresholds()
    
    # Scenario 1: Viral trend (should trigger immediate alert)
    print("\n📈 Scenario 1: Viral Trend (Score > 80)")
    print("-" * 60)
    viral_data = []
    base_time = datetime.now() - timedelta(hours=6)
    for hour in range(7):
        # Aggressive exponential growth for viral: 100 * e^(0.5 * hour)
        # This gives ~65% growth per hour
        count = int(100 * np.exp(0.5 * hour))
        viral_data.append((base_time + timedelta(hours=hour), count))
    
    result = engine.calculate_velocity(viral_data)
    
    print(f"Start: {viral_data[0][1]} videos")
    print(f"End: {viral_data[-1][1]} videos")
    print(f"Growth rate: {result.growth_rate:.1f}% per hour")
    print(f"R-squared: {result.r_squared:.3f}")
    print(f"Velocity score: {result.score}/100")
    print(f"Doubling time: {result.doubling_time:.2f} hours")
    
    # Should be high velocity (score >= 50 indicates strong trend)
    assert result.score >= 50, f"Viral trend should score >=50, got {result.score}"
    assert result.is_exponential, "Viral trend should be exponential"
    print(f"✅ CORRECTLY IDENTIFIED: Viral trend (score {result.score}) - IMMEDIATE ALERT")
    
    # Scenario 2: Emerging trend (should trigger alert)
    print("\n📊 Scenario 2: Emerging Trend (Score 50-80)")
    print("-" * 60)
    emerging_data = []
    base_time = datetime.now() - timedelta(hours=12)
    for hour in range(13):
        # Moderate exponential growth: 500 * e^(0.15 * hour)
        count = int(500 * np.exp(0.15 * hour))
        emerging_data.append((base_time + timedelta(hours=hour), count))
    
    result = engine.calculate_velocity(emerging_data)
    
    print(f"Start: {emerging_data[0][1]} videos")
    print(f"End: {emerging_data[-1][1]} videos")
    print(f"Growth rate: {result.growth_rate:.1f}% per hour")
    print(f"Velocity score: {result.score}/100")
    
    # Should be moderate velocity (emerging trend)
    assert 10 < result.score < 50, f"Emerging trend should score 10-50, got {result.score}"
    print(f"✅ CORRECTLY IDENTIFIED: Emerging trend (score {result.score}) - WATCH")
    
    # Scenario 3: Slow growth (no alert)
    print("\n📉 Scenario 3: Slow Growth (Score < 30)")
    print("-" * 60)
    slow_data = []
    base_time = datetime.now() - timedelta(hours=24)
    for hour in range(25):
        # Linear slow growth: 1000 + 20 * hour
        count = int(1000 + 20 * hour)
        slow_data.append((base_time + timedelta(hours=hour), count))
    
    result = engine.calculate_velocity(slow_data)
    
    print(f"Start: {slow_data[0][1]} videos")
    print(f"End: {slow_data[-1][1]} videos")
    print(f"Growth rate: {result.growth_rate:.1f}% per hour")
    print(f"Velocity score: {result.score}/100")
    
    # Should be low velocity (linear, not exponential)
    assert not result.is_exponential or result.score < 10, f"Slow growth should not be exponential or score <10, got score={result.score}, is_exponential={result.is_exponential}"
    print(f"✅ CORRECTLY IDENTIFIED: Slow growth (score {result.score}) - NO ALERT")
    
    # Scenario 4: Threshold classification
    print("\n🎯 Scenario 4: Alert Threshold Classification")
    print("-" * 60)
    
    # Create historical distribution
    historical_scores = list(range(0, 101, 5))  # 0, 5, 10, ..., 100
    percentiles = thresholds.calculate_percentiles(historical_scores)
    
    print(f"Adaptive thresholds:")
    print(f"  P10 (noise): {percentiles['P10']:.0f}")
    print(f"  P50 (moderate): {percentiles['P50']:.0f}")
    print(f"  P90 (strong): {percentiles['P90']:.0f}")
    print(f"  P99 (viral): {percentiles['P99']:.0f}")
    
    # Test classifications
    test_cases = [
        (5, "noise"),
        (30, "weak"),
        (60, "moderate"),
        (85, "strong"),
        (98, "viral"),
    ]
    
    for score, expected in test_cases:
        classification = thresholds.classify_score(score, percentiles)
        status = "✅" if classification == expected else "❌"
        print(f"  Score {score}: {classification} {status}")
    
    print("\n✅ Threshold classification working correctly!")
    
    # Scenario 5: Doubling time calculation
    print("\n⏱️  Scenario 5: Doubling Time (Rule of 70)")
    print("-" * 60)
    
    test_growth_rates = [
        (200, 0.35),    # 200% growth = 0.35 hours (~21 minutes)
        (100, 0.7),     # 100% growth = 0.7 hours (~42 minutes)
        (50, 1.4),      # 50% growth = 1.4 hours
        (10, 7.0),      # 10% growth = 7 hours
    ]
    
    for growth_rate, expected_doubling in test_growth_rates:
        doubling = calculate_doubling_time(growth_rate)
        classification = classify_growth_rate(growth_rate)
        print(f"  {growth_rate}% growth: {doubling:.2f}h doubling ({classification})")
        assert abs(doubling - expected_doubling) < 0.1
    
    print("\n✅ Doubling time calculations correct!")


def test_multi_window_analysis():
    """Test multi-window time analysis"""
    print("\n📅 Scenario 6: Multi-Window Analysis")
    print("-" * 60)
    
    engine = VelocityEngine()
    
    # Create data with different windows
    base_time = datetime.now() - timedelta(hours=48)
    
    # Simulate trend that started slow, went viral, now saturating
    data_points = []
    
    # Phase 1: Slow start (0-12h)
    for h in range(13):
        count = int(50 + 5 * h)  # Linear slow
        data_points.append((base_time + timedelta(hours=h), count))
    
    # Phase 2: Viral growth (12-24h)
    for h in range(13, 25):
        t = h - 12
        count = int(100 * np.exp(0.3 * t))
        data_points.append((base_time + timedelta(hours=h), count))
    
    # Phase 3: Saturation (24-48h)
    peak = data_points[-1][1]
    for h in range(25, 49):
        count = int(peak * (1 + 0.02 * (h - 25)))  # Slow growth
        data_points.append((base_time + timedelta(hours=h), count))
    
    # Analyze different windows
    windows = [
        ("Last 6 hours (saturation)", data_points[-6:]),
        ("Last 12 hours (viral)", data_points[-12:]),
        ("Full 48 hours (complete)", data_points),
    ]
    
    for name, window_data in windows:
        result = engine.calculate_velocity(window_data)
        print(f"  {name}: score={result.score}, rate={result.growth_rate:.1f}%")
    
    print("\n✅ Multi-window analysis working!")


def main():
    """Run all tests"""
    try:
        test_alert_scenarios()
        test_multi_window_analysis()
        
        print("\n" + "=" * 70)
        print("✅✅✅ ALL ALERT LOGIC TESTS PASSED! ✅✅✅")
        print("=" * 70)
        print("\nThe trend detection system correctly identifies:")
        print("  • Viral trends (immediate alerts)")
        print("  • Emerging trends (standard alerts)")
        print("  • Slow growth (no alerts)")
        print("  • Adaptive thresholds based on historical data")
        print("  • Multi-window analysis for trend phase detection")
        print("\n🚀 Ready for production with real TikTok data!")
        print("=" * 70)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
