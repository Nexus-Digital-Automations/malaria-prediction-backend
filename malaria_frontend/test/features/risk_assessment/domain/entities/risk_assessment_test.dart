import 'package:flutter_test/flutter_test.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/entities/risk_assessment.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/entities/questionnaire.dart';

void main() {
  group('RiskAssessment Entity Tests', () {
    late RiskAssessment testAssessment;
    late PatientDemographics testDemographics;
    late EnvironmentalRiskFactors testEnvironmentalFactors;
    late List<QuestionnaireResponse> testResponses;
    late List<AssessmentRecommendation> testRecommendations;

    setUp(() {
      testDemographics = const PatientDemographics(
        fullName: 'John Doe',
        dateOfBirth: '1990-01-01',
        age: 33,
        gender: Gender.male,
        phoneNumber: '+1234567890',
        preferredLanguage: 'en',
        travelHistory: [],
        malariaHistory: [],
        currentMedications: [],
        allergies: [],
        chronicConditions: [],
      );

      testEnvironmentalFactors = const EnvironmentalRiskFactors(
        averageTemperature: 25.0,
        rainfallLevel: 150.0,
        vegetationIndex: 0.7,
        waterProximity: 0.5,
        altitude: 1200.0,
        populationDensity: 500.0,
        vectorControlMeasures: [],
      );

      testResponses = [
        QuestionnaireResponse(
          questionId: 'q1',
          selectedOptionIds: ['option1'],
          timestamp: DateTime.now(),
          confidence: 1.0,
        ),
        QuestionnaireResponse(
          questionId: 'q2',
          booleanResponse: true,
          timestamp: DateTime.now(),
          confidence: 0.9,
        ),
      ];

      testRecommendations = [
        const AssessmentRecommendation(
          id: 'rec1',
          type: RecommendationType.prevention,
          priority: RecommendationPriority.high,
          description: 'Use bed nets consistently',
          timeframe: Duration(hours: 24),
          requiredResources: ['Bed nets'],
          followUpActions: ['Monitor compliance'],
        ),
      ];

      testAssessment = RiskAssessment(
        id: 'assessment_123',
        patientId: 'patient_456',
        assessorId: 'provider_789',
        createdAt: DateTime.parse('2023-01-01T12:00:00Z'),
        updatedAt: DateTime.parse('2023-01-01T14:00:00Z'),
        status: AssessmentStatus.completed,
        responses: testResponses,
        riskScore: 0.75,
        riskCategory: RiskCategory.high,
        environmentalFactors: testEnvironmentalFactors,
        demographics: testDemographics,
        recommendations: testRecommendations,
        clinicalNotes: 'Patient reports fever and chills',
        isFollowUp: false,
        language: 'en',
      );
    });

    test('should create RiskAssessment with all required properties', () {
      expect(testAssessment.id, equals('assessment_123'));
      expect(testAssessment.patientId, equals('patient_456'));
      expect(testAssessment.assessorId, equals('provider_789'));
      expect(testAssessment.status, equals(AssessmentStatus.completed));
      expect(testAssessment.riskScore, equals(0.75));
      expect(testAssessment.riskCategory, equals(RiskCategory.high));
      expect(testAssessment.isFollowUp, isFalse);
      expect(testAssessment.language, equals('en'));
    });

    test('should have correct demographics', () {
      expect(testAssessment.demographics.fullName, equals('John Doe'));
      expect(testAssessment.demographics.age, equals(33));
      expect(testAssessment.demographics.gender, equals(Gender.male));
      expect(testAssessment.demographics.preferredLanguage, equals('en'));
    });

    test('should have correct environmental factors', () {
      expect(testAssessment.environmentalFactors.averageTemperature, equals(25.0));
      expect(testAssessment.environmentalFactors.rainfallLevel, equals(150.0));
      expect(testAssessment.environmentalFactors.vegetationIndex, equals(0.7));
      expect(testAssessment.environmentalFactors.waterProximity, equals(0.5));
      expect(testAssessment.environmentalFactors.populationDensity, equals(500.0));
    });

    test('should have questionnaire responses', () {
      expect(testAssessment.responses, hasLength(2));
      expect(testAssessment.responses[0].questionId, equals('q1'));
      expect(testAssessment.responses[0].selectedOptionIds, contains('option1'));
      expect(testAssessment.responses[1].questionId, equals('q2'));
      expect(testAssessment.responses[1].booleanResponse, isTrue);
    });

    test('should have assessment recommendations', () {
      expect(testAssessment.recommendations, hasLength(1));
      expect(testAssessment.recommendations[0].type, equals(RecommendationType.prevention));
      expect(testAssessment.recommendations[0].priority, equals(RecommendationPriority.high));
      expect(testAssessment.recommendations[0].description, equals('Use bed nets consistently'));
    });

    test('should create copyWith correctly', () {
      final updatedAssessment = testAssessment.copyWith(
        status: AssessmentStatus.underReview,
        riskScore: 0.85,
        clinicalNotes: 'Updated notes',
      );

      expect(updatedAssessment.id, equals(testAssessment.id));
      expect(updatedAssessment.status, equals(AssessmentStatus.underReview));
      expect(updatedAssessment.riskScore, equals(0.85));
      expect(updatedAssessment.clinicalNotes, equals('Updated notes'));
      expect(updatedAssessment.patientId, equals(testAssessment.patientId));
    });

    test('should maintain equality with same properties', () {
      final duplicateAssessment = RiskAssessment(
        id: testAssessment.id,
        patientId: testAssessment.patientId,
        assessorId: testAssessment.assessorId,
        createdAt: testAssessment.createdAt,
        updatedAt: testAssessment.updatedAt,
        status: testAssessment.status,
        responses: testAssessment.responses,
        riskScore: testAssessment.riskScore,
        riskCategory: testAssessment.riskCategory,
        environmentalFactors: testAssessment.environmentalFactors,
        demographics: testAssessment.demographics,
        recommendations: testAssessment.recommendations,
        clinicalNotes: testAssessment.clinicalNotes,
        isFollowUp: testAssessment.isFollowUp,
        language: testAssessment.language,
      );

      expect(testAssessment, equals(duplicateAssessment));
      expect(testAssessment.hashCode, equals(duplicateAssessment.hashCode));
    });

    group('AssessmentStatus enum tests', () {
      test('should have all required status values', () {
        expect(AssessmentStatus.values, contains(AssessmentStatus.inProgress));
        expect(AssessmentStatus.values, contains(AssessmentStatus.completed));
        expect(AssessmentStatus.values, contains(AssessmentStatus.underReview));
        expect(AssessmentStatus.values, contains(AssessmentStatus.approved));
        expect(AssessmentStatus.values, contains(AssessmentStatus.needsRevision));
        expect(AssessmentStatus.values, contains(AssessmentStatus.archived));
      });
    });

    group('RiskCategory enum tests', () {
      test('should have all WHO risk categories', () {
        expect(RiskCategory.values, contains(RiskCategory.veryLow));
        expect(RiskCategory.values, contains(RiskCategory.low));
        expect(RiskCategory.values, contains(RiskCategory.moderate));
        expect(RiskCategory.values, contains(RiskCategory.high));
        expect(RiskCategory.values, contains(RiskCategory.veryHigh));
      });
    });

    group('PatientDemographics tests', () {
      test('should handle empty optional lists', () {
        final demographics = PatientDemographics(
          fullName: 'Jane Doe',
          dateOfBirth: DateTime.parse('1985-05-15'),
          age: 38,
          gender: Gender.female,
          preferredLanguage: 'en',
        );

        expect(demographics.travelHistory, isEmpty);
        expect(demographics.malariaHistory, isEmpty);
        expect(demographics.currentMedications, isEmpty);
        expect(demographics.allergies, isEmpty);
        expect(demographics.chronicConditions, isEmpty);
      });

      test('should handle pregnancy status correctly', () {
        final pregnantDemographics = testDemographics.copyWith(
          gender: Gender.female,
          isPregnant: true,
        );

        expect(pregnantDemographics.isPregnant, isTrue);
        expect(pregnantDemographics.gender, equals(Gender.female));
      });
    });

    group('EnvironmentalRiskFactors tests', () {
      test('should handle null environmental values', () {
        const factors = EnvironmentalRiskFactors();

        expect(factors.averageTemperature, isNull);
        expect(factors.rainfallLevel, isNull);
        expect(factors.vegetationIndex, isNull);
        expect(factors.waterProximity, isNull);
        expect(factors.altitude, isNull);
        expect(factors.populationDensity, isNull);
        expect(factors.vectorControlMeasures, isEmpty);
      });

      test('should calculate environmental risk correctly', () {
        const highRiskFactors = EnvironmentalRiskFactors(
          averageTemperature: 28.0, // Optimal for mosquitoes
          rainfallLevel: 250.0, // High rainfall
          vegetationIndex: 0.9, // Dense vegetation
          waterProximity: 0.8, // Very close to water
          populationDensity: 1000.0, // Dense population
        );

        expect(highRiskFactors.averageTemperature, greaterThan(20.0));
        expect(highRiskFactors.rainfallLevel, greaterThan(200.0));
        expect(highRiskFactors.vegetationIndex, greaterThan(0.7));
        expect(highRiskFactors.waterProximity, greaterThan(0.7));
      });
    });

    group('AssessmentRecommendation tests', () {
      test('should create emergency recommendations correctly', () {
        const emergencyRec = AssessmentRecommendation(
          id: 'emergency_1',
          type: RecommendationType.emergency,
          priority: RecommendationPriority.emergency,
          description: 'Immediate diagnostic testing required',
          timeframe: Duration(hours: 2),
          requiredResources: ['RDT kit', 'Healthcare provider'],
          followUpActions: ['Monitor symptoms closely'],
        );

        expect(emergencyRec.type, equals(RecommendationType.emergency));
        expect(emergencyRec.priority, equals(RecommendationPriority.emergency));
        expect(emergencyRec.timeframe.inHours, equals(2));
        expect(emergencyRec.requiredResources, contains('RDT kit'));
      });

      test('should handle prevention recommendations', () {
        const preventionRec = AssessmentRecommendation(
          id: 'prevention_1',
          type: RecommendationType.prevention,
          priority: RecommendationPriority.medium,
          description: 'Use insecticide-treated nets',
          timeframe: Duration(days: 1),
          requiredResources: ['LLIN'],
          followUpActions: ['Weekly compliance check'],
        );

        expect(preventionRec.type, equals(RecommendationType.prevention));
        expect(preventionRec.timeframe.inDays, equals(1));
        expect(preventionRec.requiredResources, contains('LLIN'));
      });
    });

    group('QuestionnaireResponse tests', () {
      test('should handle different response types', () {
        final textResponse = QuestionnaireResponse(
          questionId: 'text_q',
          textResponse: 'Patient reports headache',
          timestamp: DateTime.now(),
          confidence: 0.9,
        );

        final numericResponse = QuestionnaireResponse(
          questionId: 'numeric_q',
          numericResponse: 38.5,
          timestamp: DateTime.now(),
          confidence: 1.0,
        );

        final dateResponse = QuestionnaireResponse(
          questionId: 'date_q',
          dateResponse: DateTime.parse('2023-01-15'),
          timestamp: DateTime.now(),
          confidence: 1.0,
        );

        expect(textResponse.textResponse, equals('Patient reports headache'));
        expect(numericResponse.numericResponse, equals(38.5));
        expect(dateResponse.dateResponse, equals(DateTime.parse('2023-01-15')));
      });

      test('should handle multiple choice responses', () {
        final multiResponse = QuestionnaireResponse(
          questionId: 'multi_q',
          selectedOptionIds: ['option1', 'option3', 'option5'],
          timestamp: DateTime.now(),
          confidence: 0.8,
        );

        expect(multiResponse.selectedOptionIds, hasLength(3));
        expect(multiResponse.selectedOptionIds, contains('option1'));
        expect(multiResponse.selectedOptionIds, contains('option3'));
        expect(multiResponse.selectedOptionIds, contains('option5'));
      });

      test('should include confidence and notes', () {
        final responseWithNotes = QuestionnaireResponse(
          questionId: 'noted_q',
          booleanResponse: true,
          timestamp: DateTime.now(),
          confidence: 0.7,
          notes: 'Patient seemed uncertain about this answer',
        );

        expect(responseWithNotes.confidence, equals(0.7));
        expect(responseWithNotes.notes, equals('Patient seemed uncertain about this answer'));
      });
    });

    group('Malaria episode history tests', () {
      test('should track malaria episodes correctly', () {
        final episode = MalariaEpisode(
          diagnosisDate: DateTime.parse('2022-06-15'),
          species: MalariaSpecies.falciparum,
          treatment: 'Artemether-lumefantrine',
          outcome: TreatmentOutcome.cured,
          complications: ['Severe anemia'],
        );

        expect(episode.species, equals(MalariaSpecies.falciparum));
        expect(episode.treatment, equals('Artemether-lumefantrine'));
        expect(episode.outcome, equals(TreatmentOutcome.cured));
        expect(episode.complications, contains('Severe anemia'));
      });

      test('should handle treatment failures', () {
        final failedEpisode = MalariaEpisode(
          diagnosisDate: DateTime.parse('2022-08-20'),
          species: MalariaSpecies.vivax,
          treatment: 'Chloroquine',
          outcome: TreatmentOutcome.failed,
          complications: ['Treatment resistance'],
        );

        expect(failedEpisode.outcome, equals(TreatmentOutcome.failed));
        expect(failedEpisode.complications, contains('Treatment resistance'));
      });
    });

    group('Travel history tests', () {
      test('should track travel to endemic areas', () {
        final travel = TravelHistory(
          destination: 'Democratic Republic of Congo',
          startDate: DateTime.parse('2023-01-10'),
          endDate: DateTime.parse('2023-01-20'),
          destinationRiskLevel: RiskCategory.veryHigh,
          prophylaxis: 'Atovaquone-proguanil',
        );

        expect(travel.destination, equals('Democratic Republic of Congo'));
        expect(travel.destinationRiskLevel, equals(RiskCategory.veryHigh));
        expect(travel.prophylaxis, equals('Atovaquone-proguanil'));
        expect(travel.endDate.difference(travel.startDate).inDays, equals(10));
      });

      test('should handle travel without prophylaxis', () {
        final unprotectedTravel = TravelHistory(
          destination: 'Ghana',
          startDate: DateTime.parse('2023-02-01'),
          endDate: DateTime.parse('2023-02-14'),
          destinationRiskLevel: RiskCategory.high,
        );

        expect(unprotectedTravel.prophylaxis, isNull);
        expect(unprotectedTravel.destinationRiskLevel, equals(RiskCategory.high));
      });
    });

    group('Vector control interventions tests', () {
      test('should track intervention effectiveness', () {
        const intervention = VectorControlIntervention(
          type: InterventionType.itn,
          coverage: 85.0,
          effectiveness: 0.9,
        );

        expect(intervention.type, equals(InterventionType.itn));
        expect(intervention.coverage, equals(85.0));
        expect(intervention.effectiveness, equals(0.9));
      });

      test('should handle recent interventions', () {
        final recentIntervention = VectorControlIntervention(
          type: InterventionType.irs,
          coverage: 70.0,
          lastImplemented: DateTime.now().subtract(const Duration(days: 30)),
          effectiveness: 0.8,
        );

        expect(recentIntervention.type, equals(InterventionType.irs));
        expect(recentIntervention.lastImplemented, isNotNull);
        expect(recentIntervention.coverage, equals(70.0));
      });
    });

    group('GeoLocation tests', () {
      test('should handle geographic coordinates', () {
        const location = GeoLocation(
          latitude: -1.2921,
          longitude: 36.8219,
          accuracy: 10.0,
          administrativeRegion: 'Nairobi County',
          nearestHealthFacility: 'Kenyatta National Hospital',
        );

        expect(location.latitude, equals(-1.2921));
        expect(location.longitude, equals(36.8219));
        expect(location.accuracy, equals(10.0));
        expect(location.administrativeRegion, equals('Nairobi County'));
        expect(location.nearestHealthFacility, equals('Kenyatta National Hospital'));
      });

      test('should handle minimal location data', () {
        const minimalLocation = GeoLocation(
          latitude: 0.0,
          longitude: 0.0,
        );

        expect(minimalLocation.latitude, equals(0.0));
        expect(minimalLocation.longitude, equals(0.0));
        expect(minimalLocation.accuracy, isNull);
        expect(minimalLocation.administrativeRegion, isNull);
        expect(minimalLocation.nearestHealthFacility, isNull);
      });
    });
  });
}

