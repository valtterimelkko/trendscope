"""
Integration tests for TrendRepository with PostgreSQL.

Tests all database operations including:
- Trend CRUD operations (create, get, update)
- Platform ID-based lookups
- Listing with filters
- Velocity history recording and retrieval
- Batch operations
- Trend existence checks

Requirements:
- PostgreSQL with trends and trend_velocity_history tables
- DATABASE_URL environment variable set

If PostgreSQL is unavailable, tests are skipped gracefully.
"""

import os
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, List

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from detection.models import (
    Trend,
    TrendType,
    TrendStatus,
    TrendVelocityHistory
)


# =============================================================================
# PostgreSQL Connection Fixture
# =============================================================================

@pytest_asyncio.fixture(scope="module")
async def db_pool() -> AsyncGenerator:
    """
    Create database connection pool for integration tests.
    
    Attempts to connect to real PostgreSQL, falls back to MockPostgresPool
    if unavailable. Skips tests if neither is available.
    """
    if not ASYNCPG_AVAILABLE:
        pytest.skip("asyncpg not installed", allow_module_level=True)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set", allow_module_level=True)
    
    pool = None
    try:
        pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5,
            command_timeout=10
        )
        # Test connection
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        yield pool
    except (asyncpg.exceptions.CannotConnectNowError, 
            asyncpg.exceptions.PostgresConnectionError,
            ConnectionError) as e:
        pytest.skip(f"PostgreSQL not available: {e}", allow_module_level=True)
    finally:
        if pool:
            await pool.close()


@pytest_asyncio.fixture
async def repository(db_pool) -> AsyncGenerator:
    """Create TrendRepository instance with database pool."""
    from detection.persistence import TrendRepository
    repo = TrendRepository(db_pool)
    yield repo


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(db_pool):
    """
    Clean up test data after each test.
    
    Removes all test trends (platform_id LIKE 'test:%') and
    their associated velocity history.
    """
    yield
    # Cleanup after test
    if db_pool:
        async with db_pool.acquire() as conn:
            # Delete velocity history for test trends first (foreign key)
            await conn.execute("""
                DELETE FROM trend_velocity_history 
                WHERE trend_id IN (
                    SELECT id FROM trends 
                    WHERE platform_id LIKE 'test:%'
                )
            """)
            # Delete test trends
            await conn.execute(
                "DELETE FROM trends WHERE platform_id LIKE 'test:%'"
            )


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_trend_data() -> dict:
    """Create sample trend data for testing."""
    now = datetime.utcnow()
    return {
        "type": TrendType.HASHTAG,
        "name": "#testintegration",
        "platform_id": f"test:hashtag:{uuid.uuid4().hex[:8]}",
        "niche_id": None,
        "first_detected_at": now,
        "peak_detected_at": None,
        "status": TrendStatus.EMERGING,
        "velocity_score": 75,
        "saturation_percent": 25,
        "video_count_start": 1,
        "video_count_current": 5,
        "growth_rate": 0.45,
        "metadata": {
            "test": True,
            "source": "integration_test"
        },
        "created_at": now,
        "updated_at": now
    }


@pytest.fixture
def sample_trend_batch() -> List[dict]:
    """Create a batch of sample trends for testing."""
    now = datetime.utcnow()
    trends = []
    statuses = [TrendStatus.EMERGING, TrendStatus.PEAKING, 
                TrendStatus.SATURATED, TrendStatus.EXPIRED]
    types = [TrendType.HASHTAG, TrendType.SOUND]
    
    for i in range(5):
        trends.append({
            "type": types[i % 2],
            "name": f"#testbatch{i}",
            "platform_id": f"test:batch{i}:{uuid.uuid4().hex[:8]}",
            "niche_id": None,
            "first_detected_at": now - timedelta(hours=i * 2),
            "peak_detected_at": now if statuses[i] == TrendStatus.PEAKING else None,
            "status": statuses[i],
            "velocity_score": 80 - (i * 15),
            "saturation_percent": 20 + (i * 20),
            "video_count_start": 1,
            "video_count_current": 10 + (i * 5),
            "growth_rate": 0.5 - (i * 0.1),
            "metadata": {"batch_index": i},
            "created_at": now,
            "updated_at": now
        })
    return trends


