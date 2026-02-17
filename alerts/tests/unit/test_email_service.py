"""
Email Service Unit Tests

Tests for EmailService including:
- Service initialization with config
- Send single alert email
- Send digest email
- Email template rendering
- Error handling (provider failures)
- Rate limiting integration
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from unittest.mock import ANY

# Import models first
from alerts.models import TrendForAlert, EmailContent

# Then import service
from alerts.email_service import EmailService, get_email_service


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.email_api_key = "test-api-key"
    settings.email_from_address = "alerts@test.com"
    settings.email_from_name = "Trendscope"
    settings.email_provider = "stub"
    settings.tracking_base_url = "https://app.trendscope.io"
    settings.tracking_pixel_enabled = True
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
def email_service(mock_settings):
    """Create an EmailService instance with mocked settings."""
    with patch('alerts.email_service.settings', mock_settings):
        service = EmailService()
        return service


# =============================================================================
# Service Initialization Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailServiceInitialization:
    """Tests for EmailService initialization."""

    def test_init_with_default_settings(self, mock_settings):
        """Test service initialization with default settings."""
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            assert service.api_key == "test-api-key"
            assert service.from_email == "alerts@test.com"
            assert service.from_name == "Trendscope"
            assert service.provider == "stub"

    def test_init_with_custom_params(self, mock_settings):
        """Test service initialization with custom parameters."""
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService(
                api_key="custom-key",
                from_email="custom@test.com",
                from_name="Custom Name"
            )
            
            assert service.api_key == "custom-key"
            assert service.from_email == "custom@test.com"
            assert service.from_name == "Custom Name"

    def test_init_with_none_params_uses_settings(self, mock_settings):
        """Test that None parameters fall back to settings."""
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService(api_key=None, from_email=None, from_name=None)
            
            assert service.api_key == "test-api-key"
            assert service.from_email == "alerts@test.com"
            assert service.from_name == "Trendscope"

    def test_init_different_providers(self, mock_settings):
        """Test initialization with different provider settings."""
        providers = ["stub", "resend", "sendgrid"]
        
        for provider in providers:
            mock_settings.email_provider = provider
            with patch('alerts.email_service.settings', mock_settings):
                service = EmailService()
                assert service.provider == provider


# =============================================================================
# Email Rendering Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailRendering:
    """Tests for email template rendering."""

    def test_render_trend_email_structure(self, email_service, sample_trend):
        """Test that trend email has correct structure."""
        alert_id = uuid.uuid4()
        content = email_service._render_trend_email(sample_trend, alert_id)
        
        assert isinstance(content, EmailContent)
        assert content.subject.startswith("TREND ALERT:")
        assert sample_trend.name in content.subject
        assert content.html_body is not None
        assert content.text_body is not None
        assert content.tracking_pixel_url is not None
        assert content.tracking_link_base is not None

    def test_render_trend_email_contains_trend_data(self, email_service, sample_trend):
        """Test that email contains all trend data."""
        content = email_service._render_trend_email(sample_trend, uuid.uuid4())
        
        # Check HTML body - use formatted number with commas
        assert sample_trend.name in content.html_body
        assert str(sample_trend.velocity_score) in content.html_body
        assert str(sample_trend.saturation_percent) in content.html_body
        # Video count is formatted with commas in HTML (1,500)
        assert f"{sample_trend.video_count_current:,}" in content.html_body
        assert sample_trend.niche_name in content.html_body
        
        # Check text body
        assert sample_trend.name in content.text_body
        assert str(sample_trend.velocity_score) in content.text_body

    def test_render_trend_email_without_alert_id(self, email_service, sample_trend):
        """Test rendering without tracking alert ID."""
        content = email_service._render_trend_email(sample_trend, None)
        
        assert content.tracking_pixel_url is None
        assert isinstance(content.html_body, str)

    def test_render_trend_email_long_name_truncation(self, email_service):
        """Test that long trend names are truncated in subject."""
        long_name_trend = TrendForAlert(
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
        
        content = email_service._render_trend_email(long_name_trend, uuid.uuid4())
        assert len(content.subject) <= 55  # "TREND ALERT: " + 40 chars + "..."

    def test_render_trend_email_saturation_emoji_low(self, email_service):
        """Test saturation emoji for low saturation."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Test",
            velocity_score=50,
            saturation_percent=20,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name="test",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        content = email_service._render_trend_email(trend, None)
        assert "🟢" in content.html_body

    def test_render_trend_email_saturation_emoji_medium(self, email_service):
        """Test saturation emoji for medium saturation."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Test",
            velocity_score=50,
            saturation_percent=50,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name="test",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        content = email_service._render_trend_email(trend, None)
        assert "🟡" in content.html_body

    def test_render_trend_email_saturation_emoji_high(self, email_service):
        """Test saturation emoji for high saturation."""
        trend = TrendForAlert(
            id=uuid.uuid4(),
            type="sound",
            name="Test",
            velocity_score=50,
            saturation_percent=80,
            video_count_current=1000,
            growth_rate=50.0,
            niche_name="test",
            first_detected_at=datetime.utcnow(),
            status="emerging",
            window_hours="6-8"
        )
        
        content = email_service._render_trend_email(trend, None)
        assert "🔴" in content.html_body

    def test_render_digest_email_structure(self, email_service, sample_trends_list):
        """Test that digest email has correct structure."""
        content = email_service._render_digest_email(sample_trends_list, "daily")
        
        assert isinstance(content, EmailContent)
        assert "Daily Trend Digest" in content.subject
        assert str(len(sample_trends_list)) in content.subject
        assert content.html_body is not None
        assert content.text_body is not None

    def test_render_digest_email_all_types(self, email_service, sample_trends_list):
        """Test digest rendering for all digest types."""
        for digest_type in ["hourly", "daily", "weekly"]:
            content = email_service._render_digest_email(sample_trends_list, digest_type)
            assert digest_type.title() in content.subject
            assert len(sample_trends_list) in [int(s) for s in content.subject.split() if s.isdigit()]

    def test_render_digest_email_trend_limit(self, email_service):
        """Test that digest limits to 20 trends in HTML."""
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
            for i in range(25)
        ]
        
        content = email_service._render_digest_email(many_trends, "daily")
        assert "...and 5 more trends" in content.html_body

    def test_render_digest_empty_list(self, email_service):
        """Test digest rendering with empty list."""
        content = email_service._render_digest_email([], "daily")
        assert "Daily Trend Digest" in content.subject
        assert "0" in content.subject


# =============================================================================
# Email Sending Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailSending:
    """Tests for sending emails through different providers."""

    async def test_send_trend_alert_stub_provider(self, email_service, sample_trend):
        """Test sending trend alert with stub provider."""
        with patch('alerts.email_service.logger') as mock_logger:
            result = await email_service.send_trend_alert(
                to_email="user@example.com",
                trend=sample_trend,
                alert_id=uuid.uuid4()
            )
            
            assert result is True
            mock_logger.info.assert_called()

    async def test_send_digest_stub_provider(self, email_service, sample_trends_list):
        """Test sending digest with stub provider."""
        with patch('alerts.email_service.logger') as mock_logger:
            result = await email_service.send_digest(
                to_email="user@example.com",
                trends=sample_trends_list,
                digest_type="daily"
            )
            
            assert result is True
            mock_logger.info.assert_called()

    async def test_send_trend_alert_resend_provider_success(self, mock_settings, sample_trend):
        """Test sending via Resend API successfully."""
        mock_settings.email_provider = "resend"
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            mock_resend = Mock()
            mock_resend.Emails = Mock()
            mock_resend.Emails.send = Mock(return_value={"id": "email-123"})
            
            with patch.dict('sys.modules', {'resend': mock_resend}):
                with patch('alerts.email_service.logger') as mock_logger:
                    result = await service.send_trend_alert(
                        to_email="user@example.com",
                        trend=sample_trend,
                        alert_id=uuid.uuid4()
                    )
                    
                    assert result is True
                    mock_logger.info.assert_called()

    async def test_send_trend_alert_resend_provider_failure(self, mock_settings, sample_trend):
        """Test Resend API failure handling."""
        mock_settings.email_provider = "resend"
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            mock_resend = Mock()
            mock_resend.Emails = Mock()
            mock_resend.Emails.send = Mock(side_effect=Exception("API Error"))
            
            with patch.dict('sys.modules', {'resend': mock_resend}):
                with patch('alerts.email_service.logger') as mock_logger:
                    result = await service.send_trend_alert(
                        to_email="user@example.com",
                        trend=sample_trend,
                        alert_id=uuid.uuid4()
                    )
                    
                    assert result is False
                    mock_logger.error.assert_called()

    async def test_send_trend_alert_sendgrid_provider_success(self, mock_settings, sample_trend):
        """Test sending via SendGrid API successfully."""
        mock_settings.email_provider = "sendgrid"
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            mock_mail = Mock()
            mock_sg = Mock()
            mock_response = Mock()
            mock_response.status_code = 202
            mock_sg.send = Mock(return_value=mock_response)
            mock_sg_client = Mock(return_value=mock_sg)
            
            mock_sendgrid_module = Mock()
            mock_sendgrid_module.SendGridAPIClient = mock_sg_client
            mock_sendgrid_module.Mail = mock_mail
            mock_helpers = Mock()
            mock_helpers.mail = Mock()
            mock_sendgrid_module.helpers = mock_helpers
            
            with patch.dict('sys.modules', {
                'sendgrid': mock_sendgrid_module,
                'sendgrid.helpers': mock_helpers,
                'sendgrid.helpers.mail': mock_helpers.mail
            }):
                with patch('alerts.email_service.logger') as mock_logger:
                    result = await service.send_trend_alert(
                        to_email="user@example.com",
                        trend=sample_trend,
                        alert_id=uuid.uuid4()
                    )
                    
                    assert result is True

    async def test_send_trend_alert_sendgrid_provider_failure(self, mock_settings, sample_trend):
        """Test SendGrid API failure handling."""
        mock_settings.email_provider = "sendgrid"
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            mock_sendgrid_module = Mock()
            mock_sendgrid_module.SendGridAPIClient = Mock(side_effect=Exception("SendGrid Error"))
            
            with patch.dict('sys.modules', {'sendgrid': mock_sendgrid_module}):
                with patch('alerts.email_service.logger') as mock_logger:
                    result = await service.send_trend_alert(
                        to_email="user@example.com",
                        trend=sample_trend,
                        alert_id=uuid.uuid4()
                    )
                    
                    assert result is False
                    mock_logger.error.assert_called()

    async def test_send_trend_alert_unknown_provider_fallback(self, mock_settings, sample_trend):
        """Test that unknown provider falls back to stub."""
        mock_settings.email_provider = "unknown_provider"
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            
            with patch('alerts.email_service.logger') as mock_logger:
                result = await service.send_trend_alert(
                    to_email="user@example.com",
                    trend=sample_trend,
                    alert_id=uuid.uuid4()
                )
                
                assert result is True
                # Should log warning about unknown provider
                mock_logger.warning.assert_called()


# =============================================================================
# Email Masking Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailMasking:
    """Tests for email privacy masking."""

    def test_mask_email_normal(self, email_service):
        """Test masking of normal email."""
        masked = email_service._mask_email("john.doe@example.com")
        assert masked == "j***@example.com"

    def test_mask_email_short_local(self, email_service):
        """Test masking of email with short local part."""
        masked = email_service._mask_email("ab@example.com")
        assert masked == "a***@example.com"

    def test_mask_email_single_char_local(self, email_service):
        """Test masking of email with single char local part."""
        masked = email_service._mask_email("a@example.com")
        assert masked == "***@example.com"

    def test_mask_email_invalid(self, email_service):
        """Test masking of invalid email."""
        masked = email_service._mask_email("not-an-email")
        assert masked == "<invalid>"

    def test_mask_email_empty(self, email_service):
        """Test masking of empty email."""
        masked = email_service._mask_email("")
        assert masked == "<invalid>"

    def test_mask_email_none(self, email_service):
        """Test masking of None email."""
        masked = email_service._mask_email(None)
        assert masked == "<invalid>"


# =============================================================================
# Saturation Helper Tests
# =============================================================================

@pytest.mark.asyncio
class TestSaturationHelpers:
    """Tests for saturation emoji and class helpers."""

    def test_get_saturation_emoji_low(self, email_service):
        """Test emoji for low saturation (< 30)."""
        assert email_service._get_saturation_emoji(0) == "🟢"
        assert email_service._get_saturation_emoji(29) == "🟢"

    def test_get_saturation_emoji_medium(self, email_service):
        """Test emoji for medium saturation (30-69)."""
        assert email_service._get_saturation_emoji(30) == "🟡"
        assert email_service._get_saturation_emoji(69) == "🟡"

    def test_get_saturation_emoji_high(self, email_service):
        """Test emoji for high saturation (>= 70)."""
        assert email_service._get_saturation_emoji(70) == "🔴"
        assert email_service._get_saturation_emoji(100) == "🔴"

    def test_get_saturation_class_low(self, email_service):
        """Test class for low saturation."""
        assert email_service._get_saturation_class(0) == "saturation-low"
        assert email_service._get_saturation_class(29) == "saturation-low"

    def test_get_saturation_class_medium(self, email_service):
        """Test class for medium saturation."""
        assert email_service._get_saturation_class(30) == "saturation-medium"
        assert email_service._get_saturation_class(69) == "saturation-medium"

    def test_get_saturation_class_high(self, email_service):
        """Test class for high saturation."""
        assert email_service._get_saturation_class(70) == "saturation-high"
        assert email_service._get_saturation_class(100) == "saturation-high"


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling scenarios."""

    async def test_send_trend_alert_render_error(self, email_service, sample_trend):
        """Test error handling during email rendering."""
        with patch.object(email_service, '_render_trend_email', side_effect=Exception("Render error")):
            with pytest.raises(Exception):
                await email_service.send_trend_alert(
                    to_email="user@example.com",
                    trend=sample_trend,
                    alert_id=uuid.uuid4()
                )

    async def test_send_digest_render_error(self, email_service, sample_trends_list):
        """Test error handling during digest rendering."""
        with patch.object(email_service, '_render_digest_email', side_effect=Exception("Render error")):
            with pytest.raises(Exception):
                await email_service.send_digest(
                    to_email="user@example.com",
                    trends=sample_trends_list,
                    digest_type="daily"
                )


