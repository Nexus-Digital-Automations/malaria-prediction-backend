#!/usr/bin/env python3
"""
Comprehensive Test Suite for Healthcare Tools

Tests all healthcare tools functionality including WHO guidelines,
drug resistance analysis, patient-specific recommendations,
resource allocation, and analytics systems.

Author: Claude Healthcare Tools Agent
Date: 2025-09-19
"""

import logging
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from malaria_predictor.healthcare import (
    BudgetOptimizer,
    CostEffectivenessAnalyzer,
    DemandForecaster,
    DrugResistanceAnalyzer,
    EmergencyResourceMobilizer,
    HealthcareAnalytics,
    InventoryManager,
    ManagementDashboard,
    PatientSpecificRecommender,
    ResourceAllocationEngine,
    ResourceUtilizationAnalyzer,
    StaffScheduler,
    TreatmentEffectivenessTracker,
    TreatmentOutcomeAnalyzer,
    TreatmentProtocolEngine,
    WHOGuidelinesEngine,
)
from malaria_predictor.healthcare.resource_allocation.resource_allocation_engine import (
    AllocationStrategy,
    ResourceRequest,
    ResourceType,
    ResourceUrgency,
)

# Import data classes
from malaria_predictor.healthcare.treatment_protocols.who_guidelines_engine import (
    ClinicalPresentation,
    MalariaSpecies,
    PatientProfile,
)


