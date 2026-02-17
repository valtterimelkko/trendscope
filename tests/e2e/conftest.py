"""
End-to-End test fixtures and configuration for Trendscope pipeline.

Provides fixtures for:
- Real and mock Redis connections
- Real and mock PostgreSQL connections
- Test data generators
- Pipeline component factories
- Performance measurement utilities

Environment Variables:
- USE_REAL_REDIS: Set to "true" to use real Redis (default: false - use FakeRedis)
- USE_REAL_POSTGRES: Set to "true" to use real PostgreSQL (default: false - use mock)
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- DATABASE_URL: PostgreSQL connection URL (default: postgresql://postgres:postgres@localhost:5432/trendscope)
"""

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Dict, List, Optional, Any, Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# =============================================================================
# Performance Measurement
# =============================================================================

@dataclass
class PipelineMetrics:
    """Metrics collected during E2E pipeline execution."""
    
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    videos_pushed: int = 0
    videos_processed: int = 0
    trends_created: int = 0
    trends_updated: int = 0
    errors_encountered: int = 0
    queue_depth_samples: List[Dict[str, Any]] = field(default_factory=list)
    latency_samples: List[float] = field(default_factory=list)
    
    @property
    def total_duration(self) -> float:
        """Total pipeline duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def processing_rate(self) -> float:
        """Videos processed per second."""
        if self.total_duration > 0:
            return self.videos_processed / self.total_duration
        return 0.0
    
    @property
    def avg_latency(self) -> float:
        """Average end-to-end latency in milliseconds."""
        if self.latency_samples:
            return sum(self.latency_samples) / len(self.latency_samples)
        return 0.0
    
    def record_queue_depth(self, depth: int, label: str = "") -> None:
        """Record queue depth at a point in time."""
        self.queue_depth_samples.append({
            "timestamp": time.time() - self.start_time,
            "depth": depth,
            "label": label
        })
    
    def record_latency(self, latency_ms: float) -> None:
        """Record end-to-end latency for a video."""
        self.latency_samples.append(latency_ms)
    
    def finalize(self) -> None:
        """Finalize metrics collection."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_duration_seconds": round(self.total_duration, 3),
            "videos_pushed": self.videos_pushed,
            "videos_processed": self.videos_processed,
            "trends_created": self.trends_created,
            "trends_updated": self.trends_updated,
            "errors_encountered": self.errors_encountered,
            "processing_rate": round(self.processing_rate, 2),
            "avg_latency_ms": round(self.avg_latency, 2),
            "max_queue_depth": max((s["depth"] for s in self.queue_depth_samples), default=0),
        }


@pytest.fixture
def pipeline_metrics() -> PipelineMetrics:
    """Provide a fresh metrics collector for each test."""
    return PipelineMetrics()


# =============================================================================
# JSON Encoder for Numpy Types
# =============================================================================

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def dump_json_with_numpy(obj):
    """Dump object to JSON string, handling numpy types."""
    return json.dumps(obj, cls=NumpyEncoder)


# =============================================================================
# Mock Services
# =============================================================================

