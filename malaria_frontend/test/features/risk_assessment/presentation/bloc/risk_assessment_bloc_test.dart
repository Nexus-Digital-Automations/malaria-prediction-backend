import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dartz/dartz.dart';

import 'package:malaria_frontend/features/risk_assessment/domain/repositories/risk_assessment_repository.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/usecases/conduct_risk_assessment.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/entities/questionnaire.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/entities/risk_assessment.dart';
import 'package:malaria_frontend/features/risk_assessment/domain/entities/risk_scoring.dart';
import 'package:malaria_frontend/features/risk_assessment/presentation/bloc/risk_assessment_bloc.dart';
import 'package:malaria_frontend/features/risk_assessment/presentation/bloc/risk_assessment_event.dart';
import 'package:malaria_frontend/features/risk_assessment/presentation/bloc/risk_assessment_state.dart';
import 'package:malaria_frontend/core/errors/failures.dart';

import 'risk_assessment_bloc_test.mocks.dart';

// Generate mocks
@GenerateMocks([
  RiskAssessmentRepository,
  QuestionnaireRepository,
  RiskScoringRepository,
  ConductRiskAssessment,
])
void main() {
  group('RiskAssessmentBloc Tests', () {
    late RiskAssessmentBloc bloc;
    late MockRiskAssessmentRepository mockRiskAssessmentRepository;
    late MockQuestionnaireRepository mockQuestionnaireRepository;
    late MockRiskScoringRepository mockRiskScoringRepository;
    late MockConductRiskAssessment mockConductRiskAssessment;

    // Test data
    late Questionnaire testQuestionnaire;
    late QuestionnaireSession testSession;
    late PatientDemographics testDemographics;
    late EnvironmentalRiskFactors testEnvironmentalFactors;
    late RiskScore testRiskScore;
    late RiskAssessment testAssessment;

    setUp(() {
      mockRiskAssessmentRepository = MockRiskAssessmentRepository();
      mockQuestionnaireRepository = MockQuestionnaireRepository();
      mockRiskScoringRepository = MockRiskScoringRepository();
      mockConductRiskAssessment = MockConductRiskAssessment();

      bloc = RiskAssessmentBloc(
        riskAssessmentRepository: mockRiskAssessmentRepository,
        questionnaireRepository: mockQuestionnaireRepository,
        scoringRepository: mockRiskScoringRepository,
        conductRiskAssessment: mockConductRiskAssessment,
      );

      // Setup test data
      _setupTestData();
    });

    void _setupTestData() {
      testDemographics = const PatientDemographics(
        fullName: 'Test Patient',
        dateOfBirth: '1990-01-01',
        age: 33,
        gender: Gender.male,
        preferredLanguage: 'en',
      );

      testEnvironmentalFactors = const EnvironmentalRiskFactors(
        averageTemperature: 25.0,
        rainfallLevel: 150.0,
        vegetationIndex: 0.7,
        waterProximity: 0.5,
        populationDensity: 500.0,
      );

      testQuestionnaire = Questionnaire(
        id: 'questionnaire_1',
        title: 'Malaria Risk Assessment',
        description: 'Comprehensive malaria risk evaluation',
        version: '1.0',
        language: 'en',
        questions: [
          const Question(
            id: 'q1',
            text: 'Do you have fever?',
            type: QuestionType.boolean,
            isRequired: true,
            order: 1,
            category: QuestionnaireCategory.symptoms,
            answerOptions: [],
            riskWeight: 0.8,
            branchingRules: [],
          ),
          const Question(
            id: 'q2',
            text: 'What is your age?',
            type: QuestionType.number,
            isRequired: true,
            order: 2,
            category: QuestionnaireCategory.demographics,
            answerOptions: [],
            riskWeight: 0.3,
            branchingRules: [],
          ),
        ],
        conditionalRules: [],
        guidelineVersion: 'WHO 2023',
        targetPopulation: TargetPopulation.adults,
        estimatedDurationMinutes: 15,
        categories: [QuestionnaireCategory.symptoms, QuestionnaireCategory.demographics],
        createdAt: DateTime.parse('2023-01-01'),
        updatedAt: DateTime.parse('2023-01-01'),
      );

      testSession = QuestionnaireSession(
        id: 'session_1',
        questionnaireId: 'questionnaire_1',
        subjectId: 'patient_1',
        providerId: 'provider_1',
        startTime: DateTime.now(),
        progress: 0.0,
        responses: [],
        status: SessionStatus.inProgress,
      );

      testRiskScore = const RiskScore(
        totalScore: 0.75,
        category: RiskCategory.high,
        clinicalScore: 0.8,
        environmentalScore: 0.7,
        demographicScore: 0.6,
        behavioralScore: 0.5,
        seasonalMultiplier: 1.2,
        geographicMultiplier: 1.0,
        contributingFactors: [],
        confidenceLevel: 0.9,
        calculatedAt: '2023-01-01T12:00:00Z',
        algorithmVersion: '1.0',
      );

      testAssessment = RiskAssessment(
        id: 'assessment_1',
        patientId: 'patient_1',
        assessorId: 'provider_1',
        createdAt: DateTime.parse('2023-01-01'),
        updatedAt: DateTime.parse('2023-01-01'),
        status: AssessmentStatus.completed,
        responses: [],
        riskScore: 0.75,
        riskCategory: RiskCategory.high,
        environmentalFactors: testEnvironmentalFactors,
        demographics: testDemographics,
        recommendations: [],
      );
    }

    tearDown(() {
      bloc.close();
    });

    test('initial state should be RiskAssessmentInitial', () {
      expect(bloc.state, equals(const RiskAssessmentInitial()));
    });

    group('InitializeRiskAssessment', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [RiskAssessmentInitializing, AssessmentSessionReady] when initialization succeeds',
        build: () {
          when(mockQuestionnaireRepository.getQuestionnaires(
            targetPopulation: any(named: 'targetPopulation'),
            language: any(named: 'language'),
          )).thenAnswer((_) async => Right([testQuestionnaire]));

          when(mockRiskScoringRepository.getRiskScoringEngine())
              .thenAnswer((_) async => const Right(RiskScoringEngine(
                whoGuidelineVersion: 'WHO 2023',
                algorithmVersion: '1.0',
                lastUpdated: '2023-01-01',
                clinicalFactors: ClinicalRiskFactors(
                  symptomWeights: {},
                  historyWeights: {},
                  examinationWeights: {},
                ),
                environmentalFactors: EnvironmentalRiskFactors(),
                demographicFactors: DemographicRiskFactors(
                  ageRiskCurve: {},
                  pregnancyRiskWeight: 0.8,
                  occupationWeights: {},
                  travelWeights: {},
                ),
                behavioralFactors: BehavioralRiskFactors(
                  preventionWeights: {},
                  exposureWeights: {},
                  healthcareWeights: {},
                ),
                seasonalAdjustments: SeasonalAdjustments(
                  seasonalMultipliers: {},
                  monthlyMultipliers: {},
                ),
                geographicModifiers: GeographicRiskModifiers(
                  altitudeModifiers: {},
                  regionalCoefficients: {},
                  settingModifiers: {},
                ),
              )));

          return bloc;
        },
        act: (bloc) => bloc.add(const InitializeRiskAssessment(
          patientId: 'patient_1',
          assessorId: 'provider_1',
          targetPopulation: TargetPopulation.adults,
          language: 'en',
        )),
        expect: () => [
          isA<RiskAssessmentInitializing>()
              .having((state) => state.patientId, 'patientId', 'patient_1')
              .having((state) => state.progress, 'progress', 0.0),
          isA<RiskAssessmentInitializing>()
              .having((state) => state.progress, 'progress', 0.2),
          isA<RiskAssessmentInitializing>()
              .having((state) => state.progress, 'progress', 0.5),
          isA<RiskAssessmentInitializing>()
              .having((state) => state.progress, 'progress', 0.8),
          isA<AssessmentSessionReady>()
              .having((state) => state.questionnaire.id, 'questionnaire.id', 'questionnaire_1')
              .having((state) => state.availableQuestionnaires.length, 'availableQuestionnaires.length', 1),
        ],
        verify: (_) {
          verify(mockQuestionnaireRepository.getQuestionnaires(
            targetPopulation: TargetPopulation.adults,
            language: 'en',
          )).called(1);
          verify(mockRiskScoringRepository.getRiskScoringEngine()).called(1);
        },
      );

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [RiskAssessmentInitializing, RiskAssessmentError] when no questionnaires available',
        build: () {
          when(mockQuestionnaireRepository.getQuestionnaires(
            targetPopulation: any(named: 'targetPopulation'),
            language: any(named: 'language'),
          )).thenAnswer((_) async => const Right([]));

          return bloc;
        },
        act: (bloc) => bloc.add(const InitializeRiskAssessment(
          patientId: 'patient_1',
          assessorId: 'provider_1',
          targetPopulation: TargetPopulation.adults,
        )),
        expect: () => [
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentError>()
              .having((state) => state.errorCode, 'errorCode', 'NO_QUESTIONNAIRES')
              .having((state) => state.isRecoverable, 'isRecoverable', true),
        ],
      );

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [RiskAssessmentInitializing, RiskAssessmentError] when repository fails',
        build: () {
          when(mockQuestionnaireRepository.getQuestionnaires(
            targetPopulation: any(named: 'targetPopulation'),
            language: any(named: 'language'),
          )).thenAnswer((_) async => const Left(ServerFailure(message: 'Server error')));

          return bloc;
        },
        act: (bloc) => bloc.add(const InitializeRiskAssessment(
          patientId: 'patient_1',
          assessorId: 'provider_1',
          targetPopulation: TargetPopulation.adults,
        )),
        expect: () => [
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentError>()
              .having((state) => state.message, 'message', contains('Server error'))
              .having((state) => state.isRecoverable, 'isRecoverable', true),
        ],
      );
    });

    group('LoadExistingSession', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [AssessmentInProgress] when session loaded successfully',
        build: () {
          when(mockQuestionnaireRepository.getSessionById(sessionId: any(named: 'sessionId')))
              .thenAnswer((_) async => Right(testSession));

          when(mockQuestionnaireRepository.getQuestionnaireById(
            questionnaireId: any(named: 'questionnaireId'),
          )).thenAnswer((_) async => Right(testQuestionnaire));

          return bloc;
        },
        act: (bloc) => bloc.add(const LoadExistingSession(sessionId: 'session_1')),
        expect: () => [
          isA<AssessmentInProgress>()
              .having((state) => state.session.id, 'session.id', 'session_1')
              .having((state) => state.questionnaire.id, 'questionnaire.id', 'questionnaire_1'),
        ],
        verify: (_) {
          verify(mockQuestionnaireRepository.getSessionById(sessionId: 'session_1')).called(1);
          verify(mockQuestionnaireRepository.getQuestionnaireById(
            questionnaireId: 'questionnaire_1',
          )).called(1);
        },
      );

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [RiskAssessmentError] when session not found',
        build: () {
          when(mockQuestionnaireRepository.getSessionById(sessionId: any(named: 'sessionId')))
              .thenAnswer((_) async => const Left(NotFoundFailure(message: 'Session not found')));

          return bloc;
        },
        act: (bloc) => bloc.add(const LoadExistingSession(sessionId: 'nonexistent')),
        expect: () => [
          isA<RiskAssessmentError>()
              .having((state) => state.message, 'message', contains('Session not found')),
        ],
      );
    });

    group('StartQuestionnaire', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'emits [QuestionnaireLoading, AssessmentInProgress] when questionnaire starts successfully',
        setUp: () {
          // Set up initial session state
          bloc.emit(AssessmentSessionReady(
            session: testSession,
            questionnaire: testQuestionnaire,
            availableQuestionnaires: [testQuestionnaire],
          ));
        },
        build: () {
          when(mockQuestionnaireRepository.getQuestionnaireById(
            questionnaireId: any(named: 'questionnaireId'),
            language: any(named: 'language'),
          )).thenAnswer((_) async => Right(testQuestionnaire));

          when(mockQuestionnaireRepository.createQuestionnaireSession(
            session: any(named: 'session'),
          )).thenAnswer((_) async => const Right('session_new'));

          return bloc;
        },
        act: (bloc) => bloc.add(const StartQuestionnaire(questionnaireId: 'questionnaire_1')),
        expect: () => [
          isA<QuestionnaireLoading>()
              .having((state) => state.questionnaireId, 'questionnaireId', 'questionnaire_1'),
          isA<AssessmentInProgress>()
              .having((state) => state.currentQuestion.id, 'currentQuestion.id', 'q1'),
        ],
        verify: (_) {
          verify(mockQuestionnaireRepository.getQuestionnaireById(
            questionnaireId: 'questionnaire_1',
            language: 'en',
          )).called(1);
        },
      );
    });

    group('SubmitQuestionResponse', () {
      late QuestionnaireResponse testResponse;

      setUp(() {
        testResponse = QuestionnaireResponse(
          questionId: 'q1',
          booleanResponse: true,
          timestamp: DateTime.now(),
          confidence: 1.0,
        );
      });

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'updates current state with response when submitted',
        setUp: () {
          bloc.emit(AssessmentInProgress(
            session: testSession,
            questionnaire: testQuestionnaire,
            currentQuestion: testQuestionnaire.questions.first,
            currentQuestionIndex: 0,
            totalQuestions: 2,
            responses: [],
            visibleQuestions: testQuestionnaire.questions,
            skippedQuestionIds: [],
            currentQuestionErrors: [],
            currentQuestionWarnings: [],
            progress: 0.0,
            navigationState: const NavigationState(
              canGoToPrevious: false,
              canGoToNext: true,
              canComplete: false,
            ),
            sessionMetadata: {},
            pendingSyncOperations: [],
          ));
        },
        build: () => bloc,
        act: (bloc) => bloc.add(SubmitQuestionResponse(
          questionId: 'q1',
          response: testResponse,
          autoAdvance: false,
        )),
        expect: () => [
          isA<AssessmentInProgress>()
              .having((state) => state.draftResponse?.questionId, 'draftResponse.questionId', 'q1')
              .having((state) => state.draftResponse?.booleanResponse, 'draftResponse.booleanResponse', true),
        ],
      );
    });

    group('NavigateToNextQuestion', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'navigates to next question when current response is valid',
        setUp: () {
          bloc.emit(AssessmentInProgress(
            session: testSession,
            questionnaire: testQuestionnaire,
            currentQuestion: testQuestionnaire.questions.first,
            currentQuestionIndex: 0,
            totalQuestions: 2,
            responses: [],
            visibleQuestions: testQuestionnaire.questions,
            skippedQuestionIds: [],
            currentQuestionErrors: [],
            currentQuestionWarnings: [],
            progress: 0.0,
            navigationState: const NavigationState(
              canGoToPrevious: false,
              canGoToNext: true,
              canComplete: false,
            ),
            sessionMetadata: {},
            pendingSyncOperations: [],
          ));
        },
        build: () => bloc,
        act: (bloc) => bloc.add(NavigateToNextQuestion(
          currentResponse: QuestionnaireResponse(
            questionId: 'q1',
            booleanResponse: true,
            timestamp: DateTime.now(),
            confidence: 1.0,
          ),
        )),
        expect: () => [
          isA<AssessmentInProgress>()
              .having((state) => state.currentQuestion.id, 'currentQuestion.id', 'q2')
              .having((state) => state.currentQuestionIndex, 'currentQuestionIndex', 1),
        ],
      );

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'validates all responses when at last question',
        setUp: () {
          bloc.emit(AssessmentInProgress(
            session: testSession,
            questionnaire: testQuestionnaire,
            currentQuestion: testQuestionnaire.questions.last,
            currentQuestionIndex: 1,
            totalQuestions: 2,
            responses: [],
            visibleQuestions: testQuestionnaire.questions,
            skippedQuestionIds: [],
            currentQuestionErrors: [],
            currentQuestionWarnings: [],
            progress: 0.5,
            navigationState: const NavigationState(
              canGoToPrevious: true,
              canGoToNext: true,
              canComplete: true,
            ),
            sessionMetadata: {},
            pendingSyncOperations: [],
          ));

          when(mockQuestionnaireRepository.validateResponses(
            questionnaireId: any(named: 'questionnaireId'),
            responses: any(named: 'responses'),
          )).thenAnswer((_) async => const Right(ValidationResult(
            isValid: true,
            errors: [],
            warnings: [],
            completionPercentage: 1.0,
          )));

          when(mockRiskScoringRepository.calculateRiskScore(
            responses: any(named: 'responses'),
            demographics: any(named: 'demographics'),
            environmentalData: any(named: 'environmentalData'),
            location: any(named: 'location'),
            assessmentDate: any(named: 'assessmentDate'),
          )).thenAnswer((_) async => Right(testRiskScore));
        },
        build: () => bloc,
        act: (bloc) => bloc.add(NavigateToNextQuestion(
          currentResponse: QuestionnaireResponse(
            questionId: 'q2',
            numericResponse: 33,
            timestamp: DateTime.now(),
            confidence: 1.0,
          ),
        )),
        expect: () => [
          isA<AssessmentValidating>()
              .having((state) => state.validationProgress, 'validationProgress', 0.0),
          isA<RiskScoreCalculating>()
              .having((state) => state.calculationProgress, 'calculationProgress', 0.0),
          isA<AssessmentCompleted>()
              .having((state) => state.riskScore.totalScore, 'riskScore.totalScore', 0.75)
              .having((state) => state.riskScore.category, 'riskScore.category', RiskCategory.high),
        ],
        verify: (_) {
          verify(mockQuestionnaireRepository.validateResponses(
            questionnaireId: 'questionnaire_1',
            responses: any(named: 'responses'),
          )).called(1);
          verify(mockRiskScoringRepository.calculateRiskScore(
            responses: any(named: 'responses'),
            demographics: any(named: 'demographics'),
            environmentalData: any(named: 'environmentalData'),
            location: any(named: 'location'),
            assessmentDate: any(named: 'assessmentDate'),
          )).called(1);
        },
      );
    });

    group('CompleteAssessment', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'completes assessment with validation and risk calculation',
        setUp: () {
          bloc.emit(AssessmentInProgress(
            session: testSession.copyWith(responses: [
              QuestionnaireResponse(
                questionId: 'q1',
                booleanResponse: true,
                timestamp: DateTime.now(),
                confidence: 1.0,
              ),
              QuestionnaireResponse(
                questionId: 'q2',
                numericResponse: 33,
                timestamp: DateTime.now(),
                confidence: 1.0,
              ),
            ]),
            questionnaire: testQuestionnaire,
            currentQuestion: testQuestionnaire.questions.last,
            currentQuestionIndex: 1,
            totalQuestions: 2,
            responses: [
              QuestionnaireResponse(
                questionId: 'q1',
                booleanResponse: true,
                timestamp: DateTime.now(),
                confidence: 1.0,
              ),
              QuestionnaireResponse(
                questionId: 'q2',
                numericResponse: 33,
                timestamp: DateTime.now(),
                confidence: 1.0,
              ),
            ],
            visibleQuestions: testQuestionnaire.questions,
            skippedQuestionIds: [],
            currentQuestionErrors: [],
            currentQuestionWarnings: [],
            progress: 1.0,
            navigationState: const NavigationState(
              canGoToPrevious: true,
              canGoToNext: false,
              canComplete: true,
            ),
            sessionMetadata: {},
            pendingSyncOperations: [],
          ));

          when(mockQuestionnaireRepository.validateResponses(
            questionnaireId: any(named: 'questionnaireId'),
            responses: any(named: 'responses'),
          )).thenAnswer((_) async => const Right(ValidationResult(
            isValid: true,
            errors: [],
            warnings: [],
            completionPercentage: 1.0,
          )));

          when(mockRiskScoringRepository.calculateRiskScore(
            responses: any(named: 'responses'),
            demographics: any(named: 'demographics'),
            environmentalData: any(named: 'environmentalData'),
            location: any(named: 'location'),
            assessmentDate: any(named: 'assessmentDate'),
          )).thenAnswer((_) async => Right(testRiskScore));
        },
        build: () => bloc,
        act: (bloc) => bloc.add(const CompleteAssessment(
          clinicalNotes: 'Assessment completed successfully',
        )),
        expect: () => [
          isA<AssessmentValidating>(),
          isA<RiskScoreCalculating>(),
          isA<AssessmentCompleted>()
              .having((state) => state.assessment.status, 'assessment.status', AssessmentStatus.completed)
              .having((state) => state.riskScore.category, 'riskScore.category', RiskCategory.high),
        ],
      );
    });

    group('Error handling', () {
      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'handles network failures gracefully',
        build: () {
          when(mockQuestionnaireRepository.getQuestionnaires(
            targetPopulation: any(named: 'targetPopulation'),
            language: any(named: 'language'),
          )).thenAnswer((_) async => const Left(NetworkFailure(message: 'No internet connection')));

          return bloc;
        },
        act: (bloc) => bloc.add(const InitializeRiskAssessment(
          patientId: 'patient_1',
          assessorId: 'provider_1',
          targetPopulation: TargetPopulation.adults,
        )),
        expect: () => [
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentInitializing>(),
          isA<RiskAssessmentError>()
              .having((state) => state.message, 'message', contains('No internet connection'))
              .having((state) => state.isRecoverable, 'isRecoverable', true)
              .having((state) => state.recoveryActions, 'recoveryActions', contains(ErrorRecoveryAction.retry)),
        ],
      );

      blocTest<RiskAssessmentBloc, RiskAssessmentState>(
        'handles validation failures appropriately',
        setUp: () {
          bloc.emit(AssessmentValidating(
            session: testSession,
            questionnaire: testQuestionnaire,
            responses: [],
            validationProgress: 0.5,
            currentValidationStep: 'Validating responses',
          ));

          when(mockQuestionnaireRepository.validateResponses(
            questionnaireId: any(named: 'questionnaireId'),
            responses: any(named: 'responses'),
          )).thenAnswer((_) async => const Right(ValidationResult(
            isValid: false,
            errors: [
              ValidationError(
                questionId: 'q1',
                errorCode: 'REQUIRED_FIELD',
                errorMessage: 'This field is required',
              ),
            ],
            warnings: [],
            completionPercentage: 0.5,
          )));
        },
        build: () => bloc,
        act: (bloc) => bloc.add(const ValidateAllResponses()),
        expect: () => [
          isA<RiskAssessmentError>()
              .having((state) => state.errorCode, 'errorCode', 'VALIDATION_FAILED')
              .having((state) => state.isRecoverable, 'isRecoverable', true),
        ],
      );
    });

    group('State transitions', () {
      test('should maintain state immutability', () {
        final initialState = const RiskAssessmentInitial();
        final loadingState = const RiskAssessmentInitializing(
          patientId: 'patient_1',
          progress: 0.5,
          currentStep: 'Loading...',
        );

        expect(initialState, isNot(same(loadingState)));
        expect(initialState.props, isNot(equals(loadingState.props)));
      });

      test('should preserve equality for same state properties', () {
        final state1 = const RiskAssessmentInitializing(
          patientId: 'patient_1',
          progress: 0.5,
          currentStep: 'Loading...',
        );

        final state2 = const RiskAssessmentInitializing(
          patientId: 'patient_1',
          progress: 0.5,
          currentStep: 'Loading...',
        );

        expect(state1, equals(state2));
        expect(state1.hashCode, equals(state2.hashCode));
      });
    });
  });
}

/// Mock classes for testing
class MockConductRiskAssessment extends Mock implements ConductRiskAssessment {}

/// Helper extension for QuestionnaireSession
extension QuestionnaireSessionTestExtension on QuestionnaireSession {
  QuestionnaireSession copyWith({
    String? id,
    String? questionnaireId,
    String? subjectId,
    String? providerId,
    DateTime? startTime,
    DateTime? completionTime,
    double? progress,
    List<QuestionnaireResponse>? responses,
    String? currentQuestionId,
    SessionStatus? status,
    Map<String, dynamic>? sessionData,
  }) {
    return QuestionnaireSession(
      id: id ?? this.id,
      questionnaireId: questionnaireId ?? this.questionnaireId,
      subjectId: subjectId ?? this.subjectId,
      providerId: providerId ?? this.providerId,
      startTime: startTime ?? this.startTime,
      completionTime: completionTime ?? this.completionTime,
      progress: progress ?? this.progress,
      responses: responses ?? this.responses,
      currentQuestionId: currentQuestionId ?? this.currentQuestionId,
      status: status ?? this.status,
      sessionData: sessionData ?? this.sessionData,
    );
  }
}