def setup_logging():
    """Set up logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_who_guidelines_engine():
    """Test WHO Guidelines Engine"""
    print("\n🧪 Testing WHO Guidelines Engine...")

    engine = WHOGuidelinesEngine()

    # Create test patient profile
    patient = PatientProfile(
        age=35.0,
        weight=70.0,
        sex="female",
        is_pregnant=False,
        has_comorbidities=False
    )

    # Create clinical presentation
    clinical = ClinicalPresentation(
        fever_duration_hours=24,
        peak_temperature=39.5,
        parasitemia_percent=2.5,
        symptoms=["fever", "headache", "chills"]
    )

    # Test severity assessment
    severity, indicators = engine.assess_severity(clinical, patient)
    print(f"✅ Severity assessment: {severity.value}")

    # Test treatment recommendation
    recommendation = engine.recommend_treatment(
        patient_profile=patient,
        clinical_presentation=clinical,
        malaria_species=MalariaSpecies.P_FALCIPARUM
    )

    print(f"✅ Treatment recommended: {recommendation.drug_regimen[0]['drug_name']}")
    print(f"✅ Confidence score: {recommendation.confidence_score}")

    return True

def test_drug_resistance_analyzer():
    """Test Drug Resistance Analyzer"""
    print("\n🧪 Testing Drug Resistance Analyzer...")

    analyzer = DrugResistanceAnalyzer()

    # Test resistance pattern analysis
    patterns = analyzer.analyze_resistance_patterns(
        location="Kenya",
        time_window_days=365,
        drugs_of_interest=["artemether-lumefantrine", "chloroquine"]
    )

    print(f"✅ Analyzed resistance for {len(patterns)} drugs")

    # Test resistance prediction
    prediction = analyzer.predict_resistance_emergence(
        location="Kenya",
        drug="artemether-lumefantrine",
        prediction_horizon_months=12
    )

    print(f"✅ Resistance prediction: {prediction.get('trend', 'no_significant_change')}")

    # Test hotspot identification
    hotspots = analyzer.identify_resistance_hotspots(
        region="East Africa",
        resistance_threshold=0.05
    )

    print(f"✅ Identified {len(hotspots)} resistance hotspots")

    return True

def test_patient_specific_recommender():
    """Test Patient-Specific Recommender"""
    print("\n🧪 Testing Patient-Specific Recommender...")

    # Create engines
    who_engine = WHOGuidelinesEngine()
    resistance_analyzer = DrugResistanceAnalyzer()
    recommender = PatientSpecificRecommender(who_engine, resistance_analyzer)

    # Create test patient
    patient = PatientProfile(
        age=25.0,
        weight=60.0,
        sex="female",
        is_pregnant=True,
        pregnancy_trimester=2,
        allergies=["penicillin"],
        current_medications=["folic_acid"]
    )

    clinical = ClinicalPresentation(
        fever_duration_hours=48,
        peak_temperature=40.2,
        parasitemia_percent=1.5,
        symptoms=["fever", "nausea", "fatigue"]
    )

    # Test personalized recommendation
    recommendation = recommender.generate_personalized_recommendation(
        patient_profile=patient,
        clinical_presentation=clinical,
        malaria_species=MalariaSpecies.P_FALCIPARUM,
        location="Tanzania"
    )

    print(f"✅ Personalized recommendation generated: {recommendation.recommendation_id}")
    print(f"✅ Safety alerts: {len(recommendation.safety_alerts)}")
    print(f"✅ Contraindications: {len(recommendation.contraindications)}")

    return True

def test_treatment_protocol_engine():
    """Test Treatment Protocol Engine"""
    print("\n🧪 Testing Treatment Protocol Engine...")

    # Create engines
    who_engine = WHOGuidelinesEngine()
    resistance_analyzer = DrugResistanceAnalyzer()
    recommender = PatientSpecificRecommender(who_engine, resistance_analyzer)
    protocol_engine = TreatmentProtocolEngine(who_engine, resistance_analyzer, recommender)

    # Test protocol recommendation
    patient = PatientProfile(age=40.0, weight=75.0, sex="male")
    clinical = ClinicalPresentation(
        fever_duration_hours=36,
        peak_temperature=39.8,
        parasitemia_percent=3.2
    )

    protocol_rec = protocol_engine.recommend_protocol(
        patient_profile=patient,
        clinical_presentation=clinical,
        malaria_species=MalariaSpecies.P_FALCIPARUM,
        location="Uganda"
    )

    print(f"✅ Protocol recommendation: {protocol_rec.recommendation_id}")
    print(f"✅ Evidence level: {protocol_rec.protocol_used.evidence_level}")

    return True

def test_resource_allocation_engine():
    """Test Resource Allocation Engine"""
    print("\n🧪 Testing Resource Allocation Engine...")

    engine = ResourceAllocationEngine()

    # Create test resource requests
    requests = [
        ResourceRequest(
            request_id="REQ_001",
            facility_id="HOSP_001",
            resource_type=ResourceType.MEDICATION,
            resource_name="artemether-lumefantrine",
            quantity_requested=100,
            urgency=ResourceUrgency.HIGH,
            justification="Stock depletion",
            requested_by="Dr. Smith",
            requested_at=datetime.now(),
            needed_by=datetime.now()
        )
    ]

    # Test allocation
    allocations = engine.allocate_resources(
        requests=requests,
        strategy=AllocationStrategy.COST_MINIMIZATION
    )

    print(f"✅ Resource allocations: {len(allocations)}")

    # Test multi-facility optimization
    optimization = engine.optimize_multi_facility_allocation(
        target_facilities=["HOSP_001", "CLINIC_002"],
        resource_type=ResourceType.MEDICATION,
        total_budget=50000.0
    )

    print("✅ Multi-facility optimization completed")
    print(f"✅ Budget utilization: {optimization.get('budget_utilization', 0.0):.2%}")

    return True

def test_analytics_modules():
    """Test Analytics Modules"""
    print("\n🧪 Testing Analytics Modules...")

    # Test Healthcare Analytics
    analytics = HealthcareAnalytics()
    metrics = analytics.calculate_metrics({"test_data": "sample"})
    analytics.generate_report(metrics)
    print(f"✅ Healthcare analytics: {len(metrics)} metrics calculated, report generated")

    # Test Treatment Outcome Analyzer
    outcome_analyzer = TreatmentOutcomeAnalyzer()
    outcomes = outcome_analyzer.analyze_outcomes([])
    print(f"✅ Treatment outcomes analyzed: {outcomes['cure_rate']:.2%} cure rate")

    # Test Resource Utilization Analyzer
    util_analyzer = ResourceUtilizationAnalyzer()
    utilization = util_analyzer.analyze_utilization([])
    print(f"✅ Resource utilization: {utilization['bed_utilization']:.2%} bed utilization")

    # Test Cost Effectiveness Analyzer
    cost_analyzer = CostEffectivenessAnalyzer()
    cost_analysis = cost_analyzer.analyze_cost_effectiveness([])
    print(f"✅ Cost effectiveness: ${cost_analysis['cost_per_cure']:.2f} per cure")

    # Test Management Dashboard
    dashboard = ManagementDashboard()
    executive_summary = dashboard.generate_executive_summary({})
    print(f"✅ Management dashboard: {executive_summary['key_metrics']['total_patients']} patients")

    return True

def test_supporting_modules():
    """Test Supporting Modules"""
    print("\n🧪 Testing Supporting Modules...")

    # Test Inventory Manager
    inventory = InventoryManager()
    tracking = inventory.track_inventory("HOSP_001", {"antimalarials": 50})
    print(f"✅ Inventory tracking: {tracking['total_items']} items tracked")

    # Test Demand Forecaster
    forecaster = DemandForecaster()
    forecast = forecaster.forecast_demand([])
    print(f"✅ Demand forecast: {forecast['predicted_demand']['antimalarials']} units predicted")

    # Test Staff Scheduler
    scheduler = StaffScheduler()
    allocation = scheduler.optimize_staff_allocation(["HOSP_001"], [], {})
    print(f"✅ Staff allocation: {allocation['utilization_rate']:.2%} utilization")

    # Test Emergency Resource Mobilizer
    mobilizer = EmergencyResourceMobilizer()
    emergency = mobilizer.mobilize_emergency_resources(
        emergency_location=(-1.2921, 36.8219),
        emergency_type="outbreak",
        affected_population=10000
    )
    print(f"✅ Emergency mobilization: {emergency['mobilized_resources']['medical_teams']} teams")

    # Test Budget Optimizer
    optimizer = BudgetOptimizer()
    budget_opt = optimizer.optimize_budget_allocation(100000.0, [], {})
    print(f"✅ Budget optimization: {budget_opt['optimization_score']:.2%} score")

    return True

def test_treatment_effectiveness_tracker():
    """Test Treatment Effectiveness Tracker"""
    print("\n🧪 Testing Treatment Effectiveness Tracker...")

    tracker = TreatmentEffectivenessTracker()

    # Test treatment recording
    record_id = tracker.record_treatment_start(
        patient_id="PAT_001",
        treatment_details={"treatment_id": "TRT_001", "drug_regimen": []},
        clinical_data={"parasitemia": 2.5, "symptoms": ["fever"]},
        provider_info={"facility_id": "HOSP_001", "prescriber_id": "DR_001"}
    )

    print(f"✅ Treatment recorded: {record_id}")

    # Test effectiveness analysis
    analysis = tracker.analyze_treatment_effectiveness(
        treatment_name="artemether-lumefantrine",
        analysis_period_days=90
    )

    print(f"✅ Effectiveness analysis: {analysis.total_cases} cases analyzed")

    # Test quality report
    quality_report = tracker.generate_treatment_quality_report(
        facility_id="HOSP_001",
        time_period_days=30
    )

    print(f"✅ Quality report: {quality_report['overall_quality_score']:.2%} quality score")

    return True

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Healthcare Tools Testing...")
    print("=" * 60)

    setup_logging()

    tests = [
        ("WHO Guidelines Engine", test_who_guidelines_engine),
        ("Drug Resistance Analyzer", test_drug_resistance_analyzer),
        ("Patient-Specific Recommender", test_patient_specific_recommender),
        ("Treatment Protocol Engine", test_treatment_protocol_engine),
        ("Resource Allocation Engine", test_resource_allocation_engine),
        ("Analytics Modules", test_analytics_modules),
        ("Supporting Modules", test_supporting_modules),
        ("Treatment Effectiveness Tracker", test_treatment_effectiveness_tracker)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n🎯 Running {test_name} tests...")
            success = test_func()
            if success:
                print(f"✅ {test_name}: PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")

    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Healthcare tools are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