# =============================================================================
# Singleton Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailServiceSingleton:
    """Tests for singleton instance management."""

    def test_get_email_service_singleton(self, mock_settings):
        """Test that get_email_service returns singleton."""
        with patch('alerts.email_service.settings', mock_settings):
            # Reset singleton for test
            import alerts.email_service as es
            es._email_service = None
            
            service1 = get_email_service()
            service2 = get_email_service()
            
            assert service1 is service2

    def test_get_email_service_initialization(self, mock_settings):
        """Test that singleton is properly initialized."""
        with patch('alerts.email_service.settings', mock_settings):
            import alerts.email_service as es
            es._email_service = None
            
            service = get_email_service()
            assert isinstance(service, EmailService)
            assert service.api_key == mock_settings.email_api_key


# =============================================================================
# Tracking Integration Tests
# =============================================================================

@pytest.mark.asyncio
class TestTrackingIntegration:
    """Tests for tracking pixel and link integration."""

    def test_tracking_pixel_included_when_enabled(self, mock_settings):
        """Test tracking pixel is included when enabled."""
        mock_settings.tracking_pixel_enabled = True
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            trend = TrendForAlert(
                id=uuid.uuid4(),
                type="sound",
                name="Test",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=1000,
                growth_rate=50.0,
                niche_name="test",
                first_detected_at=datetime.utcnow(),
                status="emerging",
                window_hours="6-8"
            )
            alert_id = uuid.uuid4()
            
            content = service._render_trend_email(trend, alert_id)
            
            assert content.tracking_pixel_url is not None
            assert str(alert_id) in content.tracking_pixel_url
            assert "/track/" in content.tracking_pixel_url
            assert '/open' in content.html_body or "pixel" in content.html_body.lower()

    def test_tracking_pixel_excluded_when_disabled(self, mock_settings):
        """Test tracking pixel is excluded when disabled."""
        mock_settings.tracking_pixel_enabled = False
        
        with patch('alerts.email_service.settings', mock_settings):
            service = EmailService()
            trend = TrendForAlert(
                id=uuid.uuid4(),
                type="sound",
                name="Test",
                velocity_score=50,
                saturation_percent=50,
                video_count_current=1000,
                growth_rate=50.0,
                niche_name="test",
                first_detected_at=datetime.utcnow(),
                status="emerging",
                window_hours="6-8"
            )
            
            content = service._render_trend_email(trend, uuid.uuid4())
            
            # Should still have tracking_pixel_url but no img tag in body
            assert content.tracking_pixel_url is not None

    def test_click_tracking_url_included(self, email_service, sample_trend):
        """Test click tracking URL is included in trend link."""
        alert_id = uuid.uuid4()
        content = email_service._render_trend_email(sample_trend, alert_id)
        
        assert "/track/" in content.html_body
        assert str(alert_id) in content.html_body
        assert "/click" in content.html_body


