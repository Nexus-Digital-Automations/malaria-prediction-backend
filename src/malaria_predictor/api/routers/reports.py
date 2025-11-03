"""
Reports API Routes for Custom Report Generation and Management.

This module provides comprehensive API endpoints for report generation,
template management, scheduling, and export functionality with support
for multiple formats and automated delivery.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from ...database.models import Report, ReportSchedule, ReportTemplate
from ...database.session import get_session as get_db
from ...services.report_generator import get_report_generator
from ...services.report_scheduler import get_report_scheduler
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


# Pydantic models for request/response
class ReportGenerationRequest(BaseModel):
    """Request model for report generation."""
    title: str = Field(..., description="Report title")
    description: str | None = Field(None, description="Report description")
    report_type: str = Field(default="custom", description="Type of report")
    template_id: int | None = Field(None, description="Template ID to use")
    export_formats: list[str] = Field(default=["pdf"], description="Export formats")
    data_period_start: datetime | None = Field(None, description="Data period start")
    data_period_end: datetime | None = Field(None, description="Data period end")
    custom_parameters: dict[str, Any] | None = Field(None, description="Custom parameters")
    include_prediction_accuracy: bool = Field(default=True, description="Include prediction data")
    include_climate_data: bool = Field(default=True, description="Include climate data")


class ReportTemplateRequest(BaseModel):
    """Request model for report template creation/update."""
    name: str = Field(..., description="Template name")
    description: str | None = Field(None, description="Template description")
    category: str = Field(..., description="Template category")
    layout_configuration: dict[str, Any] = Field(..., description="Layout configuration")
    widgets: list[dict[str, Any]] = Field(..., description="Widget definitions")
    data_sources: list[str] = Field(..., description="Data source configurations")
    chart_configurations: dict[str, Any] | None = Field(None, description="Chart configurations")
    default_parameters: dict[str, Any] | None = Field(None, description="Default parameters")
    export_formats: list[str] = Field(default=["pdf"], description="Supported export formats")
    is_public: bool = Field(default=False, description="Public template availability")


class ReportScheduleRequest(BaseModel):
    """Request model for report schedule creation/update."""
    name: str = Field(..., description="Schedule name")
    description: str | None = Field(None, description="Schedule description")
    template_id: int = Field(..., description="Template ID to use")
    schedule_type: str = Field(..., description="Schedule type: cron, interval, one_time")
    cron_expression: str | None = Field(None, description="Cron expression for cron schedules")
    interval_minutes: int | None = Field(None, description="Interval in minutes for interval schedules")
    timezone: str = Field(default="UTC", description="Schedule timezone")
    start_date: datetime | None = Field(None, description="Schedule start date")
    end_date: datetime | None = Field(None, description="Schedule end date")
    delivery_methods: list[str] = Field(..., description="Delivery methods")
    email_recipients: list[str] | None = Field(None, description="Email recipients")
    webhook_urls: list[str] | None = Field(None, description="Webhook URLs")
    storage_locations: list[dict[str, Any]] | None = Field(None, description="Storage locations")
    export_formats: list[str] = Field(default=["pdf"], description="Export formats")
    report_configuration: dict[str, Any] | None = Field(None, description="Report configuration")


class ReportResponse(BaseModel):
    """Response model for report details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    report_type: str
    template_id: int | None
    generated_by: str
    generated_at: datetime
    status: str
    export_formats: list[str] | None
    export_status: dict[str, Any] | None
    file_paths: dict[str, str] | None
    generation_time_seconds: float | None
    data_points_count: int | None


class ReportTemplateResponse(BaseModel):
    """Response model for report template details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    category: str
    template_type: str
    created_by: str
    created_at: datetime
    is_active: bool
    is_public: bool
    usage_count: int
    version: str


class ReportScheduleResponse(BaseModel):
    """Response model for report schedule details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    template_id: int
    schedule_type: str
    cron_expression: str | None
    interval_minutes: int | None
    next_execution: datetime | None
    last_execution: datetime | None
    is_active: bool
    status: str
    execution_count: int
    success_count: int
    error_count: int


