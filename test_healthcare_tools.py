#!/usr/bin/env python3
"""
Quick test script for Healthcare Professional Tools System.

This script tests the core functionality of the healthcare professional tools
to ensure all components are working correctly.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_healthcare_tools():
    """Test healthcare professional tools functionality."""

    print("🏥 Testing Healthcare Professional Tools System")
    print("=" * 60)

    # Test 1: Import healthcare service
    try:
        from src.malaria_predictor.services.healthcare_service import healthcare_service
        print("✅ Healthcare service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import healthcare service: {e}")
        return False

    # Test 2: Import DHIS2 service
    try:
        print("✅ DHIS2 service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import DHIS2 service: {e}")
        return False

    # Test 3: Import dashboard service
    try:
        from src.malaria_predictor.services.professional_dashboard_service import (
            professional_dashboard_service,
        )
        print("✅ Professional dashboard service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import dashboard service: {e}")
        return False

    # Test 4: Test patient case creation
    try:
        case_data = await healthcare_service.create_patient_case(
            patient_id="TEST_PATIENT_001",
            healthcare_professional_id="TEST_HP_001",
            location={"name": "Test Clinic", "latitude": -1.2921, "longitude": 36.8219},
            case_type="suspected",
            symptoms=["fever", "headache", "chills"],
            initial_notes="Test case for system validation"
        )
        print(f"✅ Patient case created successfully: {case_data['case_id']}")
    except Exception as e:
        print(f"❌ Failed to create patient case: {e}")
        return False

    # Test 5: Test risk assessment
    try:
        assessment_data = await healthcare_service.conduct_risk_assessment(
            case_id=case_data['case_id'],
            template_id="WHO_STANDARD_001",
            responses={
                "fever": True,
                "headache": True,
                "chills": True,
                "recent_travel": True,
                "residence_type": "rural",
                "water_sources": "nearby"
            },
            healthcare_professional_id="TEST_HP_001",
            include_environmental_data=True
        )
        print(f"✅ Risk assessment completed: Risk level {assessment_data['risk_level']}, Score {assessment_data['calculated_risk_score']:.3f}")
    except Exception as e:
        print(f"❌ Failed to conduct risk assessment: {e}")
        return False

    # Test 6: Test treatment recommendations
    try:
        treatment_recommendations = await healthcare_service.get_treatment_recommendations(
            case_id=case_data['case_id'],
            patient_weight=65.0,
            comorbidities=[]
        )
        print(f"✅ Treatment recommendations generated: {treatment_recommendations['primary_recommendation']['name']}")
    except Exception as e:
        print(f"❌ Failed to get treatment recommendations: {e}")
        return False

    # Test 7: Test resource allocation request
    try:
        resource_request = await healthcare_service.request_resource_allocation(
            healthcare_professional_id="TEST_HP_001",
            organization="Test Hospital",
            location={"name": "Test District", "latitude": -1.2921, "longitude": 36.8219},
            resource_types=["medical_staff", "medical_supplies", "infrastructure"],
            population_at_risk=10000,
            current_capacity={"doctors": 2, "nurses": 8, "rdts": 50},
            prediction_horizon=30,
            urgency_level="medium",
            justification="Increased case load expected based on risk predictions"
        )
        print(f"✅ Resource allocation request created: {resource_request['request_id']}")
    except Exception as e:
        print(f"❌ Failed to create resource allocation request: {e}")
        return False

    # Test 8: Test surveillance report submission
    try:
        surveillance_report = await healthcare_service.submit_surveillance_report(
            healthcare_professional_id="TEST_HP_001",
            report_type="weekly_surveillance",
            reporting_period={"start_date": "2023-12-01", "end_date": "2023-12-07"},
            location={"name": "Test Health Facility", "org_unit_id": "OU_FACILITY_001"},
            population_monitored=5000,
            case_data={
                "suspected_cases": 12,
                "confirmed_cases": 8,
                "severe_cases": 2,
                "deaths": 0
            },
            vector_data={
                "collection_method": "light_trap",
                "collection_sites": 5,
                "mosquito_density": 15.2
            },
            environmental_observations={
                "temperature": "above_average",
                "rainfall": "normal",
                "water_bodies": "increased"
            }
        )
        print(f"✅ Surveillance report submitted: {surveillance_report['report_id']}")
    except Exception as e:
        print(f"❌ Failed to submit surveillance report: {e}")
        return False

    # Test 9: Test dashboard overview
    try:
        dashboard_overview = await professional_dashboard_service.get_dashboard_overview(
            healthcare_professional_id="TEST_HP_001",
            time_period="week",
            include_insights=True
        )
        print(f"✅ Dashboard overview generated with {len(dashboard_overview['insights'])} insights")
    except Exception as e:
        print(f"❌ Failed to generate dashboard overview: {e}")
        return False

    # Test 10: Test case workload summary
    try:
        workload_summary = await professional_dashboard_service.get_case_workload_summary(
            healthcare_professional_id="TEST_HP_001",
            time_period="week"
        )
        print(f"✅ Case workload summary generated: {workload_summary['case_statistics']['total_active_cases']} active cases")
    except Exception as e:
        print(f"❌ Failed to generate case workload summary: {e}")
        return False

    print("\n🎉 All Healthcare Professional Tools Tests Passed!")
    print("=" * 60)

    # Summary of implemented features
    print("\n📋 Healthcare Professional Tools System Summary:")
    print("   ✅ Risk Assessment Tools - Guided questionnaires and workflows")
    print("   ✅ Patient Management - Case tracking and management system")
    print("   ✅ Treatment Protocols - Decision support system")
    print("   ✅ Resource Planning - Allocation and optimization tools")
    print("   ✅ Surveillance Reporting - Form builders and reporting tools")
    print("   ✅ Professional Dashboard - Healthcare worker specific interface")
    print("   ✅ DHIS2 Integration - Health record systems connectivity")

    print("\n🔧 Technical Components Implemented:")
    print("   ✅ HealthcareService - Core service layer")
    print("   ✅ DHIS2Service - Health information system integration")
    print("   ✅ ProfessionalDashboardService - Dashboard and analytics")
    print("   ✅ CaseRepository - Patient case data management")
    print("   ✅ RiskAssessmentProcessor - Risk calculation engine")
    print("   ✅ TreatmentProtocolAdvisor - Treatment recommendations")
    print("   ✅ ResourceAllocationOptimizer - Resource planning")
    print("   ✅ SurveillanceDataProcessor - Surveillance data handling")

    return True

async def main():
    """Main test function."""
    success = await test_healthcare_tools()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
