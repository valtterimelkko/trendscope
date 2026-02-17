"""
Service Registry for Monitoring

Provides service discovery and registration for the monitoring layer.
Tracks which services are running and their endpoints.

This is a lightweight in-memory registry suitable for single-node deployments.
For distributed deployments, consider using Consul or etcd.
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import structlog


logger = structlog.get_logger(__name__)


class ServiceStatus(str, Enum):
    """Status of a registered service."""

    UP = "up"
    DOWN = "down"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Type of Trendscope service."""

    API = "api"
    SCRAPER = "scraper"
    DETECTION = "detection"
    ALERTS = "alerts"
    WORKER = "worker"
    MONITORING = "monitoring"


class ServiceInfo(BaseModel):
    """Information about a registered service."""

    name: str = Field(
        ...,
        description="Unique service name",
    )
    service_type: ServiceType = Field(
        ...,
        description="Type of service",
    )
    version: str = Field(
        default="1.0.0",
        description="Service version",
    )
    host: str = Field(
        default="localhost",
        description="Service hostname",
    )
    port: int = Field(
        ...,
        description="Service port",
    )
    status: ServiceStatus = Field(
        default=ServiceStatus.UP,
        description="Current service status",
    )
    registered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When service was registered",
    )
    last_heartbeat: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last heartbeat received",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional service metadata",
    )

    @property
    def base_url(self) -> str:
        """Get the base URL for this service."""
        return f"http://{self.host}:{self.port}"

    @property
    def metrics_url(self) -> str:
        """Get the metrics endpoint URL."""
        return f"{self.base_url}/metrics"

    @property
    def health_url(self) -> str:
        """Get the health check endpoint URL."""
        return f"{self.base_url}/health"

    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if service is considered healthy.

        Args:
            timeout_seconds: Max seconds since last heartbeat

        Returns:
            True if service is up and heartbeat is recent
        """
        if self.status != ServiceStatus.UP:
            return False

        age = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return age <= timeout_seconds


class ServiceRegistry:
    """Registry for Trendscope services.

    Provides:
    - Service registration and deregistration
    - Heartbeat tracking
    - Service discovery by type
    - Health status tracking

    Example:
        registry = ServiceRegistry()

        # Register a service
        registry.register(
            name="trendscope-api",
            service_type=ServiceType.API,
            port=8000,
            version="1.0.0",
        )

        # Find services
        api_services = registry.get_by_type(ServiceType.API)

        # Heartbeat
        registry.heartbeat("trendscope-api")
    """

    def __init__(
        self,
        heartbeat_timeout_seconds: int = 60,
        cleanup_interval_seconds: int = 30,
    ):
        """Initialize the service registry.

        Args:
            heartbeat_timeout_seconds: Seconds before service considered stale
            cleanup_interval_seconds: How often to clean up stale services
        """
        self.heartbeat_timeout = heartbeat_timeout_seconds
        self.cleanup_interval = cleanup_interval_seconds
        self._services: Dict[str, ServiceInfo] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def register(
        self,
        service_name: str,
        version: str = "1.0.0",
        port: int = 8000,
        host: str = "localhost",
        service_type: Optional[ServiceType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceInfo:
        """Register a service.

        Args:
            service_name: Unique name for this service instance
            version: Service version
            port: Service port
            host: Service hostname
            service_type: Type of service (auto-detected if not provided)
            metadata: Additional metadata

        Returns:
            The registered ServiceInfo
        """
        # Auto-detect service type from name
        if service_type is None:
            service_type = self._detect_service_type(service_name)

        service = ServiceInfo(
            name=service_name,
            service_type=service_type,
            version=version,
            host=host,
            port=port,
            status=ServiceStatus.UP,
            metadata=metadata or {},
        )

        self._services[service_name] = service

        logger.info(
            "service_registered",
            service_name=service_name,
            service_type=service_type.value,
            port=port,
        )

        return service

    def deregister(self, service_name: str) -> bool:
        """Deregister a service.

        Args:
            service_name: Name of service to deregister

        Returns:
            True if service was deregistered
        """
        if service_name in self._services:
            del self._services[service_name]
            logger.info("service_deregistered", service_name=service_name)
            return True
        return False

    def heartbeat(
        self,
        service_name: str,
        status: Optional[ServiceStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record a heartbeat for a service.

        Args:
            service_name: Name of the service
            status: Optional status update
            metadata: Optional metadata update

        Returns:
            True if heartbeat was recorded
        """
        if service_name not in self._services:
            logger.warning(
                "heartbeat_unknown_service",
                service_name=service_name,
            )
            return False

        service = self._services[service_name]
        service.last_heartbeat = datetime.utcnow()

        if status:
            service.status = status

        if metadata:
            service.metadata.update(metadata)

        return True

    def get(self, service_name: str) -> Optional[ServiceInfo]:
        """Get a service by name.

        Args:
            service_name: Service name

        Returns:
            ServiceInfo or None
        """
        return self._services.get(service_name)

    def get_by_type(self, service_type: ServiceType) -> List[ServiceInfo]:
        """Get all services of a given type.

        Args:
            service_type: Type to filter by

        Returns:
            List of matching services
        """
        return [
            s for s in self._services.values()
            if s.service_type == service_type
        ]

    def get_all(self) -> List[ServiceInfo]:
        """Get all registered services.

        Returns:
            List of all services
        """
        return list(self._services.values())

    def get_healthy(self) -> List[ServiceInfo]:
        """Get all healthy services.

        Returns:
            List of healthy services
        """
        return [
            s for s in self._services.values()
            if s.is_healthy(self.heartbeat_timeout)
        ]

    def get_unhealthy(self) -> List[ServiceInfo]:
        """Get all unhealthy services.

        Returns:
            List of unhealthy services
        """
        return [
            s for s in self._services.values()
            if not s.is_healthy(self.heartbeat_timeout)
        ]

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of service health.

        Returns:
            Dict with health statistics
        """
        all_services = self.get_all()
        healthy = self.get_healthy()
        unhealthy = self.get_unhealthy()

        by_type: Dict[str, Dict[str, int]] = {}
        for service in all_services:
            type_name = service.service_type.value
            if type_name not in by_type:
                by_type[type_name] = {"total": 0, "healthy": 0}

            by_type[type_name]["total"] += 1
            if service.is_healthy(self.heartbeat_timeout):
                by_type[type_name]["healthy"] += 1

        return {
            "total_services": len(all_services),
            "healthy_count": len(healthy),
            "unhealthy_count": len(unhealthy),
            "by_type": by_type,
            "services": {
                s.name: {
                    "type": s.service_type.value,
                    "status": s.status.value,
                    "healthy": s.is_healthy(self.heartbeat_timeout),
                    "last_heartbeat": s.last_heartbeat.isoformat(),
                }
                for s in all_services
            },
        }

    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("service_registry_cleanup_started")

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("service_registry_cleanup_stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically clean up stale services."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_stale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("cleanup_error", error=str(e))

    def _cleanup_stale(self) -> int:
        """Remove stale services.

        Returns:
            Number of services removed
        """
        threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout * 3)
        stale = [
            name for name, service in self._services.items()
            if service.last_heartbeat < threshold
        ]

        for name in stale:
            del self._services[name]
            logger.info("service_removed_stale", service_name=name)

        if stale:
            logger.info(
                "cleanup_completed",
                removed_count=len(stale),
            )

        return len(stale)

    def _detect_service_type(self, service_name: str) -> ServiceType:
        """Detect service type from name.

        Args:
            service_name: Service name

        Returns:
            Detected ServiceType
        """
        name_lower = service_name.lower()

        if "api" in name_lower:
            return ServiceType.API
        elif "scraper" in name_lower:
            return ServiceType.SCRAPER
        elif "detection" in name_lower or "detector" in name_lower:
            return ServiceType.DETECTION
        elif "alert" in name_lower:
            return ServiceType.ALERTS
        elif "worker" in name_lower:
            return ServiceType.WORKER
        elif "monitor" in name_lower:
            return ServiceType.MONITORING
        else:
            return ServiceType.WORKER


# Singleton instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global ServiceRegistry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry
