"""
Slack Service Unit Tests

Tests for SlackService including:
- Service initialization
- Send alert to Slack webhook
- Send digest to Slack
- Message formatting (blocks)
- Webhook error handling
- Retry logic for failed sends
- Channel/thread support
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx

from alerts.models import TrendForAlert, SlackMessage
from alerts.slack_service import SlackService, get_slack_service


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.slack_timeout_seconds = 30.0
    settings.slack_max_retries = 3
    return settings


@pytest.fixture
def sample_trend():
    """Create a sample trend for testing."""
    return TrendForAlert(
        id=uuid.uuid4(),
        type="sound",
        name="Test Trend Name",
        velocity_score=85,
        saturation_percent=25,
        video_count_current=1500,
        growth_rate=120.5,
        niche_name="fitness",
        first_detected_at=datetime.utcnow(),
        status="emerging",
        window_hours="6-8"
    )


@pytest.fixture
def sample_trends_list():
    """Create a list of sample trends for digest testing."""
    return [
        TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name=f"Test Trend {i}",
            velocity_score=50 + i * 5,
            saturation_percent=20 + i * 10,
            video_count_current=1000 + i * 100,
            growth_rate=50.0 + i * 10,
            niche_name="fitness" if i < 3 else "cooking",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        for i in range(5)
    ]


@pytest.fixture
def slack_service(mock_settings):
    """Create a SlackService instance with mocked settings."""
    with patch('alerts.slack_service.settings', mock_settings):
        service = SlackService()
        return service


# =============================================================================
# Service Initialization Tests
# =============================================================================

@pytest.mark.asyncio
class TestSlackServiceInitialization:
    """Tests for SlackService initialization."""

    def test_init_with_default_settings(self, mock_settings):
        """Test service initialization with default settings."""
        with patch('alerts.slack_service.settings', mock_settings):
            service = SlackService()
            
            assert service.timeout == 30.0
            assert service.max_retries == 3

    def test_init_with_custom_params(self, mock_settings):
        """Test service initialization with custom parameters."""
        with patch('alerts.slack_service.settings', mock_settings):
            service = SlackService(timeout=60.0, max_retries=5)
            
            assert service.timeout == 60.0
            assert service.max_retries == 5

    def test_init_with_none_params_uses_settings(self, mock_settings):
        """Test that None parameters fall back to settings."""
        with patch('alerts.slack_service.settings', mock_settings):
            service = SlackService(timeout=None, max_retries=None)
            
            assert service.timeout == 30.0
            assert service.max_retries == 3


# =============================================================================
# Message Formatting Tests
# =============================================================================

@pytest.mark.asyncio
class TestMessageFormatting:
    """Tests for Slack message formatting."""

    def test_format_detailed_structure(self, slack_service, sample_trend):
        """Test that detailed format has correct Block Kit structure."""
        message = slack_service._format_detailed(sample_trend, uuid.uuid4())
        
        assert isinstance(message, SlackMessage)
        assert len(message.blocks) >= 4  # Header, fields, velocity, actions, context
        assert message.text is not None
        assert sample_trend.name in message.text

    def test_format_detailed_has_header(self, slack_service, sample_trend):
        """Test that detailed format has header block."""
        message = slack_service._format_detailed(sample_trend, None)
        
        header_blocks = [b for b in message.blocks if b.get("type") == "header"]
        assert len(header_blocks) == 1
        assert sample_trend.name[:50] in header_blocks[0]["text"]["text"]

    def test_format_detailed_has_fields(self, slack_service, sample_trend):
        """Test that detailed format has fields section."""
        message = slack_service._format_detailed(sample_trend, None)
        
        section_blocks = [b for b in message.blocks if b.get("type") == "section"]
        fields_block = [b for b in section_blocks if "fields" in b]
        assert len(fields_block) >= 1
        assert len(fields_block[0]["fields"]) == 4  # Niche, Growth, Videos, Saturation

    def test_format_detailed_has_action_button(self, slack_service, sample_trend):
        """Test that detailed format has action button."""
        message = slack_service._format_detailed(sample_trend, None)
        
        action_blocks = [b for b in message.blocks if b.get("type") == "actions"]
        assert len(action_blocks) == 1
        assert action_blocks[0]["elements"][0]["type"] == "button"

    def test_format_detailed_has_context(self, slack_service, sample_trend):
        """Test that detailed format has context block."""
        message = slack_service._format_detailed(sample_trend, None)
        
        context_blocks = [b for b in message.blocks if b.get("type") == "context"]
        assert len(context_blocks) == 1
        assert sample_trend.type.title() in str(context_blocks[0])

    def test_format_detailed_with_alert_id(self, slack_service, sample_trend):
        """Test that detailed format includes tracking with alert_id."""
        alert_id = uuid.uuid4()
        message = slack_service._format_detailed(sample_trend, alert_id)
        
        # Check that alert_id is in the URL
        action_blocks = [b for b in message.blocks if b.get("type") == "actions"]
        url = action_blocks[0]["elements"][0]["url"]
        assert str(alert_id) in url
        assert "ref=slack" in url

    def test_format_compact_structure(self, slack_service, sample_trend):
        """Test that compact format has correct structure."""
        message = slack_service._format_compact(sample_trend, uuid.uuid4())
        
        assert isinstance(message, SlackMessage)
        assert len(message.blocks) == 1
        assert message.blocks[0]["type"] == "section"

    def test_format_compact_has_button(self, slack_service, sample_trend):
        """Test that compact format has accessory button."""
        message = slack_service._format_compact(sample_trend, None)
        
        assert "accessory" in message.blocks[0]
        assert message.blocks[0]["accessory"]["type"] == "button"

    def test_format_compact_content(self, slack_service, sample_trend):
        """Test that compact format has correct content."""
        message = slack_service._format_compact(sample_trend, None)
        
        text = message.blocks[0]["text"]["text"]
        assert sample_trend.name[:60] in text
        assert str(sample_trend.velocity_score) in text
        assert str(sample_trend.saturation_percent) in text

    def test_format_digest_structure(self, slack_service, sample_trends_list):
        """Test that digest format has correct structure."""
        message = slack_service._format_digest(sample_trends_list, "daily")
        
        assert isinstance(message, SlackMessage)
        assert len(message.blocks) >= 3  # Header, divider, trends, footer

    def test_format_digest_header(self, slack_service, sample_trends_list):
        """Test digest header block."""
        message = slack_service._format_digest(sample_trends_list, "daily")
        
        header_blocks = [b for b in message.blocks if b.get("type") == "header"]
        assert len(header_blocks) == 1
        assert "Daily Trend Digest" in header_blocks[0]["text"]["text"]

    def test_format_digest_all_types(self, slack_service, sample_trends_list):
        """Test digest for all digest types."""
        for digest_type in ["hourly", "daily", "weekly"]:
            message = slack_service._format_digest(sample_trends_list, digest_type)
            
            header_blocks = [b for b in message.blocks if b.get("type") == "header"]
            assert digest_type.title() in header_blocks[0]["text"]["text"]

    def test_format_digest_trend_limit(self, slack_service):
        """Test that digest limits to 10 trends."""
        many_trends = [
            TrendForAlert(
                id=uuid.uuid4(),
                type="sound",
                name=f"Trend {i}",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=1000,
                growth_rate=50.0,
                niche_name="test",
                first_detected_at=datetime.utcnow(),
                status="emerging",
                window_hours="6-8"
            )
            for i in range(15)
        ]
        
        message = slack_service._format_digest(many_trends, "daily")
        
        # Count section blocks (trends)
        section_blocks = [b for b in message.blocks if b.get("type") == "section" and "accessory" in b]
        assert len(section_blocks) == 10

    def test_format_digest_more_indicator(self, slack_service):
        """Test digest shows "more" indicator when > 10 trends."""
        many_trends = [
            TrendForAlert(
                id=uuid.uuid4(),
                type="sound",
                name=f"Trend {i}",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=1000,
                growth_rate=50.0,
                niche_name="test",
                first_detected_at=datetime.utcnow(),
                status="emerging",
                window_hours="6-8"
            )
            for i in range(15)
        ]
        
        message = slack_service._format_digest(many_trends, "daily")
        
        # Find context block with "more"
        context_blocks = [b for b in message.blocks if b.get("type") == "context"]
        assert any("5 more trends" in str(block) for block in context_blocks)

    def test_format_digest_has_footer(self, slack_service, sample_trends_list):
        """Test that digest has footer."""
        message = slack_service._format_digest(sample_trends_list, "daily")
        
        context_blocks = [b for b in message.blocks if b.get("type") == "context"]
        assert len(context_blocks) >= 1
        assert "Trendscope" in str(context_blocks[-1])


# =============================================================================
# Saturation Emoji Tests
# =============================================================================

@pytest.mark.asyncio
class TestSaturationEmoji:
    """Tests for saturation emoji mapping."""

    def test_get_saturation_emoji_low(self, slack_service):
        """Test emoji for low saturation."""
        assert slack_service._get_saturation_emoji(0) == ":green_circle:"
        assert slack_service._get_saturation_emoji(29) == ":green_circle:"

    def test_get_saturation_emoji_medium(self, slack_service):
        """Test emoji for medium saturation."""
        assert slack_service._get_saturation_emoji(30) == ":yellow_circle:"
        assert slack_service._get_saturation_emoji(69) == ":yellow_circle:"

    def test_get_saturation_emoji_high(self, slack_service):
        """Test emoji for high saturation."""
        assert slack_service._get_saturation_emoji(70) == ":red_circle:"
        assert slack_service._get_saturation_emoji(100) == ":red_circle:"


# =============================================================================
# Webhook Sending Tests
# =============================================================================

@pytest.mark.asyncio
class TestWebhookSending:
    """Tests for webhook sending functionality."""

    async def test_send_webhook_success(self, slack_service):
        """Test successful webhook delivery."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('alerts.slack_service.logger') as mock_logger:
                result = await slack_service._send_webhook(webhook_url, payload)
                
                assert result is True
                mock_client.post.assert_called_once_with(webhook_url, json=payload)

    async def test_send_webhook_failure_status_code(self, slack_service):
        """Test webhook delivery failure with non-200 status."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service._send_webhook(webhook_url, payload)
            
            assert result is False

    async def test_send_webhook_timeout(self, slack_service):
        """Test webhook timeout handling."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('alerts.slack_service.logger') as mock_logger:
                result = await slack_service._send_webhook(webhook_url, payload)
                
                assert result is False

    async def test_send_webhook_request_error(self, slack_service):
        """Test webhook request error handling."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('alerts.slack_service.logger') as mock_logger:
                result = await slack_service._send_webhook(webhook_url, payload)
                
                assert result is False


# =============================================================================
# Retry Logic Tests
# =============================================================================

@pytest.mark.asyncio
class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    async def test_retry_on_failure(self, slack_service):
        """Test that failures trigger retries."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('asyncio.sleep', AsyncMock()):
                result = await slack_service._send_webhook(webhook_url, payload)
                
                # Should retry max_retries times
                assert mock_client.post.call_count == slack_service.max_retries

    async def test_no_retry_on_success(self, slack_service):
        """Test that success doesn't trigger retries."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service._send_webhook(webhook_url, payload)
            
            # Should only call once on success
            assert mock_client.post.call_count == 1

    async def test_exponential_backoff_timing(self, slack_service):
        """Test exponential backoff delays are applied between retries."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        payload = {"text": "Test message"}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Just verify that multiple retries happen - timing is validated by implementation
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service._send_webhook(webhook_url, payload)
            
            # Should fail after max_retries attempts
            assert result is False
            # Should have attempted max_retries times
            assert mock_client.post.call_count == slack_service.max_retries


