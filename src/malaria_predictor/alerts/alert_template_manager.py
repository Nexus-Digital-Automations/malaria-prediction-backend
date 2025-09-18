"""Customizable alert template management system.

Provides comprehensive template management for alert messages including:
- Dynamic template creation and editing
- Multi-language support and localization
- Template versioning and rollback
- Variable substitution and validation
- Template testing and preview
- User-specific template customization
- Template analytics and optimization
"""

import json
import logging
import re
from datetime import datetime

from pydantic import BaseModel, Field, validator

from ..config import settings
from ..database.models import AlertTemplate
from ..database.session import get_session

logger = logging.getLogger(__name__)


class TemplateVariable(BaseModel):
    """Template variable definition."""

    name: str
    type: str  # string, number, boolean, date, location, risk_score
    description: str
    required: bool = True
    default_value: str | None = None
    validation_pattern: str | None = None  # Regex pattern for validation
    format_options: dict[str, any] | None = None  # Formatting options (e.g., decimal places)


class TemplateFormat(BaseModel):
    """Template formatting options."""

    # Text formatting
    max_title_length: int = 100
    max_body_length: int = 500
    line_breaks_enabled: bool = True
    html_enabled: bool = False
    markdown_enabled: bool = False

    # Variable formatting
    variable_prefix: str = "{{"
    variable_suffix: str = "}}"
    escape_html: bool = True

    # Conditional logic
    if_statements_enabled: bool = True
    loop_statements_enabled: bool = False

    # Rich content
    images_enabled: bool = True
    links_enabled: bool = True
    attachments_enabled: bool = False


class TemplateTranslation(BaseModel):
    """Template translation for different languages."""

    language_code: str  # ISO 639-1 code (en, es, fr, etc.)
    language_name: str
    title_template: str
    body_template: str
    variables_translation: dict[str, str] = {}  # Variable name -> translated description
    formatting_locale: str | None = None  # For number/date formatting


class AlertTemplateDefinition(BaseModel):
    """Complete alert template definition."""

    template_id: str
    name: str
    description: str
    category: str  # malaria_alert, system_notification, emergency, etc.

    # Template content
    title_template: str
    body_template: str
    summary_template: str | None = None

    # Variables and validation
    variables: list[TemplateVariable]
    required_variables: list[str]
    optional_variables: list[str] = []

    # Formatting and display
    format_options: TemplateFormat = Field(default_factory=TemplateFormat)

    # Localization
    default_language: str = "en"
    translations: list[TemplateTranslation] = []

    # Usage and targeting
    allowed_alert_levels: list[str] = ["low", "medium", "high", "critical", "emergency"]
    target_channels: list[str] = ["push", "email", "sms", "webhook"]
    user_customizable: bool = True

    # Template metadata
    version: str = "1.0"
    created_by: str | None = None
    is_active: bool = True
    is_system_template: bool = False  # System templates cannot be deleted

    # Analytics and optimization
    usage_count: int = 0
    effectiveness_score: float = 0.0  # Based on user engagement
    last_used: datetime | None = None

    # Validation settings
    require_preview: bool = True
    allow_empty_variables: bool = False

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('template_id')
    def validate_template_id(cls, v):
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError('Template ID must contain only lowercase letters, numbers, and underscores')
        return v


class TemplateValidationResult(BaseModel):
    """Result of template validation."""

    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    variable_analysis: dict[str, any] = {}
    estimated_length: dict[str, int] = {}  # Channel -> estimated message length


class TemplatePreview(BaseModel):
    """Template preview with sample data."""

    template_id: str
    language: str
    channel: str  # push, email, sms, webhook

    # Rendered content
    rendered_title: str
    rendered_body: str
    rendered_summary: str | None = None

    # Metadata
    estimated_length: int
    fits_channel_limits: bool
    variable_values_used: dict[str, str]

    # Rendering info
    rendering_time_ms: float
    warnings: list[str] = []