# Report Generation Endpoints
@router.post("/generate", response_model=dict[str, Any])
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Generate a custom report with specified configuration.

    Creates a comprehensive report with multiple export formats,
    chart generation, and template processing.
    """
    try:
        logger.info(f"Generating report '{request.title}' for user {current_user['sub']}")

        # Prepare report configuration
        report_config = {
            'title': request.title,
            'description': request.description,
            'type': request.report_type,
            'start_date': request.data_period_start,
            'end_date': request.data_period_end,
            'include_prediction_accuracy': request.include_prediction_accuracy,
            'include_climate_data': request.include_climate_data,
            **(request.custom_parameters or {})
        }

        # Get report generator
        generator = get_report_generator(db)

        # Generate report
        result = await generator.generate_report(
            template_id=request.template_id,
            report_config=report_config,
            user_id=current_user['sub'],
            export_formats=request.export_formats
        )

        return {
            "status": "success",
            "message": "Report generated successfully",
            "report_id": result['report_id'],
            "generation_time_seconds": result['generation_time_seconds'],
            "export_results": result['export_results'],
            "file_paths": result['file_paths']
        }

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}") from e


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    report_type: str | None = Query(None, description="Filter by report type"),
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search in title and description"),
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> list[ReportResponse]:
    """
    Get list of reports with filtering and pagination.

    Returns paginated list of reports for the current user
    with optional filtering by type, status, and search terms.
    """
    try:
        # Build query
        query = db.query(Report).filter(Report.generated_by == current_user['sub'])

        # Apply filters
        if report_type:
            query = query.filter(Report.report_type == report_type)
        if status:
            query = query.filter(Report.status == status)
        if search:
            query = query.filter(
                or_(
                    Report.title.ilike(f"%{search}%"),
                    Report.description.ilike(f"%{search}%")
                )
            )

        # Apply pagination and ordering
        reports = query.order_by(desc(Report.generated_at)).offset(skip).limit(limit).all()

        return [
            ReportResponse.model_validate(report)
            for report in reports
        ]

    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports") from e


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> ReportResponse:
    """
    Get detailed information about a specific report.

    Returns comprehensive report metadata including export status,
    file paths, and generation metrics.
    """
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user['sub']
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return ReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report") from e


@router.get("/{report_id}/download/{format_name}")
async def download_report(
    report_id: int,
    format_name: str,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> FileResponse:
    """
    Download a report file in the specified format.

    Returns the report file as a downloadable attachment
    with proper content type and filename.
    """
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user['sub']
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if not report.file_paths or format_name not in report.file_paths:
            raise HTTPException(status_code=404, detail=f"Report format '{format_name}' not found")

        file_path = report.file_paths[format_name]

        # Determine content type
        content_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }

        content_type = content_types.get(format_name, 'application/octet-stream')

        # Generate filename
        safe_title = report.title.replace(' ', '_').replace('/', '_')
        filename = f"{safe_title}_{report.id}.{format_name}"

        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id} format {format_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download report") from e


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """
    Delete a report and its associated files.

    Removes the report record and cleans up exported files
    from the filesystem.
    """
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user['sub']
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Clean up files
        if report.file_paths:
            import os
            for file_path in report.file_paths.values():
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error deleting file {file_path}: {str(e)}")

        # Delete report record
        db.delete(report)
        db.commit()

        logger.info(f"Deleted report {report_id} for user {current_user['sub']}")
        return {"status": "success", "message": f"Report {report_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete report") from e


# Template Management Endpoints
@router.get("/templates/", response_model=list[ReportTemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search in name and description"),
    include_public: bool = Query(True, description="Include public templates"),
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> list[ReportTemplateResponse]:
    """
    Get list of report templates with filtering and pagination.

    Returns templates created by the user and optionally public templates
    with filtering by category and search terms.
    """
    try:
        # Build query
        if include_public:
            query = db.query(ReportTemplate).filter(
                or_(
                    ReportTemplate.created_by == current_user['sub'],
                    ReportTemplate.is_public
                )
            )
        else:
            query = db.query(ReportTemplate).filter(ReportTemplate.created_by == current_user['sub'])

        # Apply filters
        if category:
            query = query.filter(ReportTemplate.category == category)
        if search:
            query = query.filter(
                or_(
                    ReportTemplate.name.ilike(f"%{search}%"),
                    ReportTemplate.description.ilike(f"%{search}%")
                )
            )

        # Apply active filter and pagination
        templates = query.filter(ReportTemplate.is_active)\
                         .order_by(desc(ReportTemplate.created_at))\
                         .offset(skip).limit(limit).all()

        return [
            ReportTemplateResponse.model_validate(template)
            for template in templates
        ]

    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates") from e


@router.post("/templates/", response_model=ReportTemplateResponse)
async def create_template(
    request: ReportTemplateRequest,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> ReportTemplateResponse:
    """
    Create a new report template.

    Creates a customizable report template with layout configuration,
    widget definitions, and styling options.
    """
    try:
        logger.info(f"Creating template '{request.name}' for user {current_user['sub']}")

        template = ReportTemplate(
            name=request.name,
            description=request.description,
            created_by=current_user['sub'],
            template_type="custom",
            category=request.category,
            layout_configuration=request.layout_configuration,
            widgets=request.widgets,
            data_sources=request.data_sources,
            chart_configurations=request.chart_configurations,
            default_parameters=request.default_parameters,
            export_formats=request.export_formats,
            is_public=request.is_public
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(f"Created template {template.id}: {request.name}")

        return ReportTemplateResponse.model_validate(template)

    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}") from e


@router.get("/templates/{template_id}", response_model=dict[str, Any])
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Get detailed template configuration.

    Returns complete template configuration including layout,
    widgets, styling, and metadata.
    """
    try:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id,
            or_(
                ReportTemplate.created_by == current_user['sub'],
                ReportTemplate.is_public
            )
        ).first()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "template_type": template.template_type,
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat(),
            "layout_configuration": template.layout_configuration,
            "style_configuration": template.style_configuration,
            "page_configuration": template.page_configuration,
            "widgets": template.widgets,
            "data_sources": template.data_sources,
            "chart_configurations": template.chart_configurations,
            "default_parameters": template.default_parameters,
            "required_parameters": template.required_parameters,
            "export_formats": template.export_formats,
            "is_active": template.is_active,
            "is_public": template.is_public,
            "usage_count": template.usage_count,
            "version": template.version
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve template") from e