/// Extension to add copyWith method to PatientDemographics for testing
extension PatientDemographicsTestExtension on PatientDemographics {
  PatientDemographics copyWith({
    String? fullName,
    DateTime? dateOfBirth,
    int? age,
    Gender? gender,
    String? phoneNumber,
    String? email,
    String? address,
    String? nationalId,
    String? insuranceNumber,
    EmergencyContact? emergencyContact,
    String? preferredLanguage,
    String? occupation,
    EducationLevel? educationLevel,
    MaritalStatus? maritalStatus,
    int? householdSize,
    bool? isPregnant,
    List<TravelHistory>? travelHistory,
    List<MalariaEpisode>? malariaHistory,
    List<String>? currentMedications,
    List<String>? allergies,
    List<String>? chronicConditions,
  }) {
    return PatientDemographics(
      fullName: fullName ?? this.fullName,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      age: age ?? this.age,
      gender: gender ?? this.gender,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      email: email ?? this.email,
      address: address ?? this.address,
      nationalId: nationalId ?? this.nationalId,
      insuranceNumber: insuranceNumber ?? this.insuranceNumber,
      emergencyContact: emergencyContact ?? this.emergencyContact,
      preferredLanguage: preferredLanguage ?? this.preferredLanguage,
      occupation: occupation ?? this.occupation,
      educationLevel: educationLevel ?? this.educationLevel,
      maritalStatus: maritalStatus ?? this.maritalStatus,
      householdSize: householdSize ?? this.householdSize,
      isPregnant: isPregnant ?? this.isPregnant,
      travelHistory: travelHistory ?? this.travelHistory,
      malariaHistory: malariaHistory ?? this.malariaHistory,
      currentMedications: currentMedications ?? this.currentMedications,
      allergies: allergies ?? this.allergies,
      chronicConditions: chronicConditions ?? this.chronicConditions,
    );
  }
}