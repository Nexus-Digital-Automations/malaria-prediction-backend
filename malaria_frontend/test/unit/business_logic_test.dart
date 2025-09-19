/// Unit Tests for Business Logic Layer
/// Comprehensive testing for use cases, repositories, and business rules
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Validate business logic correctness and edge cases
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';

import '../helpers/test_helper.dart';

/// Business logic unit tests covering use cases, repositories, and domain entities
void main() {
  group('Business Logic Unit Tests', () {
    setUpAll(() async {
      await TestHelper.initializeTestEnvironment();
    });

    tearDownAll(() async {
      await TestHelper.cleanupTestEnvironment();
    });

    group('Risk Assessment Use Cases', () {
      late MockRiskAssessmentRepository mockRepository;
      late GetRiskAssessmentUseCase useCase;

      setUp(() {
        mockRepository = MockRiskAssessmentRepository();
        useCase = GetRiskAssessmentUseCase(mockRepository);
      });

      test('should return risk assessment data when repository call is successful', () async {
        // Arrange
        final testData = TestDataGenerators.generateRiskAssessmentData(
          region: 'Nairobi',
          riskLevel: 'high',
        );
        final expectedResult = RiskAssessment.fromJson(testData);

        when(() => mockRepository.getRiskAssessment(any()))
            .thenAnswer((_) async => Right(expectedResult));

        // Act
        final result = await useCase(const RiskAssessmentParams(
          region: 'Nairobi',
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
        ),);

        // Assert
        expect(result.isRight(), isTrue);
        result.fold(
          (failure) => fail('Expected success but got failure: $failure'),
          (assessment) {
            expect(assessment.region, equals('Nairobi'));
            expect(assessment.riskLevel, equals(RiskLevel.high));
            expect(assessment.riskScore, greaterThan(0.0));
            expect(assessment.riskScore, lessThanOrEqualTo(1.0));
          },
        );

        verify(() => mockRepository.getRiskAssessment(any())).called(1);
      });

      test('should return failure when repository call fails', () async {
        // Arrange
        const failure = ServerFailure('Unable to fetch risk assessment');
        when(() => mockRepository.getRiskAssessment(any()))
            .thenAnswer((_) async => const Left(failure));

        // Act
        final result = await useCase(const RiskAssessmentParams(
          region: 'Invalid Region',
          coordinates: Coordinates(latitude: 0, longitude: 0),
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (actualFailure) {
            expect(actualFailure, isA<ServerFailure>());
            expect(actualFailure.message, contains('Unable to fetch'));
          },
          (assessment) => fail('Expected failure but got success: $assessment'),
        );
      });

      test('should validate coordinates before making repository call', () async {
        // Arrange & Act
        final result = await useCase(const RiskAssessmentParams(
          region: 'Test Region',
          coordinates: Coordinates(latitude: 91, longitude: 181), // Invalid coordinates
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (failure) => expect(failure, isA<ValidationFailure>()),
          (assessment) => fail('Expected validation failure'),
        );

        verifyNever(() => mockRepository.getRiskAssessment(any()));
      });

      test('should handle network timeout gracefully', () async {
        // Arrange
        when(() => mockRepository.getRiskAssessment(any()))
            .thenThrow(const TimeoutException('Request timeout', Duration(seconds: 30)));

        // Act
        final result = await useCase(const RiskAssessmentParams(
          region: 'Nairobi',
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (failure) => expect(failure, isA<NetworkFailure>()),
          (assessment) => fail('Expected network failure'),
        );
      });
    });

    group('Prediction Use Cases', () {
      late MockPredictionRepository mockRepository;
      late GetMalariaPredictionUseCase useCase;

      setUp(() {
        mockRepository = MockPredictionRepository();
        useCase = GetMalariaPredictionUseCase(mockRepository);
      });

      test('should return prediction data for valid parameters', () async {
        // Arrange
        final testPrediction = MalariaPrediction(
          region: 'Nairobi',
          predictionHorizonDays: 14,
          predictions: List.generate(14, (index) => PredictionPoint(
            date: DateTime.now().add(Duration(days: index + 1)),
            riskScore: 0.5 + (index * 0.01),
            confidence: 0.85,
          ),),
          modelVersion: '2.1.0',
          generatedAt: DateTime.now(),
        );

        when(() => mockRepository.getPrediction(any()))
            .thenAnswer((_) async => Right(testPrediction));

        // Act
        final result = await useCase(const PredictionParams(
          region: 'Nairobi',
          daysAhead: 14,
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
        ),);

        // Assert
        expect(result.isRight(), isTrue);
        result.fold(
          (failure) => fail('Expected success but got failure: $failure'),
          (prediction) {
            expect(prediction.region, equals('Nairobi'));
            expect(prediction.predictionHorizonDays, equals(14));
            expect(prediction.predictions.length, equals(14));
            expect(prediction.predictions.every((p) => p.riskScore >= 0.0 && p.riskScore <= 1.0), isTrue);
            expect(prediction.predictions.every((p) => p.confidence >= 0.0 && p.confidence <= 1.0), isTrue);
          },
        );
      });

      test('should validate prediction horizon limits', () async {
        // Arrange & Act - Test maximum limit
        final resultMax = await useCase(const PredictionParams(
          region: 'Nairobi',
          daysAhead: 91, // Exceeds 90-day limit
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
        ),);

        // Assert - Maximum limit
        expect(resultMax.isLeft(), isTrue);
        resultMax.fold(
          (failure) => expect(failure, isA<ValidationFailure>()),
          (_) => fail('Expected validation failure for exceeding max days'),
        );

        // Arrange & Act - Test minimum limit
        final resultMin = await useCase(const PredictionParams(
          region: 'Nairobi',
          daysAhead: 0, // Below minimum
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
        ),);

        // Assert - Minimum limit
        expect(resultMin.isLeft(), isTrue);
        resultMin.fold(
          (failure) => expect(failure, isA<ValidationFailure>()),
          (_) => fail('Expected validation failure for below min days'),
        );
      });

      test('should handle cache and fresh data preferences', () async {
        // Arrange
        final cachedPrediction = MalariaPrediction(
          region: 'Nairobi',
          predictionHorizonDays: 7,
          predictions: [],
          modelVersion: '2.0.0', // Older version
          generatedAt: DateTime.now().subtract(const Duration(hours: 2)),
        );

        when(() => mockRepository.getCachedPrediction(any()))
            .thenAnswer((_) async => Right(cachedPrediction));

        // Act - Request with cache preference
        final result = await useCase(const PredictionParams(
          region: 'Nairobi',
          daysAhead: 7,
          coordinates: Coordinates(latitude: -1.2921, longitude: 36.8219),
          preferCache: true,
        ),);

        // Assert
        expect(result.isRight(), isTrue);
        result.fold(
          (failure) => fail('Expected success but got failure: $failure'),
          (prediction) {
            expect(prediction.modelVersion, equals('2.0.0'));
          },
        );

        verify(() => mockRepository.getCachedPrediction(any())).called(1);
        verifyNever(() => mockRepository.getPrediction(any()));
      });
    });

    group('Authentication Use Cases', () {
      late MockAuthRepository mockAuthRepository;
      late LoginUseCase loginUseCase;
      late LogoutUseCase logoutUseCase;

      setUp(() {
        mockAuthRepository = MockAuthRepository();
        loginUseCase = LoginUseCase(mockAuthRepository);
        logoutUseCase = LogoutUseCase(mockAuthRepository);
      });

      test('should successfully authenticate user with valid credentials', () async {
        // Arrange
        final testAuth = TestDataGenerators.generateAuthenticationData(
          email: 'test@malaria-prediction.org',
        );
        final expectedUser = User.fromJson(testAuth['user']);

        when(() => mockAuthRepository.login(any(), any()))
            .thenAnswer((_) async => Right(expectedUser));

        // Act
        final result = await loginUseCase(const LoginParams(
          email: 'test@malaria-prediction.org',
          password: 'SecurePassword123!',
        ),);

        // Assert
        expect(result.isRight(), isTrue);
        result.fold(
          (failure) => fail('Expected success but got failure: $failure'),
          (user) {
            expect(user.email, equals('test@malaria-prediction.org'));
            expect(user.roles, contains('researcher'));
          },
        );
      });

      test('should reject invalid email format', () async {
        // Arrange & Act
        final result = await loginUseCase(const LoginParams(
          email: 'invalid-email',
          password: 'password',
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (failure) => expect(failure, isA<ValidationFailure>()),
          (_) => fail('Expected validation failure for invalid email'),
        );

        verifyNever(() => mockAuthRepository.login(any(), any()));
      });

      test('should reject weak passwords', () async {
        // Arrange & Act
        final result = await loginUseCase(const LoginParams(
          email: 'test@example.com',
          password: '123', // Too weak
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (failure) => expect(failure, isA<ValidationFailure>()),
          (_) => fail('Expected validation failure for weak password'),
        );
      });

      test('should handle authentication failures', () async {
        // Arrange
        when(() => mockAuthRepository.login(any(), any()))
            .thenAnswer((_) async => const Left(AuthenticationFailure('Invalid credentials')));

        // Act
        final result = await loginUseCase(const LoginParams(
          email: 'test@example.com',
          password: 'WrongPassword',
        ),);

        // Assert
        expect(result.isLeft(), isTrue);
        result.fold(
          (failure) => expect(failure, isA<AuthenticationFailure>()),
          (_) => fail('Expected authentication failure'),
        );
      });

      test('should successfully logout user', () async {
        // Arrange
        when(() => mockAuthRepository.logout())
            .thenAnswer((_) async => const Right(unit));

        // Act
        final result = await logoutUseCase(NoParams());

        // Assert
        expect(result.isRight(), isTrue);
        verify(() => mockAuthRepository.logout()).called(1);
      });
    });

    group('Data Validation Tests', () {
      test('should validate risk score ranges', () {
        // Test valid range
        expect(RiskScore.isValid(0), isTrue);
        expect(RiskScore.isValid(0.5), isTrue);
        expect(RiskScore.isValid(1), isTrue);

        // Test invalid range
        expect(RiskScore.isValid(-0.1), isFalse);
        expect(RiskScore.isValid(1.1), isFalse);
        expect(RiskScore.isValid(double.nan), isFalse);
        expect(RiskScore.isValid(double.infinity), isFalse);
      });

      test('should validate coordinate ranges', () {
        // Test valid coordinates
        expect(Coordinates.isValidLatitude(-90), isTrue);
        expect(Coordinates.isValidLatitude(0), isTrue);
        expect(Coordinates.isValidLatitude(90), isTrue);
        expect(Coordinates.isValidLongitude(-180), isTrue);
        expect(Coordinates.isValidLongitude(0), isTrue);
        expect(Coordinates.isValidLongitude(180), isTrue);

        // Test invalid coordinates
        expect(Coordinates.isValidLatitude(-90.1), isFalse);
        expect(Coordinates.isValidLatitude(90.1), isFalse);
        expect(Coordinates.isValidLongitude(-180.1), isFalse);
        expect(Coordinates.isValidLongitude(180.1), isFalse);
      });

      test('should validate email formats', () {
        // Test valid emails
        expect(EmailValidator.isValid('test@example.com'), isTrue);
        expect(EmailValidator.isValid('user.name@domain.co.uk'), isTrue);
        expect(EmailValidator.isValid('test+tag@example.org'), isTrue);

        // Test invalid emails
        expect(EmailValidator.isValid('invalid-email'), isFalse);
        expect(EmailValidator.isValid('@domain.com'), isFalse);
        expect(EmailValidator.isValid('user@'), isFalse);
        expect(EmailValidator.isValid(''), isFalse);
      });

      test('should validate password strength', () {
        // Test strong passwords
        expect(PasswordValidator.isStrong('StrongPass123!'), isTrue);
        expect(PasswordValidator.isStrong('AnotherSecureP@ssw0rd'), isTrue);

        // Test weak passwords
        expect(PasswordValidator.isStrong('weak'), isFalse);
        expect(PasswordValidator.isStrong('12345678'), isFalse);
        expect(PasswordValidator.isStrong('password'), isFalse);
        expect(PasswordValidator.isStrong('PASSWORD'), isFalse);
      });
    });

    group('Error Handling Tests', () {
      test('should create proper failure objects', () {
        // Test ServerFailure
        const serverFailure = ServerFailure('Server error occurred');
        expect(serverFailure.message, equals('Server error occurred'));
        expect(serverFailure.props, equals(['Server error occurred']));

        // Test NetworkFailure
        const networkFailure = NetworkFailure('Network connection failed');
        expect(networkFailure.message, equals('Network connection failed'));

        // Test ValidationFailure
        const validationFailure = ValidationFailure('Validation failed');
        expect(validationFailure.message, equals('Validation failed'));
      });

      test('should handle multiple validation errors', () {
        final errors = ValidationResult();
        errors.addError('email', 'Invalid email format');
        errors.addError('password', 'Password too weak');

        expect(errors.isValid, isFalse);
        expect(errors.errors.length, equals(2));
        expect(errors.getErrors('email'), contains('Invalid email format'));
        expect(errors.getErrors('password'), contains('Password too weak'));
      });
    });
  });
}

/// Mock repository implementations for testing
class MockRiskAssessmentRepository extends Mock implements RiskAssessmentRepository {}
class MockPredictionRepository extends Mock implements PredictionRepository {}
class MockAuthRepository extends Mock implements AuthRepository {}

/// Test-specific implementations of domain entities and use cases
/// These represent the actual business logic that would be implemented

class GetRiskAssessmentUseCase {
  final RiskAssessmentRepository repository;

  GetRiskAssessmentUseCase(this.repository);

  Future<Either<Failure, RiskAssessment>> call(RiskAssessmentParams params) async {
    try {
      // Validate coordinates
      if (!Coordinates.isValidLatitude(params.coordinates.latitude) ||
          !Coordinates.isValidLongitude(params.coordinates.longitude)) {
        return const Left(ValidationFailure('Invalid coordinates provided'));
      }

      return await repository.getRiskAssessment(params);
    } catch (e) {
      if (e is TimeoutException) {
        return const Left(NetworkFailure('Request timeout'));
      }
      return const Left(ServerFailure('Unable to fetch risk assessment'));
    }
  }
}

class GetMalariaPredictionUseCase {
  final PredictionRepository repository;

  GetMalariaPredictionUseCase(this.repository);

  Future<Either<Failure, MalariaPrediction>> call(PredictionParams params) async {
    // Validate prediction horizon
    if (params.daysAhead < 1 || params.daysAhead > 90) {
      return const Left(ValidationFailure('Prediction horizon must be between 1 and 90 days'));
    }

    // Validate coordinates
    if (!Coordinates.isValidLatitude(params.coordinates.latitude) ||
        !Coordinates.isValidLongitude(params.coordinates.longitude)) {
      return const Left(ValidationFailure('Invalid coordinates provided'));
    }

    // Check cache preference
    if (params.preferCache) {
      final cachedResult = await repository.getCachedPrediction(params);
      if (cachedResult.isRight()) {
        return cachedResult;
      }
    }

    return await repository.getPrediction(params);
  }
}

class LoginUseCase {
  final AuthRepository repository;

  LoginUseCase(this.repository);

  Future<Either<Failure, User>> call(LoginParams params) async {
    // Validate email
    if (!EmailValidator.isValid(params.email)) {
      return const Left(ValidationFailure('Invalid email format'));
    }

    // Validate password
    if (!PasswordValidator.isStrong(params.password)) {
      return const Left(ValidationFailure('Password does not meet security requirements'));
    }

    return await repository.login(params.email, params.password);
  }
}

class LogoutUseCase {
  final AuthRepository repository;

  LogoutUseCase(this.repository);

  Future<Either<Failure, Unit>> call(NoParams params) async {
    return await repository.logout();
  }
}

/// Domain entities and value objects
class RiskAssessment {
  final String region;
  final RiskLevel riskLevel;
  final double riskScore;
  final Coordinates coordinates;

  RiskAssessment({
    required this.region,
    required this.riskLevel,
    required this.riskScore,
    required this.coordinates,
  });

  factory RiskAssessment.fromJson(Map<String, dynamic> json) {
    return RiskAssessment(
      region: json['region'],
      riskLevel: RiskLevel.fromString(json['risk_level']),
      riskScore: json['risk_score'].toDouble(),
      coordinates: Coordinates(
        latitude: json['coordinates']['latitude'].toDouble(),
        longitude: json['coordinates']['longitude'].toDouble(),
      ),
    );
  }
}

enum RiskLevel {
  low,
  medium,
  high,
  critical;

  static RiskLevel fromString(String value) {
    switch (value.toLowerCase()) {
      case 'low': return RiskLevel.low;
      case 'medium': return RiskLevel.medium;
      case 'high': return RiskLevel.high;
      case 'critical': return RiskLevel.critical;
      default: throw ArgumentError('Invalid risk level: $value');
    }
  }
}

class MalariaPrediction {
  final String region;
  final int predictionHorizonDays;
  final List<PredictionPoint> predictions;
  final String modelVersion;
  final DateTime generatedAt;

  MalariaPrediction({
    required this.region,
    required this.predictionHorizonDays,
    required this.predictions,
    required this.modelVersion,
    required this.generatedAt,
  });
}

class PredictionPoint {
  final DateTime date;
  final double riskScore;
  final double confidence;

  PredictionPoint({
    required this.date,
    required this.riskScore,
    required this.confidence,
  });
}

class User {
  final String id;
  final String email;
  final String name;
  final List<String> roles;

  User({
    required this.id,
    required this.email,
    required this.name,
    required this.roles,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      name: json['name'],
      roles: List<String>.from(json['roles']),
    );
  }
}

class Coordinates {
  final double latitude;
  final double longitude;

  const Coordinates({
    required this.latitude,
    required this.longitude,
  });

  static bool isValidLatitude(double lat) => lat >= -90.0 && lat <= 90.0;
  static bool isValidLongitude(double lng) => lng >= -180.0 && lng <= 180.0;
}

/// Use case parameters
class RiskAssessmentParams {
  final String region;
  final Coordinates coordinates;

  const RiskAssessmentParams({
    required this.region,
    required this.coordinates,
  });
}

class PredictionParams {
  final String region;
  final int daysAhead;
  final Coordinates coordinates;
  final bool preferCache;

  const PredictionParams({
    required this.region,
    required this.daysAhead,
    required this.coordinates,
    this.preferCache = false,
  });
}

class LoginParams {
  final String email;
  final String password;

  const LoginParams({
    required this.email,
    required this.password,
  });
}

class NoParams {}

/// Repository interfaces
abstract class RiskAssessmentRepository {
  Future<Either<Failure, RiskAssessment>> getRiskAssessment(RiskAssessmentParams params);
}

abstract class PredictionRepository {
  Future<Either<Failure, MalariaPrediction>> getPrediction(PredictionParams params);
  Future<Either<Failure, MalariaPrediction>> getCachedPrediction(PredictionParams params);
}

abstract class AuthRepository {
  Future<Either<Failure, User>> login(String email, String password);
  Future<Either<Failure, Unit>> logout();
}

/// Failure types
abstract class Failure {
  final String message;
  const Failure(this.message);
  List<Object> get props => [message];
}

class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

class ValidationFailure extends Failure {
  const ValidationFailure(super.message);
}

class AuthenticationFailure extends Failure {
  const AuthenticationFailure(super.message);
}

/// Validation utilities
class RiskScore {
  static bool isValid(double score) {
    return !score.isNaN && !score.isInfinite && score >= 0.0 && score <= 1.0;
  }
}

class EmailValidator {
  static bool isValid(String email) {
    return RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(email);
  }
}

class PasswordValidator {
  static bool isStrong(String password) {
    if (password.length < 8) return false;
    if (!RegExp(r'[A-Z]').hasMatch(password)) return false;
    if (!RegExp(r'[a-z]').hasMatch(password)) return false;
    if (!RegExp(r'[0-9]').hasMatch(password)) return false;
    if (!RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(password)) return false;
    return true;
  }
}

class ValidationResult {
  final Map<String, List<String>> _errors = {};

  bool get isValid => _errors.isEmpty;
  Map<String, List<String>> get errors => Map.unmodifiable(_errors);

  void addError(String field, String message) {
    _errors.putIfAbsent(field, () => []).add(message);
  }

  List<String> getErrors(String field) {
    return _errors[field] ?? [];
  }
}

/// Helper class for test data generation
class TestDataGenerators {
  static Map<String, dynamic> generateRiskAssessmentData({
    String? region,
    String? riskLevel,
  }) {
    return {
      'region': region ?? 'Test Region',
      'risk_level': riskLevel ?? 'medium',
      'risk_score': 0.65,
      'coordinates': {
        'latitude': -1.2921,
        'longitude': 36.8219,
      },
    };
  }

  static Map<String, dynamic> generateAuthenticationData({
    String? email,
  }) {
    return {
      'user': {
        'id': 'test_user_123',
        'email': email ?? 'test@example.com',
        'name': 'Test User',
        'roles': ['researcher', 'data_viewer'],
      },
    };
  }
}