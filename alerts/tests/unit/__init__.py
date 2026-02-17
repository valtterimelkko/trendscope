"""
Unit tests for the alerts module.

Tests cover:
- Alert models (Pydantic validation, status transitions)
- Deduplication service (Redis-based duplicate detection)
- Tier router (subscription-based routing decisions)
- Configuration (environment-based settings)
"""
