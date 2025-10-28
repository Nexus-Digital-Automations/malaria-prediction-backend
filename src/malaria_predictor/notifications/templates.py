"""
Notification Template Engine for Dynamic Message Composition.

This module provides a flexible template system for creating dynamic push notifications
with context-based content generation, internationalization support, and rich media integration.
"""

import logging
from datetime import datetime
from typing import Any

from jinja2 import Environment, Template, TemplateError
from pydantic import BaseModel, Field, field_validator

from .models import NotificationPriority, NotificationTemplate

logger = logging.getLogger(__name__)


class TemplateContext(BaseModel):
    """
    Context data for template rendering.

    Provides structured data that can be used in notification templates
    for dynamic content generation.
    """

    # User information
    user_id: str | None = None
    user_name: str | None = None
    user_location: dict[str, Any] | None = None

    # Malaria-related data
    risk_score: float | None = Field(None, ge=0.0, le=1.0)
    risk_level: str | None = None  # "low", "medium", "high", "critical"
    location_name: str | None = None
    coordinates: dict[str, float] | None = None

    # Environmental data
    temperature: float | None = None
    humidity: float | None = None
    precipitation: float | None = None
    vegetation_index: float | None = None

    # Time-related context
    timestamp: datetime = Field(default_factory=datetime.now)
    forecast_date: datetime | None = None
    period: str | None = None  # "daily", "weekly", "monthly"

    # Alert-specific data
    alert_type: str | None = None
    severity: str | None = None
    outbreak_probability: float | None = Field(None, ge=0.0, le=1.0)

    # Custom data
    custom_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str | None) -> str | None:
        """Validate risk level values."""
        if v is not None and v not in ['low', 'medium', 'high', 'critical']:
            raise ValueError("Risk level must be one of: low, medium, high, critical")
        return v

    def to_template_vars(self) -> dict[str, Any]:
        """
        Convert context to template variables.

        Returns:
            Dictionary of variables for template rendering
        """
        data = self.model_dump()

        # Add formatted values for templates
        if self.risk_score is not None:
            data['risk_percentage'] = round(self.risk_score * 100, 1)
            data['risk_color'] = self._get_risk_color(self.risk_score)

        if self.timestamp:
            data['formatted_time'] = self.timestamp.strftime("%Y-%m-%d %H:%M")
            data['date'] = self.timestamp.strftime("%Y-%m-%d")
            data['time'] = self.timestamp.strftime("%H:%M")

        if self.forecast_date:
            data['forecast_formatted'] = self.forecast_date.strftime("%Y-%m-%d")

        return data

    def _get_risk_color(self, risk_score: float) -> str:
        """Get color code based on risk score."""
        if risk_score < 0.3:
            return "#4CAF50"  # Green
        elif risk_score < 0.6:
            return "#FF9800"  # Orange
        elif risk_score < 0.8:
            return "#FF5722"  # Red
        else:
            return "#9C27B0"  # Purple (critical)