class FakeRedis:
    """
    In-memory Redis mock for E2E testing.
    
    Supports list operations (lpush, rpop, lrange, ltrim, llen),
    TTL management, and pipeline operations.
    """
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._pipelines: List['FakePipeline'] = []
    
    async def ping(self) -> bool:
        return True
    
    async def get(self, key: str) -> Optional[bytes]:
        self._cleanup_expired()
        value = self._data.get(key)
        if value is None:
            return None
        return value.encode() if isinstance(value, str) else value
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        if ex:
            self._expiry[key] = datetime.now(timezone.utc).timestamp() + ex
        return True
    
    async def delete(self, key: str) -> int:
        if key in self._data:
            del self._data[key]
            self._expiry.pop(key, None)
            return 1
        return 0
    
    async def lpush(self, key: str, value: str) -> int:
        if key not in self._data:
            self._data[key] = []
        if not isinstance(self._data[key], list):
            self._data[key] = []
        self._data[key].insert(0, value)
        return len(self._data[key])
    
    async def brpop(self, key: str, timeout: int = 0) -> Optional[tuple]:
        """Blocking right pop - non-blocking in mock."""
        result = await self.rpop(key)
        if result:
            return (key.encode(), result)
        return None
    
    async def rpop(self, key: str) -> Optional[bytes]:
        self._cleanup_expired()
        if key in self._data and isinstance(self._data[key], list):
            if self._data[key]:
                value = self._data[key].pop()
                return value.encode() if isinstance(value, str) else value
        return None
    
    async def llen(self, key: str) -> int:
        if key in self._data and isinstance(self._data[key], list):
            return len(self._data[key])
        return 0
    
    async def exists(self, key: str) -> int:
        self._cleanup_expired()
        return 1 if key in self._data else 0
    
    async def keys(self, pattern: str) -> List[bytes]:
        """Simple pattern matching (supports * wildcard only)."""
        self._cleanup_expired()
        import fnmatch
        matching = [k.encode() for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
        return matching
    
    async def lrange(self, key: str, start: int, end: int) -> List[bytes]:
        if key in self._data and isinstance(self._data[key], list):
            items = self._data[key][start:end+1 if end >= 0 else None]
            return [item.encode() if isinstance(item, str) else item for item in items]
        return []
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to keep only elements from start to end (inclusive)."""
        if key in self._data and isinstance(self._data[key], list):
            self._data[key] = self._data[key][start:end+1 if end >= 0 else None]
            return True
        return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._data:
            self._expiry[key] = datetime.now(timezone.utc).timestamp() + seconds
            return True
        return False
    
    async def ttl(self, key: str) -> int:
        if key in self._expiry:
            remaining = int(self._expiry[key] - datetime.now(timezone.utc).timestamp())
            return max(remaining, 0)
        return -1
    
    async def flushall(self) -> bool:
        """Clear all data - useful for test cleanup."""
        self._data.clear()
        self._expiry.clear()
        return True
    
    def _cleanup_expired(self):
        now = datetime.now(timezone.utc).timestamp()
        expired = [k for k, exp in self._expiry.items() if exp <= now]
        for k in expired:
            self._data.pop(k, None)
            self._expiry.pop(k, None)
    
    def pipeline(self):
        """Create a pipeline for batch operations."""
        pipe = FakePipeline(self)
        self._pipelines.append(pipe)
        return pipe
    
    async def close(self):
        """Close the mock connection."""
        self._data.clear()
        self._expiry.clear()


class FakePipeline:
    """Mock Redis pipeline for batch operations."""
    
    def __init__(self, redis: FakeRedis):
        self._redis = redis
        self._commands: List[tuple] = []
    
    def lpush(self, key: str, value: str) -> 'FakePipeline':
        self._commands.append(('lpush', key, value))
        return self
    
    def expire(self, key: str, seconds: int) -> 'FakePipeline':
        self._commands.append(('expire', key, seconds))
        return self
    
    async def execute(self) -> List[Any]:
        """Execute all pipelined commands."""
        results = []
        for cmd, *args in self._commands:
            if cmd == 'lpush':
                result = await self._redis.lpush(args[0], args[1])
            elif cmd == 'expire':
                result = await self._redis.expire(args[0], args[1])
            else:
                result = None
            results.append(result)
        self._commands.clear()
        return results
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class MockAsyncpgRecord:
    """Mock asyncpg Record that supports dict-like access."""
    
    def __init__(self, data: Dict):
        self._data = data
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()


class MockPostgresConnection:
    """Mock PostgreSQL connection for E2E testing."""
    
    def __init__(self, pool: "MockPostgresPool"):
        self._pool = pool
    
    async def fetch(self, query: str, *args) -> List[MockAsyncpgRecord]:
        """Delegate to pool fetch."""
        results = await self._pool._fetch(query, *args)
        return [MockAsyncpgRecord(r) if isinstance(r, dict) else r for r in results]
    
    async def fetchrow(self, query: str, *args) -> Optional[MockAsyncpgRecord]:
        """Delegate to pool fetchrow."""
        result = await self._pool._fetchrow(query, *args)
        return MockAsyncpgRecord(result) if isinstance(result, dict) else result
    
    async def execute(self, query: str, *args) -> str:
        """Delegate to pool execute."""
        return await self._pool._execute(query, *args)


class MockPoolAcquireContext:
    """Async context manager for pool acquire."""
    
    def __init__(self, pool: "MockPostgresPool"):
        self._pool = pool
        self._connection = None
    
    async def __aenter__(self) -> MockPostgresConnection:
        self._connection = MockPostgresConnection(self._pool)
        return self._connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._connection = None
        return False


class MockPostgresPool:
    """
    Mock PostgreSQL connection pool for E2E testing.
    
    Simulates trend persistence with in-memory storage.
    Compatible with asyncpg Pool interface.
    """
    
    def __init__(self):
        self._data: Dict[str, List[Dict]] = {
            "trends": [],
            "trend_velocity_history": []
        }
        self.closed = False
        self._id_counter = 0
        self._lock = asyncio.Lock()
    
    def _next_id(self) -> str:
        self._id_counter += 1
        return f"mock_id_{self._id_counter}"
    
    def _parse_json(self, data):
        """Parse JSON data, converting numpy types to Python native types."""
        import numpy as np
        
        if isinstance(data, str):
            parsed = json.loads(data)
        else:
            parsed = data
        
        # Recursively convert numpy types
        def convert(obj):
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj
        
        return convert(parsed)
    
    def _serialize_for_json(self, obj):
        """Serialize object for JSON, handling numpy types."""
        import numpy as np
        
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(v) for v in obj]
        return obj
    
    def acquire(self) -> MockPoolAcquireContext:
        """Acquire a connection from the pool."""
        return MockPoolAcquireContext(self)
    
    async def release(self, connection: MockPostgresConnection):
        """Release a connection back to the pool."""
        pass
    
    async def __aenter__(self) -> MockPostgresConnection:
        return MockPostgresConnection(self)
    
    async def __aexit__(self, *args):
        pass
    
    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Mock fetch operation."""
        query_upper = query.upper()
        
        if "FROM TRENDS" in query_upper:
            # Simple filtering support
            results = list(self._data["trends"])
            
            # Handle WHERE clause for status filter
            if "WHERE" in query_upper and "STATUS IN" in query_upper:
                # Filter by status list
                statuses = [arg for arg in args if isinstance(arg, str) and arg in ['emerging', 'peaking', 'saturated', 'expired']]
                if statuses:
                    results = [r for r in results if r.get("status") in statuses]
            elif "WHERE" in query_upper and "STATUS =" in query_upper:
                # Extract status from query or args
                for trend in results[:]:
                    if args and trend.get("status") != args[0]:
                        results.remove(trend)
            
            # Handle ORDER BY and LIMIT
            if "ORDER BY" in query_upper and "VELOCITY_SCORE" in query_upper:
                results.sort(key=lambda x: x.get("velocity_score", 0), reverse=True)
            
            if "LIMIT" in query_upper and args:
                limit = args[-2] if len(args) >= 2 else args[-1]
                if isinstance(limit, int):
                    results = results[:limit]
            
            return results
        
        elif "FROM TREND_VELOCITY_HISTORY" in query_upper:
            trend_id = args[0] if args else None
            if trend_id:
                history = [h for h in self._data["trend_velocity_history"] 
                       if str(h.get("trend_id")) == str(trend_id)]
                # Sort by timestamp
                history.sort(key=lambda x: x.get("timestamp", datetime.min))
                return history
            return list(self._data["trend_velocity_history"])
        
        return []
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Public fetch method - for direct pool usage."""
        return await self._fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Mock fetchrow operation."""
        query_upper = query.upper()
        
        if "SELECT * FROM TRENDS" in query_upper and "TYPE =" in query_upper and "PLATFORM_ID =" in query_upper:
            # Get by platform_id lookup (get_by_platform_id)
            trend_type = args[0] if len(args) > 0 else None
            platform_id = args[1] if len(args) > 1 else None
            for trend in self._data["trends"]:
                if (trend.get("type") == trend_type and 
                    trend.get("platform_id") == platform_id):
                    return trend
            return None
        
        elif "SELECT * FROM TRENDS WHERE ID =" in query_upper:
            trend_id = args[0] if args else None
            for trend in self._data["trends"]:
                if str(trend.get("id")) == str(trend_id):
                    return trend
            return None
        
        elif "INSERT INTO TRENDS" in query_upper:
            # Create new trend
            import uuid
            trend_id = args[0] if args else uuid.uuid4()
            trend = {
                "id": trend_id,
                "type": args[1] if len(args) > 1 else None,
                "name": args[2] if len(args) > 2 else None,
                "platform_id": args[3] if len(args) > 3 else None,
                "niche_id": args[4] if len(args) > 4 else None,
                "first_detected_at": args[5] if len(args) > 5 else datetime.now(timezone.utc),
                "peak_detected_at": args[6] if len(args) > 6 else None,
                "status": args[7] if len(args) > 7 else "emerging",
                "velocity_score": args[8] if len(args) > 8 else 0,
                "saturation_percent": args[9] if len(args) > 9 else 0,
                "video_count_start": args[10] if len(args) > 10 else 1,
                "video_count_current": args[11] if len(args) > 11 else 1,
                "growth_rate": float(args[12]) if len(args) > 12 and args[12] else 0.0,
                "metadata": self._parse_json(args[13]) if len(args) > 13 and args[13] else {},
                "created_at": args[14] if len(args) > 14 else datetime.now(timezone.utc),
                "updated_at": args[15] if len(args) > 15 else datetime.now(timezone.utc),
            }
            
            # Check for conflict
            for existing in self._data["trends"]:
                if (existing.get("type") == trend["type"] and 
                    existing.get("platform_id") == trend["platform_id"]):
                    return None  # Conflict
            
            self._data["trends"].append(trend)
            return trend
        
        elif "UPDATE TRENDS" in query_upper:
            trend_id = args[0] if args else None
            for i, trend in enumerate(self._data["trends"]):
                if str(trend.get("id")) == str(trend_id):
                    # Parse the SET clause to extract fields to update
                    # Query format: UPDATE trends SET updated_at = NOW(), field1 = $2, field2 = $3, ... WHERE id = $1
                    # args[0] = trend_id, args[1] = value1, args[2] = value2, etc.
                    
                    # Extract field names from query (between SET and WHERE)
                    import re
                    # Match SET ... WHERE, handling queries with RETURNING clause
                    # Pattern: SET clause, then WHERE clause (which may be followed by RETURNING)
                    set_match = re.search(r'SET\s+(.+?)\s+WHERE', query, re.IGNORECASE | re.DOTALL)
                    if set_match:
                        set_clause = set_match.group(1)
                        # Find all field assignments like "field = $N" or "field = $N::type"
                        # Note: The query may have escaped backslash-dollar (\\$) or just dollar ($)
                        # Pattern handles: field = $N, field = \$N, field = $N::typename
                        # We match both "field = $N" and "field = \$N" patterns
                        assignments = re.findall(r'(\w+)\s*=\s*\\?\$(\d+)(?:::\w+)?', set_clause)
                        
                        for field_name, param_idx in assignments:
                            # Skip updated_at as it's handled separately
                            if field_name == "updated_at":
                                continue
                            param_index = int(param_idx) - 1  # Convert to 0-based index
                            if param_index < len(args):
                                value = args[param_index]
                                # Handle special case for metadata (needs to be parsed if JSON string)
                                if field_name == "metadata" and isinstance(value, str):
                                    value = self._parse_json(value)
                                # Handle numpy types
                                value = self._serialize_for_json(value)
                                self._data["trends"][i][field_name] = value
                    
                    # Always update timestamp
                    self._data["trends"][i]["updated_at"] = datetime.now(timezone.utc)
                    return self._data["trends"][i]
            return None
        
        return None
    
    async def _fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Internal fetchrow implementation."""
        return await self.fetchrow(query, *args)
    
    async def execute(self, query: str, *args) -> str:
        """Mock execute operation."""
        query_upper = query.upper()
        
        if "INSERT INTO TREND_VELOCITY_HISTORY" in query_upper:
            history = {
                "id": self._next_id(),
                "trend_id": args[0] if len(args) > 0 else None,
                "timestamp": args[1] if len(args) > 1 else datetime.now(timezone.utc),
                "video_count": args[2] if len(args) > 2 else 0,
                "velocity_score": args[3] if len(args) > 3 else None,
                "growth_rate": float(args[4]) if len(args) > 4 and args[4] else None,
                "saturation_percent": args[5] if len(args) > 5 else None,
            }
            self._data["trend_velocity_history"].append(history)
            return "INSERT 0 1"
        
        elif "DELETE FROM TREND_VELOCITY_HISTORY" in query_upper:
            return "DELETE 0"
        
        return "OK"
    
    async def _execute(self, query: str, *args) -> str:
        """Internal execute implementation."""
        return await self.execute(query, *args)
    
    async def close(self):
        """Close the mock pool."""
        self.closed = True


# =============================================================================
# Redis Fixtures
# =============================================================================

def _is_real_redis_available() -> bool:
    """Check if real Redis is available."""
    if os.getenv("USE_REAL_REDIS", "false").lower() != "true":
        return False
    try:
        import redis.asyncio as redis
        # Try to connect
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        # Note: We can't actually test connection here without async context
        return True
    except ImportError:
        return False


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[FakeRedis, None]:
    """
    Provide a Redis client for E2E testing.
    
    Uses FakeRedis by default. Set USE_REAL_REDIS=true to use real Redis.
    """
    use_real = os.getenv("USE_REAL_REDIS", "false").lower() == "true"
    
    if use_real:
        try:
            import redis.asyncio as redis
            client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                encoding="utf-8",
                decode_responses=False
            )
            # Test connection
            await client.ping()
            yield client
            await client.close()
        except Exception as e:
            pytest.skip(f"Real Redis not available: {e}")
    else:
        # Use FakeRedis
        client = FakeRedis()
        yield client
        await client.close()


@pytest_asyncio.fixture
async def clean_redis(redis_client: FakeRedis) -> AsyncGenerator[FakeRedis, None]:
    """Provide a clean Redis instance with all data cleared."""
    await redis_client.flushall()
    yield redis_client
    await redis_client.flushall()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(autouse=True, scope="session")
def patch_json_encoder():
    """
    Patch json.dumps in persistence module to handle numpy types.
    
    This is needed because the TrendDetector creates metadata with numpy types
    (e.g., np.bool_, np.float64) which are not JSON serializable by default.
    """
    import detection.persistence as persistence_module
    
    original_json_loads = persistence_module.json.loads
    original_json_dumps = persistence_module.json.dumps
    
    def patched_dumps(obj, **kwargs):
        """json.dumps that handles numpy types."""
        return original_json_dumps(obj, cls=NumpyEncoder, **kwargs)
    
    # Patch the json module in persistence
    persistence_module.json.dumps = patched_dumps
    
    yield
    
    # Restore original
    persistence_module.json.dumps = original_json_dumps


@pytest_asyncio.fixture
async def db_pool() -> AsyncGenerator[MockPostgresPool, None]:
    """
    Provide a database pool for E2E testing.
    
    Uses MockPostgresPool by default. Set USE_REAL_POSTGRES=true to use real PostgreSQL.
    """
    use_real = os.getenv("USE_REAL_POSTGRES", "false").lower() == "true"
    
    if use_real:
        try:
            import asyncpg
            pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trendscope"),
                min_size=2,
                max_size=10
            )
            yield pool
            await pool.close()
        except Exception as e:
            pytest.skip(f"Real PostgreSQL not available: {e}")
    else:
        # Use MockPostgresPool
        pool = MockPostgresPool()
        yield pool
        await pool.close()


@pytest_asyncio.fixture
async def clean_db(db_pool: MockPostgresPool) -> AsyncGenerator[MockPostgresPool, None]:
    """Provide a clean database with all data cleared."""
    db_pool._data["trends"].clear()
    db_pool._data["trend_velocity_history"].clear()
    db_pool._id_counter = 0
    yield db_pool
    db_pool._data["trends"].clear()
    db_pool._data["trend_velocity_history"].clear()


# =============================================================================
# Test Data Generators
# =============================================================================

@pytest.fixture
def video_factory() -> Callable[..., Dict[str, Any]]:
    """Factory for creating test video data."""
    def _create_video(
        video_id: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        play_count: int = 10000,
        author_followers: int = 5000,
        hours_ago: float = 0,
        with_music: bool = True
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        create_time = int((now - timedelta(hours=hours_ago)).timestamp())
        
        return {
            "id": video_id or f"video_{uuid.uuid4().hex[:12]}",
            "desc": f"Test video with {' '.join(hashtags or ['#test'])}",
            "createTime": create_time,
            "stats": {
                "playCount": play_count,
                "diggCount": int(play_count * 0.15),
                "shareCount": int(play_count * 0.02),
                "commentCount": int(play_count * 0.01)
            },
            "author": {
                "uniqueId": f"creator_{uuid.uuid4().hex[:8]}",
                "nickname": "Test Creator",
                "followerCount": author_followers
            },
            "music": {
                "id": f"sound_{uuid.uuid4().hex[:8]}",
                "title": "Test Sound",
                "authorName": "Test Artist"
            } if with_music else None,
            "hashtags": hashtags or ["test"],
            "scraped_at": now.isoformat(),
            "source_type": "trending",
            "source_query": None
        }
    return _create_video


@pytest.fixture
def generate_test_video(video_factory) -> Callable[..., "VideoData"]:
    """Factory for creating VideoData model instances."""
    def _create(
        hashtags: Optional[List[str]] = None,
        play_count: int = 10000,
        hours_ago: float = 0
    ) -> "VideoData":
        from detection.models import VideoData, VideoStats, VideoAuthor, VideoMusic
        
        now = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        
        stats = VideoStats(
            play_count=play_count,
            digg_count=int(play_count * 0.15),
            share_count=int(play_count * 0.02),
            comment_count=int(play_count * 0.01)
        )
        
        author = VideoAuthor(
            unique_id=f"creator_{uuid.uuid4().hex[:8]}",
            nickname="Test Creator",
            follower_count=5000
        )
        
        music = VideoMusic(
            id=f"sound_{uuid.uuid4().hex[:8]}",
            title="Test Sound",
            author_name="Test Artist"
        )
        
        return VideoData(
            id=f"video_{uuid.uuid4().hex[:12]}",
            desc=f"Test video with {' '.join(hashtags or ['#test'])}",
            create_time=int(now.timestamp()),
            stats=stats,
            author=author,
            music=music,
            hashtags=hashtags or ["test"],
            scraped_at=now,
            source_type="trending",
            source_query=None
        )
    return _create


@pytest.fixture
def generate_viral_videos(video_factory) -> Callable[[int, str], List[Dict[str, Any]]]:
    """Generate multiple videos with viral growth pattern for a hashtag."""
    def _generate(count: int = 50, hashtag: str = "#viraltrend") -> List[Dict[str, Any]]:
        videos = []
        base_views = 5000
        
        for i in range(count):
            # Exponential growth pattern
            growth_multiplier = 1.3 ** i
            play_count = int(base_views * growth_multiplier)
            
            video = video_factory(
                video_id=f"video_{hashtag.strip('#')}_{i}",
                hashtags=[hashtag, "#viral", "#trending"],
                play_count=play_count,
                hours_ago=i * 0.5  # 30 minutes apart
            )
            videos.append(video)
        
        return videos
    return _generate


@pytest.fixture
def generate_batch_videos(video_factory) -> Callable[[int, List[str]], List[Dict[str, Any]]]:
    """Generate a batch of videos with specified hashtags."""
    def _generate(count: int, hashtags: List[str]) -> List[Dict[str, Any]]:
        videos = []
        for i in range(count):
            video = video_factory(
                video_id=f"batch_video_{i}",
                hashtags=hashtags,
                play_count=10000 + (i * 1000),
                hours_ago=i * 0.1
            )
            videos.append(video)
        return videos
    return _generate


# =============================================================================
# Pipeline Component Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def producer(redis_client) -> AsyncGenerator["TikTokProducer", None]:
    """Provide a configured TikTokProducer for E2E testing."""
    from scraper.producer import TikTokProducer
    producer = TikTokProducer(redis_client)
    yield producer


@pytest_asyncio.fixture
async def trend_repository(db_pool) -> AsyncGenerator["TrendRepository", None]:
    """Provide a TrendRepository for E2E testing."""
    from detection.persistence import TrendRepository
    repo = TrendRepository(db_pool)
    yield repo


@pytest_asyncio.fixture
async def trend_detector(trend_repository) -> AsyncGenerator["TrendDetector", None]:
    """Provide a configured TrendDetector for E2E testing."""
    from detection.trend_detector import TrendDetector
    from detection.velocity_engine import VelocityEngine
    from detection.saturation import SaturationEngine
    from detection.lifecycle_manager import LifecycleManager
    
    detector = TrendDetector(
        repository=trend_repository,
        velocity_engine=VelocityEngine(),
        saturation_engine=SaturationEngine(),
        lifecycle_manager=LifecycleManager()
    )
    yield detector


@pytest_asyncio.fixture
async def trend_consumer(redis_client, db_pool, trend_detector) -> AsyncGenerator["TrendConsumer", None]:
    """Provide a configured TrendConsumer for E2E testing."""
    from detection.consumer import TrendConsumer
    consumer = TrendConsumer(
        redis_client=redis_client,
        db_pool=db_pool,
        trend_detector=trend_detector
    )
    yield consumer


# =============================================================================
# Lifecycle State Fixtures
# =============================================================================

@pytest.fixture
def lifecycle_state_factory() -> Callable[[str, int], Dict[str, Any]]:
    """Factory for creating trends at specific lifecycle states."""
    def _create(state: str, data_points: int = 10) -> Dict[str, Any]:
        from detection.models import TrendType, TrendStatus
        
        now = datetime.now(timezone.utc)
        
        # Configure based on state
        configs = {
            "emerging": {
                "velocity_score": 45,
                "saturation_percent": 25,
                "growth_rate": 0.5,
                "status": TrendStatus.EMERGING
            },
            "peaking": {
                "velocity_score": 85,
                "saturation_percent": 60,
                "growth_rate": 1.2,
                "status": TrendStatus.PEAKING
            },
            "saturated": {
                "velocity_score": 30,
                "saturation_percent": 85,
                "growth_rate": 0.2,
                "status": TrendStatus.SATURATED
            },
            "expired": {
                "velocity_score": 10,
                "saturation_percent": 95,
                "growth_rate": 0.05,
                "status": TrendStatus.EXPIRED
            }
        }
        
        config = configs.get(state, configs["emerging"])
        
        return {
            "id": uuid.uuid4(),
            "type": TrendType.HASHTAG,
            "name": f"#{state}trend",
            "platform_id": f"{state}trend",
            "first_detected_at": now - timedelta(hours=data_points),
            "peak_detected_at": now - timedelta(hours=5) if state in ["peaking", "saturated", "expired"] else None,
            "status": config["status"],
            "velocity_score": config["velocity_score"],
            "saturation_percent": config["saturation_percent"],
            "video_count_start": 1,
            "video_count_current": data_points,
            "growth_rate": config["growth_rate"],
            "metadata": {},
            "created_at": now - timedelta(hours=data_points),
            "updated_at": now
        }
    return _create


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def measure_latency() -> Callable[[], Callable[[], float]]:
    """Context manager for measuring operation latency."""
    def _start() -> Callable[[], float]:
        start = time.time()
        def _end() -> float:
            return (time.time() - start) * 1000  # Return milliseconds
        return _end
    return _start


@pytest.fixture
def assert_trend_properties() -> Callable[[Dict, Dict], None]:
    """Helper for asserting trend properties."""
    def _assert(trend: Dict, expected: Dict):
        for key, value in expected.items():
            actual = trend.get(key)
            if key in ["velocity_score", "saturation_percent"]:
                # Allow small tolerance for calculated values
                assert abs(actual - value) < 5, f"{key}: expected ~{value}, got {actual}"
            else:
                assert actual == value, f"{key}: expected {value}, got {actual}"
    return _assert


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def e2e_cleanup():
    """Auto-cleanup after each E2E test."""
    yield
    # Cleanup is handled by individual fixtures
