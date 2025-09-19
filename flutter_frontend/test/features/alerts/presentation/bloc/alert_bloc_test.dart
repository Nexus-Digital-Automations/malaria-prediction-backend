/// AlertBloc Unit Tests - Comprehensive testing for alert functionality
///
/// Tests cover all AlertBloc events and states with proper mocking
/// and verification of error handling, state transitions, and
/// business logic implementation.

import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dartz/dartz.dart';

import 'package:flutter_frontend/core/errors/failures.dart';
import 'package:flutter_frontend/core/utils/app_logger.dart';
import 'package:flutter_frontend/features/alerts/domain/entities/alert.dart';
import 'package:flutter_frontend/features/alerts/domain/entities/alert_settings.dart';
import 'package:flutter_frontend/features/alerts/domain/repositories/alert_repository.dart';
import 'package:flutter_frontend/features/alerts/presentation/bloc/alert_bloc.dart';

import 'alert_bloc_test.mocks.dart';

@GenerateMocks([AlertRepository, AppLogger])
void main() {
  group('AlertBloc', () {
    late AlertBloc alertBloc;
    late MockAlertRepository mockAlertRepository;
    late MockAppLogger mockAppLogger;

    // Test data
    final testAlert = Alert(
      id: 'test-alert-1',
      title: 'Test Alert',
      message: 'This is a test alert message',
      priority: AlertPriority.high,
      type: AlertType.riskIncrease,
      status: AlertStatus.unread,
      source: AlertSource.prediction,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final testAlertSettings = AlertSettings(
      userId: 'test-user',
      alertsEnabled: true,
      lastUpdated: DateTime.now(),
    );

    final testPagedResult = AlertPagedResult(
      alerts: [testAlert],
      currentPage: 0,
      totalPages: 1,
      totalCount: 1,
      limit: 20,
      hasNextPage: false,
    );

    setUp(() {
      mockAlertRepository = MockAlertRepository();
      mockAppLogger = MockAppLogger();
      alertBloc = AlertBloc(
        alertRepository: mockAlertRepository,
        logger: mockAppLogger,
      );
    });

    tearDown(() {
      alertBloc.close();
    });

    test('initial state is AlertInitial', () {
      expect(alertBloc.state, equals(const AlertInitial()));
    });

    group('LoadAlerts', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertsLoaded] when loadAlerts succeeds',
        setUp: () {
          when(mockAlertRepository.getAlertSettings(any))
              .thenAnswer((_) async => Right(testAlertSettings));
          when(mockAlertRepository.loadAlerts(
            filter: anyNamed('filter'),
            page: anyNamed('page'),
            limit: anyNamed('limit'),
            sortBy: anyNamed('sortBy'),
            forceRefresh: anyNamed('forceRefresh'),
            unreadOnly: anyNamed('unreadOnly'),
            includeArchived: anyNamed('includeArchived'),
          )).thenAnswer((_) async => Right(testPagedResult));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const LoadAlerts()),
        expect: () => [
          const AlertLoading(
            message: 'Loading alerts...',
            progress: 0.0,
            isBackground: false,
          ),
          const AlertLoading(
            message: 'Fetching alert data...',
            progress: 0.3,
            isBackground: false,
          ),
          isA<AlertsLoaded>()
              .having((state) => state.alerts.length, 'alerts length', 1)
              .having((state) => state.currentPage, 'current page', 0)
              .having((state) => state.totalCount, 'total count', 1),
        ],
        verify: (_) {
          verify(mockAlertRepository.loadAlerts(
            filter: null,
            page: 0,
            limit: 20,
            sortBy: AlertSortCriteria.dateDescending,
            forceRefresh: false,
            unreadOnly: false,
            includeArchived: false,
          )).called(1);
        },
      );

      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertError] when loadAlerts fails',
        setUp: () {
          when(mockAlertRepository.getAlertSettings(any))
              .thenAnswer((_) async => Right(testAlertSettings));
          when(mockAlertRepository.loadAlerts(
            filter: anyNamed('filter'),
            page: anyNamed('page'),
            limit: anyNamed('limit'),
            sortBy: anyNamed('sortBy'),
            forceRefresh: anyNamed('forceRefresh'),
            unreadOnly: anyNamed('unreadOnly'),
            includeArchived: anyNamed('includeArchived'),
          )).thenAnswer((_) async => const Left(ServerFailure(message: 'Server error')));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const LoadAlerts()),
        expect: () => [
          const AlertLoading(
            message: 'Loading alerts...',
            progress: 0.0,
            isBackground: false,
          ),
          const AlertLoading(
            message: 'Fetching alert data...',
            progress: 0.3,
            isBackground: false,
          ),
          const AlertError(
            message: 'Server error',
            canRetry: true,
            suggestions: ['Check your internet connection', 'Try refreshing the alerts'],
          ),
        ],
      );
    });

    group('MarkAlertRead', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertUpdated] when markAlertRead succeeds',
        setUp: () {
          final readAlert = testAlert.copyWith(status: AlertStatus.read);
          when(mockAlertRepository.markAlertRead(
            any,
            readAt: anyNamed('readAt'),
            immediate: anyNamed('immediate'),
          )).thenAnswer((_) async => Right(readAlert));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const MarkAlertRead(alertId: 'test-alert-1')),
        expect: () => [
          isA<AlertUpdated>()
              .having((state) => state.alert.status, 'alert status', AlertStatus.read)
              .having((state) => state.updateType, 'update type', AlertUpdateType.markRead)
              .having((state) => state.message, 'message', 'Alert marked as read'),
        ],
        verify: (_) {
          verify(mockAlertRepository.markAlertRead(
            'test-alert-1',
            readAt: null,
            immediate: true,
          )).called(1);
        },
      );

      blocTest<AlertBloc, AlertState>(
        'emits [AlertError] when markAlertRead fails',
        setUp: () {
          when(mockAlertRepository.markAlertRead(
            any,
            readAt: anyNamed('readAt'),
            immediate: anyNamed('immediate'),
          )).thenAnswer((_) async => const Left(ServerFailure(message: 'Failed to update alert')));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const MarkAlertRead(alertId: 'test-alert-1')),
        expect: () => [
          const AlertError(
            message: 'Failed to update alert',
            canRetry: true,
          ),
        ],
      );
    });

    group('CreateAlert', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertCreated] when createAlert succeeds',
        setUp: () {
          when(mockAlertRepository.createAlert(
            title: anyNamed('title'),
            message: anyNamed('message'),
            priority: anyNamed('priority'),
            type: anyNamed('type'),
            location: anyNamed('location'),
            riskLevel: anyNamed('riskLevel'),
            environmentalFactors: anyNamed('environmentalFactors'),
            metadata: anyNamed('metadata'),
            expiresAt: anyNamed('expiresAt'),
            targetUserId: anyNamed('targetUserId'),
            targetGroup: anyNamed('targetGroup'),
            sendNotifications: anyNamed('sendNotifications'),
            notificationChannels: anyNamed('notificationChannels'),
          )).thenAnswer((_) async => Right(testAlert));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const CreateAlert(
          title: 'Test Alert',
          message: 'This is a test alert message',
          priority: AlertPriority.high,
          type: AlertType.riskIncrease,
        )),
        expect: () => [
          const AlertLoading(
            message: 'Creating alert...',
            progress: 0.0,
          ),
          const AlertLoading(
            message: 'Validating alert data...',
            progress: 0.3,
          ),
          const AlertLoading(
            message: 'Saving alert...',
            progress: 0.7,
          ),
          isA<AlertCreated>()
              .having((state) => state.createdAlert.title, 'alert title', 'Test Alert')
              .having((state) => state.message, 'message', 'Alert created successfully'),
        ],
        verify: (_) {
          verify(mockAlertRepository.createAlert(
            title: 'Test Alert',
            message: 'This is a test alert message',
            priority: AlertPriority.high,
            type: AlertType.riskIncrease,
            location: null,
            riskLevel: null,
            environmentalFactors: null,
            metadata: null,
            expiresAt: null,
            targetUserId: null,
            targetGroup: null,
            sendNotifications: true,
            notificationChannels: null,
          )).called(1);
        },
      );
    });

    group('DismissAlert', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertUpdated] when dismissAlert succeeds',
        setUp: () {
          final dismissedAlert = testAlert.copyWith(isDismissed: true);
          when(mockAlertRepository.dismissAlert(
            any,
            reason: anyNamed('reason'),
            permanent: anyNamed('permanent'),
            dismissSimilar: anyNamed('dismissSimilar'),
          )).thenAnswer((_) async => Right(dismissedAlert));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const DismissAlert(alertId: 'test-alert-1')),
        expect: () => [
          const AlertLoading(
            message: 'Dismissing alert...',
            isBackground: true,
          ),
          isA<AlertUpdated>()
              .having((state) => state.alert.isDismissed, 'alert dismissed', true)
              .having((state) => state.updateType, 'update type', AlertUpdateType.dismiss)
              .having((state) => state.message, 'message', 'Alert dismissed permanently'),
        ],
        verify: (_) {
          verify(mockAlertRepository.dismissAlert(
            'test-alert-1',
            reason: null,
            permanent: true,
            dismissSimilar: false,
          )).called(1);
        },
      );
    });

    group('UpdateAlertSettings', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertSettingsUpdated] when updateAlertSettings succeeds',
        setUp: () {
          when(mockAlertRepository.validateAlertSettings(any))
              .thenAnswer((_) async => const Right(AlertSettingsValidationResult(
                isValid: true,
                errors: [],
                warnings: [],
              )));
          when(mockAlertRepository.updateAlertSettings(
            any,
            immediate: anyNamed('immediate'),
            validate: anyNamed('validate'),
          )).thenAnswer((_) async => Right(testAlertSettings));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(UpdateAlertSettings(
          settings: testAlertSettings,
          validate: true,
        )),
        expect: () => [
          const AlertLoading(
            message: 'Updating alert settings...',
            progress: 0.0,
          ),
          const AlertLoading(
            message: 'Validating settings...',
            progress: 0.3,
          ),
          const AlertLoading(
            message: 'Saving settings...',
            progress: 0.7,
          ),
          isA<AlertSettingsUpdated>()
              .having((state) => state.updatedSettings.userId, 'user id', 'test-user')
              .having((state) => state.message, 'message', 'Alert settings updated successfully')
              .having((state) => state.wasValidated, 'was validated', true),
        ],
        verify: (_) {
          verify(mockAlertRepository.validateAlertSettings(testAlertSettings)).called(1);
          verify(mockAlertRepository.updateAlertSettings(
            testAlertSettings,
            immediate: true,
            validate: false,
          )).called(1);
        },
      );
    });

    group('RefreshAlerts', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertsLoaded] when refreshAlerts succeeds',
        setUp: () {
          when(mockAlertRepository.refreshAlerts(
            filter: anyNamed('filter'),
            resetPagination: anyNamed('resetPagination'),
            alertTypes: anyNamed('alertTypes'),
          )).thenAnswer((_) async => Right(testPagedResult));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const RefreshAlerts()),
        expect: () => [
          const AlertLoading(
            message: 'Refreshing alerts...',
            progress: 0.0,
          ),
          isA<AlertsLoaded>()
              .having((state) => state.alerts.length, 'alerts length', 1)
              .having((state) => state.fromCache, 'from cache', false),
        ],
        verify: (_) {
          verify(mockAlertRepository.refreshAlerts(
            filter: null,
            resetPagination: false,
            alertTypes: null,
          )).called(1);
        },
      );
    });

    group('AlertReceived', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertUpdated] when real-time alert is received',
        seed: () => AlertsLoaded(
          alerts: [],
          timestamp: DateTime.now(),
        ),
        build: () => alertBloc,
        act: (bloc) => bloc.add(AlertReceived(alert: testAlert)),
        expect: () => [
          isA<AlertsLoaded>()
              .having((state) => state.alerts.length, 'alerts length', 1)
              .having((state) => state.alerts.first.id, 'first alert id', 'test-alert-1')
              .having((state) => state.isConnected, 'is connected', true),
        ],
      );

      blocTest<AlertBloc, AlertState>(
        'emits [AlertUpdated] when not in AlertsLoaded state',
        build: () => alertBloc,
        act: (bloc) => bloc.add(AlertReceived(alert: testAlert)),
        expect: () => [
          isA<AlertUpdated>()
              .having((state) => state.alert.id, 'alert id', 'test-alert-1')
              .having((state) => state.updateType, 'update type', AlertUpdateType.created)
              .having((state) => state.message, 'message', 'New alert received'),
        ],
      );
    });

    group('SearchAlerts', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertsLoaded] when searchAlerts succeeds',
        setUp: () {
          when(mockAlertRepository.searchAlerts(
            query: anyNamed('query'),
            searchFields: anyNamed('searchFields'),
            filter: anyNamed('filter'),
            page: anyNamed('page'),
            limit: anyNamed('limit'),
          )).thenAnswer((_) async => Right(testPagedResult));
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const SearchAlerts(query: 'test')),
        expect: () => [
          const AlertLoading(
            message: 'Searching alerts...',
            progress: 0.0,
          ),
          isA<AlertsLoaded>()
              .having((state) => state.alerts.length, 'alerts length', 1),
        ],
        verify: (_) {
          verify(mockAlertRepository.searchAlerts(
            query: 'test',
            searchFields: const ['title', 'message'],
            filter: null,
            page: 0,
            limit: 20,
          )).called(1);
        },
      );
    });
  });
}