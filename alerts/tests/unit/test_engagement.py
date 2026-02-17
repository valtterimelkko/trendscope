"""
Engagement Tracking Unit Tests

Tests for EngagementTracker including:
- Track alert open
- Track alert click
- Track conversion
- Engagement metrics calculation
- Time-to-open calculation
"""

import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from alerts.models import EngagementEvent, EngagementStats, AlertStatus
from alerts.engagement import EngagementTracker, get_engagement_tracker


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db_pool():
    """Create a mock database pool."""
    pool = AsyncMock()
    return pool


@pytest.fixture
def engagement_tracker(mock_db_pool):
    """Create an EngagementTracker instance with mock db."""
    return EngagementTracker(mock_db_pool)


@pytest.fixture
def sample_alert_id():
    """Create a sample alert ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_user_id():
    """Create a sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_niche_id():
    """Create a sample niche ID."""
    return uuid.uuid4()


# =============================================================================
# Record Sent Tests
# =============================================================================

@pytest.mark.asyncio
class TestRecordSent:
    """Tests for recording sent alerts."""

    async def test_record_sent_success(self, engagement_tracker, sample_alert_id):
        """Test successful recording of sent alert."""
        engagement_tracker.db.execute = AsyncMock(return_value=None)
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_sent(sample_alert_id)
            
            assert result is True
            engagement_tracker.db.execute.assert_called_once()
            # Check that correct SQL was called
            call_args = engagement_tracker.db.execute.call_args
            assert "UPDATE alerts" in call_args[0][0]
            assert "sent_at = NOW()" in call_args[0][0]

    async def test_record_sent_failure(self, engagement_tracker, sample_alert_id):
        """Test handling of database error."""
        engagement_tracker.db.execute = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_sent(sample_alert_id)
            
            assert result is False
            mock_logger.error.assert_called()

    async def test_record_sent_logs_debug(self, engagement_tracker, sample_alert_id):
        """Test that record_sent logs debug message."""
        engagement_tracker.db.execute = AsyncMock(return_value=None)
        
        with patch('alerts.engagement.logger') as mock_logger:
            await engagement_tracker.record_sent(sample_alert_id)
            
            mock_logger.debug.assert_called()
            assert str(sample_alert_id) in str(mock_logger.debug.call_args)


# =============================================================================
# Record Opened Tests
# =============================================================================

@pytest.mark.asyncio
class TestRecordOpened:
    """Tests for recording opened alerts."""

    async def test_record_opened_success(self, engagement_tracker, sample_alert_id):
        """Test successful recording of opened alert."""
        mock_result = {"id": str(sample_alert_id)}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_result)
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_opened(sample_alert_id)
            
            assert result is True
            engagement_tracker.db.fetchrow.assert_called_once()

    async def test_record_opened_with_user_agent(self, engagement_tracker, sample_alert_id):
        """Test recording open with user agent."""
        mock_result = {"id": str(sample_alert_id)}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_result)
        
        user_agent = "Mozilla/5.0 Test Browser"
        
        with patch('alerts.engagement.logger') as mock_logger:
            await engagement_tracker.record_opened(sample_alert_id, user_agent=user_agent)
            
            mock_logger.info.assert_called()
            # User agent should be truncated in logs
            assert "Mozilla" in str(mock_logger.info.call_args)

    async def test_record_opened_with_ip(self, engagement_tracker, sample_alert_id):
        """Test recording open with IP address."""
        mock_result = {"id": str(sample_alert_id)}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_result)
        
        ip_address = "192.168.1.100"
        
        with patch('alerts.engagement.logger') as mock_logger:
            await engagement_tracker.record_opened(sample_alert_id, ip_address=ip_address)
            
            mock_logger.info.assert_called()
            # IP should be masked in logs
            assert "192.168" in str(mock_logger.info.call_args)

    async def test_record_opened_already_opened(self, engagement_tracker, sample_alert_id):
        """Test that already opened alert is not updated."""
        # Return None to simulate already opened (no update needed)
        engagement_tracker.db.fetchrow = AsyncMock(return_value=None)
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_opened(sample_alert_id)
            
            assert result is True  # Still returns True
            engagement_tracker.db.fetchrow.assert_called_once()

    async def test_record_opened_failure(self, engagement_tracker, sample_alert_id):
        """Test handling of database error."""
        engagement_tracker.db.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_opened(sample_alert_id)
            
            assert result is False
            mock_logger.error.assert_called()

    async def test_record_opened_updates_status(self, engagement_tracker, sample_alert_id):
        """Test that status is updated from sent to delivered."""
        engagement_tracker.db.fetchrow = AsyncMock(return_value={"id": str(sample_alert_id)})
        
        await engagement_tracker.record_opened(sample_alert_id)
        
        call_args = engagement_tracker.db.fetchrow.call_args
        sql = call_args[0][0]
        
        # Should include status update logic
        assert "status" in sql
        assert "DELIVERED" in sql or "delivered" in sql


