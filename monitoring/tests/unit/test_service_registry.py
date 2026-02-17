"""
Unit tests for Service Registry.

Tests ServiceRegistry, ServiceInfo, and related functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from monitoring.service_registry import (
    ServiceStatus,
    ServiceType,
    ServiceInfo,
    ServiceRegistry,
    get_service_registry,
)


class TestServiceStatus:
    """Test ServiceStatus enum."""

    def test_service_status_values(self):
        """ServiceStatus should have correct values."""
        assert ServiceStatus.UP == "up"
        assert ServiceStatus.DOWN == "down"
        assert ServiceStatus.STARTING == "starting"
        assert ServiceStatus.STOPPING == "stopping"
        assert ServiceStatus.UNKNOWN == "unknown"


class TestServiceType:
    """Test ServiceType enum."""

    def test_service_type_values(self):
        """ServiceType should have correct values."""
        assert ServiceType.API == "api"
        assert ServiceType.SCRAPER == "scraper"
        assert ServiceType.DETECTION == "detection"
        assert ServiceType.ALERTS == "alerts"
        assert ServiceType.WORKER == "worker"
        assert ServiceType.MONITORING == "monitoring"


class TestServiceInfo:
    """Test ServiceInfo model."""

    def test_service_info_creation(self):
        """Should create ServiceInfo with required fields."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            version="1.0.0",
            host="localhost",
            port=8000,
        )
        
        assert info.name == "test-service"
        assert info.service_type == ServiceType.API
        assert info.version == "1.0.0"
        assert info.host == "localhost"
        assert info.port == 8000
        assert info.status == ServiceStatus.UP
        assert isinstance(info.registered_at, datetime)
        assert isinstance(info.last_heartbeat, datetime)

    def test_service_info_defaults(self):
        """Should use defaults for optional fields."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.WORKER,
            port=8000,
        )
        
        assert info.version == "1.0.0"
        assert info.host == "localhost"
        assert info.status == ServiceStatus.UP
        assert info.metadata == {}

    def test_base_url_property(self):
        """Should generate correct base URL."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            host="localhost",
            port=8000,
        )
        
        assert info.base_url == "http://localhost:8000"

    def test_base_url_custom_host(self):
        """Should use custom host in base URL."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            host="192.168.1.100",
            port=8080,
        )
        
        assert info.base_url == "http://192.168.1.100:8080"

    def test_metrics_url_property(self):
        """Should generate correct metrics URL."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            port=8000,
        )
        
        assert info.metrics_url == "http://localhost:8000/metrics"

    def test_health_url_property(self):
        """Should generate correct health URL."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            port=8000,
        )
        
        assert info.health_url == "http://localhost:8000/health"

    def test_is_healthy_recent_heartbeat(self):
        """Should be healthy with recent heartbeat."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            port=8000,
        )
        
        assert info.is_healthy(timeout_seconds=60) is True

    def test_is_healthy_old_heartbeat(self):
        """Should not be healthy with old heartbeat."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            port=8000,
        )
        
        # Set old heartbeat
        info.last_heartbeat = datetime.utcnow() - timedelta(seconds=120)
        
        assert info.is_healthy(timeout_seconds=60) is False

    def test_is_healthy_not_up_status(self):
        """Should not be healthy if status is not UP."""
        info = ServiceInfo(
            name="test-service",
            service_type=ServiceType.API,
            port=8000,
            status=ServiceStatus.DOWN,
        )
        
        assert info.is_healthy(timeout_seconds=60) is False


class TestServiceRegistryInitialization:
    """Test ServiceRegistry initialization."""

    def test_initialization_with_defaults(self):
        """Should initialize with default values."""
        registry = ServiceRegistry()
        
        assert registry.heartbeat_timeout == 60
        assert registry.cleanup_interval == 30
        assert registry._services == {}

    def test_initialization_with_custom_values(self):
        """Should accept custom configuration."""
        registry = ServiceRegistry(
            heartbeat_timeout_seconds=120,
            cleanup_interval_seconds=60,
        )
        
        assert registry.heartbeat_timeout == 120
        assert registry.cleanup_interval == 60


class TestServiceRegistryRegistration:
    """Test service registration."""

    def test_register_service(self):
        """Should register a service."""
        registry = ServiceRegistry()
        
        service = registry.register(
            service_name="test-service",
            service_type=ServiceType.API,
            port=8000,
            version="1.0.0",
        )
        
        assert service.name == "test-service"
        assert "test-service" in registry._services

    def test_register_with_auto_detected_type(self):
        """Should auto-detect service type from name."""
        registry = ServiceRegistry()
        
        api_service = registry.register("my-api", port=8000)
        scraper_service = registry.register("my-scraper", port=8001)
        
        assert api_service.service_type == ServiceType.API
        assert scraper_service.service_type == ServiceType.SCRAPER

    def test_register_with_metadata(self):
        """Should store service metadata."""
        registry = ServiceRegistry()
        
        service = registry.register(
            service_name="test-service",
            service_type=ServiceType.WORKER,
            port=8000,
            metadata={
                "region": "us-east-1",
                "instance_type": "medium",
            },
        )
        
        assert service.metadata["region"] == "us-east-1"
        assert service.metadata["instance_type"] == "medium"


class TestServiceRegistryDeregistration:
    """Test service deregistration."""

    def test_deregister_existing_service(self):
        """Should deregister an existing service."""
        registry = ServiceRegistry()
        registry.register("test-service", port=8000)
        
        result = registry.deregister("test-service")
        
        assert result is True
        assert "test-service" not in registry._services

    def test_deregister_nonexistent_service(self):
        """Should return False for nonexistent service."""
        registry = ServiceRegistry()
        
        result = registry.deregister("nonexistent")
        
        assert result is False


class TestServiceRegistryHeartbeat:
    """Test heartbeat functionality."""

    def test_heartbeat_updates_timestamp(self):
        """Should update heartbeat timestamp."""
        registry = ServiceRegistry()
        service = registry.register("test-service", port=8000)
        
        old_heartbeat = service.last_heartbeat
        
        # Wait a tiny bit
        import time
        time.sleep(0.01)
        
        registry.heartbeat("test-service")
        
        assert service.last_heartbeat > old_heartbeat

    def test_heartbeat_unknown_service(self):
        """Should return False for unknown service."""
        registry = ServiceRegistry()
        
        result = registry.heartbeat("unknown")
        
        assert result is False

    def test_heartbeat_with_status_update(self):
        """Should update service status."""
        registry = ServiceRegistry()
        service = registry.register("test-service", port=8000)
        
        registry.heartbeat("test-service", status=ServiceStatus.DOWN)
        
        assert service.status == ServiceStatus.DOWN

    def test_heartbeat_with_metadata_update(self):
        """Should update service metadata."""
        registry = ServiceRegistry()
        registry.register("test-service", port=8000, metadata={"version": "1.0.0"})
        
        registry.heartbeat("test-service", metadata={"version": "1.1.0", "load": 0.5})
        
        service = registry.get("test-service")
        assert service.metadata["version"] == "1.1.0"
        assert service.metadata["load"] == 0.5


class TestServiceRegistryQueries:
    """Test service query methods."""

    def test_get_existing_service(self):
        """Should return existing service."""
        registry = ServiceRegistry()
        registry.register("test-service", port=8000)
        
        service = registry.get("test-service")
        
        assert service is not None
        assert service.name == "test-service"

    def test_get_nonexistent_service(self):
        """Should return None for nonexistent service."""
        registry = ServiceRegistry()
        
        service = registry.get("nonexistent")
        
        assert service is None

    def test_get_by_type(self):
        """Should return services by type."""
        registry = ServiceRegistry()
        registry.register("api-1", service_type=ServiceType.API, port=8000)
        registry.register("api-2", service_type=ServiceType.API, port=8001)
        registry.register("scraper-1", service_type=ServiceType.SCRAPER, port=8002)
        
        api_services = registry.get_by_type(ServiceType.API)
        
        assert len(api_services) == 2
        assert all(s.service_type == ServiceType.API for s in api_services)

    def test_get_all(self):
        """Should return all services."""
        registry = ServiceRegistry()
        registry.register("service-1", port=8000)
        registry.register("service-2", port=8001)
        
        all_services = registry.get_all()
        
        assert len(all_services) == 2

    def test_get_healthy(self):
        """Should return healthy services."""
        registry = ServiceRegistry(heartbeat_timeout_seconds=60)
        
        registry.register("healthy-service", port=8000)
        stale_service = registry.register("stale-service", port=8001)
        stale_service.last_heartbeat = datetime.utcnow() - timedelta(seconds=120)
        
        healthy = registry.get_healthy()
        
        assert len(healthy) == 1
        assert healthy[0].name == "healthy-service"

    def test_get_unhealthy(self):
        """Should return unhealthy services."""
        registry = ServiceRegistry(heartbeat_timeout_seconds=60)
        
        registry.register("healthy-service", port=8000)
        stale_service = registry.register("stale-service", port=8001)
        stale_service.last_heartbeat = datetime.utcnow() - timedelta(seconds=120)
        
        unhealthy = registry.get_unhealthy()
        
        assert len(unhealthy) == 1
        assert unhealthy[0].name == "stale-service"


class TestServiceRegistryHealthSummary:
    """Test health summary functionality."""

    def test_health_summary_empty(self):
        """Should return empty summary for no services."""
        registry = ServiceRegistry()
        
        summary = registry.get_health_summary()
        
        assert summary["total_services"] == 0
        assert summary["healthy_count"] == 0
        assert summary["unhealthy_count"] == 0

    def test_health_summary_with_services(self):
        """Should summarize service health."""
        registry = ServiceRegistry()
        registry.register("api-1", service_type=ServiceType.API, port=8000)
        registry.register("scraper-1", service_type=ServiceType.SCRAPER, port=8001)
        
        summary = registry.get_health_summary()
        
        assert summary["total_services"] == 2
        assert summary["healthy_count"] == 2
        assert summary["by_type"]["api"]["total"] == 1
        assert summary["by_type"]["scraper"]["total"] == 1


class TestServiceRegistryServiceTypeDetection:
    """Test service type auto-detection."""

    def test_detect_api_type(self):
        """Should detect API type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("api") == ServiceType.API
        assert registry._detect_service_type("my-api-service") == ServiceType.API
        assert registry._detect_service_type("API-PROXY") == ServiceType.API

    def test_detect_scraper_type(self):
        """Should detect scraper type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("scraper") == ServiceType.SCRAPER
        assert registry._detect_service_type("tiktok-scraper") == ServiceType.SCRAPER

    def test_detect_detection_type(self):
        """Should detect detection type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("detection") == ServiceType.DETECTION
        assert registry._detect_service_type("trend-detector") == ServiceType.DETECTION

    def test_detect_alerts_type(self):
        """Should detect alerts type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("alerts") == ServiceType.ALERTS
        assert registry._detect_service_type("alert-worker") == ServiceType.ALERTS

    def test_detect_worker_type(self):
        """Should detect worker type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("worker") == ServiceType.WORKER
        assert registry._detect_service_type("background-worker") == ServiceType.WORKER

    def test_detect_monitoring_type(self):
        """Should detect monitoring type from name."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("monitoring") == ServiceType.MONITORING
        assert registry._detect_service_type("metrics-monitor") == ServiceType.MONITORING

    def test_default_to_worker(self):
        """Should default to worker type for unknown names."""
        registry = ServiceRegistry()
        
        assert registry._detect_service_type("unknown-service") == ServiceType.WORKER
        assert registry._detect_service_type("myapp") == ServiceType.WORKER


class TestServiceRegistryCleanup:
    """Test cleanup functionality."""

    def test_cleanup_stale_services(self):
        """Should remove stale services."""
        registry = ServiceRegistry(heartbeat_timeout_seconds=60)
        
        registry.register("fresh-service", port=8000)
        stale_service = registry.register("stale-service", port=8001)
        stale_service.last_heartbeat = datetime.utcnow() - timedelta(seconds=200)
        
        removed = registry._cleanup_stale()
        
        assert removed == 1
        assert "stale-service" not in registry._services
        assert "fresh-service" in registry._services

    def test_cleanup_no_stale_services(self):
        """Should not remove fresh services."""
        registry = ServiceRegistry(heartbeat_timeout_seconds=60)
        
        registry.register("fresh-service", port=8000)
        
        removed = registry._cleanup_stale()
        
        assert removed == 0

    @pytest.mark.asyncio
    async def test_start_cleanup_task(self):
        """Should start cleanup task."""
        registry = ServiceRegistry(cleanup_interval_seconds=1)
        
        await registry.start_cleanup_task()
        
        assert registry._cleanup_task is not None
        assert not registry._cleanup_task.done()
        
        # Stop cleanup task
        await registry.stop_cleanup_task()

    @pytest.mark.asyncio
    async def test_stop_cleanup_task(self):
        """Should stop cleanup task."""
        registry = ServiceRegistry(cleanup_interval_seconds=1)
        
        await registry.start_cleanup_task()
        await registry.stop_cleanup_task()
        
        assert registry._cleanup_task.done()


class TestGetServiceRegistry:
    """Test the get_service_registry singleton function."""

    def test_singleton_instance(self):
        """Should return the same instance."""
        # Reset singleton
        import monitoring.service_registry as sr
        sr._service_registry = None
        
        reg1 = get_service_registry()
        reg2 = get_service_registry()
        
        assert reg1 is reg2

    def test_returns_service_registry(self):
        """Should return a ServiceRegistry instance."""
        # Reset singleton
        import monitoring.service_registry as sr
        sr._service_registry = None
        
        registry = get_service_registry()
        
        assert isinstance(registry, ServiceRegistry)
