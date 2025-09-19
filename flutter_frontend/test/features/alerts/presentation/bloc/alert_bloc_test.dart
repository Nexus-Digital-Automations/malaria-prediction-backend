/// AlertBloc Unit Tests - Basic testing for alert functionality
import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

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
              .thenAnswer((_) async => testAlertSettings);
          when(mockAlertRepository.loadAlerts(
            filter: anyNamed('filter'),
            page: anyNamed('page'),
            limit: anyNamed('limit'),
            sortBy: anyNamed('sortBy'),
            forceRefresh: anyNamed('forceRefresh'),
            unreadOnly: anyNamed('unreadOnly'),
            includeArchived: anyNamed('includeArchived'),
          )).thenAnswer((_) async => testPagedResult);
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
            progress: 0.5,
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
              .thenAnswer((_) async => testAlertSettings);
          when(mockAlertRepository.loadAlerts(
            filter: anyNamed('filter'),
            page: anyNamed('page'),
            limit: anyNamed('limit'),
            sortBy: anyNamed('sortBy'),
            forceRefresh: anyNamed('forceRefresh'),
            unreadOnly: anyNamed('unreadOnly'),
            includeArchived: anyNamed('includeArchived'),
          )).thenThrow(Exception('Server error'));
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
            progress: 0.5,
            isBackground: false,
          ),
          const AlertError(
            message: 'Failed to load alerts. Please try again.',
            canRetry: true,
          ),
        ],
      );
    });

    group('MarkAlertRead', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertsUpdated] when markAlertRead succeeds',
        setUp: () {
          final readAlert = testAlert.copyWith(status: AlertStatus.read);
          when(mockAlertRepository.markAlertRead(
            any,
            readAt: anyNamed('readAt'),
            immediate: anyNamed('immediate'),
          )).thenAnswer((_) async => readAlert);
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const MarkAlertRead(alertId: 'test-alert-1')),
        expect: () => [
          isA<AlertsUpdated>()
              .having((state) => state.updatedAlerts.first.status, 'alert status', AlertStatus.read)
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
    });

    group('CreateAlert', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertLoading, AlertsUpdated] when createAlert succeeds',
        setUp: () {
          when(mockAlertRepository.createAlert(
            title: anyNamed('title'),
            message: anyNamed('message'),
            priority: anyNamed('priority'),
            type: anyNamed('type'),
            targetUserId: anyNamed('targetUserId'),
            sendNotifications: anyNamed('sendNotifications'),
          )).thenAnswer((_) async => testAlert);
        },
        build: () => alertBloc,
        act: (bloc) => bloc.add(const CreateAlert(
          title: 'Test Alert',
          message: 'This is a test alert message',
          priority: AlertPriority.high,
          type: AlertType.riskIncrease,
        )),
        expect: () => [
          const AlertLoading(message: 'Creating alert...'),
          isA<AlertsUpdated>()
              .having((state) => state.updatedAlerts.first.title, 'alert title', 'Test Alert')
              .having((state) => state.message, 'message', 'Alert created successfully'),
        ],
        verify: (_) {
          verify(mockAlertRepository.createAlert(
            title: 'Test Alert',
            message: 'This is a test alert message',
            priority: AlertPriority.high,
            type: AlertType.riskIncrease,
            targetUserId: null,
            sendNotifications: true,
          )).called(1);
        },
      );
    });

    group('AlertReceived', () {
      blocTest<AlertBloc, AlertState>(
        'emits [AlertsLoaded] when real-time alert is received and state is AlertsLoaded',
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
        'emits [AlertsUpdated] when not in AlertsLoaded state',
        build: () => alertBloc,
        act: (bloc) => bloc.add(AlertReceived(alert: testAlert)),
        expect: () => [
          isA<AlertsUpdated>()
              .having((state) => state.updatedAlerts.first.id, 'alert id', 'test-alert-1')
              .having((state) => state.message, 'message', 'New alert received'),
        ],
      );
    });
  });
}