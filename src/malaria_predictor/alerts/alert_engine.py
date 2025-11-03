"""Alert engine for malaria prediction system.

Core alert processing engine that evaluates risk conditions,
generates alerts, and manages alert lifecycle.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Union, cast

from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.models import (
    Alert,
    AlertConfiguration,
    AlertRule,
    AlertTemplate,
    MalariaRiskIndex,
)
from ..database.session import get_session
from .firebase_service import firebase_service
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class RiskCondition(BaseModel):
    """Risk condition for alert evaluation."""

    field: str  # risk_score, temperature, precipitation, etc.
    operator: str  # gt, gte, lt, lte, eq, ne, in, between
    value: float | int | str | list
    weight: float = 1.0


class AlertCondition(BaseModel):
    """Complex alert condition with multiple criteria."""

    logic: str = "and"  # and, or, not
    conditions: list[Union[RiskCondition, "AlertCondition"]]
    min_matches: int | None = None  # For "or" logic, minimum conditions that must match


class AlertGenerationRequest(BaseModel):
    """Request to generate alerts for risk assessment."""
    model_config = ConfigDict(from_attributes=True)

    risk_index_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    risk_score: float | None = None
    location_name: str | None = None
    country_code: str | None = None
    admin_region: str | None = None
    environmental_data: dict | None = None
    force_evaluation: bool = False


class AlertEvaluationResult(BaseModel):
    """Result of alert rule evaluation."""
    model_config = ConfigDict(from_attributes=True)

    rule_id: int
    triggered: bool
    risk_score: float
    confidence_score: float
    conditions_met: list[str]
    evaluation_time_ms: int
    alert_level: str
    alert_priority: str
    suppressed: bool = False
    suppression_reason: str | None = None


class AlertEngine:
    """Core alert processing engine.

    Provides functionality for:
    - Alert rule evaluation
    - Risk threshold monitoring
    - Alert generation and lifecycle management
    - Template-based message generation
    - Performance monitoring and optimization
    """

    def __init__(self) -> None:
        """Initialize the alert engine."""
        self.settings = settings
        self.stats: dict[str, int | float | datetime | None] = {
            "evaluations_performed": 0,
            "alerts_generated": 0,
            "alerts_suppressed": 0,
            "rules_triggered": 0,
            "avg_evaluation_time_ms": 0.0,
            "last_evaluation": None
        }

        # Alert suppression tracking
        self.suppression_cache: dict[str, Any] = {}  # rule_id -> last_triggered_timestamp

        # Template cache for performance
        self.template_cache: dict[str, Any] = {}

    async def evaluate_risk_for_alerts(
        self,
        request: AlertGenerationRequest
    ) -> list[AlertEvaluationResult]:
        """Evaluate risk conditions and generate alerts if thresholds met.

        Args:
            request: Alert generation request

        Returns:
            List of alert evaluation results
        """
        start_time = datetime.now()

        try:
            async with get_session() as db:
                # Get active alert configurations and rules
                active_rules = await self._get_active_alert_rules(db, request)

                if not active_rules:
                    logger.debug("No active alert rules found for evaluation")
                    return []

                # Evaluate each rule
                evaluation_results = []

                for rule in active_rules:
                    result = await self._evaluate_alert_rule(db, rule, request)
                    evaluation_results.append(result)

                    # Generate alert if rule triggered and not suppressed
                    if result.triggered and not result.suppressed:
                        await self._generate_alert(db, rule, request, result)

                # Update statistics
                evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
                self.stats["evaluations_performed"] = cast(int, self.stats["evaluations_performed"]) + 1

                # Calculate running average
                evaluations_performed = cast(int, self.stats["evaluations_performed"])
                avg_time = cast(float, self.stats["avg_evaluation_time_ms"])
                self.stats["avg_evaluation_time_ms"] = (
                    (avg_time * (evaluations_performed - 1) + evaluation_time) / evaluations_performed
                )
                self.stats["last_evaluation"] = datetime.now()

                logger.info(
                    f"Alert evaluation completed: {len(evaluation_results)} rules evaluated, "
                    f"{sum(1 for r in evaluation_results if r.triggered)} triggered, "
                    f"evaluation_time={evaluation_time:.2f}ms"
                )

                return evaluation_results

        except Exception as e:
            logger.error(f"Alert evaluation failed: {e}")
            return []

        finally:
            db.close()

    async def process_risk_index(self, risk_index: MalariaRiskIndex) -> list[Alert]:
        """Process a risk index and generate alerts if needed.

        Args:
            risk_index: Risk index to process

        Returns:
            List of generated alerts
        """
        request = AlertGenerationRequest.model_validate({
            'risk_index_id': risk_index.id,
            'latitude': risk_index.latitude,
            'longitude': risk_index.longitude,
            'risk_score': risk_index.composite_risk_score,
            'location_name': risk_index.location_name,
            'environmental_data': {
                "temperature_risk": risk_index.temperature_risk_component,
                "precipitation_risk": risk_index.precipitation_risk_component,
                "humidity_risk": risk_index.humidity_risk_component,
                "vegetation_risk": risk_index.vegetation_risk_component,
                "confidence": risk_index.confidence_score,
                "risk_level": risk_index.risk_level
            }
        })

        evaluation_results = await self.evaluate_risk_for_alerts(request)

        # Return generated alerts
        async with get_session() as db:
            alerts = []
            for result in evaluation_results:
                if result.triggered and not result.suppressed:
                    alert_query = await db.execute(
                        select(Alert).filter(
                            Alert.alert_rule_id == result.rule_id,
                            Alert.created_at >= datetime.now() - timedelta(minutes=5)
                        )
                    )
                    alert = alert_query.scalar_one_or_none()
                    if alert:
                        alerts.append(alert)
            return alerts

    async def create_alert_configuration(
        self,
        user_id: str,
        config_data: dict
    ) -> AlertConfiguration | None:
        """Create a new alert configuration.

        Args:
            user_id: User ID creating the configuration
            config_data: Configuration parameters

        Returns:
            Created alert configuration or None if failed
        """
        async with get_session() as db:
            try:
                config = AlertConfiguration(
                    user_id=user_id,
                    configuration_name=config_data.get("name", "Default Configuration"),
                    low_risk_threshold=config_data.get("low_risk_threshold", 0.3),
                    medium_risk_threshold=config_data.get("medium_risk_threshold", 0.6),
                    high_risk_threshold=config_data.get("high_risk_threshold", 0.8),
                    critical_risk_threshold=config_data.get("critical_risk_threshold", 0.9),
                    latitude_min=config_data.get("latitude_min"),
                    latitude_max=config_data.get("latitude_max"),
                    longitude_min=config_data.get("longitude_min"),
                    longitude_max=config_data.get("longitude_max"),
                    country_codes=config_data.get("country_codes"),
                    admin_regions=config_data.get("admin_regions"),
                    alert_frequency_hours=config_data.get("alert_frequency_hours", 24),
                    time_horizon_days=config_data.get("time_horizon_days", 7),
                    active_hours_start=config_data.get("active_hours_start"),
                    active_hours_end=config_data.get("active_hours_end"),
                    timezone=config_data.get("timezone", "UTC"),
                    enable_push_notifications=config_data.get("enable_push_notifications", True),
                    enable_email_notifications=config_data.get("enable_email_notifications", True),
                    enable_sms_notifications=config_data.get("enable_sms_notifications", False),
                    enable_webhook_notifications=config_data.get("enable_webhook_notifications", False),
                    email_addresses=config_data.get("email_addresses"),
                    phone_numbers=config_data.get("phone_numbers"),
                    webhook_urls=config_data.get("webhook_urls"),
                    enable_emergency_escalation=config_data.get("enable_emergency_escalation", False),
                    emergency_contact_emails=config_data.get("emergency_contact_emails"),
                    emergency_contact_phones=config_data.get("emergency_contact_phones"),
                    emergency_escalation_threshold=config_data.get("emergency_escalation_threshold", 0.95),
                    is_active=config_data.get("is_active", True),
                    is_default=config_data.get("is_default", False)
                )

                db.add(config)
                await db.flush()  # To get the ID
                await db.refresh(config)

                logger.info(f"Created alert configuration {config.id} for user {user_id}")
                return config

            except Exception as e:
                logger.error(f"Failed to create alert configuration: {e}")
                raise

    async def create_alert_rule(
        self,
        configuration_id: int,
        rule_data: dict
    ) -> AlertRule | None:
        """Create a new alert rule.

        Args:
            configuration_id: Parent configuration ID
            rule_data: Rule parameters

        Returns:
            Created alert rule or None if failed
        """
        async with get_session() as db:
            try:
                rule = AlertRule(
                    configuration_id=configuration_id,
                    rule_name=rule_data.get("name", "Custom Rule"),
                    rule_description=rule_data.get("description"),
                    conditions=rule_data.get("conditions", {}),
                    rule_type=rule_data.get("type", "threshold"),
                    rule_version=rule_data.get("version", "1.0"),
                    evaluation_frequency_minutes=rule_data.get("evaluation_frequency_minutes", 60),
                    min_data_points_required=rule_data.get("min_data_points_required", 1),
                    lookback_period_hours=rule_data.get("lookback_period_hours", 24),
                    cooldown_period_hours=rule_data.get("cooldown_period_hours", 24),
                    max_alerts_per_day=rule_data.get("max_alerts_per_day", 5),
                    alert_priority=rule_data.get("priority", "medium"),
                    alert_category=rule_data.get("category", "outbreak_risk"),
                    is_active=rule_data.get("is_active", True),
                    created_by=rule_data.get("created_by")
                )

                db.add(rule)
                await db.flush()  # To get the ID
                await db.refresh(rule)

                logger.info(f"Created alert rule {rule.id} for configuration {configuration_id}")
                return rule

            except Exception as e:
                logger.error(f"Failed to create alert rule: {e}")
                raise

    async def _get_active_alert_rules(
        self,
        db: AsyncSession,
        request: AlertGenerationRequest
    ) -> list[AlertRule]:
        """Get active alert rules that apply to the request.

        Args:
            db: Database session
            request: Alert generation request

        Returns:
            List of applicable alert rules
        """
        # Base query for active rules
        query = db.query(AlertRule).join(AlertConfiguration).filter(
            AlertRule.is_active,
            AlertConfiguration.is_active
        )

        # Filter by geographic bounds if specified
        if request.latitude and request.longitude:
            query = query.filter(
                or_(
                    AlertConfiguration.latitude_min.is_(None),
                    AlertConfiguration.latitude_min <= request.latitude
                ),
                or_(
                    AlertConfiguration.latitude_max.is_(None),
                    AlertConfiguration.latitude_max >= request.latitude
                ),
                or_(
                    AlertConfiguration.longitude_min.is_(None),
                    AlertConfiguration.longitude_min <= request.longitude
                ),
                or_(
                    AlertConfiguration.longitude_max.is_(None),
                    AlertConfiguration.longitude_max >= request.longitude
                )
            )

        # Filter by country/region if specified
        if request.country_code:
            query = query.filter(
                or_(
                    AlertConfiguration.country_codes.is_(None),
                    AlertConfiguration.country_codes.contains([request.country_code])
                )
            )

        return query.all() # type: ignore[no-any-return]

    async def _evaluate_alert_rule(
        self,
        db: AsyncSession,
        rule: AlertRule,
        request: AlertGenerationRequest
    ) -> AlertEvaluationResult:
        """Evaluate a single alert rule against request data.

        Args:
            db: Database session
            rule: Alert rule to evaluate
            request: Alert generation request

        Returns:
            Alert evaluation result
        """
        start_time = datetime.now()

        try:
            # Parse rule conditions
            conditions = AlertCondition(**rule.conditions)

            # Evaluate conditions
            triggered, conditions_met, confidence = await self._evaluate_conditions(
                conditions, request
            )

            # Determine alert level based on risk score and rule configuration
            alert_level = self._determine_alert_level(request.risk_score or 0.0, rule)

            # Check for suppression
            suppressed, suppression_reason = await self._check_suppression(db, rule, request)

            # Update rule statistics
            rule.evaluation_count += 1
            rule.last_evaluation = datetime.now()

            if triggered:
                rule.triggered_count += 1
                self.stats["rules_triggered"] = cast(int, self.stats["rules_triggered"]) + 1

            await db.commit()

            evaluation_time = (datetime.now() - start_time).total_seconds() * 1000

            return AlertEvaluationResult.model_validate({
                'rule_id': rule.id,
                'triggered': triggered,
                'risk_score': request.risk_score or 0.0,
                'confidence_score': confidence,
                'conditions_met': conditions_met,
                'evaluation_time_ms': int(evaluation_time),
                'alert_level': alert_level,
                'alert_priority': rule.alert_priority,
                'suppressed': suppressed,
                'suppression_reason': suppression_reason
            })

        except Exception as e:
            logger.error(f"Failed to evaluate alert rule {rule.id}: {e}")

            return AlertEvaluationResult.model_validate({
                'rule_id': rule.id,
                'triggered': False,
                'risk_score': request.risk_score or 0.0,
                'confidence_score': 0.0,
                'conditions_met': [],
                'evaluation_time_ms': 0,
                'alert_level': "low",
                'alert_priority': rule.alert_priority,
                'suppressed': True,
                'suppression_reason': "evaluation_error"
            })

    async def _evaluate_conditions(
        self,
        conditions: AlertCondition,
        request: AlertGenerationRequest
    ) -> tuple[bool, list[str], float]:
        """Evaluate alert conditions against request data.

        Args:
            conditions: Alert conditions to evaluate
            request: Alert generation request

        Returns:
            Tuple of (triggered, conditions_met, confidence_score)
        """
        conditions_met = []
        total_weight = 0.0
        met_weight = 0.0

        for condition in conditions.conditions:
            if isinstance(condition, RiskCondition):
                # Evaluate risk condition
                field_value = self._get_field_value(condition.field, request)
                condition_met = self._evaluate_operator(
                    field_value, condition.operator, condition.value
                )

                total_weight += condition.weight
                if condition_met:
                    met_weight += condition.weight
                    conditions_met.append(f"{condition.field} {condition.operator} {condition.value}")

            elif isinstance(condition, AlertCondition):
                # Recursive evaluation for nested conditions
                nested_triggered, nested_met, _ = await self._evaluate_conditions(condition, request)

                total_weight += 1.0
                if nested_triggered:
                    met_weight += 1.0
                    conditions_met.extend(nested_met)

        # Determine if conditions are met based on logic
        if conditions.logic == "and":
            triggered = met_weight == total_weight
        elif conditions.logic == "or":
            min_matches = conditions.min_matches or 1
            triggered = len(conditions_met) >= min_matches
        else:  # "not"
            triggered = met_weight == 0

        confidence = met_weight / max(total_weight, 1.0)

        return triggered, conditions_met, confidence

    def _get_field_value(self, field: str, request: AlertGenerationRequest) -> float | str | None:
        """Get field value from request data.

        Args:
            field: Field name to extract
            request: Alert generation request

        Returns:
            Field value or None if not found
        """
        # Direct request fields
        if hasattr(request, field):
            return getattr(request, field) # type: ignore[no-any-return]

        # Environmental data fields
        if request.environmental_data and field in request.environmental_data:
            return request.environmental_data[field] # type: ignore[no-any-return]

        return None

    def _evaluate_operator(
        self,
        field_value: float | str | None,
        operator: str,
        condition_value: float | int | str | list
    ) -> bool:
        """Evaluate operator condition.

        Args:
            field_value: Actual field value
            operator: Comparison operator
            condition_value: Expected value

        Returns:
            True if condition met, False otherwise
        """
        if field_value is None:
            return False

        try:
            if operator == "gt":
                if isinstance(condition_value, list):
                    return False
                return float(field_value) > float(condition_value)
            elif operator == "gte":
                if isinstance(condition_value, list):
                    return False
                return float(field_value) >= float(condition_value)
            elif operator == "lt":
                if isinstance(condition_value, list):
                    return False
                return float(field_value) < float(condition_value)
            elif operator == "lte":
                if isinstance(condition_value, list):
                    return False
                return float(field_value) <= float(condition_value)
            elif operator == "eq":
                return field_value == condition_value
            elif operator == "ne":
                return field_value != condition_value
            elif operator == "in":
                return field_value in condition_value # type: ignore[operator]
            elif operator == "between":
                if isinstance(condition_value, list) and len(condition_value) == 2:
                    return condition_value[0] <= float(field_value) <= condition_value[1] # type: ignore[no-any-return]

            return False

        except (TypeError, ValueError):
            return False

    def _determine_alert_level(self, risk_score: float, rule: AlertRule) -> str:
        """Determine alert level based on risk score and rule configuration.

        Args:
            risk_score: Current risk score
            rule: Alert rule

        Returns:
            Alert level string
        """
        config = rule.configuration

        if risk_score >= config.critical_risk_threshold:
            return "critical"
        elif risk_score >= config.high_risk_threshold:
            return "high"
        elif risk_score >= config.medium_risk_threshold:
            return "medium"
        elif risk_score >= config.low_risk_threshold:
            return "low"
        else:
            return "info"

    async def _check_suppression(
        self,
        db: AsyncSession,
        rule: AlertRule,
        request: AlertGenerationRequest
    ) -> tuple[bool, str | None]:
        """Check if alert should be suppressed.

        Args:
            db: Database session
            rule: Alert rule
            request: Alert generation request

        Returns:
            Tuple of (suppressed, suppression_reason)
        """
        now = datetime.now()

        # Check cooldown period
        if rule.id in self.suppression_cache:
            last_triggered = self.suppression_cache[rule.id]
            cooldown_end = last_triggered + timedelta(hours=int(rule.cooldown_period_hours))

            if now < cooldown_end:
                return True, "cooldown_period"

        # Check daily alert limit (SQLAlchemy 2.0 async)
        from sqlalchemy import func
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_alerts = await db.scalar(
            select(func.count()).select_from(Alert).where(
                Alert.alert_rule_id == rule.id,
                Alert.created_at >= today_start
            )
        ) or 0

        if today_alerts >= rule.max_alerts_per_day:
            return True, "daily_limit_exceeded"

        # Check active hours
        config = rule.configuration
        if config.active_hours_start is not None and config.active_hours_end is not None:
            current_hour = now.hour

            if config.active_hours_start <= config.active_hours_end:
                # Normal range (e.g., 9-17)
                if not (config.active_hours_start <= current_hour <= config.active_hours_end):
                    return True, "outside_active_hours"
            else:
                # Overnight range (e.g., 22-6)
                if not (current_hour >= config.active_hours_start or current_hour <= config.active_hours_end):
                    return True, "outside_active_hours"

        return False, None

    async def _generate_alert(
        self,
        db: AsyncSession,
        rule: AlertRule,
        request: AlertGenerationRequest,
        result: AlertEvaluationResult
    ) -> Alert | None:
        """Generate and store an alert.

        Args:
            db: Database session
            rule: Triggered alert rule
            request: Alert generation request
            result: Evaluation result

        Returns:
            Generated alert or None if failed
        """
        try:
            # Generate alert message using templates
            alert_title, alert_message = await self._generate_alert_message(
                db, rule, request, result
            )

            # Create alert record
            alert = Alert(
                alert_rule_id=rule.id,
                configuration_id=rule.configuration_id,
                alert_type=rule.alert_category,
                alert_level=result.alert_level,
                alert_title=alert_title,
                alert_message=alert_message,
                latitude=request.latitude,
                longitude=request.longitude,
                location_name=request.location_name,
                country_code=request.country_code,
                admin_region=request.admin_region,
                risk_score=result.risk_score,
                confidence_score=result.confidence_score,
                alert_data={
                    "conditions_met": result.conditions_met,
                    "rule_id": rule.id,
                    "evaluation_time_ms": result.evaluation_time_ms
                },
                environmental_data=request.environmental_data,
                priority=result.alert_priority,
                is_emergency=result.alert_level == "critical" and result.risk_score >= 0.95
            )

            db.add(alert)
            await db.commit()
            await db.refresh(alert)

            # Update suppression cache
            self.suppression_cache[str(rule.id)] = datetime.now()

            # Update statistics
            self.stats["alerts_generated"] = cast(int, self.stats["alerts_generated"]) + 1

            # Send real-time notifications
            await self._send_alert_notifications(alert)

            logger.info(f"Generated alert {alert.id} for rule {rule.id}")
            return alert

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to generate alert for rule {rule.id}: {e}")
            return None

    async def _generate_alert_message(
        self,
        db: AsyncSession,
        rule: AlertRule,
        request: AlertGenerationRequest,
        result: AlertEvaluationResult
    ) -> tuple[str, str]:
        """Generate alert title and message from templates.

        Args:
            db: Database session
            rule: Alert rule
            request: Alert generation request
            result: Evaluation result

        Returns:
            Tuple of (title, message)
        """
        # Get appropriate template (SQLAlchemy 2.0 async)
        template_result = await db.execute(
            select(AlertTemplate).where(
                AlertTemplate.template_type == rule.alert_category,
                AlertTemplate.channel == "general",
                AlertTemplate.is_active
            )
        )
        template = template_result.scalar_one_or_none()

        if not template:
            # Fallback to default message
            return self._generate_default_message(request, result)

        # Template variables
        variables = {
            "risk_score": f"{result.risk_score:.1%}" if result.risk_score else "Unknown",
            "risk_level": result.alert_level.title(),
            "location": request.location_name or request.admin_region or "Unknown Location",
            "country": request.country_code or "",
            "confidence": f"{result.confidence_score:.1%}" if result.confidence_score else "Unknown",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "conditions": ", ".join(result.conditions_met[:3])  # Limit to first 3 conditions
        }

        # Apply template substitution
        title = template.subject_template or "Malaria Risk Alert"
        message = template.message_template

        for var, value in variables.items():
            title = title.replace(f"{{{var}}}", str(value))
            message = message.replace(f"{{{var}}}", str(value))

        return title, message

    def _generate_default_message(
        self,
        request: AlertGenerationRequest,
        result: AlertEvaluationResult
    ) -> tuple[str, str]:
        """Generate default alert message when no template available.

        Args:
            request: Alert generation request
            result: Evaluation result

        Returns:
            Tuple of (title, message)
        """
        location = request.location_name or request.admin_region or "your area"
        risk_level = result.alert_level.title()

        title = f"{risk_level} Malaria Risk Alert - {location}"

        message = (
            f"A {risk_level.lower()} malaria risk has been detected in {location}. "
            f"Risk score: {result.risk_score:.1%}. "
            f"Confidence: {result.confidence_score:.1%}. "
            f"Please take appropriate preventive measures."
        )

        return title, message

    async def _send_alert_notifications(self, alert: Alert) -> None:
        """Send notifications for generated alert.

        Args:
            alert: Alert to send notifications for
        """
        try:
            # Send WebSocket notification
            await websocket_manager.broadcast_alert(alert)

            # Send push notifications
            await firebase_service.send_alert_notification(alert)

            logger.info(f"Sent notifications for alert {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send notifications for alert {alert.id}: {e}")

    def get_stats(self) -> dict:
        """Get alert engine statistics.

        Returns:
            Dictionary with current statistics
        """
        return self.stats.copy()


# Global alert engine instance
alert_engine = AlertEngine()