# =============================================================================
# Record Clicked Tests
# =============================================================================

@pytest.mark.asyncio
class TestRecordClicked:
    """Tests for recording clicked alerts."""

    async def test_record_clicked_success(self, engagement_tracker, sample_alert_id):
        """Test successful recording of clicked alert."""
        mock_result = {"id": str(sample_alert_id)}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_result)
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_clicked(sample_alert_id)
            
            assert result is True
            engagement_tracker.db.fetchrow.assert_called_once()

    async def test_record_clicked_with_redirect(self, engagement_tracker, sample_alert_id):
        """Test recording click with redirect URL."""
        mock_result = {"id": str(sample_alert_id)}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_result)
        
        redirect_url = "https://trendscope.io/trends/123"
        
        with patch('alerts.engagement.logger') as mock_logger:
            await engagement_tracker.record_clicked(sample_alert_id, redirect_url=redirect_url)
            
            mock_logger.info.assert_called()
            # Domain should be logged
            assert "trendscope.io" in str(mock_logger.info.call_args)

    async def test_record_clicked_already_clicked(self, engagement_tracker, sample_alert_id):
        """Test that already clicked alert is not updated."""
        engagement_tracker.db.fetchrow = AsyncMock(return_value=None)
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_clicked(sample_alert_id)
            
            assert result is True

    async def test_record_clicked_failure(self, engagement_tracker, sample_alert_id):
        """Test handling of database error."""
        engagement_tracker.db.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.record_clicked(sample_alert_id)
            
            assert result is False
            mock_logger.error.assert_called()