# Schedule Management Endpoints
@router.get("/schedules/", response_model=list[ReportScheduleResponse])
async def list_schedules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> list[ReportScheduleResponse]:
    """
    Get list of report schedules with filtering and pagination.

    Returns scheduled reports created by the current user
    with optional status filtering.
    """
    try:
        # Build query
        query = db.query(ReportSchedule).filter(ReportSchedule.created_by == current_user['sub'])

        # Apply filters
        if status:
            query = query.filter(ReportSchedule.status == status)

        # Apply pagination
        schedules = query.order_by(desc(ReportSchedule.created_at)).offset(skip).limit(limit).all()

        return [
            ReportScheduleResponse.model_validate(schedule)
            for schedule in schedules
        ]

    except Exception as e:
        logger.error(f"Error listing schedules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schedules") from e


@router.post("/schedules/", response_model=ReportScheduleResponse)
async def create_schedule(
    request: ReportScheduleRequest,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> ReportScheduleResponse:
    """
    Create a new report schedule.

    Creates an automated report generation schedule with
    timing configuration and delivery options.
    """
    try:
        logger.info(f"Creating schedule '{request.name}' for user {current_user['sub']}")

        # Get scheduler service
        scheduler = get_report_scheduler(db)

        # Prepare schedule configuration
        schedule_config = {
            'schedule_type': request.schedule_type,
            'cron_expression': request.cron_expression,
            'interval_minutes': request.interval_minutes,
            'timezone': request.timezone,
            'start_date': request.start_date,
            'end_date': request.end_date,
            'delivery_methods': request.delivery_methods,
            'email_recipients': request.email_recipients,
            'webhook_urls': request.webhook_urls,
            'storage_locations': request.storage_locations,
            'export_formats': request.export_formats,
            'report_config': request.report_configuration or {}
        }

        # Create schedule
        schedule = await scheduler.create_schedule(
            name=request.name,
            template_id=request.template_id,
            schedule_config=schedule_config,
            user_id=current_user['sub']
        )

        return ReportScheduleResponse.model_validate(schedule)

    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}") from e


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def update_schedule(
    schedule_id: int,
    request: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> ReportScheduleResponse:
    """
    Update an existing report schedule.

    Updates schedule configuration including timing,
    delivery methods, and activation status.
    """
    try:
        # Get scheduler service
        scheduler = get_report_scheduler(db)

        # Update schedule
        schedule = await scheduler.update_schedule(
            schedule_id=schedule_id,
            updates=request,
            user_id=current_user['sub']
        )

        return ReportScheduleResponse.model_validate(schedule)

    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}") from e


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """
    Delete a report schedule.

    Removes the schedule and stops automated report generation.
    """
    try:
        # Get scheduler service
        scheduler = get_report_scheduler(db)

        # Delete schedule
        success = await scheduler.delete_schedule(
            schedule_id=schedule_id,
            user_id=current_user['sub']
        )

        if success:
            return {"status": "success", "message": f"Schedule {schedule_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Schedule not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}") from e