@pytest.fixture
def velocity_history_data() -> List[dict]:
    """Create velocity history time-series data."""
    history = []
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(10):
        history.append({
            "timestamp": base_time + timedelta(hours=i * 2),
            "video_count": 100 + (i * 50),
            "velocity_score": 50 + (i * 5),
            "growth_rate": 0.3 + (i * 0.02),
            "saturation_percent": 10 + (i * 8)
        })
    return history


# =============================================================================
# Tests: Trend CRUD Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_create_trend(repository, sample_trend_data):
    """Test creating a new trend record."""
    trend = Trend(**sample_trend_data)
    
    created = await repository.create(trend)
    
    assert created is not None
    assert created.id is not None
    assert created.platform_id == trend.platform_id
    assert created.name == trend.name
    assert created.type == trend.type
    assert created.status == trend.status
    assert created.velocity_score == trend.velocity_score


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_create_duplicate_trend_returns_existing(repository, sample_trend_data):
    """Test that creating a duplicate trend returns the existing one."""
    trend = Trend(**sample_trend_data)
    
    # Create first trend
    created1 = await repository.create(trend)
    
    # Try to create duplicate (same type + platform_id)
    trend2 = Trend(**sample_trend_data)
    trend2.name = "Different Name"  # Different name but same platform_id
    created2 = await repository.create(trend2)
    
    # Should return the first trend
    assert created2.id == created1.id
    assert created2.name == created1.name  # Name should match first, not second


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_trend_by_id(repository, sample_trend_data):
    """Test retrieving a trend by its UUID."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    retrieved = await repository.get_by_id(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.platform_id == trend.platform_id
    assert retrieved.name == trend.name


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_trend_by_id_not_found(repository):
    """Test retrieving a non-existent trend returns None."""
    fake_id = uuid.uuid4()
    retrieved = await repository.get_by_id(fake_id)
    
    assert retrieved is None


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_trend_by_platform_id(repository, sample_trend_data):
    """Test retrieving a trend by type and platform ID."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    retrieved = await repository.get_by_platform_id(
        trend.type, 
        trend.platform_id
    )
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.platform_id == trend.platform_id


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_trend_by_platform_id_not_found(repository):
    """Test retrieving non-existent trend by platform_id returns None."""
    retrieved = await repository.get_by_platform_id(
        TrendType.HASHTAG,
        "test:nonexistent:123"
    )
    
    assert retrieved is None