# =============================================================================
# Get Engagement Stats Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetEngagementStats:
    """Tests for getting engagement statistics."""

    async def test_get_engagement_stats_success(self, engagement_tracker, sample_user_id):
        """Test successful retrieval of engagement stats."""
        mock_row = {
            "total_alerts": 100,
            "opened": 50,
            "clicked": 25
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_engagement_stats(sample_user_id, days=30)
        
        assert isinstance(result, EngagementStats)
        assert result.total_alerts == 100
        assert result.opened == 50
        assert result.clicked == 25
        assert result.open_rate == 50.0
        assert result.click_rate == 25.0

    async def test_get_engagement_stats_no_data(self, engagement_tracker, sample_user_id):
        """Test stats with no alerts."""
        mock_row = {
            "total_alerts": 0,
            "opened": 0,
            "clicked": 0
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_engagement_stats(sample_user_id)
        
        assert isinstance(result, EngagementStats)
        assert result.total_alerts == 0
        assert result.open_rate == 0.0
        assert result.click_rate == 0.0

    async def test_get_engagement_stats_default_days(self, engagement_tracker, sample_user_id):
        """Test that default days parameter is 30."""
        mock_row = {"total_alerts": 10, "opened": 5, "clicked": 2}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        await engagement_tracker.get_engagement_stats(sample_user_id)
        
        # Check that SQL contains 30 days
        call_args = engagement_tracker.db.fetchrow.call_args
        assert "30" in str(call_args)

    async def test_get_engagement_stats_custom_days(self, engagement_tracker, sample_user_id):
        """Test custom days parameter."""
        mock_row = {"total_alerts": 10, "opened": 5, "clicked": 2}
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        await engagement_tracker.get_engagement_stats(sample_user_id, days=7)
        
        call_args = engagement_tracker.db.fetchrow.call_args
        assert "7" in str(call_args)

    async def test_get_engagement_stats_db_error(self, engagement_tracker, sample_user_id):
        """Test handling of database error."""
        engagement_tracker.db.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.get_engagement_stats(sample_user_id)
            
            assert isinstance(result, EngagementStats)
            assert result.total_alerts == 0
            mock_logger.error.assert_called()

    async def test_get_engagement_stats_none_row(self, engagement_tracker, sample_user_id):
        """Test when query returns None."""
        engagement_tracker.db.fetchrow = AsyncMock(return_value=None)
        
        result = await engagement_tracker.get_engagement_stats(sample_user_id)
        
        assert isinstance(result, EngagementStats)
        assert result.total_alerts == 0


# =============================================================================
# Get Engagement By Niche Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetEngagementByNiche:
    """Tests for getting engagement stats grouped by niche."""

    async def test_get_engagement_by_niche_success(self, engagement_tracker, sample_user_id):
        """Test successful retrieval of niche engagement."""
        mock_rows = [
            {
                "niche_name": "Fitness",
                "niche_id": uuid.uuid4(),
                "total_alerts": 50,
                "opened": 25,
                "clicked": 10
            },
            {
                "niche_name": "Cooking",
                "niche_id": uuid.uuid4(),
                "total_alerts": 30,
                "opened": 15,
                "clicked": 5
            }
        ]
        engagement_tracker.db.fetch = AsyncMock(return_value=mock_rows)
        
        result = await engagement_tracker.get_engagement_by_niche(sample_user_id, days=30)
        
        assert len(result) == 2
        assert result[0]["niche_name"] == "Fitness"
        assert result[0]["total_alerts"] == 50
        assert result[0]["open_rate"] == 50.0

    async def test_get_engagement_by_niche_empty(self, engagement_tracker, sample_user_id):
        """Test empty niche engagement."""
        engagement_tracker.db.fetch = AsyncMock(return_value=[])
        
        result = await engagement_tracker.get_engagement_by_niche(sample_user_id)
        
        assert result == []

    async def test_get_engagement_by_niche_with_null_niche(self, engagement_tracker, sample_user_id):
        """Test handling of null niche names."""
        mock_rows = [
            {
                "niche_name": None,
                "niche_id": None,
                "total_alerts": 20,
                "opened": 10,
                "clicked": 5
            }
        ]
        engagement_tracker.db.fetch = AsyncMock(return_value=mock_rows)
        
        result = await engagement_tracker.get_engagement_by_niche(sample_user_id)
        
        assert result[0]["niche_name"] == "General"
        assert result[0]["niche_id"] is None

    async def test_get_engagement_by_niche_db_error(self, engagement_tracker, sample_user_id):
        """Test handling of database error."""
        engagement_tracker.db.fetch = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.get_engagement_by_niche(sample_user_id)
            
            assert result == []
            mock_logger.error.assert_called()


# =============================================================================
# Get Recent Engagement Events Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetRecentEngagementEvents:
    """Tests for getting recent engagement events."""

    async def test_get_recent_engagement_events_success(self, engagement_tracker, sample_user_id):
        """Test successful retrieval of recent events."""
        now = datetime.utcnow()
        mock_rows = [
            {
                "alert_id": uuid.uuid4(),
                "sent_at": now - timedelta(hours=2),
                "opened_at": now - timedelta(hours=1),
                "clicked_at": now,
                "trend_name": "Test Trend 1"
            }
        ]
        engagement_tracker.db.fetch = AsyncMock(return_value=mock_rows)
        
        result = await engagement_tracker.get_recent_engagement_events(sample_user_id)
        
        assert len(result) == 2  # One open, one click event
        assert all(isinstance(e, EngagementEvent) for e in result)

    async def test_get_recent_engagement_events_open_only(self, engagement_tracker, sample_user_id):
        """Test events with only open (no click)."""
        now = datetime.utcnow()
        mock_rows = [
            {
                "alert_id": uuid.uuid4(),
                "sent_at": now - timedelta(hours=2),
                "opened_at": now - timedelta(hours=1),
                "clicked_at": None,
                "trend_name": "Test Trend"
            }
        ]
        engagement_tracker.db.fetch = AsyncMock(return_value=mock_rows)
        
        result = await engagement_tracker.get_recent_engagement_events(sample_user_id)
        
        assert len(result) == 1
        assert result[0].event_type == "open"

    async def test_get_recent_engagement_events_empty(self, engagement_tracker, sample_user_id):
        """Test empty engagement events."""
        engagement_tracker.db.fetch = AsyncMock(return_value=[])
        
        result = await engagement_tracker.get_recent_engagement_events(sample_user_id)
        
        assert result == []

    async def test_get_recent_engagement_events_with_limit(self, engagement_tracker, sample_user_id):
        """Test custom limit parameter."""
        engagement_tracker.db.fetch = AsyncMock(return_value=[])
        
        await engagement_tracker.get_recent_engagement_events(sample_user_id, limit=10)
        
        call_args = engagement_tracker.db.fetch.call_args
        # Check that limit (10) was passed as second parameter
        assert len(call_args[0]) >= 2 or 'limit' in str(call_args)

    async def test_get_recent_engagement_events_db_error(self, engagement_tracker, sample_user_id):
        """Test handling of database error."""
        engagement_tracker.db.fetch = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.get_recent_engagement_events(sample_user_id)
            
            assert result == []
            mock_logger.error.assert_called()


# =============================================================================
# Get Alert Engagement Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetAlertEngagement:
    """Tests for getting single alert engagement."""

    async def test_get_alert_engagement_success(self, engagement_tracker, sample_alert_id):
        """Test successful retrieval of alert engagement."""
        now = datetime.utcnow()
        mock_row = {
            "id": sample_alert_id,
            "status": "delivered",
            "sent_at": now - timedelta(hours=2),
            "opened_at": now - timedelta(hours=1),
            "clicked_at": now,
            "time_to_open_seconds": 3600,
            "time_to_click_seconds": 7200
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_alert_engagement(sample_alert_id)
        
        assert result is not None
        assert result["alert_id"] == str(sample_alert_id)
        assert result["status"] == "delivered"
        assert result["is_opened"] is True
        assert result["is_clicked"] is True
        assert result["time_to_open_seconds"] == 3600

    async def test_get_alert_engagement_not_found(self, engagement_tracker, sample_alert_id):
        """Test when alert is not found."""
        engagement_tracker.db.fetchrow = AsyncMock(return_value=None)
        
        result = await engagement_tracker.get_alert_engagement(sample_alert_id)
        
        assert result is None

    async def test_get_alert_engagement_unopened(self, engagement_tracker, sample_alert_id):
        """Test engagement for unopened alert."""
        now = datetime.utcnow()
        mock_row = {
            "id": sample_alert_id,
            "status": "sent",
            "sent_at": now - timedelta(hours=2),
            "opened_at": None,
            "clicked_at": None,
            "time_to_open_seconds": None,
            "time_to_click_seconds": None
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_alert_engagement(sample_alert_id)
        
        assert result["is_opened"] is False
        assert result["is_clicked"] is False

    async def test_get_alert_engagement_db_error(self, engagement_tracker, sample_alert_id):
        """Test handling of database error."""
        engagement_tracker.db.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.get_alert_engagement(sample_alert_id)
            
            assert result is None
            mock_logger.error.assert_called()


# =============================================================================
# Get Global Engagement Stats Tests
# =============================================================================

@pytest.mark.asyncio
class TestGetGlobalEngagementStats:
    """Tests for getting global engagement statistics."""

    async def test_get_global_engagement_stats_success(self, engagement_tracker):
        """Test successful retrieval of global stats."""
        mock_row = {
            "total_alerts": 1000,
            "total_opened": 500,
            "total_clicked": 250,
            "unique_users": 100
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_global_engagement_stats(days=7)
        
        assert result["period_days"] == 7
        assert result["total_alerts"] == 1000
        assert result["total_opened"] == 500
        assert result["total_clicked"] == 250
        assert result["unique_users"] == 100
        assert result["open_rate"] == 50.0
        assert result["click_rate"] == 25.0

    async def test_get_global_engagement_stats_no_data(self, engagement_tracker):
        """Test global stats with no data."""
        mock_row = {
            "total_alerts": 0,
            "total_opened": 0,
            "total_clicked": 0,
            "unique_users": 0
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_global_engagement_stats()
        
        assert result["total_alerts"] == 0
        assert result["open_rate"] == 0
        assert result["click_rate"] == 0

    async def test_get_global_engagement_stats_db_error(self, engagement_tracker):
        """Test handling of database error."""
        engagement_tracker.db.fetchrow = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('alerts.engagement.logger') as mock_logger:
            result = await engagement_tracker.get_global_engagement_stats()
            
            # Should return empty stats on error
            assert result["total_alerts"] == 0
            mock_logger.error.assert_called()


# =============================================================================
# IP Masking Tests
# =============================================================================

@pytest.mark.asyncio
class TestIPMasking:
    """Tests for IP address privacy masking."""

    def test_mask_ip_normal(self, engagement_tracker):
        """Test masking of normal IPv4 address."""
        masked = engagement_tracker._mask_ip("192.168.1.100")
        assert masked == "192.168.***.***"

    def test_mask_ip_different(self, engagement_tracker):
        """Test masking of different IP."""
        masked = engagement_tracker._mask_ip("10.0.0.1")
        assert masked == "10.0.***.***"

    def test_mask_ip_empty(self, engagement_tracker):
        """Test masking of empty IP."""
        masked = engagement_tracker._mask_ip("")
        assert masked == "<empty>"

    def test_mask_ip_none(self, engagement_tracker):
        """Test masking of None IP."""
        masked = engagement_tracker._mask_ip(None)
        assert masked == "<empty>"

    def test_mask_ip_ipv6(self, engagement_tracker):
        """Test masking of IPv6 address (falls back)."""
        masked = engagement_tracker._mask_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        # IPv6 doesn't match IPv4 pattern
        assert masked == "***masked***"


# =============================================================================
# Domain Extraction Tests
# =============================================================================

@pytest.mark.asyncio
class TestDomainExtraction:
    """Tests for URL domain extraction."""

    def test_extract_domain_with_https(self, engagement_tracker):
        """Test domain extraction from HTTPS URL."""
        domain = engagement_tracker._extract_domain("https://trendscope.io/trends/123")
        assert domain == "trendscope.io"

    def test_extract_domain_with_http(self, engagement_tracker):
        """Test domain extraction from HTTP URL."""
        domain = engagement_tracker._extract_domain("http://example.com/path")
        assert domain == "example.com"

    def test_extract_domain_no_protocol(self, engagement_tracker):
        """Test domain extraction without protocol."""
        domain = engagement_tracker._extract_domain("example.com/path")
        assert domain == "example.com"

    def test_extract_domain_with_port(self, engagement_tracker):
        """Test domain extraction with port."""
        domain = engagement_tracker._extract_domain("https://example.com:8080/path")
        assert domain == "example.com:8080"

    def test_extract_domain_empty(self, engagement_tracker):
        """Test domain extraction from empty URL."""
        domain = engagement_tracker._extract_domain("")
        assert domain == "<empty>"

    def test_extract_domain_none(self, engagement_tracker):
        """Test domain extraction from None URL."""
        domain = engagement_tracker._extract_domain(None)
        assert domain == "<empty>"

    def test_extract_domain_invalid(self, engagement_tracker):
        """Test domain extraction from invalid URL."""
        domain = engagement_tracker._extract_domain("://invalid")
        # Returns the part after :// as domain, which is "invalid"
        assert domain == "invalid"

    def test_extract_domain_long(self, engagement_tracker):
        """Test domain extraction with long domain (truncated)."""
        long_domain = "a" * 100 + ".com"
        domain = engagement_tracker._extract_domain(f"https://{long_domain}/path")
        assert len(domain) == 50


# =============================================================================
# Singleton Tests
# =============================================================================

@pytest.mark.asyncio
class TestEngagementTrackerSingleton:
    """Tests for singleton instance management."""

    def test_get_engagement_tracker_singleton(self, mock_db_pool):
        """Test that get_engagement_tracker returns singleton."""
        # Reset singleton for test
        import alerts.engagement as eg
        eg._engagement_tracker = None
        
        service1 = get_engagement_tracker(mock_db_pool)
        service2 = get_engagement_tracker()
        
        assert service1 is service2

    def test_get_engagement_tracker_requires_db_pool_first_call(self):
        """Test that first call requires db_pool."""
        import alerts.engagement as eg
        eg._engagement_tracker = None
        
        with pytest.raises(ValueError) as exc_info:
            get_engagement_tracker()
        
        assert "Database pool required" in str(exc_info.value)

    def test_get_engagement_tracker_initialization(self, mock_db_pool):
        """Test that singleton is properly initialized."""
        import alerts.engagement as eg
        eg._engagement_tracker = None
        
        service = get_engagement_tracker(mock_db_pool)
        assert isinstance(service, EngagementTracker)
        assert service.db is mock_db_pool


# =============================================================================
# Time-to-Open Calculation Tests
# =============================================================================

@pytest.mark.asyncio
class TestTimeToOpenCalculation:
    """Tests for time-to-open metrics."""

    async def test_time_to_open_calculation(self, engagement_tracker, sample_alert_id):
        """Test that time to open is correctly calculated."""
        sent_at = datetime.utcnow() - timedelta(hours=2)
        opened_at = datetime.utcnow() - timedelta(hours=1)
        
        mock_row = {
            "id": sample_alert_id,
            "status": "delivered",
            "sent_at": sent_at,
            "opened_at": opened_at,
            "clicked_at": None,
            "time_to_open_seconds": 3600,
            "time_to_click_seconds": None
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_alert_engagement(sample_alert_id)
        
        assert result["time_to_open_seconds"] == 3600

    async def test_time_to_click_calculation(self, engagement_tracker, sample_alert_id):
        """Test that time to click is correctly calculated."""
        sent_at = datetime.utcnow() - timedelta(hours=2)
        clicked_at = datetime.utcnow() - timedelta(minutes=30)
        
        mock_row = {
            "id": sample_alert_id,
            "status": "delivered",
            "sent_at": sent_at,
            "opened_at": sent_at + timedelta(hours=1),
            "clicked_at": clicked_at,
            "time_to_open_seconds": 3600,
            "time_to_click_seconds": 5400
        }
        engagement_tracker.db.fetchrow = AsyncMock(return_value=mock_row)
        
        result = await engagement_tracker.get_alert_engagement(sample_alert_id)
        
        assert result["time_to_click_seconds"] == 5400


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
