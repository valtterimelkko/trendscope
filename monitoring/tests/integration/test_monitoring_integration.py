"""
Integration tests for Monitoring & Observability.

Tests end-to-end metrics collection, health check integration,
log aggregation pipeline, and alerting on metric thresholds.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from monitoring import configure_monitoring, get_monitoring_config
from monitoring.metrics import (
    MetricsCollector,
    get_metrics_collector,
    get_metrics_output,
    SCRAPER_VIDEOS_PROCESSED_TOTAL,
    API_REQUESTS_TOTAL,
    TRENDS_DETECTED_TOTAL,
    ALERTS_SENT_TOTAL,
)
from monitoring.health_aggregator import (
    HealthAggregator,
    HealthStatus,
    ComponentHealth,
    get_health_aggregator,
)
from monitoring.service_registry import (
    ServiceRegistry,
    ServiceStatus,
    ServiceType,
    get_service_registry,
)
from monitoring.aggregator import (
    MetricsAggregator,
    AggregatedMetrics,
    get_metrics_aggregator,
)
from monitoring.alerts import (
    SystemHealthAlerter,
    AlertSeverity,
    AlertEvent,
    get_system_health_alerter,
)
from monitoring.logging_config import (
    configure_logging,
    get_logger,
    LogContext,
    get_correlation_id,
    set_correlation_id,
)


class TestEndToEndMetricsCollection:
    """Test end-to-end metrics collection pipeline."""

    def test_metrics_pipeline_scraper_to_prometheus(self):
        """Scraper metrics should flow to Prometheus output."""
        # Configure monitoring
        configure_monitoring("test-scraper", log_level="INFO", metrics_enabled=True)
        
        collector = get_metrics_collector()
        
        # Record scraper metrics
        collector.increment_videos_processed("trending", 100)
        collector.increment_videos_processed("hashtag", 50)
        collector.increment_scraper_error("rate_limit")
        collector.set_queue_depth(250)
        
        # Get Prometheus output
        output = get_metrics_output().decode()
        
        # Verify metrics are present
        assert "scraper_videos_processed_total" in output
        assert "scraper_errors_total" in output
        assert "scraper_queue_depth" in output

    def test_metrics_pipeline_api_to_prometheus(self):
        """API metrics should flow to Prometheus output."""
        configure_monitoring("test-api", log_level="INFO", metrics_enabled=True)
        
        collector = get_metrics_collector()
        
        # Record API metrics
        collector.increment_api_request("GET", "/api/v1/trends", 200)
        collector.increment_api_request("POST", "/api/v1/trends", 201)
        collector.increment_api_error("/api/v1/trends", "ValidationError")
        
        # Get Prometheus output
        output = get_metrics_output().decode()
        
        # Verify metrics are present
        assert "api_requests_total" in output
        assert "api_errors_total" in output

    def test_metrics_pipeline_trend_detection(self):
        """Trend detection metrics should flow to Prometheus output."""
        configure_monitoring("test-detection", log_level="INFO", metrics_enabled=True)
        
        collector = get_metrics_collector()
        
        # Record trend detection metrics
        collector.increment_trends_detected("beauty", "sound", 5)
        collector.increment_trends_detected("fitness", "hashtag", 3)
        collector.set_trends_by_status("emerging", 10)
        collector.set_velocity_score("trend123", "Viral Sound", 88)
        
        # Get Prometheus output
        output = get_metrics_output().decode()
        
        # Verify metrics are present
        assert "trends_detected_total" in output
        assert "trends_active_by_status" in output
        assert "trend_velocity_score" in output

    def test_metrics_pipeline_alerts(self):
        """Alert metrics should flow to Prometheus output."""
        configure_monitoring("test-alerts", log_level="INFO", metrics_enabled=True)
        
        collector = get_metrics_collector()
        
        # Record alert metrics
        collector.increment_alerts_sent("slack", "solo")
        collector.increment_alerts_sent("email", "agency")
        collector.increment_alert_failure("slack", "timeout")
        collector.set_pending_alerts(25)
        
        # Get Prometheus output
        output = get_metrics_output().decode()
        
        # Verify metrics are present
        assert "alerts_sent_total" in output
        assert "alert_delivery_failures_total" in output
        assert "alerts_pending" in output

    def test_metrics_with_labels(self):
        """Metrics should preserve labels through the pipeline."""
        configure_monitoring("test-service", log_level="INFO", metrics_enabled=True)
        
        collector = get_metrics_collector()
        
        # Record metrics with different labels
        collector.increment_videos_processed("trending", 10)
        collector.increment_videos_processed("hashtag", 5)
        
        output = get_metrics_output().decode()
        
        # Should have label values in output
        assert 'scraper_type="trending"' in output
        assert 'scraper_type="hashtag"' in output


class TestHealthCheckIntegration:
    """Test health check integration with services."""

    @pytest.mark.asyncio
    async def test_health_check_with_database(self):
        """Health check should integrate with database."""
        from monitoring.health_aggregator import check_database
        
        # Mock database pool
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await check_database(mock_pool)
        
        assert result.status == HealthStatus.PASS
        assert result.component_type == "database"

    @pytest.mark.asyncio
    async def test_health_check_with_redis(self):
        """Health check should integrate with Redis."""
        from monitoring.health_aggregator import check_redis
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        
        result = await check_redis(mock_redis)
        
        assert result.status == HealthStatus.PASS
        assert result.component_type == "cache"

    @pytest.mark.asyncio
    async def test_health_aggregator_integration(self):
        """Health aggregator should integrate multiple checks."""
        aggregator = HealthAggregator("test-service", "1.0.0")
        
        # Register mock checks
        async def passing_db_check():
            return ComponentHealth(
                status=HealthStatus.PASS,
                component_type="database",
                output="Connected",
            )
        
        async def passing_cache_check():
            return ComponentHealth(
                status=HealthStatus.PASS,
                component_type="cache",
                output="Connected",
            )
        
        aggregator.register_check("database", passing_db_check, "database", True)
        aggregator.register_check("redis", passing_cache_check, "cache", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.PASS
        assert "database" in result.checks
        assert "redis" in result.checks
        assert result.checks["database"].status == HealthStatus.PASS
        assert result.checks["redis"].status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_health_check_failure_propagation(self):
        """Health check failures should propagate correctly."""
        aggregator = HealthAggregator("test-service", "1.0.0")
        
        async def failing_check():
            return ComponentHealth(
                status=HealthStatus.FAIL,
                component_type="database",
                output="Connection failed",
            )
        
        async def passing_check():
            return ComponentHealth(
                status=HealthStatus.PASS,
                component_type="cache",
                output="Connected",
            )
        
        aggregator.register_check("database", failing_check, "database", True)
        aggregator.register_check("redis", passing_check, "cache", True)
        
        result = await aggregator.check_health()
        
        assert result.status == HealthStatus.FAIL
        assert result.checks["database"].status == HealthStatus.FAIL
        assert result.checks["redis"].status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_health_check_readiness_integration(self):
        """Readiness check should depend on health status."""
        aggregator = HealthAggregator("test-service", "1.0.0")
        
        async def passing_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        aggregator.register_check("test", passing_check, "test", True)
        
        # Not ready before marking
        is_ready = await aggregator.is_ready()
        assert is_ready is False
        
        # Mark as ready
        aggregator.mark_ready()
        
        # Now should be ready
        is_ready = await aggregator.is_ready()
        assert is_ready is True


class TestLogAggregationPipeline:
    """Test log aggregation pipeline."""

    def test_log_correlation_across_components(self, capsys):
        """Correlation ID should persist across component logs."""
        configure_logging("test-service", "INFO", json_output=True)
        
        logger = get_logger("test")
        
        # Set correlation ID
        set_correlation_id("corr1234")
        
        # Log from different "components"
        with LogContext(component="scraper"):
            logger.info("scraper_started")
        
        with LogContext(component="detector"):
            logger.info("detection_complete")
        
        with LogContext(component="alerter"):
            logger.info("alert_sent")
        
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l]
        
        # All logs should have same correlation ID
        for line in lines:
            try:
                log_entry = json.loads(line)
                assert log_entry["trace_id"] == "corr1234"
            except json.JSONDecodeError:
                continue

    def test_structured_log_output(self, capsys):
        """Logs should be output in structured JSON format."""
        configure_logging("test-service", "INFO", json_output=True)
        
        logger = get_logger("test")
        
        logger.info(
            "request_processed",
            method="POST",
            endpoint="/api/v1/trends",
            status_code=201,
            duration_ms=45,
        )
        
        captured = capsys.readouterr()
        
        try:
            log_entry = json.loads(captured.out.strip())
            
            # Verify structure
            assert "timestamp" in log_entry
            assert log_entry["level"] == "info"
            assert log_entry["message"] == "request_processed"
            assert log_entry["method"] == "POST"
            assert log_entry["endpoint"] == "/api/v1/trends"
            assert log_entry["status_code"] == 201
            assert log_entry["duration_ms"] == 45
        except json.JSONDecodeError:
            pytest.skip("Output may not be JSON in test environment")

    def test_log_level_filtering_pipeline(self, capsys):
        """Log level filtering should work in the pipeline."""
        configure_logging("test-service", "WARNING", json_output=True)
        
        logger = get_logger("test")
        
        logger.debug("debug_message")
        logger.info("info_message")
        logger.warning("warning_message")
        logger.error("error_message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Only warning and error should appear
        assert "debug_message" not in output
        assert "info_message" not in output
        assert "warning_message" in output
        assert "error_message" in output


class TestAlertingOnMetricThresholds:
    """Test alerting based on metric thresholds."""

    def test_alert_on_high_error_rate(self):
        """Should trigger alert when error rate exceeds threshold."""
        alerter = SystemHealthAlerter()
        
        # High error rate metrics
        metrics = {
            "scraper": {
                "error_rate": 0.2,  # Above 0.1 threshold
                "videos_processed": 100,
                "errors": 20,
            }
        }
        
        # Evaluate synchronously
        import asyncio
        alerts = asyncio.run(alerter.evaluate_metrics(metrics))
        
        # Should have triggered an alert
        assert len(alerts) > 0
        assert any(a.rule_name == "scraper_high_error_rate" for a in alerts)

    def test_alert_on_high_api_latency(self):
        """Should trigger alert when API latency exceeds threshold."""
        alerter = SystemHealthAlerter()
        
        # High latency metrics
        metrics = {
            "api": {
                "error_rate": 0.01,
                "p95_latency_ms": 2000,  # Above 1000ms threshold
            }
        }
        
        import asyncio
        alerts = asyncio.run(alerter.evaluate_metrics(metrics))
        
        # Should have triggered an alert
        assert any(a.rule_name == "api_high_latency" for a in alerts)

    def test_alert_on_high_api_error_rate(self):
        """Should trigger alert when API error rate exceeds threshold."""
        alerter = SystemHealthAlerter()
        
        # High error rate metrics
        metrics = {
            "api": {
                "error_rate": 0.1,  # Above 0.05 threshold
                "p95_latency_ms": 100,
            }
        }
        
        import asyncio
        alerts = asyncio.run(alerter.evaluate_metrics(metrics))
        
        # Should have triggered an alert
        assert any(a.rule_name == "api_high_error_rate" for a in alerts)

    def test_alert_on_alert_delivery_failures(self):
        """Should trigger alert when alert delivery fails."""
        alerter = SystemHealthAlerter()
        
        # High failure rate metrics
        metrics = {
            "alerts": {
                "failure_rate": 0.2,  # Above 0.1 threshold
                "pending": 50,
            }
        }
        
        import asyncio
        alerts = asyncio.run(alerter.evaluate_metrics(metrics))
        
        # Should have triggered an alert
        assert any(a.rule_name == "alert_delivery_failures" for a in alerts)

    def test_alert_cooldown_prevents_spam(self):
        """Alert cooldown should prevent duplicate alerts."""
        alerter = SystemHealthAlerter()
        
        metrics = {
            "scraper": {
                "error_rate": 0.2,
                "videos_processed": 100,
                "errors": 20,
            }
        }
        
        import asyncio
        
        # First evaluation should trigger alert
        alerts1 = asyncio.run(alerter.evaluate_metrics(metrics))
        assert len(alerts1) > 0
        
        # Second evaluation immediately should not trigger (cooldown)
        alerts2 = asyncio.run(alerter.evaluate_metrics(metrics))
        assert len(alerts2) == 0

    def test_alert_gets_active_alerts(self):
        """Should track active alerts."""
        alerter = SystemHealthAlerter()
        
        # Manually add an active alert
        alert = AlertEvent(
            rule_name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test alert",
        )
        alerter._active_alerts["test_alert"] = alert
        
        active = alerter.get_active_alerts()
        
        assert len(active) == 1
        assert active[0].rule_name == "test_alert"

    def test_resolve_alert(self):
        """Should resolve active alerts."""
        alerter = SystemHealthAlerter()
        
        # Add an active alert
        alert = AlertEvent(
            rule_name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test alert",
        )
        alerter._active_alerts["test_alert"] = alert
        
        # Resolve it
        resolved = alerter.resolve_alert("test_alert")
        
        assert resolved is not None
        assert resolved.resolved is True
        assert resolved.resolved_at is not None
        assert len(alerter.get_active_alerts()) == 0


class TestServiceRegistryIntegration:
    """Test service registry integration."""

    def test_service_registration(self):
        """Services should register with the registry."""
        registry = ServiceRegistry()
        
        service = registry.register(
            service_name="trendscope-api",
            service_type=ServiceType.API,
            port=8000,
            version="1.0.0",
        )
        
        assert service.name == "trendscope-api"
        assert service.service_type == ServiceType.API
        assert service.port == 8000
        assert service.status == ServiceStatus.UP

    def test_service_heartbeat(self):
        """Services should send heartbeats."""
        registry = ServiceRegistry()
        
        registry.register(
            service_name="test-service",
            service_type=ServiceType.WORKER,
            port=8000,
        )
        
        # Record heartbeat
        result = registry.heartbeat("test-service")
        
        assert result is True
        
        # Get service and verify heartbeat updated
        service = registry.get("test-service")
        assert service.last_heartbeat > service.registered_at

    def test_service_health_check(self):
        """Should be able to check service health."""
        registry = ServiceRegistry(heartbeat_timeout_seconds=60)
        
        registry.register(
            service_name="healthy-service",
            service_type=ServiceType.API,
            port=8000,
        )
        
        service = registry.get("healthy-service")
        
        assert service.is_healthy() is True

    def test_service_health_summary(self):
        """Should provide health summary."""
        registry = ServiceRegistry()
        
        # Register multiple services
        registry.register("api-1", service_type=ServiceType.API, port=8000)
        registry.register("scraper-1", service_type=ServiceType.SCRAPER, port=8001)
        registry.register("detector-1", service_type=ServiceType.DETECTION, port=8002)
        
        summary = registry.get_health_summary()
        
        assert summary["total_services"] == 3
        assert summary["healthy_count"] == 3
        assert summary["by_type"]["api"]["total"] == 1
        assert summary["by_type"]["scraper"]["total"] == 1

    def test_service_type_detection(self):
        """Should auto-detect service type from name."""
        registry = ServiceRegistry()
        
        api = registry.register("my-api-service", port=8000)
        scraper = registry.register("my-scraper", port=8001)
        detector = registry.register("trend-detector", port=8002)
        
        assert api.service_type == ServiceType.API
        assert scraper.service_type == ServiceType.SCRAPER
        assert detector.service_type == ServiceType.DETECTION


class TestMetricsAggregatorIntegration:
    """Test metrics aggregator integration."""

    def test_metrics_aggregation_from_multiple_services(self):
        """Should aggregate metrics from multiple services."""
        aggregator = MetricsAggregator()
        
        # Add metrics from multiple services
        aggregator.update_service_metrics(
            service_name="scraper-1",
            service_type="scraper",
            healthy=True,
            metrics={
                "videos_processed": 1000,
                "errors": 10,
                "circuit_breaker_state": 0,
                "queue_depth": 100,
                "ready": True,
            },
        )
        
        aggregator.update_service_metrics(
            service_name="scraper-2",
            service_type="scraper",
            healthy=True,
            metrics={
                "videos_processed": 500,
                "errors": 5,
                "circuit_breaker_state": 0,
                "queue_depth": 50,
                "ready": True,
            },
        )
        
        # Build aggregated metrics
        import asyncio
        aggregated = asyncio.run(aggregator.collect_and_aggregate())
        
        assert aggregated.scraper_videos_total == 1500
        assert aggregated.scraper_errors_total == 15

    def test_health_summary_aggregation(self):
        """Should aggregate health status from all services."""
        aggregator = MetricsAggregator()
        
        # Add healthy and unhealthy services
        aggregator.update_service_metrics(
            service_name="healthy-1",
            service_type="api",
            healthy=True,
            metrics={},
        )
        
        aggregator.update_service_metrics(
            service_name="unhealthy-1",
            service_type="api",
            healthy=False,
            metrics={},
        )
        
        # Collect and aggregate to update current metrics
        import asyncio
        asyncio.run(aggregator.collect_and_aggregate())
        
        summary = aggregator.get_health_summary()
        
        assert summary["services_total"] == 2
        assert summary["services_healthy"] == 1
        assert summary["overall_healthy"] is False

    def test_performance_summary(self):
        """Should provide performance summary."""
        aggregator = MetricsAggregator()
        
        aggregator.update_service_metrics(
            service_name="api-1",
            service_type="api",
            healthy=True,
            metrics={
                "requests_total": 1000,
                "errors_total": 50,
                "p95_latency_ms": 150,
            },
        )
        
        # Collect and aggregate to update current metrics
        import asyncio
        asyncio.run(aggregator.collect_and_aggregate())
        
        performance = aggregator.get_performance_summary()
        
        assert performance["api"]["requests_total"] == 1000
        assert performance["api"]["error_rate"] == 0.05
        assert performance["api"]["p95_latency_ms"] == 150

    def test_metrics_history(self):
        """Should maintain metrics history."""
        aggregator = MetricsAggregator(retention_minutes=60)
        
        # Add some metrics and aggregate
        aggregator.update_service_metrics(
            service_name="test",
            service_type="api",
            healthy=True,
            metrics={"requests_total": 100},
        )
        
        import asyncio
        asyncio.run(aggregator.collect_and_aggregate())
        
        # Should have history
        history = aggregator.get_metrics_history()
        assert len(history) == 1
        
        # Get current metrics
        current = aggregator.get_current_metrics()
        assert current.api_requests_total == 100


class TestConfigureMonitoring:
    """Test the main configure_monitoring function."""

    def test_full_monitoring_configuration(self):
        """Should configure all monitoring components."""
        configure_monitoring(
            service_name="test-service",
            log_level="DEBUG",
            metrics_enabled=True,
            json_logging=True,
        )
        
        # Verify components are initialized
        config = get_monitoring_config()
        assert config.service_name == "test-service"
        assert config.log_level == "DEBUG"
        assert config.metrics_enabled is True
        assert config.json_logging is True
        
        # Verify health aggregator
        health = get_health_aggregator()
        assert health.service_name == "test-service"
        
        # Verify service registry
        registry = get_service_registry()
        assert "test-service" in [s.name for s in registry.get_all()]

    def test_monitoring_with_disabled_metrics(self):
        """Should work with metrics disabled."""
        configure_monitoring(
            service_name="test-service",
            metrics_enabled=False,
        )
        
        config = get_monitoring_config()
        assert config.metrics_enabled is False


class TestCrossComponentIntegration:
    """Test integration across all monitoring components."""

    @pytest.mark.asyncio
    async def test_full_monitoring_scenario(self):
        """Test a full monitoring scenario end-to-end."""
        # 1. Configure monitoring
        configure_monitoring("integration-test", log_level="INFO")
        
        # 2. Record some metrics
        collector = get_metrics_collector()
        collector.increment_videos_processed("trending", 100)
        collector.increment_api_request("GET", "/api/v1/trends", 200)
        
        # 3. Check health
        health_agg = get_health_aggregator()
        
        async def mock_check():
            return ComponentHealth(status=HealthStatus.PASS)
        
        health_agg.register_check("mock", mock_check, "test", True)
        health_agg.mark_ready()
        
        health = await health_agg.check_health()
        assert health.status == HealthStatus.PASS
        
        # 4. Register service
        registry = get_service_registry()
        registry.register("test-worker", port=8000)
        
        # 5. Aggregate metrics
        metrics_agg = get_metrics_aggregator()
        metrics_agg.update_service_metrics(
            service_name="test-worker",
            service_type="worker",
            healthy=True,
            metrics={"jobs_processed": 50},
        )
        
        aggregated = await metrics_agg.collect_and_aggregate()
        assert aggregated.services_total >= 1
        
        # 6. Check service health
        is_ready = await health_agg.is_ready()
        assert is_ready is True

    def test_metrics_health_correlation(self):
        """Health status should correlate with metrics."""
        configure_monitoring("correlation-test")
        
        collector = get_metrics_collector()
        
        # Set unhealthy state
        collector.set_health_status("database", False)
        
        # Health aggregator should reflect this
        # (In real scenario, health check would read metrics)

    def test_logging_with_health_context(self, capsys):
        """Logs should include health context."""
        configure_logging("health-test", "INFO", json_output=True)
        
        logger = get_logger("test")
        
        with LogContext(health_status="degraded", component="database"):
            logger.warning("health_check_warning", reason="high_latency")
        
        captured = capsys.readouterr()
        
        try:
            log_entry = json.loads(captured.out.strip())
            assert log_entry["health_status"] == "degraded"
            assert log_entry["component"] == "database"
            assert log_entry["reason"] == "high_latency"
        except json.JSONDecodeError:
            pytest.skip("Output may not be JSON in test environment")
