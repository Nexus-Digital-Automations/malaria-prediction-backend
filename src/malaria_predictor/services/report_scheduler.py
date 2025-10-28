"""
Report Scheduler Service for Automated Report Generation.

This module provides comprehensive automated report scheduling capabilities
with support for cron expressions, interval-based scheduling, email delivery,
and webhook notifications.
"""

import asyncio
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiofiles
import aiohttp
from croniter import croniter
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..database.models import Report, ReportSchedule, ReportTemplate
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class EmailDeliveryService:
    """Email delivery service for scheduled reports."""

    def __init__(self, smtp_config: dict[str, Any]) -> None:
        """
        Initialize email delivery service.

        Args:
            smtp_config: SMTP configuration dictionary
        """
        self.smtp_config = smtp_config

    async def send_report_email(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachments: dict[str, bytes],
        sender: str | None = None
    ) -> bool:
        """
        Send report via email with attachments.

        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Email body content
            attachments: Dictionary of filename -> file_content
            sender: Sender email address

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            sender = sender or self.smtp_config.get('sender')
            if not sender:
                logger.error("No sender email address configured")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(body, 'html'))

            # Add attachments
            for filename, content in attachments.items():
                attachment = MIMEApplication(content)
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachment)

            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                if self.smtp_config.get('username'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])

                server.send_message(msg)

            logger.info(f"Report email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending report email: {str(e)}")
            return False


class WebhookDeliveryService:
    """Webhook delivery service for scheduled reports."""

    async def send_report_webhook(
        self,
        webhook_urls: list[str],
        report_data: dict[str, Any],
        timeout: int = 30
    ) -> dict[str, bool]:
        """
        Send report data to webhook endpoints.

        Args:
            webhook_urls: List of webhook URLs
            report_data: Report data to send
            timeout: Request timeout in seconds

        Returns:
            Dictionary of URL -> success status
        """
        results = {}

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            for url in webhook_urls:
                try:
                    async with session.post(url, json=report_data) as response:
                        if response.status == 200:
                            results[url] = True
                            logger.info(f"Webhook sent successfully to {url}")
                        else:
                            results[url] = False
                            logger.error(f"Webhook failed for {url}: HTTP {response.status}")

                except Exception as e:
                    results[url] = False
                    logger.error(f"Webhook error for {url}: {str(e)}")

        return results


class ReportScheduler:
    """Comprehensive report scheduling and execution engine."""

    def __init__(
        self,
        db_session: Session,
        email_config: dict[str, Any] | None = None
    ):
        """
        Initialize report scheduler.

        Args:
            db_session: Database session for schedule management
            email_config: Email configuration for delivery
        """
        self.db = db_session
        self.report_generator = ReportGenerator(db_session)
        self.email_service = EmailDeliveryService(email_config or {}) if email_config else None
        self.webhook_service = WebhookDeliveryService()
        self.running = False

    async def start_scheduler(self) -> None:
        """Start the report scheduler background task."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        logger.info("Starting report scheduler")

        try:
            while self.running:
                await self._process_scheduled_reports()
                await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
        finally:
            self.running = False
            logger.info("Report scheduler stopped")

    async def stop_scheduler(self) -> None:
        """Stop the report scheduler."""
        self.running = False
        logger.info("Stopping report scheduler")

    async def _process_scheduled_reports(self) -> None:
        """Process all scheduled reports that are due for execution."""
        try:
            # Get schedules due for execution
            current_time = datetime.utcnow()
            due_schedules = self.db.query(ReportSchedule).filter(
                and_(
                    ReportSchedule.is_active,
                    ReportSchedule.next_execution <= current_time,
                    ReportSchedule.status == "active"
                )
            ).all()

            if not due_schedules:
                return

            logger.info(f"Processing {len(due_schedules)} scheduled reports")

            for schedule in due_schedules:
                try:
                    await self._execute_scheduled_report(schedule)
                except Exception as e:
                    logger.error(f"Error executing schedule {schedule.id}: {str(e)}")
                    # Update schedule with error
                    schedule.error_count += 1
                    schedule.last_error_message = str(e)
                    if schedule.error_count >= 5:  # Max retries
                        schedule.status = "failed"
                        logger.error(f"Schedule {schedule.id} disabled after 5 failures")

            self.db.commit()

        except Exception as e:
            logger.error(f"Error processing scheduled reports: {str(e)}")

    async def _execute_scheduled_report(self, schedule: ReportSchedule) -> None:
        """
        Execute a single scheduled report.

        Args:
            schedule: ReportSchedule object to execute
        """
        execution_start = datetime.utcnow()
        logger.info(f"Executing scheduled report {schedule.id}: {schedule.name}")

        try:
            # Generate report
            report_result = await self.report_generator.generate_report(
                template_id=schedule.template_id,
                report_config=schedule.report_configuration,
                user_id=f"schedule_{schedule.id}",
                export_formats=schedule.export_formats
            )

            if report_result['status'] == 'completed':
                # Deliver report based on delivery methods
                await self._deliver_report(schedule, report_result)

                # Update schedule success metrics
                schedule.success_count += 1
                schedule.last_status = "success"
                schedule.last_error_message = None

            else:
                raise Exception(f"Report generation failed: {report_result.get('error', 'Unknown error')}")

            # Calculate next execution time
            schedule.next_execution = self._calculate_next_execution(schedule)
            schedule.last_execution = execution_start
            schedule.execution_count += 1

            # Update performance metrics
            execution_time = (datetime.utcnow() - execution_start).total_seconds()
            schedule.last_execution_time = execution_time

            if schedule.average_execution_time is None:
                schedule.average_execution_time = execution_time
            else:
                # Exponential moving average
                schedule.average_execution_time = (
                    0.8 * schedule.average_execution_time + 0.2 * execution_time
                )

            logger.info(f"Schedule {schedule.id} executed successfully in {execution_time:.2f}s")

        except Exception as e:
            logger.error(f"Error executing schedule {schedule.id}: {str(e)}")
            schedule.error_count += 1
            schedule.last_status = "failed"
            schedule.last_error_message = str(e)

            # Still calculate next execution for retry
            schedule.next_execution = self._calculate_next_execution(schedule)
            raise

    async def _deliver_report(
        self,
        schedule: ReportSchedule,
        report_result: dict[str, Any]
    ) -> None:
        """
        Deliver report based on configured delivery methods.

        Args:
            schedule: ReportSchedule configuration
            report_result: Report generation results
        """
        delivery_methods = schedule.delivery_methods
        report_id = report_result['report_id']

        # Load actual report from database
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise Exception(f"Report {report_id} not found for delivery")

        # Email delivery
        if "email" in delivery_methods and schedule.email_recipients and self.email_service:
            await self._deliver_via_email(schedule, report, report_result)

        # Webhook delivery
        if "webhook" in delivery_methods and schedule.webhook_urls:
            await self._deliver_via_webhook(schedule, report, report_result)

        # Storage delivery (copy to specific locations)
        if "storage" in delivery_methods and schedule.storage_locations:
            await self._deliver_via_storage(schedule, report, report_result)

    async def _deliver_via_email(
        self,
        schedule: ReportSchedule,
        report: Report,
        report_result: dict[str, Any]
    ) -> None:
        """Deliver report via email."""
        try:
            # Prepare email content
            subject = f"Scheduled Report: {report.title}"
            body = f"""
            <html>
            <body>
                <h2>{report.title}</h2>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
                <p><strong>Description:</strong> {report.description or 'N/A'}</p>
                <p><strong>Data Period:</strong> {report.data_period_start} to {report.data_period_end}</p>
                <p><strong>Generation Time:</strong> {report.generation_time_seconds:.2f} seconds</p>
                <p><strong>Data Points:</strong> {report.data_points_count:,}</p>

                <h3>Export Formats:</h3>
                <ul>
                {"".join([f"<li>{fmt.upper()}: {status['status']}</li>"
                         for fmt, status in report.export_status.items()])}
                </ul>

                <p>Report files are attached to this email.</p>
            </body>
            </html>
            """

            # Load attachments
            attachments = {}
            for format_name, file_path in report.file_paths.items():
                try:
                    async with aiofiles.open(file_path, 'rb') as f:
                        content = await f.read()
                    filename = f"{report.title.replace(' ', '_')}_{report.id}.{format_name}"
                    attachments[filename] = content
                except Exception as e:
                    logger.error(f"Error loading attachment {file_path}: {str(e)}")

            # Send email
            success = await self.email_service.send_report_email(
                recipients=schedule.email_recipients,
                subject=subject,
                body=body,
                attachments=attachments
            )

            if success:
                logger.info(f"Report {report.id} delivered via email to {len(schedule.email_recipients)} recipients")
            else:
                raise Exception("Email delivery failed")

        except Exception as e:
            logger.error(f"Error delivering report {report.id} via email: {str(e)}")
            raise

    async def _deliver_via_webhook(
        self,
        schedule: ReportSchedule,
        report: Report,
        report_result: dict[str, Any]
    ) -> None:
        """Deliver report via webhook."""
        try:
            webhook_data = {
                'schedule_id': schedule.id,
                'schedule_name': schedule.name,
                'report_id': report.id,
                'report_title': report.title,
                'generated_at': report.generated_at.isoformat(),
                'generation_time_seconds': report.generation_time_seconds,
                'data_points_count': report.data_points_count,
                'export_status': report.export_status,
                'file_paths': report.file_paths,
                'metadata': {
                    'template_id': report.template_id,
                    'report_type': report.report_type,
                    'data_period_start': report.data_period_start.isoformat() if report.data_period_start else None,
                    'data_period_end': report.data_period_end.isoformat() if report.data_period_end else None
                }
            }

            results = await self.webhook_service.send_report_webhook(
                webhook_urls=schedule.webhook_urls,
                report_data=webhook_data
            )

            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Report {report.id} delivered via webhook to {success_count}/{len(results)} endpoints")

            if success_count == 0:
                raise Exception("All webhook deliveries failed")

        except Exception as e:
            logger.error(f"Error delivering report {report.id} via webhook: {str(e)}")
            raise

    async def _deliver_via_storage(
        self,
        schedule: ReportSchedule,
        report: Report,
        report_result: dict[str, Any]
    ) -> None:
        """Deliver report to configured storage locations."""
        try:
            for storage_config in schedule.storage_locations:
                storage_type = storage_config.get('type', 'local')
                storage_path = storage_config.get('path')

                if storage_type == 'local' and storage_path:
                    # Copy files to local storage path
                    import shutil
                    from pathlib import Path

                    dest_dir = Path(storage_path) / f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    for _format_name, file_path in report.file_paths.items():
                        src_file = Path(file_path)
                        dest_file = dest_dir / src_file.name
                        shutil.copy2(src_file, dest_file)

                    logger.info(f"Report {report.id} copied to storage: {dest_dir}")

        except Exception as e:
            logger.error(f"Error delivering report {report.id} via storage: {str(e)}")
            raise

    def _calculate_next_execution(self, schedule: ReportSchedule) -> datetime:
        """
        Calculate the next execution time for a schedule.

        Args:
            schedule: ReportSchedule object

        Returns:
            Next execution datetime
        """
        current_time = datetime.utcnow()

        if schedule.schedule_type == "cron":
            if not schedule.cron_expression:
                raise ValueError(f"Cron expression required for schedule {schedule.id}")

            cron = croniter(schedule.cron_expression, current_time)
            next_time = cron.get_next(datetime)

            # Respect end date
            if schedule.end_date and next_time > schedule.end_date:
                schedule.status = "completed"
                return schedule.end_date

            return next_time

        elif schedule.schedule_type == "interval":
            if not schedule.interval_minutes:
                raise ValueError(f"Interval minutes required for schedule {schedule.id}")

            next_time = current_time + timedelta(minutes=schedule.interval_minutes)

            # Respect end date
            if schedule.end_date and next_time > schedule.end_date:
                schedule.status = "completed"
                return schedule.end_date

            return next_time

        elif schedule.schedule_type == "one_time":
            # One-time schedules are marked as completed after execution
            schedule.status = "completed"
            return current_time

        else:
            raise ValueError(f"Unknown schedule type: {schedule.schedule_type}")

    async def create_schedule(
        self,
        name: str,
        template_id: int,
        schedule_config: dict[str, Any],
        user_id: str
    ) -> ReportSchedule:
        """
        Create a new report schedule.

        Args:
            name: Schedule name
            template_id: Report template ID
            schedule_config: Schedule configuration
            user_id: User creating the schedule

        Returns:
            Created ReportSchedule object
        """
        try:
            # Validate template exists
            template = self.db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Validate schedule configuration
            self._validate_schedule_config(schedule_config)

            # Calculate initial next execution
            schedule = ReportSchedule(
                name=name,
                created_by=user_id,
                template_id=template_id,
                report_configuration=schedule_config.get('report_config', {}),
                schedule_type=schedule_config['schedule_type'],
                cron_expression=schedule_config.get('cron_expression'),
                interval_minutes=schedule_config.get('interval_minutes'),
                timezone=schedule_config.get('timezone', 'UTC'),
                start_date=schedule_config.get('start_date'),
                end_date=schedule_config.get('end_date'),
                delivery_methods=schedule_config.get('delivery_methods', ['storage']),
                email_recipients=schedule_config.get('email_recipients'),
                webhook_urls=schedule_config.get('webhook_urls'),
                storage_locations=schedule_config.get('storage_locations', [{'type': 'local', 'path': 'exports/scheduled'}]),
                export_formats=schedule_config.get('export_formats', ['pdf']),
                compression_enabled=schedule_config.get('compression_enabled', False),
                retention_days=schedule_config.get('retention_days')
            )

            # Calculate next execution
            schedule.next_execution = self._calculate_next_execution(schedule)

            self.db.add(schedule)
            self.db.commit()

            logger.info(f"Created schedule {schedule.id}: {name}")
            return schedule

        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            self.db.rollback()
            raise

    def _validate_schedule_config(self, config: dict[str, Any]) -> None:
        """Validate schedule configuration."""
        schedule_type = config.get('schedule_type')
        if schedule_type not in ['cron', 'interval', 'one_time']:
            raise ValueError(f"Invalid schedule type: {schedule_type}")

        if schedule_type == 'cron' and not config.get('cron_expression'):
            raise ValueError("Cron expression required for cron schedule")

        if schedule_type == 'interval' and not config.get('interval_minutes'):
            raise ValueError("Interval minutes required for interval schedule")

        delivery_methods = config.get('delivery_methods', [])
        if 'email' in delivery_methods and not config.get('email_recipients'):
            raise ValueError("Email recipients required for email delivery")

        if 'webhook' in delivery_methods and not config.get('webhook_urls'):
            raise ValueError("Webhook URLs required for webhook delivery")

    async def update_schedule(
        self,
        schedule_id: int,
        updates: dict[str, Any],
        user_id: str
    ) -> ReportSchedule:
        """
        Update an existing report schedule.

        Args:
            schedule_id: Schedule ID to update
            updates: Dictionary of updates to apply
            user_id: User making the update

        Returns:
            Updated ReportSchedule object
        """
        try:
            schedule = self.db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")

            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'is_active', 'cron_expression', 'interval_minutes',
                'email_recipients', 'webhook_urls', 'storage_locations', 'export_formats',
                'compression_enabled', 'retention_days', 'start_date', 'end_date'
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(schedule, field, value)

            # Recalculate next execution if timing changed
            if any(field in updates for field in ['cron_expression', 'interval_minutes', 'start_date']):
                schedule.next_execution = self._calculate_next_execution(schedule)

            schedule.last_modified_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated schedule {schedule_id}")
            return schedule

        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
            self.db.rollback()
            raise

    async def delete_schedule(self, schedule_id: int, user_id: str) -> bool:
        """
        Delete a report schedule.

        Args:
            schedule_id: Schedule ID to delete
            user_id: User performing the deletion

        Returns:
            True if deleted successfully
        """
        try:
            schedule = self.db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")

            self.db.delete(schedule)
            self.db.commit()

            logger.info(f"Deleted schedule {schedule_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
            self.db.rollback()
            raise


# Service factory function
def get_report_scheduler(
    db_session: Session,
    email_config: dict[str, Any] | None = None
) -> ReportScheduler:
    """
    Factory function to create ReportScheduler instance.

    Args:
        db_session: Database session
        email_config: Email configuration for delivery

    Returns:
        Configured ReportScheduler instance
    """
    return ReportScheduler(db_session, email_config)
