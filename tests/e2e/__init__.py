"""
End-to-End tests for Trendscope pipeline.

This package contains E2E tests that verify the complete data flow:
- Producer → Redis Queue → Consumer → Trend Detector → PostgreSQL

Test categories:
- test_full_pipeline.py: Complete pipeline scenarios
- test_error_recovery.py: Error handling and recovery
- test_pipeline_integrity.py: Data integrity verification

Usage:
    pytest tests/e2e/ -v -m e2e

Environment Variables:
    USE_REAL_REDIS: Set to "true" to use real Redis (default: false)
    USE_REAL_POSTGRES: Set to "true" to use real PostgreSQL (default: false)
"""
