"""
Outbreak Pattern Recognition Charts

Advanced visualization charts for outbreak timeline analysis, epidemic curves,
and transmission pattern visualization using data visualization libraries.

Author: AI Agent - Outbreak Pattern Recognition Specialist
"""

from datetime import datetime, timedelta
from typing import Any

import structlog
from pydantic import BaseModel, Field

from ..models import (
    CaseCluster,
    OutbreakEvent,
    SurveillanceData,
    TransmissionPattern,
)

logger = structlog.get_logger(__name__)


class ChartConfiguration(BaseModel):
    """Base configuration for outbreak charts."""
    title: str
    width: int = 800
    height: int = 600
    theme: str = "light"
    interactive: bool = True
    export_formats: list[str] = ["png", "svg", "pdf"]
    color_scheme: str = "viridis"


class OutbreakTimelineChart:
    """
    Timeline chart visualization for outbreak events with event markers.

    Creates comprehensive timeline visualizations showing outbreak progression,
    key events, and intervention timelines with interactive features.
    """

    def __init__(self, config: ChartConfiguration | None = None) -> None:
        """Initialize outbreak timeline chart."""
        self.logger = logger.bind(service="outbreak_timeline_chart")
        self.config = config or ChartConfiguration(title="Outbreak Timeline")

        # Chart styling configuration
        self.styles: dict[str, Any] = {
            "outbreak_severity": {
                "low": {"color": "#28a745", "size": 8},
                "moderate": {"color": "#ffc107", "size": 10},
                "high": {"color": "#fd7e14", "size": 12},
                "critical": {"color": "#dc3545", "size": 14},
                "emergency": {"color": "#6f42c1", "size": 16}
            },
            "event_types": {
                "detection": {"marker": "circle", "color": "#007bff"},
                "peak": {"marker": "triangle", "color": "#dc3545"},
                "intervention": {"marker": "square", "color": "#28a745"},
                "containment": {"marker": "diamond", "color": "#17a2b8"}
            }
        }

        self.logger.info("Outbreak timeline chart initialized", config=self.config.model_dump())

    async def generate_timeline_chart(
        self,
        outbreaks: list[OutbreakEvent],
        surveillance_data: list[SurveillanceData] | None = None,
        time_range_days: int = 365
    ) -> dict[str, Any]:
        """
        Generate comprehensive outbreak timeline chart.

        Args:
            outbreaks: List of outbreak events to visualize
            surveillance_data: Optional surveillance data for context
            time_range_days: Time range for chart in days

        Returns:
            Chart configuration and data for frontend rendering
        """
        operation_id = f"timeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(
            "Generating outbreak timeline chart",
            operation_id=operation_id,
            outbreak_count=len(outbreaks),
            time_range=time_range_days
        )

        try:
            # Prepare timeline data
            timeline_data = await self._prepare_timeline_data(outbreaks, time_range_days)

            # Add surveillance context if available
            if surveillance_data:
                surveillance_context = await self._prepare_surveillance_context(surveillance_data)
                timeline_data["surveillance"] = surveillance_context

            # Generate event annotations
            annotations = await self._generate_event_annotations(outbreaks)

            # Configure chart layout
            layout = await self._configure_timeline_layout(timeline_data)

            # Prepare interactive features
            interactions = await self._configure_timeline_interactions(outbreaks)

            chart_config = {
                "chart_id": f"outbreak_timeline_{operation_id}",
                "type": "timeline",
                "config": self.config.model_dump(),
                "data": timeline_data,
                "layout": layout,
                "annotations": annotations,
                "interactions": interactions,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "outbreak_count": len(outbreaks),
                    "time_range_days": time_range_days
                }
            }

            self.logger.info(
                "Outbreak timeline chart generated successfully",
                operation_id=operation_id,
                data_points=len(timeline_data.get("events", []))
            )

            return chart_config

        except Exception as e:
            self.logger.error(
                "Failed to generate outbreak timeline chart",
                operation_id=operation_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def _prepare_timeline_data(
        self,
        outbreaks: list[OutbreakEvent],
        time_range_days: int
    ) -> dict[str, Any]:
        """Prepare timeline data structure."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)

        # Filter outbreaks to time range
        relevant_outbreaks = [
            outbreak for outbreak in outbreaks
            if outbreak.detection_date >= start_date
        ]

        # Prepare event timeline
        events = []
        for outbreak in relevant_outbreaks:
            # Detection event
            events.append({
                "id": f"{outbreak.outbreak_id}_detection",
                "date": outbreak.detection_date.isoformat(),
                "type": "detection",
                "outbreak_id": outbreak.outbreak_id,
                "title": f"Outbreak Detected: {outbreak.event_name}",
                "severity": outbreak.severity.value,
                "status": outbreak.status.value,
                "cases": outbreak.total_cases,
                "location": {
                    "lat": outbreak.location.coordinates[1],
                    "lon": outbreak.location.coordinates[0]
                },
                "style": self.styles["outbreak_severity"][outbreak.severity.value]
            })

            # Peak event (if available)
            if outbreak.peak_date:
                events.append({
                    "id": f"{outbreak.outbreak_id}_peak",
                    "date": outbreak.peak_date.isoformat(),
                    "type": "peak",
                    "outbreak_id": outbreak.outbreak_id,
                    "title": f"Peak: {outbreak.event_name}",
                    "severity": outbreak.severity.value,
                    "cases": outbreak.total_cases,
                    "style": self.styles["event_types"]["peak"]
                })

            # End event (if available)
            if outbreak.end_date:
                events.append({
                    "id": f"{outbreak.outbreak_id}_end",
                    "date": outbreak.end_date.isoformat(),
                    "type": "containment",
                    "outbreak_id": outbreak.outbreak_id,
                    "title": f"Contained: {outbreak.event_name}",
                    "cases": outbreak.total_cases,
                    "style": self.styles["event_types"]["containment"]
                })

            # Intervention events
            for idx, measure in enumerate(outbreak.response_measures):
                intervention_date = outbreak.detection_date + timedelta(days=idx * 7)
                events.append({
                    "id": f"{outbreak.outbreak_id}_intervention_{idx}",
                    "date": intervention_date.isoformat(),
                    "type": "intervention",
                    "outbreak_id": outbreak.outbreak_id,
                    "title": f"Intervention: {measure}",
                    "intervention": measure,
                    "style": self.styles["event_types"]["intervention"]
                })

        # Sort events by date
        events.sort(key=lambda x: x["date"])

        return {
            "events": events,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "outbreak_count": len(relevant_outbreaks)
        }

    async def _prepare_surveillance_context(
        self,
        surveillance_data: list[SurveillanceData]
    ) -> dict[str, Any]:
        """Prepare surveillance data context for timeline."""
        # Aggregate surveillance data by date
        daily_data: dict[str, Any] = {}

        for data in surveillance_data:
            date_key = data.reported_at.date().isoformat()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "total_cases": 0,
                    "total_tests": 0,
                    "total_population": 0,
                    "alert_level": 0
                }

            daily_data[date_key]["total_cases"] += data.confirmed_cases
            daily_data[date_key]["total_tests"] += data.tests_performed
            daily_data[date_key]["total_population"] += data.population_monitored
            daily_data[date_key]["alert_level"] = max(
                daily_data[date_key]["alert_level"],
                data.alert_level
            )

        # Convert to timeline format
        timeline_data = list(daily_data.values())
        timeline_data.sort(key=lambda x: str(x["date"]))

        return {
            "daily_surveillance": timeline_data,
            "summary": {
                "total_days": len(timeline_data),
                "peak_cases": max([d["total_cases"] for d in timeline_data], default=0),
                "peak_date": max(timeline_data, key=lambda x: int(x["total_cases"]), default={"date": None}).get("date") if timeline_data else None,
                "average_cases": sum([d["total_cases"] for d in timeline_data]) / max(len(timeline_data), 1)
            }
        }

    async def _generate_event_annotations(self, outbreaks: list[OutbreakEvent]) -> list[dict[str, Any]]:
        """Generate chart annotations for key events."""
        annotations = []

        for outbreak in outbreaks:
            # Major outbreak annotation
            if outbreak.severity.value in ["critical", "emergency"]:
                annotation = {
                    "id": f"annotation_{outbreak.outbreak_id}",
                    "type": "text",
                    "x": outbreak.detection_date.isoformat(),
                    "y": outbreak.total_cases,
                    "text": f"CRITICAL: {outbreak.event_name}",
                    "style": {
                        "color": "#dc3545",
                        "font_size": 12,
                        "font_weight": "bold",
                        "background": "#fff3cd",
                        "border": "1px solid #ffeaa7"
                    }
                }
                annotations.append(annotation)

            # Intervention annotations
            if outbreak.response_measures:
                intervention_text = f"Interventions: {', '.join(outbreak.response_measures[:2])}"
                if len(outbreak.response_measures) > 2:
                    intervention_text += f" (+{len(outbreak.response_measures) - 2} more)"

                annotation = {
                    "id": f"intervention_{outbreak.outbreak_id}",
                    "type": "text",
                    "x": outbreak.detection_date.isoformat(),
                    "y": 0,
                    "text": intervention_text,
                    "style": {
                        "color": "#28a745",
                        "font_size": 10,
                        "background": "#d4edda",
                        "border": "1px solid #c3e6cb"
                    }
                }
                annotations.append(annotation)

        return annotations

    async def _configure_timeline_layout(self, timeline_data: dict[str, Any]) -> dict[str, Any]:
        """Configure chart layout and styling."""
        return {
            "title": {
                "text": self.config.title,
                "font": {"size": 16, "weight": "bold"},
                "position": "top"
            },
            "axes": {
                "x": {
                    "title": "Timeline",
                    "type": "datetime",
                    "range": [
                        timeline_data["time_range"]["start"],
                        timeline_data["time_range"]["end"]
                    ],
                    "tick_format": "%Y-%m-%d"
                },
                "y": {
                    "title": "Cases / Event Intensity",
                    "type": "linear",
                    "range": [0, "auto"]
                }
            },
            "legend": {
                "position": "right",
                "items": [
                    {"label": "Detection", "style": self.styles["event_types"]["detection"]},
                    {"label": "Peak", "style": self.styles["event_types"]["peak"]},
                    {"label": "Intervention", "style": self.styles["event_types"]["intervention"]},
                    {"label": "Containment", "style": self.styles["event_types"]["containment"]}
                ]
            },
            "grid": {
                "x": True,
                "y": True,
                "style": {"color": "#e9ecef", "width": 1}
            },
            "margins": {"top": 50, "right": 100, "bottom": 80, "left": 80}
        }

    async def _configure_timeline_interactions(self, outbreaks: list[OutbreakEvent]) -> dict[str, Any]:
        """Configure interactive features for timeline chart."""
        return {
            "hover": {
                "enabled": True,
                "template": """
                <b>{title}</b><br>
                Date: {date}<br>
                Cases: {cases}<br>
                Severity: {severity}<br>
                Status: {status}
                """
            },
            "zoom": {
                "enabled": True,
                "modes": ["x", "y", "xy"]
            },
            "pan": {
                "enabled": True,
                "modes": ["x", "y", "xy"]
            },
            "click": {
                "enabled": True,
                "action": "show_details"
            },
            "brush_select": {
                "enabled": True,
                "mode": "x"
            },
            "export": {
                "enabled": True,
                "formats": self.config.export_formats
            }
        }


class EpidemicCurveChart:
    """
    Epidemic curve visualization showing case progression over time.

    Creates epidemic curve charts with case counts, trends, and
    epidemiological indicators for outbreak analysis.
    """

    def __init__(self, config: ChartConfiguration | None = None) -> None:
        """Initialize epidemic curve chart."""
        self.logger = logger.bind(service="epidemic_curve_chart")
        self.config = config or ChartConfiguration(title="Epidemic Curve")

        self.logger.info("Epidemic curve chart initialized")

    async def generate_epidemic_curve(
        self,
        surveillance_data: list[SurveillanceData],
        outbreak_events: list[OutbreakEvent] | None = None,
        aggregation: str = "daily"
    ) -> dict[str, Any]:
        """
        Generate epidemic curve visualization.

        Args:
            surveillance_data: Surveillance data for curve generation
            outbreak_events: Optional outbreak events for context
            aggregation: Data aggregation level (daily, weekly, monthly)

        Returns:
            Chart configuration for epidemic curve
        """
        operation_id = f"epidemic_curve_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(
            "Generating epidemic curve",
            operation_id=operation_id,
            data_points=len(surveillance_data),
            aggregation=aggregation
        )

        try:
            # Prepare curve data
            curve_data = await self._prepare_curve_data(surveillance_data, aggregation)

            # Add outbreak context
            outbreak_markers = []
            if outbreak_events:
                outbreak_markers = await self._prepare_outbreak_markers(outbreak_events)

            # Calculate trend lines
            trend_lines = await self._calculate_trend_lines(curve_data)

            # Configure layout
            layout = await self._configure_curve_layout(curve_data, aggregation)

            chart_config = {
                "chart_id": f"epidemic_curve_{operation_id}",
                "type": "epidemic_curve",
                "config": self.config.model_dump(),
                "data": {
                    "curve": curve_data,
                    "outbreak_markers": outbreak_markers,
                    "trend_lines": trend_lines
                },
                "layout": layout,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "aggregation": aggregation,
                    "data_points": len(curve_data)
                }
            }

            self.logger.info(
                "Epidemic curve generated successfully",
                operation_id=operation_id
            )

            return chart_config

        except Exception as e:
            self.logger.error(
                "Failed to generate epidemic curve",
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def _prepare_curve_data(
        self,
        surveillance_data: list[SurveillanceData],
        aggregation: str
    ) -> list[dict[str, Any]]:
        """Prepare epidemic curve data."""
        # Group data by time period
        aggregated_data: dict[str, Any] = {}

        for data in surveillance_data:
            # Determine aggregation key
            if aggregation == "daily":
                key = data.reported_at.date().isoformat()
                period = data.reported_at.date()
            elif aggregation == "weekly":
                # Get Monday of the week
                monday = data.reported_at.date() - timedelta(days=data.reported_at.weekday())
                key = monday.isoformat()
                period = monday
            elif aggregation == "monthly":
                key = data.reported_at.strftime("%Y-%m")
                period = data.reported_at.replace(day=1).date()
            else:
                raise ValueError(f"Unsupported aggregation: {aggregation}")

            if key not in aggregated_data:
                aggregated_data[key] = {
                    "period": period.isoformat(),
                    "confirmed_cases": 0,
                    "suspected_cases": 0,
                    "severe_cases": 0,
                    "deaths": 0,
                    "tests_performed": 0,
                    "positive_tests": 0,
                    "population_monitored": 0
                }

            # Aggregate values
            aggregated_data[key]["confirmed_cases"] += data.confirmed_cases
            aggregated_data[key]["suspected_cases"] += data.suspected_cases
            aggregated_data[key]["severe_cases"] += data.severe_cases
            aggregated_data[key]["deaths"] += data.deaths
            aggregated_data[key]["tests_performed"] += data.tests_performed
            aggregated_data[key]["positive_tests"] += data.positive_tests
            aggregated_data[key]["population_monitored"] += data.population_monitored

        # Convert to list and sort
        curve_data = list(aggregated_data.values())
        curve_data.sort(key=lambda x: str(x["period"]))

        # Calculate additional metrics
        for point in curve_data:
            # Case fatality rate
            if point["confirmed_cases"] > 0:
                point["case_fatality_rate"] = point["deaths"] / point["confirmed_cases"]
            else:
                point["case_fatality_rate"] = 0

            # Test positivity rate
            if point["tests_performed"] > 0:
                point["test_positivity_rate"] = point["positive_tests"] / point["tests_performed"]
            else:
                point["test_positivity_rate"] = 0

            # Incidence rate per 100,000
            if point["population_monitored"] > 0:
                point["incidence_rate"] = (point["confirmed_cases"] / point["population_monitored"]) * 100000
            else:
                point["incidence_rate"] = 0

        return curve_data

    async def _prepare_outbreak_markers(self, outbreak_events: list[OutbreakEvent]) -> list[dict[str, Any]]:
        """Prepare outbreak event markers for curve."""
        markers = []

        for outbreak in outbreak_events:
            marker = {
                "id": outbreak.outbreak_id,
                "date": outbreak.detection_date.isoformat(),
                "type": "outbreak_detection",
                "title": outbreak.event_name,
                "severity": outbreak.severity.value,
                "cases": outbreak.total_cases,
                "style": {
                    "color": "#dc3545",
                    "shape": "triangle",
                    "size": 12
                }
            }
            markers.append(marker)

            # Add peak marker if available
            if outbreak.peak_date:
                peak_marker = {
                    "id": f"{outbreak.outbreak_id}_peak",
                    "date": outbreak.peak_date.isoformat(),
                    "type": "outbreak_peak",
                    "title": f"Peak: {outbreak.event_name}",
                    "severity": outbreak.severity.value,
                    "cases": outbreak.total_cases,
                    "style": {
                        "color": "#ffc107",
                        "shape": "star",
                        "size": 14
                    }
                }
                markers.append(peak_marker)

        return markers

    async def _calculate_trend_lines(self, curve_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Calculate trend lines for epidemic curve."""
        if len(curve_data) < 3:
            return []

        trend_lines = []

        # Moving average trend
        window_size = min(7, len(curve_data) // 3)
        if window_size >= 2:
            moving_avg = []
            for i in range(len(curve_data) - window_size + 1):
                window_data = curve_data[i:i + window_size]
                avg_cases = sum(d["confirmed_cases"] for d in window_data) / window_size
                moving_avg.append({
                    "period": curve_data[i + window_size // 2]["period"],
                    "value": avg_cases
                })

            trend_lines.append({
                "id": "moving_average",
                "name": f"{window_size}-period Moving Average",
                "type": "moving_average",
                "data": moving_avg,
                "style": {
                    "color": "#007bff",
                    "width": 2,
                    "dash": "5,5"
                }
            })

        return trend_lines

    async def _configure_curve_layout(
        self,
        curve_data: list[dict[str, Any]],
        aggregation: str
    ) -> dict[str, Any]:
        """Configure epidemic curve layout."""
        return {
            "title": {
                "text": f"Epidemic Curve ({aggregation.title()})",
                "font": {"size": 16, "weight": "bold"}
            },
            "axes": {
                "x": {
                    "title": f"Time ({aggregation.title()})",
                    "type": "datetime"
                },
                "y": {
                    "title": "Number of Cases",
                    "type": "linear",
                    "range": [0, "auto"]
                }
            },
            "series": [
                {
                    "name": "Confirmed Cases",
                    "type": "bar",
                    "y_field": "confirmed_cases",
                    "style": {"color": "#dc3545", "opacity": 0.8}
                },
                {
                    "name": "Suspected Cases",
                    "type": "bar",
                    "y_field": "suspected_cases",
                    "style": {"color": "#ffc107", "opacity": 0.6}
                },
                {
                    "name": "Deaths",
                    "type": "line",
                    "y_field": "deaths",
                    "style": {"color": "#343a40", "width": 2}
                }
            ],
            "legend": {"position": "top"},
            "grid": {"x": True, "y": True}
        }


class TransmissionPatternChart:
    """
    Transmission pattern visualization for spread analysis.

    Creates advanced visualizations for transmission patterns including
    network diagrams, flow maps, and intensity heatmaps.
    """

    def __init__(self, config: ChartConfiguration | None = None) -> None:
        """Initialize transmission pattern chart."""
        self.logger = logger.bind(service="transmission_pattern_chart")
        self.config = config or ChartConfiguration(title="Transmission Patterns")

        self.logger.info("Transmission pattern chart initialized")

    async def generate_transmission_chart(
        self,
        transmission_pattern: TransmissionPattern,
        clusters: list[CaseCluster] | None = None
    ) -> dict[str, Any]:
        """
        Generate transmission pattern visualization.

        Args:
            transmission_pattern: Transmission pattern data
            clusters: Optional case clusters for context

        Returns:
            Chart configuration for transmission pattern visualization
        """
        operation_id = f"transmission_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(
            "Generating transmission pattern chart",
            operation_id=operation_id,
            pattern_id=transmission_pattern.pattern_id
        )

        try:
            # Prepare network visualization
            network_data = await self._prepare_network_data(transmission_pattern)

            # Prepare intensity heatmap
            intensity_data = await self._prepare_intensity_data(transmission_pattern)

            # Add cluster context
            cluster_data = []
            if clusters:
                cluster_data = await self._prepare_cluster_data(clusters)

            # Configure layout
            layout = await self._configure_transmission_layout()

            chart_config = {
                "chart_id": f"transmission_pattern_{operation_id}",
                "type": "transmission_pattern",
                "config": self.config.model_dump(),
                "data": {
                    "network": network_data,
                    "intensity": intensity_data,
                    "clusters": cluster_data,
                    "risk_score": transmission_pattern.transmission_risk_score()
                },
                "layout": layout,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "pattern_id": transmission_pattern.pattern_id,
                    "transmission_mode": transmission_pattern.transmission_mode.value
                }
            }

            self.logger.info(
                "Transmission pattern chart generated successfully",
                operation_id=operation_id
            )

            return chart_config

        except Exception as e:
            self.logger.error(
                "Failed to generate transmission pattern chart",
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def _prepare_network_data(self, pattern: TransmissionPattern) -> dict[str, Any]:
        """Prepare network visualization data."""
        nodes = []
        edges = []

        # Create nodes from hotspots
        for idx, hotspot in enumerate(pattern.hotspot_locations):
            node = {
                "id": f"hotspot_{idx}",
                "type": "hotspot",
                "lat": hotspot.coordinates[1],
                "lon": hotspot.coordinates[0],
                "size": 10,
                "color": "#dc3545",
                "label": f"Hotspot {idx + 1}"
            }
            nodes.append(node)

        # Create edges from transmission networks
        for network in pattern.transmission_networks:
            node_count = network.get("node_count", 0)

            # Create simplified network representation
            for i in range(min(node_count, 10)):  # Limit nodes for visualization
                if i < len(nodes):
                    # Connect to existing nodes
                    for j in range(i + 1, min(i + 3, len(nodes))):
                        edge = {
                            "id": f"edge_{i}_{j}",
                            "source": nodes[i]["id"],
                            "target": nodes[j]["id"],
                            "weight": pattern.connectivity_index,
                            "color": "#007bff",
                            "width": max(1, pattern.connectivity_index * 5)
                        }
                        edges.append(edge)

        return {
            "nodes": nodes,
            "edges": edges,
            "network_metrics": {
                "connectivity": pattern.connectivity_index,
                "clustering": pattern.spatial_clustering,
                "centrality": pattern.centrality_measures
            }
        }

    async def _prepare_intensity_data(self, pattern: TransmissionPattern) -> dict[str, Any]:
        """Prepare transmission intensity heatmap data."""
        # Create intensity grid based on geographic scope
        scope_coords = pattern.geographic_scope.coordinates[0]  # Get first ring of polygon

        # Calculate bounding box
        lats = [coord[1] for coord in scope_coords]
        lons = [coord[0] for coord in scope_coords]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Create grid
        grid_size = 20
        lat_step = (max_lat - min_lat) / grid_size
        lon_step = (max_lon - min_lon) / grid_size

        intensity_grid = []
        for i in range(grid_size):
            for j in range(grid_size):
                lat = min_lat + i * lat_step
                lon = min_lon + j * lon_step

                # Calculate intensity based on distance to hotspots
                intensity = 0.0
                for hotspot in pattern.hotspot_locations:
                    h_lat = hotspot.coordinates[1]
                    h_lon = hotspot.coordinates[0]
                    distance = ((lat - h_lat) ** 2 + (lon - h_lon) ** 2) ** 0.5
                    intensity += max(0, 1 - distance * 100)  # Decay with distance

                intensity = min(intensity, pattern.transmission_intensity)

                intensity_grid.append({
                    "lat": lat,
                    "lon": lon,
                    "intensity": intensity,
                    "color_value": intensity / max(pattern.transmission_intensity, 1)
                })

        return {
            "grid": intensity_grid,
            "bounds": {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon
            },
            "intensity_range": {
                "min": 0,
                "max": pattern.transmission_intensity
            }
        }

    async def _prepare_cluster_data(self, clusters: list[CaseCluster]) -> list[dict[str, Any]]:
        """Prepare cluster data for visualization."""
        cluster_data = []

        for cluster in clusters:
            cluster_info = {
                "id": cluster.cluster_id,
                "centroid": {
                    "lat": cluster.centroid.coordinates[1],
                    "lon": cluster.centroid.coordinates[0]
                },
                "radius_km": cluster.radius_km,
                "case_count": cluster.case_count,
                "relative_risk": cluster.relative_risk,
                "urgency_score": cluster.urgency_score(),
                "cluster_type": cluster.cluster_type.value,
                "style": {
                    "color": "#ffc107" if cluster.relative_risk > 2 else "#28a745",
                    "opacity": min(0.8, cluster.urgency_score()),
                    "border_width": 2
                }
            }
            cluster_data.append(cluster_info)

        return cluster_data

    async def _configure_transmission_layout(self) -> dict[str, Any]:
        """Configure transmission pattern chart layout."""
        return {
            "title": {
                "text": "Transmission Pattern Analysis",
                "font": {"size": 16, "weight": "bold"}
            },
            "panels": [
                {
                    "id": "network",
                    "type": "network",
                    "position": {"x": 0, "y": 0, "width": 0.5, "height": 1},
                    "title": "Transmission Network"
                },
                {
                    "id": "heatmap",
                    "type": "heatmap",
                    "position": {"x": 0.5, "y": 0, "width": 0.5, "height": 1},
                    "title": "Intensity Heatmap"
                }
            ],
            "legend": {
                "position": "bottom",
                "items": [
                    {"label": "High Intensity", "color": "#dc3545"},
                    {"label": "Medium Intensity", "color": "#ffc107"},
                    {"label": "Low Intensity", "color": "#28a745"},
                    {"label": "Transmission Link", "color": "#007bff"}
                ]
            }
        }
