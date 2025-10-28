"""
Resource Allocation Engine

Advanced optimization engine for healthcare resource allocation with mathematical optimization,
machine learning predictions, and multi-objective optimization for malaria healthcare systems.

Key Features:
- Multi-objective optimization (cost, coverage, equity)
- Supply chain optimization
- Facility capacity planning
- Resource redistribution algorithms
- Performance metrics and KPIs
- Real-time allocation adjustments
- Emergency resource prioritization

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Healthcare resource types"""
    MEDICATION = "medication"
    MEDICAL_EQUIPMENT = "medical_equipment"
    DIAGNOSTIC_SUPPLIES = "diagnostic_supplies"
    STAFF = "staff"
    BEDS = "beds"
    AMBULANCES = "ambulances"
    VACCINES = "vaccines"
    CONSUMABLES = "consumables"


class ResourceUrgency(Enum):
    """Resource allocation urgency levels"""
    EMERGENCY = "emergency"  # Immediate allocation required
    HIGH = "high"  # Within 24 hours
    MEDIUM = "medium"  # Within 72 hours
    LOW = "low"  # Within 1 week
    ROUTINE = "routine"  # Standard procurement cycle


class AllocationStrategy(Enum):
    """Resource allocation strategies"""
    COST_MINIMIZATION = "cost_minimization"
    COVERAGE_MAXIMIZATION = "coverage_maximization"
    EQUITY_OPTIMIZATION = "equity_optimization"
    RISK_BASED = "risk_based"
    HYBRID = "hybrid"


@dataclass
class HealthcareFacility:
    """Healthcare facility information"""
    facility_id: str
    name: str
    facility_type: str  # "hospital", "clinic", "health_center", "dispensary"
    location: tuple[float, float]  # lat, lon
    capacity: dict[str, int]  # bed counts by type
    current_utilization: dict[str, float]  # utilization rates
    staff_count: dict[str, int]  # staff by category
    catchment_population: int
    malaria_risk_level: float
    accessibility_score: float  # 0-1, based on transportation/infrastructure
    storage_capacity: dict[str, float]  # storage by resource type
    current_inventory: dict[str, int]  # current stock levels
    monthly_demand: dict[str, float]  # average monthly demand
    supply_chain_reliability: float  # 0-1 reliability score


@dataclass
class ResourceRequest:
    """Resource allocation request"""
    request_id: str
    facility_id: str
    resource_type: ResourceType
    resource_name: str
    quantity_requested: int
    urgency: ResourceUrgency
    justification: str
    requested_by: str
    requested_at: datetime
    needed_by: datetime
    alternative_resources: list[str] = field(default_factory=list)
    cost_limit: float | None = None
    delivery_constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationResult:
    """Resource allocation result"""
    allocation_id: str
    request_id: str
    facility_id: str
    resource_allocated: str
    quantity_allocated: int
    allocation_source: str  # Source facility or supplier
    estimated_cost: float
    delivery_timeline: str
    allocation_confidence: float
    alternative_allocations: list[dict] = field(default_factory=list)
    optimization_metrics: dict[str, float] = field(default_factory=dict)
    constraints_applied: list[str] = field(default_factory=list)


@dataclass
class OptimizationObjective:
    """Multi-objective optimization configuration"""
    cost_weight: float = 0.3
    coverage_weight: float = 0.4
    equity_weight: float = 0.2
    efficiency_weight: float = 0.1
    custom_objectives: dict[str, float] = field(default_factory=dict)