# =============================================================================
# Tests: Trend Updates
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_update_trend(repository, sample_trend_data):
    """Test updating a trend record."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    updates = {
        "velocity_score": 90,
        "saturation_percent": 60,
        "status": TrendStatus.PEAKING,
        "video_count_current": 100
    }
    
    updated = await repository.update(created.id, updates)
    
    assert updated.velocity_score == 90
    assert updated.saturation_percent == 60
    assert updated.status == TrendStatus.PEAKING
    assert updated.video_count_current == 100
    assert updated.id == created.id  # ID unchanged


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_update_trend_not_found(repository):
    """Test updating a non-existent trend raises ValueError."""
    fake_id = uuid.uuid4()
    
    with pytest.raises(ValueError, match="Trend not found"):
        await repository.update(fake_id, {"velocity_score": 50})


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_update_trend_no_updates(repository, sample_trend_data):
    """Test updating with empty updates raises ValueError."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    with pytest.raises(ValueError, match="No updates provided"):
        await repository.update(created.id, {})


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_update_preserves_other_fields(repository, sample_trend_data):
    """Test that updates don't affect non-updated fields."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    original_name = created.name
    original_type = created.type
    
    # Update only velocity_score
    updated = await repository.update(created.id, {"velocity_score": 95})
    
    assert updated.velocity_score == 95
    assert updated.name == original_name
    assert updated.type == original_type


# =============================================================================
# Tests: Trend Listing with Filters
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_list_trends_no_filter(repository, sample_trend_batch):
    """Test listing trends without filters."""
    # Create batch of trends
    created_ids = []
    for data in sample_trend_batch:
        trend = await repository.create(Trend(**data))
        created_ids.append(trend.id)
    
    trends = await repository.get_trends(limit=10)
    
    assert len(trends) >= len(sample_trend_batch)
    # Verify our created trends are in the list
    trend_ids = [t.id for t in trends]
    for cid in created_ids:
        assert cid in trend_ids


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_list_trends_by_status(repository, sample_trend_batch):
    """Test listing trends filtered by status."""
    # Create batch with different statuses
    for data in sample_trend_batch:
        await repository.create(Trend(**data))
    
    # Get only EMERGING trends
    emerging = await repository.get_trends(
        status=TrendStatus.EMERGING,
        limit=10
    )
    
    for trend in emerging:
        assert trend.status == TrendStatus.EMERGING


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_list_trends_pagination(repository, sample_trend_batch):
    """Test trend listing pagination."""
    # Create batch of trends
    for data in sample_trend_batch:
        await repository.create(Trend(**data))
    
    # Get first page
    page1 = await repository.get_trends(limit=2, offset=0)
    # Get second page
    page2 = await repository.get_trends(limit=2, offset=2)
    
    assert len(page1) <= 2
    assert len(page2) <= 2
    
    # Pages should not overlap (if enough data exists)
    page1_ids = {t.id for t in page1}
    page2_ids = {t.id for t in page2}
    assert not page1_ids.intersection(page2_ids)


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_list_trends_order_by(repository, sample_trend_batch):
    """Test trend listing with custom ordering."""
    # Create batch with different velocity scores
    for data in sample_trend_batch:
        await repository.create(Trend(**data))
    
    # Get trends ordered by velocity_score DESC
    trends = await repository.get_trends(
        limit=10,
        order_by="velocity_score DESC"
    )
    
    # Verify ordering
    for i in range(len(trends) - 1):
        assert trends[i].velocity_score >= trends[i + 1].velocity_score


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_list_trends_limit_capped(repository):
    """Test that limit is capped at 100."""
    # Request more than 100
    trends = await repository.get_trends(limit=200)
    
    # Should be capped (but we may not have 100 test records)
    assert len(trends) <= 100


# =============================================================================
# Tests: Velocity History
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_record_velocity_history(repository, sample_trend_data):
    """Test recording velocity history for a trend."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    # Record history entry
    await repository.record_velocity_history(
        trend_id=created.id,
        timestamp=datetime.utcnow(),
        video_count=150,
        velocity_score=65,
        growth_rate=0.35,
        saturation_percent=30
    )
    
    # Verify by retrieving history
    history = await repository.get_velocity_history(created.id, hours=24)
    
    assert len(history) >= 1
    assert history[0].trend_id == created.id
    assert history[0].video_count == 150
    assert history[0].velocity_score == 65


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_velocity_history_time_window(repository, sample_trend_data, velocity_history_data):
    """Test retrieving velocity history with time window filtering."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    # Record multiple history entries
    for entry in velocity_history_data:
        await repository.record_velocity_history(
            trend_id=created.id,
            **entry
        )
    
    # Get last 12 hours of history
    history = await repository.get_velocity_history(created.id, hours=12)
    
    # Should only get entries within 12 hours
    cutoff = datetime.utcnow() - timedelta(hours=12)
    for entry in history:
        assert entry.timestamp > cutoff


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_velocity_history_empty(repository, sample_trend_data):
    """Test retrieving velocity history for trend with no history."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    history = await repository.get_velocity_history(created.id)
    
    assert history == []


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_velocity_history_data_integrity(repository, sample_trend_data):
    """Test that velocity history data is stored and retrieved correctly."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    test_data = {
        "timestamp": datetime.utcnow(),
        "video_count": 999,
        "velocity_score": 88,
        "growth_rate": 0.55,
        "saturation_percent": 42
    }
    
    await repository.record_velocity_history(created.id, **test_data)
    history = await repository.get_velocity_history(created.id)
    
    assert len(history) == 1
    entry = history[0]
    assert entry.video_count == test_data["video_count"]
    assert entry.velocity_score == test_data["velocity_score"]
    assert abs(entry.growth_rate - test_data["growth_rate"]) < 0.001
    assert entry.saturation_percent == test_data["saturation_percent"]


# =============================================================================
# Tests: Aggregation and Monitoring
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_active_trend_count(repository, sample_trend_batch):
    """Test getting count of trends by status."""
    # Create batch with different statuses
    for data in sample_trend_batch:
        await repository.create(Trend(**data))
    
    counts = await repository.get_active_trend_count()
    
    assert isinstance(counts, dict)
    # Should have counts for our test statuses
    for data in sample_trend_batch:
        status_value = data["status"].value
        if status_value in counts:
            assert counts[status_value] >= 1


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_get_trends_for_alert(repository, sample_trend_batch):
    """Test getting trends eligible for alerting."""
    # Create batch with various velocity scores
    for data in sample_trend_batch:
        await repository.create(Trend(**data))
    
    # Get high velocity trends
    alerts = await repository.get_trends_for_alert(
        min_velocity=50,
        limit=10
    )
    
    for trend in alerts:
        assert trend.velocity_score >= 50
        assert trend.status in [TrendStatus.EMERGING, TrendStatus.PEAKING]


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_cleanup_old_velocity_history(repository, sample_trend_data):
    """Test cleaning up old velocity history records."""
    trend = Trend(**sample_trend_data)
    created = await repository.create(trend)
    
    # Record a recent entry
    await repository.record_velocity_history(
        trend_id=created.id,
        timestamp=datetime.utcnow(),
        video_count=100,
        velocity_score=50,
        growth_rate=0.2,
        saturation_percent=20
    )
    
    # Cleanup with very short retention (should not delete recent)
    deleted = await repository.cleanup_old_velocity_history(hours=1)
    
    # Recent entry should still exist
    history = await repository.get_velocity_history(created.id)
    assert len(history) >= 1


# =============================================================================
# Tests: Edge Cases and Error Handling
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_create_trend_with_null_optional_fields(repository):
    """Test creating trend with null optional fields."""
    trend = Trend(
        type=TrendType.SOUND,
        name="Test Sound",
        platform_id=f"test:sound:{uuid.uuid4().hex[:8]}",
        niche_id=None,
        first_detected_at=datetime.utcnow(),
        peak_detected_at=None,  # Optional
        status=TrendStatus.EMERGING,
        velocity_score=60,
        saturation_percent=30,
        video_count_start=1,
        video_count_current=1,
        growth_rate=0.3,
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    created = await repository.create(trend)
    
    assert created.peak_detected_at is None
    assert created.niche_id is None


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_trend_with_complex_metadata(repository):
    """Test trend with nested metadata structure."""
    trend = Trend(
        type=TrendType.HASHTAG,
        name="#complexmetadata",
        platform_id=f"test:complex:{uuid.uuid4().hex[:8]}",
        niche_id=None,
        first_detected_at=datetime.utcnow(),
        status=TrendStatus.EMERGING,
        velocity_score=70,
        saturation_percent=25,
        video_count_start=1,
        video_count_current=10,
        growth_rate=0.4,
        metadata={
            "example_videos": ["vid1", "vid2", "vid3"],
            "example_creators": [
                {"username": "user1", "follower_count": 5000},
                {"username": "user2", "follower_count": 8000}
            ],
            "nested_data": {
                "key1": "value1",
                "key2": [1, 2, 3],
                "key3": {"a": "b"}
            }
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    created = await repository.create(trend)
    retrieved = await repository.get_by_id(created.id)
    
    assert retrieved.metadata == trend.metadata
    assert retrieved.metadata["example_videos"] == ["vid1", "vid2", "vid3"]


@pytest.mark.integration
@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_concurrent_trend_creation(repository, sample_trend_data):
    """Test creating the same trend concurrently handles conflicts gracefully."""
    trend = Trend(**sample_trend_data)
    
    # Simulate concurrent creation attempts
    results = await asyncio.gather(
        repository.create(trend),
        repository.create(trend),
        repository.create(trend),
        return_exceptions=True
    )
    
    # All should succeed (duplicates return existing)
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) == 3
    
    # All should have the same ID
    ids = [r.id for r in successful]
    assert len(set(ids)) == 1


# Import asyncio for concurrent test
import asyncio