class UserTemplateCustomization(BaseModel):
    """User-specific template customizations."""

    user_id: str
    template_id: str

    # Customizations
    custom_title: str | None = None
    custom_body: str | None = None
    custom_variables: dict[str, str] = {}  # Variable overrides

    # Preferences
    preferred_language: str = "en"
    enabled_channels: list[str] = ["push", "email"]
    notification_frequency: str = "normal"  # low, normal, high

    # Personalization
    location_based_content: bool = True
    time_based_formatting: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AlertTemplateManager:
    """Manages customizable alert templates and user customizations.

    Provides functionality for:
    - Template creation, editing, and versioning
    - Multi-language support and localization
    - Template validation and testing
    - User-specific customizations
    - Template analytics and optimization
    - Dynamic variable substitution
    """

    def __init__(self):
        """Initialize the alert template manager."""
        self.settings = settings

        # Template storage
        self.templates: dict[str, AlertTemplateDefinition] = {}
        self.user_customizations: dict[str, dict[str, UserTemplateCustomization]] = {}

        # Template validation and rendering
        self.variable_pattern = re.compile(r'\{\{(\w+)(?:\|([^}]+))?\}\}')  # {{variable|format}}
        self.conditional_pattern = re.compile(r'\{\%\s*(if|endif|else)\s+([^%]*)\s*\%\}')

        # Channel limits
        self.channel_limits = {
            "push": {"title": 65, "body": 240},
            "sms": {"total": 160},
            "email": {"title": 78, "body": 10000},
            "webhook": {"title": 200, "body": 2000}
        }

        # Statistics
        self.stats = {
            "templates_created": 0,
            "templates_rendered": 0,
            "customizations_applied": 0,
            "validations_performed": 0,
            "translations_added": 0,
            "avg_render_time_ms": 0.0,
            "most_used_templates": {},
            "template_effectiveness": {}
        }

    async def create_template(
        self,
        template_def: AlertTemplateDefinition,
        user_id: str | None = None
    ) -> bool:
        """Create a new alert template.

        Args:
            template_def: Template definition
            user_id: User creating the template

        Returns:
            True if template created successfully
        """
        try:
            # Validate template
            validation_result = await self.validate_template(template_def)
            if not validation_result.is_valid:
                logger.error(f"Template validation failed: {validation_result.errors}")
                return False

            # Set metadata
            template_def.created_by = user_id
            template_def.created_at = datetime.now()
            template_def.updated_at = datetime.now()

            # Store template
            self.templates[template_def.template_id] = template_def

            # Save to database
            await self._save_template_to_db(template_def)

            self.stats["templates_created"] += 1
            logger.info(f"Created template: {template_def.template_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False

    async def update_template(
        self,
        template_id: str,
        updates: dict[str, any],
        user_id: str | None = None
    ) -> bool:
        """Update an existing template.

        Args:
            template_id: Template identifier
            updates: Fields to update
            user_id: User making the update

        Returns:
            True if template updated successfully
        """
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return False

            # Check permissions
            if template.is_system_template and user_id != template.created_by:
                logger.error("Cannot modify system template")
                return False

            # Create new version
            old_version = template.version
            new_version = self._increment_version(old_version)

            # Apply updates
            updated_template = template.copy(update=updates)
            updated_template.version = new_version
            updated_template.updated_at = datetime.now()

            # Validate updated template
            validation_result = await self.validate_template(updated_template)
            if not validation_result.is_valid:
                logger.error(f"Updated template validation failed: {validation_result.errors}")
                return False

            # Store updated template
            self.templates[template_id] = updated_template

            # Save to database
            await self._save_template_to_db(updated_template)

            logger.info(f"Updated template {template_id} from v{old_version} to v{new_version}")
            return True

        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False

    async def validate_template(
        self,
        template: AlertTemplateDefinition
    ) -> TemplateValidationResult:
        """Validate a template definition.

        Args:
            template: Template to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        variable_analysis = {}

        try:
            # Basic validation
            if not template.title_template or not template.body_template:
                errors.append("Title and body templates are required")

            # Variable validation
            title_vars = self._extract_variables(template.title_template)
            body_vars = self._extract_variables(template.body_template)
            all_template_vars = set(title_vars + body_vars)

            # Check required variables
            defined_vars = {var.name for var in template.variables}
            required_vars = set(template.required_variables)

            missing_required = required_vars - defined_vars
            if missing_required:
                errors.append(f"Missing required variable definitions: {missing_required}")

            unused_defined = defined_vars - all_template_vars
            if unused_defined:
                warnings.append(f"Defined but unused variables: {unused_defined}")

            undefined_used = all_template_vars - defined_vars
            if undefined_used:
                errors.append(f"Undefined variables used in template: {undefined_used}")

            # Variable analysis
            for var in template.variables:
                variable_analysis[var.name] = {
                    "type": var.type,
                    "required": var.required,
                    "used_in_title": var.name in title_vars,
                    "used_in_body": var.name in body_vars,
                    "has_default": var.default_value is not None
                }

            # Channel length validation
            estimated_length = {}
            for channel in template.target_channels:
                if channel in self.channel_limits:
                    limits = self.channel_limits[channel]

                    if "title" in limits:
                        title_len = len(template.title_template)
                        if title_len > limits["title"]:
                            warnings.append(f"Title may exceed {channel} limit ({title_len} > {limits['title']})")

                    if "body" in limits:
                        body_len = len(template.body_template)
                        if body_len > limits["body"]:
                            warnings.append(f"Body may exceed {channel} limit ({body_len} > {limits['body']})")

                    if "total" in limits:
                        total_len = len(template.title_template) + len(template.body_template)
                        estimated_length[channel] = total_len
                        if total_len > limits["total"]:
                            warnings.append(f"Total length may exceed {channel} limit ({total_len} > {limits['total']})")

            # Translation validation
            for translation in template.translations:
                trans_title_vars = self._extract_variables(translation.title_template)
                trans_body_vars = self._extract_variables(translation.body_template)
                trans_vars = set(trans_title_vars + trans_body_vars)

                if trans_vars != all_template_vars:
                    warnings.append(f"Translation {translation.language_code} has mismatched variables")

            self.stats["validations_performed"] += 1

            return TemplateValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                variable_analysis=variable_analysis,
                estimated_length=estimated_length
            )

        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return TemplateValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    async def render_template(
        self,
        template_id: str,
        variables: dict[str, any],
        language: str = "en",
        channel: str = "push",
        user_customization: UserTemplateCustomization | None = None
    ) -> TemplatePreview | None:
        """Render a template with provided variables.

        Args:
            template_id: Template identifier
            variables: Variable values for substitution
            language: Language for rendering
            channel: Target channel for rendering
            user_customization: User-specific customizations

        Returns:
            Rendered template preview or None if failed
        """
        start_time = datetime.now()

        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return None

            # Get appropriate translation
            title_template, body_template = self._get_template_content(template, language)

            # Apply user customizations
            if user_customization:
                if user_customization.custom_title:
                    title_template = user_customization.custom_title
                if user_customization.custom_body:
                    body_template = user_customization.custom_body

                # Override variables
                variables = {**variables, **user_customization.custom_variables}

            # Validate variables
            validation_errors = self._validate_variables(template, variables)
            if validation_errors:
                logger.warning(f"Variable validation issues: {validation_errors}")

            # Apply defaults for missing optional variables
            complete_variables = self._apply_variable_defaults(template, variables)

            # Render templates
            rendered_title = self._render_template_content(title_template, complete_variables, template.format_options)
            rendered_body = self._render_template_content(body_template, complete_variables, template.format_options)

            rendered_summary = None
            if template.summary_template:
                rendered_summary = self._render_template_content(
                    template.summary_template, complete_variables, template.format_options
                )

            # Calculate length and channel compatibility
            total_length = len(rendered_title) + len(rendered_body)
            fits_limits = self._check_channel_limits(channel, rendered_title, rendered_body)

            # Calculate rendering time
            render_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_render_stats(render_time)

            # Track usage
            await self._track_template_usage(template_id)

            preview = TemplatePreview(
                template_id=template_id,
                language=language,
                channel=channel,
                rendered_title=rendered_title,
                rendered_body=rendered_body,
                rendered_summary=rendered_summary,
                estimated_length=total_length,
                fits_channel_limits=fits_limits,
                variable_values_used=complete_variables,
                rendering_time_ms=render_time,
                warnings=validation_errors
            )

            self.stats["templates_rendered"] += 1
            return preview

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return None

    async def create_user_customization(
        self,
        user_id: str,
        template_id: str,
        customization: UserTemplateCustomization
    ) -> bool:
        """Create user-specific template customization.

        Args:
            user_id: User identifier
            template_id: Template identifier
            customization: Customization settings

        Returns:
            True if customization created successfully
        """
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return False

            if not template.user_customizable:
                logger.error(f"Template {template_id} is not user customizable")
                return False

            # Store customization
            if user_id not in self.user_customizations:
                self.user_customizations[user_id] = {}

            self.user_customizations[user_id][template_id] = customization

            # Save to database
            await self._save_customization_to_db(customization)

            self.stats["customizations_applied"] += 1
            logger.info(f"Created customization for user {user_id}, template {template_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to create user customization: {e}")
            return False

    async def add_translation(
        self,
        template_id: str,
        translation: TemplateTranslation
    ) -> bool:
        """Add a translation to a template.

        Args:
            template_id: Template identifier
            translation: Translation to add

        Returns:
            True if translation added successfully
        """
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return False

            # Check if translation already exists
            existing_languages = {t.language_code for t in template.translations}
            if translation.language_code in existing_languages:
                logger.warning(f"Translation for {translation.language_code} already exists")
                return False

            # Validate translation variables
            title_vars = self._extract_variables(translation.title_template)
            body_vars = self._extract_variables(translation.body_template)
            trans_vars = set(title_vars + body_vars)

            template_vars = self._extract_variables(template.title_template) + self._extract_variables(template.body_template)
            template_vars = set(template_vars)

            if trans_vars != template_vars:
                logger.error("Translation variables don't match template variables")
                return False

            # Add translation
            template.translations.append(translation)
            template.updated_at = datetime.now()

            # Save to database
            await self._save_template_to_db(template)

            self.stats["translations_added"] += 1
            logger.info(f"Added {translation.language_code} translation to template {template_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to add translation: {e}")
            return False

    async def get_template_analytics(self, template_id: str) -> dict[str, any]:
        """Get analytics data for a template.

        Args:
            template_id: Template identifier

        Returns:
            Analytics data for the template
        """
        try:
            template = self.templates.get(template_id)
            if not template:
                return {}

            # Get usage statistics
            usage_count = template.usage_count
            effectiveness_score = template.effectiveness_score
            last_used = template.last_used

            # Calculate metrics
            customization_count = sum(
                1 for user_customs in self.user_customizations.values()
                if template_id in user_customs
            )

            translation_count = len(template.translations)
            available_languages = [template.default_language] + [t.language_code for t in template.translations]

            return {
                "template_id": template_id,
                "name": template.name,
                "category": template.category,
                "usage_count": usage_count,
                "effectiveness_score": effectiveness_score,
                "last_used": last_used.isoformat() if last_used else None,
                "customization_count": customization_count,
                "translation_count": translation_count,
                "available_languages": available_languages,
                "target_channels": template.target_channels,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
                "version": template.version,
                "is_active": template.is_active
            }

        except Exception as e:
            logger.error(f"Failed to get template analytics: {e}")
            return {}

    async def list_templates(
        self,
        category: str | None = None,
        user_id: str | None = None,
        language: str | None = None
    ) -> list[dict[str, any]]:
        """List available templates with filtering.

        Args:
            category: Filter by category
            user_id: Filter by templates available to user
            language: Filter by language support

        Returns:
            List of template summaries
        """
        try:
            templates = []

            for template in self.templates.values():
                # Apply filters
                if category and template.category != category:
                    continue

                if language:
                    available_languages = [template.default_language] + [t.language_code for t in template.translations]
                    if language not in available_languages:
                        continue

                # Get user customization if available
                user_customization = None
                if user_id and user_id in self.user_customizations:
                    user_customization = self.user_customizations[user_id].get(template.template_id)

                templates.append({
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "version": template.version,
                    "is_active": template.is_active,
                    "user_customizable": template.user_customizable,
                    "has_user_customization": user_customization is not None,
                    "available_languages": [template.default_language] + [t.language_code for t in template.translations],
                    "target_channels": template.target_channels,
                    "usage_count": template.usage_count,
                    "effectiveness_score": template.effectiveness_score,
                    "last_used": template.last_used.isoformat() if template.last_used else None
                })

            # Sort by usage count and effectiveness
            templates.sort(key=lambda t: (t["usage_count"], t["effectiveness_score"]), reverse=True)

            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def _extract_variables(self, template_content: str) -> list[str]:
        """Extract variable names from template content."""
        matches = self.variable_pattern.findall(template_content)
        return [match[0] for match in matches]

    def _get_template_content(
        self,
        template: AlertTemplateDefinition,
        language: str
    ) -> tuple[str, str]:
        """Get template content for specified language."""
        # Try to find translation
        for translation in template.translations:
            if translation.language_code == language:
                return translation.title_template, translation.body_template

        # Fall back to default language
        return template.title_template, template.body_template

    def _validate_variables(
        self,
        template: AlertTemplateDefinition,
        variables: dict[str, any]
    ) -> list[str]:
        """Validate provided variables against template requirements."""
        errors = []

        # Check required variables
        for var_def in template.variables:
            if var_def.required and var_def.name not in variables:
                if var_def.default_value is None:
                    errors.append(f"Required variable '{var_def.name}' is missing")

        # Validate variable patterns
        for var_def in template.variables:
            if var_def.name in variables and var_def.validation_pattern:
                value = str(variables[var_def.name])
                if not re.match(var_def.validation_pattern, value):
                    errors.append(f"Variable '{var_def.name}' does not match required pattern")

        return errors

    def _apply_variable_defaults(
        self,
        template: AlertTemplateDefinition,
        variables: dict[str, any]
    ) -> dict[str, str]:
        """Apply default values for missing variables."""
        complete_variables = variables.copy()

        for var_def in template.variables:
            if var_def.name not in complete_variables and var_def.default_value is not None:
                complete_variables[var_def.name] = var_def.default_value

        # Convert all values to strings for template rendering
        return {k: str(v) for k, v in complete_variables.items()}

    def _render_template_content(
        self,
        template_content: str,
        variables: dict[str, str],
        format_options: TemplateFormat
    ) -> str:
        """Render template content with variable substitution."""
        result = template_content

        # Basic variable substitution
        for var_name, var_value in variables.items():
            placeholder = f"{format_options.variable_prefix}{var_name}{format_options.variable_suffix}"
            result = result.replace(placeholder, var_value)

        # Handle escape HTML if enabled
        if format_options.escape_html:
            result = self._escape_html(result)

        # Handle line breaks
        if not format_options.line_breaks_enabled:
            result = result.replace('\n', ' ').replace('\r', ' ')

        return result

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))

    def _check_channel_limits(
        self,
        channel: str,
        title: str,
        body: str
    ) -> bool:
        """Check if rendered content fits channel limits."""
        if channel not in self.channel_limits:
            return True

        limits = self.channel_limits[channel]

        if "title" in limits and len(title) > limits["title"]:
            return False

        if "body" in limits and len(body) > limits["body"]:
            return False

        if "total" in limits and (len(title) + len(body)) > limits["total"]:
            return False

        return True

    def _increment_version(self, current_version: str) -> str:
        """Increment template version number."""
        try:
            parts = current_version.split('.')
            if len(parts) == 2:
                major, minor = parts
                return f"{major}.{int(minor) + 1}"
            else:
                return f"{current_version}.1"
        except Exception:
            return "1.0"

    async def _save_template_to_db(self, template: AlertTemplateDefinition):
        """Save template to database."""
        try:
            async with get_session() as db:
                # Check if template exists
                existing = db.query(AlertTemplate).filter(
                    AlertTemplate.template_id == template.template_id
                ).first()

                if existing:
                    # Update existing
                    existing.name = template.name
                    existing.description = template.description
                    existing.category = template.category
                    existing.title_template = template.title_template
                    existing.body_template = template.body_template
                    existing.variables = json.dumps([var.dict() for var in template.variables])
                    existing.format_options = json.dumps(template.format_options.dict())
                    existing.translations = json.dumps([trans.dict() for trans in template.translations])
                    existing.target_channels = json.dumps(template.target_channels)
                    existing.version = template.version
                    existing.is_active = template.is_active
                    existing.updated_at = template.updated_at
                else:
                    # Create new
                    db_template = AlertTemplate(
                        template_id=template.template_id,
                        name=template.name,
                        description=template.description,
                        category=template.category,
                        title_template=template.title_template,
                        body_template=template.body_template,
                        variables=json.dumps([var.dict() for var in template.variables]),
                        format_options=json.dumps(template.format_options.dict()),
                        translations=json.dumps([trans.dict() for trans in template.translations]),
                        target_channels=json.dumps(template.target_channels),
                        version=template.version,
                        created_by=template.created_by,
                        is_active=template.is_active,
                        created_at=template.created_at,
                        updated_at=template.updated_at
                    )
                    db.add(db_template)

                db.commit()

        except Exception as e:
            logger.error(f"Failed to save template to database: {e}")

    async def _save_customization_to_db(self, customization: UserTemplateCustomization):
        """Save user customization to database."""
        # This would implement database storage for user customizations
        # For now, just log the action
        logger.info(f"Saving customization for user {customization.user_id}")

    async def _track_template_usage(self, template_id: str):
        """Track template usage for analytics."""
        try:
            template = self.templates.get(template_id)
            if template:
                template.usage_count += 1
                template.last_used = datetime.now()

                # Update most used templates stats
                self.stats["most_used_templates"][template_id] = template.usage_count

        except Exception as e:
            logger.error(f"Failed to track template usage: {e}")

    def _update_render_stats(self, render_time: float):
        """Update rendering performance statistics."""
        current_avg = self.stats["avg_render_time_ms"]
        render_count = self.stats["templates_rendered"]

        if render_count == 0:
            self.stats["avg_render_time_ms"] = render_time
        else:
            self.stats["avg_render_time_ms"] = (
                (current_avg * render_count + render_time) / (render_count + 1)
            )

    def get_stats(self) -> dict[str, any]:
        """Get template manager statistics."""
        return {
            **self.stats,
            "total_templates": len(self.templates),
            "total_customizations": sum(len(customs) for customs in self.user_customizations.values()),
            "templates_by_category": self._get_templates_by_category(),
            "templates_by_language": self._get_templates_by_language(),
            "channel_limits": self.channel_limits
        }

    def _get_templates_by_category(self) -> dict[str, int]:
        """Get template count by category."""
        categories = {}
        for template in self.templates.values():
            categories[template.category] = categories.get(template.category, 0) + 1
        return categories

    def _get_templates_by_language(self) -> dict[str, int]:
        """Get template count by supported languages."""
        languages = {}
        for template in self.templates.values():
            all_languages = [template.default_language] + [t.language_code for t in template.translations]
            for lang in all_languages:
                languages[lang] = languages.get(lang, 0) + 1
        return languages


# Global instance
alert_template_manager = AlertTemplateManager()