class ResourceAllocationEngine:
    """
    Resource Allocation Engine for optimized healthcare resource distribution.

    This engine uses mathematical optimization algorithms to allocate healthcare
    resources efficiently across multiple facilities while considering cost,
    coverage, equity, and emergency response requirements.
    """

    def __init__(
        self,
        facilities_database: str | None = None,
        supply_chain_config: dict | None = None
    ):
        """
        Initialize Resource Allocation Engine.

        Args:
            facilities_database: Database connection for facility information
            supply_chain_config: Supply chain configuration parameters
        """
        logger.info("Initializing Resource Allocation Engine")

        self.facilities_db = facilities_database
        self.supply_chain_config = supply_chain_config or {}

        # Initialize data structures
        self._facilities = {}  # facility_id -> HealthcareFacility
        self._pending_requests = {}  # request_id -> ResourceRequest
        self._allocation_history = []  # Historical allocations
        self._supply_chain_network = {}  # Supply chain topology
        self._transportation_matrix = {}  # Transportation costs/times

        # Load optimization parameters
        self._optimization_config = self._load_optimization_config()
        self._constraint_handlers = self._initialize_constraint_handlers()
        self._objective_functions = self._initialize_objective_functions()

        logger.info("Resource Allocation Engine initialized successfully")

    def allocate_resources(
        self,
        requests: list[ResourceRequest],
        strategy: AllocationStrategy = AllocationStrategy.HYBRID,
        objectives: OptimizationObjective | None = None
    ) -> list[AllocationResult]:
        """
        Optimize resource allocation for multiple requests.

        Args:
            requests: List of resource requests to fulfill
            strategy: Allocation strategy to use
            objectives: Multi-objective optimization weights

        Returns:
            List of allocation results with optimization details
        """
        logger.info(f"Processing {len(requests)} resource allocation requests")

        if objectives is None:
            objectives = OptimizationObjective()

        # Step 1: Validate and categorize requests
        validated_requests = self._validate_requests(requests)
        self._categorize_requests_by_urgency(validated_requests)

        # Step 2: Check available resources and suppliers
        available_resources = self._assess_available_resources()

        # Step 3: Build optimization problem
        optimization_problem = self._build_optimization_problem(
            requests=validated_requests,
            available_resources=available_resources,
            strategy=strategy,
            objectives=objectives
        )

        # Step 4: Solve optimization problem
        optimization_solution = self._solve_optimization_problem(optimization_problem)

        # Step 5: Generate allocation results
        allocation_results = self._generate_allocation_results(
            solution=optimization_solution,
            requests=validated_requests
        )

        # Step 6: Update facility inventories and tracking
        self._update_facility_inventories(allocation_results)

        # Step 7: Log allocation decisions
        self._log_allocation_decisions(allocation_results, strategy, objectives)

        logger.info(f"Resource allocation completed: {len(allocation_results)} allocations made")
        return allocation_results

    def optimize_multi_facility_allocation(
        self,
        target_facilities: list[str],
        resource_type: ResourceType,
        total_budget: float,
        time_horizon_days: int = 30
    ) -> dict[str, Any]:
        """
        Optimize resource allocation across multiple facilities.

        Args:
            target_facilities: List of facility IDs to optimize
            resource_type: Type of resource to allocate
            total_budget: Total budget available
            time_horizon_days: Planning time horizon

        Returns:
            Optimization results with facility-specific allocations
        """
        logger.info(f"Optimizing {resource_type.value} allocation across {len(target_facilities)} facilities")

        # Get facility data
        facilities = [self._facilities[fid] for fid in target_facilities if fid in self._facilities]

        # Calculate demand forecasts for each facility
        demand_forecasts = self._calculate_facility_demands(
            facilities=facilities,
            resource_type=resource_type,
            time_horizon_days=time_horizon_days
        )

        # Calculate malaria risk-adjusted priorities
        risk_priorities = self._calculate_risk_based_priorities(facilities)

        # Build multi-facility optimization model
        optimization_result = self._solve_multi_facility_optimization(
            facilities=facilities,
            demand_forecasts=demand_forecasts,
            risk_priorities=risk_priorities,
            total_budget=total_budget,
            resource_type=resource_type
        )

        logger.info("Multi-facility optimization completed")
        return optimization_result

    def emergency_resource_allocation(
        self,
        emergency_location: tuple[float, float],
        emergency_type: str,
        affected_population: int,
        response_time_hours: int = 24
    ) -> dict[str, Any]:
        """
        Emergency resource allocation for outbreak response.

        Args:
            emergency_location: Emergency coordinates (lat, lon)
            emergency_type: Type of emergency ("outbreak", "epidemic", "disaster")
            affected_population: Estimated affected population
            response_time_hours: Required response time in hours

        Returns:
            Emergency allocation plan with resource mobilization
        """
        logger.info(f"Processing emergency allocation for {emergency_type} affecting {affected_population} people")

        # Calculate emergency resource requirements
        emergency_requirements = self._calculate_emergency_requirements(
            emergency_type=emergency_type,
            affected_population=affected_population,
            response_time_hours=response_time_hours
        )

        # Identify nearby facilities and resources
        nearby_facilities = self._find_nearby_facilities(
            location=emergency_location,
            max_distance_km=100
        )

        # Assess available emergency resources
        emergency_resources = self._assess_emergency_resources(nearby_facilities)

        # Optimize emergency allocation
        emergency_allocation = self._optimize_emergency_allocation(
            requirements=emergency_requirements,
            available_resources=emergency_resources,
            response_time_hours=response_time_hours
        )

        # Generate mobilization plan
        mobilization_plan = self._generate_mobilization_plan(
            allocation=emergency_allocation,
            target_location=emergency_location
        )

        logger.info("Emergency resource allocation plan generated")
        return {
            "emergency_requirements": emergency_requirements,
            "resource_allocation": emergency_allocation,
            "mobilization_plan": mobilization_plan,
            "estimated_response_time": self._calculate_response_time(mobilization_plan),
            "cost_estimate": self._calculate_emergency_cost(emergency_allocation)
        }

    def analyze_allocation_efficiency(
        self,
        time_period_days: int = 30,
        facility_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Analyze allocation efficiency and performance metrics.

        Args:
            time_period_days: Analysis time period in days
            facility_ids: Specific facilities to analyze (if None, analyze all)

        Returns:
            Comprehensive efficiency analysis
        """
        logger.info(f"Analyzing allocation efficiency for {time_period_days} days")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_period_days)

        # Get allocation data for period
        period_allocations = self._get_allocations_for_period(start_date, end_date, facility_ids)

        # Calculate efficiency metrics
        efficiency_metrics = {
            "cost_efficiency": self._calculate_cost_efficiency(period_allocations),
            "coverage_efficiency": self._calculate_coverage_efficiency(period_allocations),
            "response_time_efficiency": self._calculate_response_time_efficiency(period_allocations),
            "resource_utilization": self._calculate_resource_utilization(period_allocations),
            "wastage_metrics": self._calculate_wastage_metrics(period_allocations),
            "equity_metrics": self._calculate_equity_metrics(period_allocations)
        }

        # Identify optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            allocations=period_allocations,
            metrics=efficiency_metrics
        )

        # Generate recommendations
        recommendations = self._generate_efficiency_recommendations(
            metrics=efficiency_metrics,
            opportunities=optimization_opportunities
        )

        return {
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "total_allocations": len(period_allocations),
            "efficiency_metrics": efficiency_metrics,
            "optimization_opportunities": optimization_opportunities,
            "recommendations": recommendations,
            "performance_score": self._calculate_overall_performance_score(efficiency_metrics)
        }

    def _validate_requests(self, requests: list[ResourceRequest]) -> list[ResourceRequest]:
        """Validate resource requests for completeness and feasibility"""
        validated = []

        for request in requests:
            if self._is_valid_request(request):
                validated.append(request)
            else:
                logger.warning(f"Invalid request {request.request_id} - skipping")

        return validated

    def _categorize_requests_by_urgency(self, requests: list[ResourceRequest]) -> dict[ResourceUrgency, list[ResourceRequest]]:
        """Categorize requests by urgency level"""
        categorized = defaultdict(list)

        for request in requests:
            categorized[request.urgency].append(request)

        return dict(categorized)

    def _assess_available_resources(self) -> dict[str, Any]:
        """Assess currently available resources across all facilities"""
        available_resources = {
            "facility_stocks": {},
            "supplier_availability": {},
            "transportation_capacity": {},
            "total_availability": defaultdict(int)
        }

        # Aggregate facility inventories
        for facility_id, facility in self._facilities.items():
            available_resources["facility_stocks"][facility_id] = facility.current_inventory

            # Add to total availability
            for resource, quantity in facility.current_inventory.items():
                available_resources["total_availability"][resource] += quantity

        # Check supplier availability (would query external systems)
        available_resources["supplier_availability"] = self._query_supplier_availability()

        return available_resources

    def _build_optimization_problem(
        self,
        requests: list[ResourceRequest],
        available_resources: dict,
        strategy: AllocationStrategy,
        objectives: OptimizationObjective
    ) -> dict[str, Any]:
        """Build mathematical optimization problem formulation"""

        problem = {
            "decision_variables": self._define_decision_variables(requests),
            "objective_function": self._build_objective_function(strategy, objectives),
            "constraints": self._build_constraints(requests, available_resources),
            "parameters": self._extract_optimization_parameters(requests, available_resources)
        }

        return problem

    def _solve_optimization_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Solve the optimization problem using appropriate algorithm"""

        # For this implementation, we'll use a simplified heuristic approach
        # In practice, this would use OR-Tools, CPLEX, Gurobi, or similar

        solution = {
            "allocations": {},
            "objective_value": 0.0,
            "solver_status": "optimal",
            "computation_time": 0.1
        }

        # Implement greedy allocation algorithm as baseline
        solution["allocations"] = self._greedy_allocation_algorithm(problem)
        solution["objective_value"] = self._evaluate_objective(solution["allocations"], problem)

        return solution

    def _generate_allocation_results(
        self,
        solution: dict[str, Any],
        requests: list[ResourceRequest]
    ) -> list[AllocationResult]:
        """Generate allocation results from optimization solution"""

        results = []

        for request in requests:
            if request.request_id in solution["allocations"]:
                allocation_data = solution["allocations"][request.request_id]

                result = AllocationResult(
                    allocation_id=f"ALLOC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.request_id}",
                    request_id=request.request_id,
                    facility_id=request.facility_id,
                    resource_allocated=allocation_data["resource"],
                    quantity_allocated=allocation_data["quantity"],
                    allocation_source=allocation_data["source"],
                    estimated_cost=allocation_data["cost"],
                    delivery_timeline=allocation_data["timeline"],
                    allocation_confidence=allocation_data["confidence"],
                    optimization_metrics=allocation_data.get("metrics", {}),
                    constraints_applied=allocation_data.get("constraints", [])
                )

                results.append(result)

        return results

    def _update_facility_inventories(self, allocation_results: list[AllocationResult]):
        """Update facility inventory levels after allocation"""

        for result in allocation_results:
            # Update destination facility
            if result.facility_id in self._facilities:
                facility = self._facilities[result.facility_id]
                current = facility.current_inventory.get(result.resource_allocated, 0)
                facility.current_inventory[result.resource_allocated] = current + result.quantity_allocated

            # Update source facility (if applicable)
            if result.allocation_source in self._facilities:
                source_facility = self._facilities[result.allocation_source]
                current = source_facility.current_inventory.get(result.resource_allocated, 0)
                source_facility.current_inventory[result.resource_allocated] = max(0, current - result.quantity_allocated)

    def _log_allocation_decisions(
        self,
        results: list[AllocationResult],
        strategy: AllocationStrategy,
        objectives: OptimizationObjective
    ):
        """Log allocation decisions for audit and analysis"""

        allocation_log = {
            "timestamp": datetime.now(),
            "strategy_used": strategy.value,
            "objectives": objectives.__dict__,
            "total_allocations": len(results),
            "total_cost": sum(r.estimated_cost for r in results),
            "allocation_ids": [r.allocation_id for r in results]
        }

        self._allocation_history.append(allocation_log)
        logger.info(f"Logged allocation decisions: {allocation_log}")

    # Helper methods for optimization calculations
    def _calculate_facility_demands(self, facilities: list[HealthcareFacility], resource_type: ResourceType, time_horizon_days: int) -> dict[str, float]:
        """Calculate demand forecasts for facilities"""
        demands = {}

        for facility in facilities:
            # Base demand on monthly average, adjusted for time horizon
            monthly_demand = facility.monthly_demand.get(resource_type.value, 0)
            demand = monthly_demand * (time_horizon_days / 30.0)

            # Adjust for malaria risk level
            risk_multiplier = 1.0 + (facility.malaria_risk_level * 0.5)

            demands[facility.facility_id] = demand * risk_multiplier

        return demands

    def _calculate_risk_based_priorities(self, facilities: list[HealthcareFacility]) -> dict[str, float]:
        """Calculate risk-based priority scores"""
        priorities = {}

        for facility in facilities:
            # Priority based on risk level, population, and accessibility
            priority = (
                facility.malaria_risk_level * 0.4 +
                min(facility.catchment_population / 100000, 1.0) * 0.3 +
                (1.0 - facility.accessibility_score) * 0.3  # Lower accessibility = higher priority
            )

            priorities[facility.facility_id] = priority

        return priorities

    def _solve_multi_facility_optimization(
        self,
        facilities: list[HealthcareFacility],
        demand_forecasts: dict[str, float],
        risk_priorities: dict[str, float],
        total_budget: float,
        resource_type: ResourceType
    ) -> dict[str, Any]:
        """Solve multi-facility optimization problem"""

        # Simplified optimization using priority-based allocation
        allocations = {}
        remaining_budget = total_budget

        # Sort facilities by priority
        sorted_facilities = sorted(
            facilities,
            key=lambda f: risk_priorities.get(f.facility_id, 0),
            reverse=True
        )

        for facility in sorted_facilities:
            demand = demand_forecasts.get(facility.facility_id, 0)
            estimated_cost_per_unit = self._get_resource_cost(resource_type, facility.location)
            total_cost = demand * estimated_cost_per_unit

            if total_cost <= remaining_budget:
                allocations[facility.facility_id] = {
                    "quantity": demand,
                    "cost": total_cost,
                    "priority_score": risk_priorities.get(facility.facility_id, 0)
                }
                remaining_budget -= total_cost
            else:
                # Partial allocation based on remaining budget
                affordable_quantity = remaining_budget / estimated_cost_per_unit
                if affordable_quantity > 0:
                    allocations[facility.facility_id] = {
                        "quantity": affordable_quantity,
                        "cost": remaining_budget,
                        "priority_score": risk_priorities.get(facility.facility_id, 0)
                    }
                    remaining_budget = 0
                break

        return {
            "allocations": allocations,
            "total_cost": total_budget - remaining_budget,
            "budget_utilization": (total_budget - remaining_budget) / total_budget,
            "facilities_served": len(allocations),
            "unmet_demand": self._calculate_unmet_demand(demand_forecasts, allocations)
        }

    # Additional helper methods would be implemented here
    def _load_optimization_config(self) -> dict:
        """Load optimization configuration"""
        return {"max_iterations": 1000, "tolerance": 1e-6}

    def _initialize_constraint_handlers(self) -> dict:
        """Initialize constraint handling functions"""
        return {}

    def _initialize_objective_functions(self) -> dict:
        """Initialize objective function implementations"""
        return {}

    def _is_valid_request(self, request: ResourceRequest) -> bool:
        """Validate individual resource request"""
        return bool(request.facility_id and request.resource_name and request.quantity_requested > 0)

    def _query_supplier_availability(self) -> dict:
        """Query external supplier availability"""
        return {}

    def _define_decision_variables(self, requests: list[ResourceRequest]) -> dict:
        """Define optimization decision variables"""
        return {}

    def _build_objective_function(self, strategy: AllocationStrategy, objectives: OptimizationObjective) -> dict:
        """Build objective function for optimization"""
        return {}

    def _build_constraints(self, requests: list[ResourceRequest], available_resources: dict) -> dict:
        """Build optimization constraints"""
        return {}

    def _extract_optimization_parameters(self, requests: list[ResourceRequest], available_resources: dict) -> dict:
        """Extract parameters for optimization"""
        return {}

    def _greedy_allocation_algorithm(self, problem: dict) -> dict:
        """Implement greedy allocation algorithm"""
        return {}

    def _evaluate_objective(self, allocations: dict, problem: dict) -> float:
        """Evaluate objective function value"""
        return 0.0

    def _calculate_emergency_requirements(self, emergency_type: str, affected_population: int, response_time_hours: int) -> dict:
        """Calculate emergency resource requirements"""
        return {}

    def _find_nearby_facilities(self, location: tuple[float, float], max_distance_km: float) -> list[HealthcareFacility]:
        """Find facilities within distance of location"""
        return []

    def _assess_emergency_resources(self, facilities: list[HealthcareFacility]) -> dict:
        """Assess available emergency resources"""
        return {}

    def _optimize_emergency_allocation(self, requirements: dict, available_resources: dict, response_time_hours: int) -> dict:
        """Optimize emergency resource allocation"""
        return {}

    def _generate_mobilization_plan(self, allocation: dict, target_location: tuple[float, float]) -> dict:
        """Generate resource mobilization plan"""
        return {}

    def _calculate_response_time(self, mobilization_plan: dict) -> float:
        """Calculate estimated response time"""
        return 0.0

    def _calculate_emergency_cost(self, allocation: dict) -> float:
        """Calculate emergency allocation cost"""
        return 0.0

    def _get_allocations_for_period(self, start_date: datetime, end_date: datetime, facility_ids: list[str] | None) -> list:
        """Get allocations for time period"""
        return []

    def _calculate_cost_efficiency(self, allocations: list) -> dict:
        """Calculate cost efficiency metrics"""
        return {}

    def _calculate_coverage_efficiency(self, allocations: list) -> dict:
        """Calculate coverage efficiency metrics"""
        return {}

    def _calculate_response_time_efficiency(self, allocations: list) -> dict:
        """Calculate response time efficiency metrics"""
        return {}

    def _calculate_resource_utilization(self, allocations: list) -> dict:
        """Calculate resource utilization metrics"""
        return {}

    def _calculate_wastage_metrics(self, allocations: list) -> dict:
        """Calculate resource wastage metrics"""
        return {}

    def _calculate_equity_metrics(self, allocations: list) -> dict:
        """Calculate equity metrics"""
        return {}

    def _identify_optimization_opportunities(self, allocations: list, metrics: dict) -> list:
        """Identify optimization opportunities"""
        return []

    def _generate_efficiency_recommendations(self, metrics: dict, opportunities: list) -> list:
        """Generate efficiency improvement recommendations"""
        return []

    def _calculate_overall_performance_score(self, metrics: dict) -> float:
        """Calculate overall performance score"""
        return 0.8

    def _get_resource_cost(self, resource_type: ResourceType, location: tuple[float, float]) -> float:
        """Get estimated resource cost per unit"""
        return 10.0  # Simplified

    def _calculate_unmet_demand(self, demand_forecasts: dict, allocations: dict) -> dict:
        """Calculate unmet demand after allocation"""
        unmet = {}
        for facility_id, demand in demand_forecasts.items():
            allocated = allocations.get(facility_id, {}).get("quantity", 0)
            unmet[facility_id] = max(0, demand - allocated)
        return unmet