class NotificationTemplateEngine:
    """
    Template engine for dynamic notification content generation.

    Provides comprehensive template management with Jinja2 templating,
    context-aware content generation, and multi-language support.
    """

    def __init__(self) -> None:
        """Initialize the template engine."""
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.jinja_env.filters['risk_emoji'] = self._risk_emoji_filter
        self.jinja_env.filters['format_percentage'] = self._percentage_filter
        self.jinja_env.filters['format_temperature'] = self._temperature_filter
        self.jinja_env.filters['capitalize_words'] = self._capitalize_words_filter

        logger.info("Notification template engine initialized")

    def render_template(
        self,
        template: NotificationTemplate,
        context: TemplateContext,
        language: str = "en",
    ) -> dict[str, str]:
        """
        Render a notification template with provided context.

        Args:
            template: Notification template to render
            context: Context data for template variables
            language: Language code for localization (future use)

        Returns:
            Dictionary with rendered title, body, and other content

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template_vars = context.to_template_vars()

            # Render title
            title_template = Template(template.title_template)
            rendered_title = title_template.render(**template_vars)

            # Render body
            body_template = Template(template.body_template)
            rendered_body = body_template.render(**template_vars)

            # Render deep link if present
            rendered_deep_link = None
            if template.deep_link:
                deep_link_template = Template(template.deep_link)
                rendered_deep_link = deep_link_template.render(**template_vars)

            logger.debug(f"Successfully rendered template '{template.name}' for context")

            return {
                "title": rendered_title.strip(),
                "body": rendered_body.strip(),
                "deep_link": rendered_deep_link,
                "image_url": template.image_url,
                "category": template.category,
                "priority": template.priority,
            }

        except TemplateError as e:
            error_msg = f"Template rendering failed for '{template.name}': {str(e)}"
            logger.error(error_msg)
            raise TemplateError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error rendering template '{template.name}': {str(e)}"
            logger.error(error_msg)
            raise TemplateError(error_msg) from e

    def create_malaria_alert_template(self) -> NotificationTemplate:
        """
        Create a standard malaria risk alert template.

        Returns:
            NotificationTemplate for malaria alerts
        """
        return NotificationTemplate(
            name="malaria_risk_alert",
            title_template="🦟 Malaria Risk Alert - {{ risk_level|capitalize }} Risk",
            body_template="""
            {%- if location_name -%}
            Malaria risk in {{ location_name }} has increased to {{ risk_percentage }}%.
            {%- else -%}
            Malaria risk in your area has increased to {{ risk_percentage }}%.
            {%- endif -%}
            {% if temperature and humidity %}
            Current conditions: {{ temperature }}°C, {{ humidity }}% humidity.
            {% endif %}
            Take preventive measures and consult healthcare if symptoms occur.
            """,
            category="alert",
            priority=NotificationPriority.HIGH,
            deep_link="/risk-map?lat={{ coordinates.lat }}&lng={{ coordinates.lng }}",
            image_url="https://example.com/malaria-alert.png",
            android_config={
                "notification_icon": "ic_malaria_alert",
                "notification_color": "#FF5722",
                "notification_channel_id": "malaria_alerts",
            },
            ios_config={
                "sound": "alert.wav",
                "badge": 1,
                "category": "MALARIA_ALERT",
            },
            web_config={
                "icon": "/icons/malaria-alert-192x192.png",
                "badge": "/icons/badge-72x72.png",
                "require_interaction": True,
            },
        )

    def create_outbreak_warning_template(self) -> NotificationTemplate:
        """
        Create a template for outbreak warnings.

        Returns:
            NotificationTemplate for outbreak warnings
        """
        return NotificationTemplate(
            name="outbreak_warning",
            title_template="🚨 Malaria Outbreak Warning",
            body_template="""
            URGENT: Potential malaria outbreak detected in {{ location_name }}.
            Outbreak probability: {{ outbreak_probability|format_percentage }}%.

            Seek immediate medical attention if you experience fever, chills, or flu-like symptoms.
            Avoid mosquito-prone areas and use protective measures.
            """,
            category="emergency",
            priority=NotificationPriority.CRITICAL,
            deep_link="/outbreak-details?location={{ location_name }}",
            android_config={
                "priority": "high",
                "notification_icon": "ic_emergency",
                "notification_color": "#D32F2F",
                "notification_channel_id": "emergency_alerts",
            },
            ios_config={
                "sound": "emergency.wav",
                "badge": 1,
                "content_available": True,
                "mutable_content": True,
            },
            web_config={
                "icon": "/icons/emergency-192x192.png",
                "require_interaction": True,
                "tag": "emergency_alert",
            },
        )

    def create_daily_summary_template(self) -> NotificationTemplate:
        """
        Create a template for daily risk summaries.

        Returns:
            NotificationTemplate for daily summaries
        """
        return NotificationTemplate(
            name="daily_risk_summary",
            title_template="📊 Daily Malaria Risk Update",
            body_template="""
            Today's malaria risk: {{ risk_level|capitalize }} ({{ risk_percentage }}%)

            Weather: {{ temperature }}°C, {{ humidity }}% humidity
            {% if precipitation > 0 -%}
            Recent rainfall may increase mosquito activity.
            {%- endif %}

            Stay protected and monitor symptoms.
            """,
            category="summary",
            priority=NotificationPriority.NORMAL,
            deep_link="/dashboard",
            android_config={
                "notification_channel_id": "daily_updates",
            },
            ios_config={
                "content_available": True,
            },
            web_config={
                "icon": "/icons/summary-192x192.png",
                "silent": False,
            },
        )

    def create_medication_reminder_template(self) -> NotificationTemplate:
        """
        Create a template for medication reminders.

        Returns:
            NotificationTemplate for medication reminders
        """
        return NotificationTemplate(
            name="medication_reminder",
            title_template="💊 Malaria Prevention Reminder",
            body_template="""
            Time for your antimalarial medication.

            {% if custom_data.medication_name -%}
            Medication: {{ custom_data.medication_name }}
            {%- endif %}
            {% if custom_data.dosage -%}
            Dosage: {{ custom_data.dosage }}
            {%- endif %}

            Consistent medication is key to malaria prevention.
            """,
            category="reminder",
            priority=NotificationPriority.NORMAL,
            deep_link="/medication-tracker",
            action_buttons=[
                {"action": "taken", "title": "Mark as Taken"},
                {"action": "snooze", "title": "Remind Later"},
            ],
            android_config={
                "notification_channel_id": "medication_reminders",
            },
            ios_config={
                "category": "MEDICATION_REMINDER",
            },
            web_config={
                "actions": [
                    {"action": "taken", "title": "✅ Taken"},
                    {"action": "snooze", "title": "⏰ Later"},
                ],
            },
        )

    def create_travel_alert_template(self) -> NotificationTemplate:
        """
        Create a template for travel-related malaria alerts.

        Returns:
            NotificationTemplate for travel alerts
        """
        return NotificationTemplate(
            name="travel_alert",
            title_template="✈️ Travel Malaria Advisory",
            body_template="""
            {% if custom_data.destination -%}
            Malaria risk advisory for {{ custom_data.destination }}:
            {%- else -%}
            Malaria risk advisory for your travel destination:
            {%- endif %}

            Risk Level: {{ risk_level|capitalize }} ({{ risk_percentage }}%)

            {% if risk_score > 0.5 -%}
            Consider antimalarial prophylaxis and protective measures.
            {%- else -%}
            Use mosquito repellent and protective clothing.
            {%- endif %}
            """,
            category="travel",
            priority=NotificationPriority.HIGH,
            deep_link="/travel-health",
            android_config={
                "notification_channel_id": "travel_alerts",
            },
            ios_config={
                "category": "TRAVEL_ALERT",
            },
            web_config={
                "icon": "/icons/travel-192x192.png",
            },
        )

    def get_built_in_templates(self) -> list[NotificationTemplate]:
        """
        Get all built-in notification templates.

        Returns:
            List of built-in notification templates
        """
        return [
            self.create_malaria_alert_template(),
            self.create_outbreak_warning_template(),
            self.create_daily_summary_template(),
            self.create_medication_reminder_template(),
            self.create_travel_alert_template(),
        ]

    def _risk_emoji_filter(self, risk_level: str) -> str:
        """Jinja2 filter to get emoji for risk level."""
        emoji_map = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }
        return emoji_map.get(risk_level.lower(), "⚪")

    def _percentage_filter(self, value: float | None) -> str:
        """Jinja2 filter to format as percentage."""
        if value is None:
            return "N/A"
        return f"{round(value * 100, 1)}%"

    def _temperature_filter(self, value: float | None) -> str:
        """Jinja2 filter to format temperature."""
        if value is None:
            return "N/A"
        return f"{round(value, 1)}°C"

    def _capitalize_words_filter(self, value: str) -> str:
        """Jinja2 filter to capitalize each word."""
        return value.title() if value else ""


class MessageComposer:
    """
    High-level message composition service.

    Combines template rendering with FCM message data preparation
    for streamlined notification creation.
    """

    def __init__(self, template_engine: NotificationTemplateEngine) -> None:
        """
        Initialize message composer.

        Args:
            template_engine: Template engine instance
        """
        self.template_engine = template_engine
        logger.info("Message composer initialized")

    def compose_malaria_alert(
        self,
        risk_score: float,
        location_name: str | None = None,
        coordinates: dict[str, float] | None = None,
        environmental_data: dict[str, float] | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Compose a malaria risk alert notification.

        Args:
            risk_score: Risk score (0.0 to 1.0)
            location_name: Human-readable location name
            coordinates: Location coordinates
            environmental_data: Environmental conditions
            user_id: Target user ID

        Returns:
            Composed notification data
        """
        # Determine risk level
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        elif risk_score < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Create context
        context = TemplateContext(
            user_id=user_id,
            risk_score=risk_score,
            risk_level=risk_level,
            location_name=location_name,
            coordinates=coordinates,
            **(environmental_data or {}),
        )

        # Get template and render
        template = self.template_engine.create_malaria_alert_template()
        return self.template_engine.render_template(template, context)

    def compose_outbreak_warning(
        self,
        location_name: str,
        outbreak_probability: float,
        additional_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Compose an outbreak warning notification.

        Args:
            location_name: Location where outbreak is detected
            outbreak_probability: Probability of outbreak (0.0 to 1.0)
            additional_context: Additional context data

        Returns:
            Composed notification data
        """
        context = TemplateContext(
            location_name=location_name,
            outbreak_probability=outbreak_probability,
            alert_type="outbreak",
            severity="critical",
            custom_data=additional_context or {},
        )

        template = self.template_engine.create_outbreak_warning_template()
        return self.template_engine.render_template(template, context)

    def compose_medication_reminder(
        self,
        user_id: str,
        medication_name: str | None = None,
        dosage: str | None = None,
    ) -> dict[str, Any]:
        """
        Compose a medication reminder notification.

        Args:
            user_id: Target user ID
            medication_name: Name of medication
            dosage: Dosage information

        Returns:
            Composed notification data
        """
        context = TemplateContext(
            user_id=user_id,
            custom_data={
                "medication_name": medication_name,
                "dosage": dosage,
            },
        )

        template = self.template_engine.create_medication_reminder_template()
        return self.template_engine.render_template(template, context)