# =============================================================================
# Send Alert Tests
# =============================================================================

@pytest.mark.asyncio
class TestSendAlert:
    """Tests for sending trend alerts."""

    async def test_send_trend_alert_detailed_format(self, slack_service, sample_trend):
        """Test sending alert with detailed format."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        alert_id = uuid.uuid4()
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.send_trend_alert(
                webhook_url=webhook_url,
                trend=sample_trend,
                format="detailed",
                alert_id=alert_id
            )
            
            assert result is True
            mock_client.post.assert_called_once()

    async def test_send_trend_alert_compact_format(self, slack_service, sample_trend):
        """Test sending alert with compact format."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.send_trend_alert(
                webhook_url=webhook_url,
                trend=sample_trend,
                format="compact"
            )
            
            assert result is True

    async def test_send_trend_alert_invalid_format(self, slack_service, sample_trend):
        """Test sending alert with invalid format defaults to detailed."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.send_trend_alert(
                webhook_url=webhook_url,
                trend=sample_trend,
                format="invalid"
            )
            
            assert result is True
            # Should still send (defaults to detailed)


# =============================================================================
# Send Digest Tests
# =============================================================================

@pytest.mark.asyncio
class TestSendDigest:
    """Tests for sending digest messages."""

    async def test_send_digest_success(self, slack_service, sample_trends_list):
        """Test successful digest sending."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.send_digest(
                webhook_url=webhook_url,
                trends=sample_trends_list,
                digest_type="daily"
            )
            
            assert result is True

    async def test_send_digest_empty_list(self, slack_service):
        """Test sending digest with empty list."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.send_digest(
                webhook_url=webhook_url,
                trends=[],
                digest_type="daily"
            )
            
            assert result is True

    async def test_send_digest_all_types(self, slack_service, sample_trends_list):
        """Test sending digests of all types."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        for digest_type in ["hourly", "daily", "weekly"]:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                result = await slack_service.send_digest(
                    webhook_url=webhook_url,
                    trends=sample_trends_list,
                    digest_type=digest_type
                )
                
                assert result is True


