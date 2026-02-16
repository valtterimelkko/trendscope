#!/usr/bin/env python3
"""
Trend Signals - Google Trends via pytrends

Provides trend velocity, rising queries, and related terms for keyword research.
No API key required.

Usage:
    python trend_signals.py --keywords "keyword1,keyword2,keyword3"
    python trend_signals.py --keywords "saas billing" --timeframe "today 12-m"
    python trend_signals.py --keywords "project management" --geo "US"
"""

import argparse
import json
import sys
import time

try:
    from pytrends.request import TrendReq
except ImportError:
    print(json.dumps({
        "error": "pytrends not installed",
        "fix": "pip install pytrends"
    }))
    sys.exit(1)


def get_trend_data(keywords: list, timeframe: str = "today 12-m", geo: str = "") -> dict:
    """
    Fetch trend data for keywords using pytrends.

    Args:
        keywords: List of keywords (max 5)
        timeframe: Time range (e.g., "today 12-m", "today 3-m", "2023-01-01 2024-01-01")
        geo: Geographic region (e.g., "US", "GB", "" for worldwide)

    Returns:
        Dictionary with trend data
    """
    # pytrends has a 5 keyword limit per request
    if len(keywords) > 5:
        keywords = keywords[:5]

    pytrends = TrendReq(hl='en-US', tz=360)

    results = {
        "keywords": keywords,
        "timeframe": timeframe,
        "geo": geo or "Worldwide",
        "interest_over_time": {},
        "related_queries": {},
        "suggestions": {},
        "errors": []
    }

    try:
        # Build payload
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)

        # Interest over time
        try:
            iot = pytrends.interest_over_time()
            if not iot.empty:
                # Get trend direction for each keyword
                for kw in keywords:
                    if kw in iot.columns:
                        values = iot[kw].tolist()
                        if len(values) >= 2:
                            # Compare first quarter vs last quarter
                            quarter_len = len(values) // 4
                            if quarter_len > 0:
                                first_q_avg = sum(values[:quarter_len]) / quarter_len
                                last_q_avg = sum(values[-quarter_len:]) / quarter_len

                                if first_q_avg > 0:
                                    change_pct = ((last_q_avg - first_q_avg) / first_q_avg) * 100
                                else:
                                    change_pct = 100 if last_q_avg > 0 else 0

                                trend_direction = "rising" if change_pct > 10 else "declining" if change_pct < -10 else "stable"

                                results["interest_over_time"][kw] = {
                                    "current_interest": values[-1] if values else 0,
                                    "average_interest": sum(values) / len(values),
                                    "peak_interest": max(values),
                                    "change_percent": round(change_pct, 1),
                                    "trend_direction": trend_direction
                                }
        except Exception as e:
            results["errors"].append(f"interest_over_time: {str(e)}")

        # Related queries for each keyword
        time.sleep(1)  # Rate limiting
        try:
            related = pytrends.related_queries()
            for kw in keywords:
                if kw in related and related[kw] is not None:
                    top_df = related[kw].get('top')
                    rising_df = related[kw].get('rising')

                    results["related_queries"][kw] = {
                        "top": [],
                        "rising": []
                    }

                    if top_df is not None and not top_df.empty:
                        results["related_queries"][kw]["top"] = [
                            {"query": row['query'], "value": int(row['value'])}
                            for _, row in top_df.head(10).iterrows()
                        ]

                    if rising_df is not None and not rising_df.empty:
                        results["related_queries"][kw]["rising"] = [
                            {"query": row['query'], "value": str(row['value'])}
                            for _, row in rising_df.head(10).iterrows()
                        ]
        except Exception as e:
            results["errors"].append(f"related_queries: {str(e)}")

        # Suggestions (autocomplete from Google Trends)
        time.sleep(1)  # Rate limiting
        for kw in keywords:
            try:
                suggestions = pytrends.suggestions(keyword=kw)
                if suggestions:
                    results["suggestions"][kw] = [
                        {"title": s.get("title", ""), "type": s.get("type", "")}
                        for s in suggestions[:5]
                    ]
            except Exception as e:
                results["errors"].append(f"suggestions for '{kw}': {str(e)}")

    except Exception as e:
        results["errors"].append(f"general: {str(e)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch Google Trends data via pytrends")
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords (max 5)")
    parser.add_argument("--timeframe", default="today 12-m", help="Timeframe (default: today 12-m)")
    parser.add_argument("--geo", default="", help="Geographic region (default: worldwide)")
    parser.add_argument("--output", default="json", choices=["json", "summary"], help="Output format")

    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    if not keywords:
        print(json.dumps({"error": "No valid keywords provided"}))
        sys.exit(1)

    results = get_trend_data(keywords, args.timeframe, args.geo)

    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Summary output
        print(f"\n=== Trend Analysis for: {', '.join(keywords)} ===\n")
        print(f"Timeframe: {results['timeframe']}")
        print(f"Region: {results['geo']}\n")

        print("--- Interest Over Time ---")
        for kw, data in results["interest_over_time"].items():
            direction_emoji = {"rising": "+", "declining": "-", "stable": "="}
            emoji = direction_emoji.get(data["trend_direction"], "?")
            print(f"  [{emoji}] {kw}: {data['change_percent']:+.1f}% ({data['trend_direction']})")
            print(f"      Current: {data['current_interest']}, Peak: {data['peak_interest']}, Avg: {data['average_interest']:.1f}")

        print("\n--- Rising Queries ---")
        for kw, data in results["related_queries"].items():
            if data.get("rising"):
                print(f"  {kw}:")
                for q in data["rising"][:5]:
                    print(f"    - {q['query']} ({q['value']})")

        if results["errors"]:
            print("\n--- Errors ---")
            for err in results["errors"]:
                print(f"  ! {err}")


if __name__ == "__main__":
    main()