# Analytics and Metrics Endpoints
@router.get("/analytics/metrics", response_model=dict[str, Any])
async def get_report_metrics(
    period: str = Query("monthly", description="Aggregation period: daily, weekly, monthly"),
    start_date: datetime | None = Query(None, description="Start date for metrics"),
    end_date: datetime | None = Query(None, description="End date for metrics"),
    db: Session = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Get report generation metrics and analytics.

    Returns comprehensive metrics including generation counts,
    performance statistics, and usage patterns.
    """
    try:
        # Get user's reports for analysis
        query = db.query(Report).filter(Report.generated_by == current_user['sub'])

        if start_date:
            query = query.filter(Report.generated_at >= start_date)
        if end_date:
            query = query.filter(Report.generated_at <= end_date)

        reports = query.all()

        # Calculate metrics
        total_reports = len(reports)
        successful_reports = len([r for r in reports if r.status == "completed"])
        failed_reports = len([r for r in reports if r.status == "failed"])

        avg_generation_time = None
        if successful_reports > 0:
            times = [r.generation_time_seconds for r in reports if r.generation_time_seconds]
            if times:
                avg_generation_time = sum(times) / len(times)

        # Format distribution
        format_usage: dict[str, int] = {}
        for report in reports:
            if report.export_formats:
                for fmt in report.export_formats:  # type: ignore[attr-defined]
                    format_usage[fmt] = format_usage.get(fmt, 0) + 1

        # Template usage
        template_usage: dict[str, int] = {}
        for report in reports:
            if report.template_id:
                template_usage[report.template_id] = template_usage.get(report.template_id, 0) + 1  # type: ignore[index, call-overload]

        return {
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_reports": total_reports,
            "successful_reports": successful_reports,
            "failed_reports": failed_reports,
            "success_rate": (successful_reports / total_reports * 100) if total_reports > 0 else 0,
            "average_generation_time_seconds": avg_generation_time,
            "format_usage": format_usage,
            "template_usage": template_usage
        }

    except Exception as e:
        logger.error(f"Error retrieving report metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics") from e