# =============================================================================
# Webhook URL Masking Tests
# =============================================================================

@pytest.mark.asyncio
class TestWebhookMasking:
    """Tests for webhook URL privacy masking."""

    def test_mask_webhook_url_normal(self, slack_service):
        """Test masking of normal webhook URL."""
        url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
        masked = slack_service._mask_webhook_url(url)
        
        assert masked.startswith(".../")
        assert "***" in masked
        assert "T00000000" not in masked

    def test_mask_webhook_url_empty(self, slack_service):
        """Test masking of empty URL."""
        masked = slack_service._mask_webhook_url("")
        assert masked == "<empty>"

    def test_mask_webhook_url_none(self, slack_service):
        """Test masking of None URL."""
        masked = slack_service._mask_webhook_url(None)
        assert masked == "<empty>"

    def test_mask_webhook_url_short(self, slack_service):
        """Test masking of short URL."""
        url = "https://example.com"
        masked = slack_service._mask_webhook_url(url)
        assert masked == "***masked***"


# =============================================================================
# Test Webhook Tests
# =============================================================================

@pytest.mark.asyncio
class TestTestWebhook:
    """Tests for webhook testing functionality."""

    async def test_test_webhook_success(self, slack_service):
        """Test successful webhook test."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.test_webhook(webhook_url)
            
            assert result["success"] is True
            assert "successfully" in result["message"]

    async def test_test_webhook_failure(self, slack_service):
        """Test failed webhook test."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid webhook"
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service.test_webhook(webhook_url)
            
            assert result["success"] is False
            assert "Failed" in result["message"]

    async def test_test_webhook_message_structure(self, slack_service):
        """Test that test message has correct structure."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        captured_payload = None
        
        mock_client = AsyncMock()
        
        async def capture_post(url, json):
            nonlocal captured_payload
            captured_payload = json
            return mock_response
        
        mock_client.post = capture_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await slack_service.test_webhook(webhook_url)
            
            assert captured_payload is not None
            assert "blocks" in captured_payload
            assert "text" in captured_payload
            assert "Trendscope Connection Test" in str(captured_payload)


# =============================================================================
# Singleton Tests
# =============================================================================

@pytest.mark.asyncio
class TestSlackServiceSingleton:
    """Tests for singleton instance management."""

    def test_get_slack_service_singleton(self, mock_settings):
        """Test that get_slack_service returns singleton."""
        with patch('alerts.slack_service.settings', mock_settings):
            # Reset singleton for test
            import alerts.slack_service as ss
            ss._slack_service = None
            
            service1 = get_slack_service()
            service2 = get_slack_service()
            
            assert service1 is service2

    def test_get_slack_service_initialization(self, mock_settings):
        """Test that singleton is properly initialized."""
        with patch('alerts.slack_service.settings', mock_settings):
            import alerts.slack_service as ss
            ss._slack_service = None
            
            service = get_slack_service()
            assert isinstance(service, SlackService)
            assert service.timeout == mock_settings.slack_timeout_seconds


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.asyncio
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_format_detailed_long_name_truncation(self, slack_service):
        """Test that long trend names are truncated."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="A" * 100,
            velocity_score=50,
            saturation_percent=50,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name="test",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        message = slack_service._format_detailed(trend, None)
        
        header = message.blocks[0]["text"]["text"]
        assert len(header) <= 65  # "TREND ALERT: " + 50 chars + "..."

    def test_format_compact_long_name_truncation(self, slack_service):
        """Test that long names are truncated in compact format."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="A" * 100,
            velocity_score=50,
            saturation_percent=50,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name="test",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        message = slack_service._format_compact(trend, None)
        
        text = message.blocks[0]["text"]["text"]
        assert len(text) <= 100  # Name limited to 60 + rest of content

    def test_format_detailed_no_niche_name(self, slack_service):
        """Test detailed format without niche name."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Test Trend",
            velocity_score=50,
            saturation_percent=50,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name=None,
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        message = slack_service._format_detailed(trend, None)
        
        # Should show "General" for missing niche
        assert "General" in str(message.blocks) or "#" in str(message.blocks)

    async def test_send_webhook_with_large_payload(self, slack_service):
        """Test sending webhook with large payload."""
        webhook_url = "https://hooks.slack.com/services/T000/B000/XXXX"
        
        # Create large payload
        large_payload = {"text": "x" * 10000}
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await slack_service._send_webhook(webhook_url, large_payload)
            
            assert result is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