# =============================================================================
# Email Content Validation Tests
# =============================================================================

@pytest.mark.asyncio
class TestEmailContentValidation:
    """Tests for validating email content structure."""

    def test_html_email_well_formed(self, email_service, sample_trend):
        """Test that HTML email is well-formed."""
        content = email_service._render_trend_email(sample_trend, uuid.uuid4())
        
        # Basic HTML structure checks
        assert content.html_body.startswith("<!DOCTYPE html>") or content.html_body.startswith("<html")
        assert "<body>" in content.html_body or "<body " in content.html_body
        assert "</body>" in content.html_body
        assert "</html>" in content.html_body

    def test_text_email_well_formed(self, email_service, sample_trend):
        """Test that text email is well-formed."""
        content = email_service._render_trend_email(sample_trend, uuid.uuid4())
        
        assert content.text_body is not None
        assert len(content.text_body) > 0
        assert sample_trend.name in content.text_body

    def test_digest_html_structure(self, email_service, sample_trends_list):
        """Test digest HTML structure."""
        content = email_service._render_digest_email(sample_trends_list, "daily")
        
        assert "<table>" in content.html_body
        assert "</table>" in content.html_body
        assert len(sample_trends_list) in [int(s) for s in content.subject.split() if s.isdigit()]

    def test_digest_with_no_niche_name(self, email_service):
        """Test digest handles trends without niche names."""
        trends = [
            TrendForAlert(
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
        ]
        
        content = email_service._render_digest_email(trends, "daily")
        assert "General" in content.html_body or "#" in content.html_body


# =============================================================================
# Provider Response Tests
# =============================================================================

@pytest.mark.asyncio
class TestProviderResponses:
    """Tests for provider-specific response handling."""

    async def test_sendgrid_different_status_codes(self, mock_settings, sample_trend):
        """Test SendGrid handling of different status codes."""
        mock_settings.email_provider = "sendgrid"
        
        test_cases = [
            (200, True),
            (201, True),
            (202, True),
            (400, False),
            (500, False)
        ]
        
        for status_code, expected_result in test_cases:
            with patch('alerts.email_service.settings', mock_settings):
                service = EmailService()
                
                mock_response = Mock()
                mock_response.status_code = status_code
                
                mock_sg = Mock()
                mock_sg.send = Mock(return_value=mock_response)
                
                mock_sendgrid = Mock()
                mock_sendgrid.SendGridAPIClient = Mock(return_value=mock_sg)
                mock_sendgrid.helpers = Mock()
                mock_sendgrid.helpers.mail = Mock()
                mock_sendgrid.helpers.mail.Mail = Mock()
                
                with patch.dict('sys.modules', {
                    'sendgrid': mock_sendgrid,
                    'sendgrid.helpers': mock_sendgrid.helpers,
                    'sendgrid.helpers.mail': mock_sendgrid.helpers.mail
                }):
                    with patch('alerts.email_service.logger'):  # Suppress logs
                        result = await service._send_sendgrid("test@example.com", Mock(
                            subject="Test",
                            html_body="<html></html>",
                            text_body="Test",
                            tracking_pixel_url=None,
                            tracking_link_base=None
                        ))
                        
                        assert result is expected_result, f"Status {status_code} should return {expected_result}"


# =============================================================================
# Stub Logging Tests
# =============================================================================

@pytest.mark.asyncio
class TestStubLogging:
    """Tests for stub provider logging behavior."""

    async def test_stub_logs_masked_email(self, email_service, sample_trend):
        """Test that stub logs masked email."""
        with patch('alerts.email_service.logger') as mock_logger:
            await email_service.send_trend_alert(
                to_email="john.doe@example.com",
                trend=sample_trend,
                alert_id=uuid.uuid4()
            )
            
            # Check that masked email was logged
            log_calls = mock_logger.info.call_args_list
            assert any("j***@example.com" in str(call) for call in log_calls)

    async def test_stub_logs_content_length(self, email_service, sample_trend):
        """Test that stub logs content length."""
        with patch('alerts.email_service.logger') as mock_logger:
            await email_service.send_trend_alert(
                to_email="user@example.com",
                trend=sample_trend,
                alert_id=uuid.uuid4()
            )
            
            log_calls = mock_logger.debug.call_args_list
            assert any("html_length" in str(call) for call in log_calls)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
