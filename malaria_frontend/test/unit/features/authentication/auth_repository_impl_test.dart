/// Unit Tests for AuthRepositoryImpl
///
/// Comprehensive test suite for authentication repository implementation
/// including login, registration, token management, biometric authentication,
/// session handling, and error scenarios for the malaria prediction system.

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:malaria_frontend/core/errors/failures.dart';
import 'package:malaria_frontend/core/errors/exceptions.dart';
import 'package:malaria_frontend/core/network/network_info.dart';
import 'package:malaria_frontend/features/authentication/domain/entities/user.dart';
import 'package:malaria_frontend/features/authentication/domain/entities/auth_tokens.dart';
import 'package:malaria_frontend/features/authentication/domain/entities/login_credentials.dart';
import 'package:malaria_frontend/features/authentication/domain/entities/registration_data.dart';
import 'package:malaria_frontend/features/authentication/data/repositories/auth_repository_impl.dart';
import 'package:malaria_frontend/features/authentication/data/datasources/auth_remote_datasource.dart';
import 'package:malaria_frontend/features/authentication/data/datasources/auth_local_datasource.dart';
import 'package:malaria_frontend/features/authentication/data/models/auth_tokens_model.dart';
import 'package:malaria_frontend/features/authentication/data/models/user_model.dart';
import 'package:malaria_frontend/features/authentication/data/models/auth_response_model.dart';
import 'package:malaria_frontend/features/authentication/data/models/login_request_model.dart';
import 'package:malaria_frontend/features/authentication/data/models/registration_request_model.dart';

import '../../../test_config.dart';

// Mock classes
class MockAuthRemoteDataSource extends Mock implements AuthRemoteDataSource {}
class MockAuthLocalDataSource extends Mock implements AuthLocalDataSource {}
class MockNetworkInfo extends Mock implements NetworkInfo {}

void main() {
  late AuthRepositoryImpl repository;
  late MockAuthRemoteDataSource mockRemoteDataSource;
  late MockAuthLocalDataSource mockLocalDataSource;
  late MockNetworkInfo mockNetworkInfo;

  // Test data
  final testTokens = AuthTokens(
    accessToken: 'test-access-token',
    refreshToken: 'test-refresh-token',
    expiresAt: DateTime.now().add(const Duration(hours: 1)),
    tokenType: 'Bearer',
  );

  final testTokensModel = AuthTokensModel(
    accessToken: 'test-access-token',
    refreshToken: 'test-refresh-token',
    expiresAt: DateTime.now().add(const Duration(hours: 1)),
    tokenType: 'Bearer',
  );

  final testUser = User(
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    role: UserRole.healthcareWorker,
    isEmailVerified: true,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  final testUserModel = UserModel(
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'healthcare_worker',
    isEmailVerified: true,
    createdAt: DateTime.now().toIso8601String(),
    updatedAt: DateTime.now().toIso8601String(),
  );

  final testCredentials = LoginCredentials(
    email: 'test@example.com',
    password: 'password123',
    rememberMe: false,
  );

  final testRegistrationData = RegistrationData(
    email: 'new@example.com',
    password: 'password123',
    confirmPassword: 'password123',
    name: 'New User',
    phoneNumber: '+1234567890',
    organization: 'Test Organization',
    locale: 'en',
    acceptTerms: true,
    acceptPrivacy: true,
    enableMarketing: false,
  );

  final testAuthResponse = AuthResponseModel(
    tokens: testTokensModel,
    user: testUserModel,
    message: 'Login successful',
  );

  setUpAll(() async {
    await TestConfig.initialize();

    // Register fallback values
    registerFallbackValue(testCredentials);
    registerFallbackValue(testRegistrationData);
    registerFallbackValue(testTokensModel);
    registerFallbackValue(testUserModel);
    registerFallbackValue(const LoginRequestModel(
      email: 'test@example.com',
      password: 'password123',
      rememberMe: false,
      deviceInfo: {},
    ));
    registerFallbackValue(const RegistrationRequestModel(
      email: 'test@example.com',
      password: 'password123',
      confirmPassword: 'password123',
      name: 'Test User',
      deviceInfo: {},
      acceptTerms: true,
      acceptPrivacy: true,
    ));
  });

  setUp(() {
    mockRemoteDataSource = MockAuthRemoteDataSource();
    mockLocalDataSource = MockAuthLocalDataSource();
    mockNetworkInfo = MockNetworkInfo();

    repository = AuthRepositoryImpl(
      remoteDataSource: mockRemoteDataSource,
      localDataSource: mockLocalDataSource,
      networkInfo: mockNetworkInfo,
    );
  });

  tearDown(() {
    repository.dispose();
  });

  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('login', () {
    test('should return tokens when login is successful', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(any())).thenAnswer((_) async => testAuthResponse);
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.storeUser(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.storeRememberMe(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.storeLastLoginEmail(any())).thenAnswer((_) async {});

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Right<Failure, AuthTokens>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (tokens) {
          expect(tokens.accessToken, testTokens.accessToken);
          expect(tokens.refreshToken, testTokens.refreshToken);
        },
      );

      verify(() => mockRemoteDataSource.login(any())).called(1);
      verify(() => mockLocalDataSource.storeTokens(any())).called(1);
      verify(() => mockLocalDataSource.storeUser(any())).called(1);
      verify(() => mockLocalDataSource.storeRememberMe(testCredentials.rememberMe)).called(1);
      verify(() => mockLocalDataSource.storeLastLoginEmail(testCredentials.email)).called(1);
    });

    test('should return NetworkFailure when no internet connection', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) => expect(failure, isA<NetworkFailure>()),
        (tokens) => fail('Should not return tokens'),
      );

      verifyNever(() => mockRemoteDataSource.login(any()));
    });

    test('should return AuthenticationFailure when credentials are invalid', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(any()))
          .thenThrow(const AuthenticationException('Invalid credentials'));

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthenticationFailure>());
          expect(failure.message, 'Invalid credentials');
        },
        (tokens) => fail('Should not return tokens'),
      );
    });

    test('should return ValidationFailure when validation fails', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(any()))
          .thenThrow(const ValidationException('Email format is invalid'));

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<ValidationFailure>());
          expect(failure.message, 'Email format is invalid');
        },
        (tokens) => fail('Should not return tokens'),
      );
    });

    test('should return ServerFailure when server error occurs', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(any()))
          .thenThrow(const ServerException('Internal server error'));

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<ServerFailure>());
          expect(failure.message, 'Internal server error');
        },
        (tokens) => fail('Should not return tokens'),
      );
    });
  });

  group('register', () {
    test('should return tokens when registration is successful', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.register(any())).thenAnswer((_) async => testAuthResponse);
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.storeUser(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.storeLastLoginEmail(any())).thenAnswer((_) async {});

      // act
      final result = await repository.register(testRegistrationData);

      // assert
      expect(result, isA<Right<Failure, AuthTokens>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (tokens) {
          expect(tokens.accessToken, testTokens.accessToken);
          expect(tokens.refreshToken, testTokens.refreshToken);
        },
      );

      verify(() => mockRemoteDataSource.register(any())).called(1);
      verify(() => mockLocalDataSource.storeTokens(any())).called(1);
      verify(() => mockLocalDataSource.storeUser(any())).called(1);
      verify(() => mockLocalDataSource.storeLastLoginEmail(testRegistrationData.email)).called(1);
    });

    test('should return ConflictFailure when email already exists', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.register(any()))
          .thenThrow(const ConflictException('Email already exists'));

      // act
      final result = await repository.register(testRegistrationData);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<ConflictFailure>());
          expect(failure.message, 'Email already exists');
        },
        (tokens) => fail('Should not return tokens'),
      );
    });
  });

  group('refreshToken', () {
    const testRefreshToken = 'test-refresh-token';

    test('should return new tokens when refresh is successful', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.refreshToken(testRefreshToken))
          .thenAnswer((_) async => testTokensModel);
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});

      // act
      final result = await repository.refreshToken(testRefreshToken);

      // assert
      expect(result, isA<Right<Failure, AuthTokens>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (tokens) {
          expect(tokens.accessToken, testTokens.accessToken);
          expect(tokens.refreshToken, testTokens.refreshToken);
        },
      );

      verify(() => mockRemoteDataSource.refreshToken(testRefreshToken)).called(1);
      verify(() => mockLocalDataSource.storeTokens(any())).called(1);
    });

    test('should clear auth data and return AuthenticationFailure when refresh fails', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.refreshToken(testRefreshToken))
          .thenThrow(const AuthenticationException('Refresh token expired'));
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.refreshToken(testRefreshToken);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthenticationFailure>());
          expect(failure.message, contains('Session expired'));
        },
        (tokens) => fail('Should not return tokens'),
      );

      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
    });
  });

  group('logout', () {
    test('should clear all auth data when logout is successful', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.logout(any())).thenAnswer((_) async {});
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, isA<Right<Failure, void>>());

      verify(() => mockRemoteDataSource.logout(testTokensModel.accessToken)).called(1);
      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
    });

    test('should clear local data even when server logout fails', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.logout(any()))
          .thenThrow(const ServerException('Server error'));
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
    });

    test('should proceed with local logout when offline', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.logout();

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
      verifyNever(() => mockRemoteDataSource.logout(any()));
    });
  });

  group('getCurrentUser', () {
    test('should return cached user when available', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredUser())
          .thenAnswer((_) async => testUserModel);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Right<Failure, User>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (user) {
          expect(user.id, testUser.id);
          expect(user.email, testUser.email);
          expect(user.name, testUser.name);
        },
      );

      verify(() => mockLocalDataSource.getStoredUser()).called(1);
      verifyNever(() => mockRemoteDataSource.getCurrentUser(any()));
    });

    test('should fetch from server when not cached and online', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredUser()).thenAnswer((_) async => null);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockRemoteDataSource.getCurrentUser(any()))
          .thenAnswer((_) async => testUserModel);
      when(() => mockLocalDataSource.storeUser(any())).thenAnswer((_) async {});

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Right<Failure, User>>());
      verify(() => mockRemoteDataSource.getCurrentUser(testTokensModel.accessToken)).called(1);
      verify(() => mockLocalDataSource.storeUser(testUserModel)).called(1);
    });

    test('should return AuthenticationFailure when no valid tokens', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredUser()).thenAnswer((_) async => null);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockLocalDataSource.getStoredTokens()).thenAnswer((_) async => null);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Left<Failure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<AuthenticationFailure>());
          expect(failure.message, 'No valid authentication tokens');
        },
        (user) => fail('Should not return user'),
      );
    });

    test('should return CacheFailure when offline and no cached data', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredUser()).thenAnswer((_) async => null);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => false);

      // act
      final result = await repository.getCurrentUser();

      // assert
      expect(result, isA<Left<Failure, User>>());
      result.fold(
        (failure) {
          expect(failure, isA<CacheFailure>());
          expect(failure.message, 'No cached user data available');
        },
        (user) => fail('Should not return user'),
      );
    });
  });

  group('isAuthenticated', () {
    test('should return true when valid tokens exist', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);

      // act
      final result = await repository.isAuthenticated();

      // assert
      expect(result, isA<Right<Failure, bool>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (isAuth) => expect(isAuth, true),
      );
    });

    test('should return false when no tokens exist', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens()).thenAnswer((_) async => null);

      // act
      final result = await repository.isAuthenticated();

      // assert
      expect(result, isA<Right<Failure, bool>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (isAuth) => expect(isAuth, false),
      );
    });

    test('should try to refresh expired tokens', () async {
      // arrange
      final expiredTokens = testTokensModel.copyWith(
        expiresAt: DateTime.now().subtract(const Duration(hours: 1)),
      );
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => expiredTokens);
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.refreshToken(any()))
          .thenAnswer((_) async => testTokensModel);
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});

      // act
      final result = await repository.isAuthenticated();

      // assert
      expect(result, isA<Right<Failure, bool>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (isAuth) => expect(isAuth, true),
      );

      verify(() => mockRemoteDataSource.refreshToken(expiredTokens.refreshToken)).called(1);
    });
  });

  group('Biometric Authentication', () {
    test('should enable biometric auth when device supports it', () async {
      // arrange
      when(() => mockLocalDataSource.isBiometricAvailable()).thenAnswer((_) async => true);
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockLocalDataSource.getStoredUser())
          .thenAnswer((_) async => testUserModel);
      when(() => mockLocalDataSource.authenticateWithBiometrics(any()))
          .thenAnswer((_) async => true);
      when(() => mockLocalDataSource.storeBiometricCredentials(any(), any()))
          .thenAnswer((_) async {});
      when(() => mockLocalDataSource.enableBiometric()).thenAnswer((_) async {});

      // act
      final result = await repository.enableBiometricAuth();

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.storeBiometricCredentials(
        testUserModel.email,
        testTokensModel.refreshToken,
      )).called(1);
      verify(() => mockLocalDataSource.enableBiometric()).called(1);
    });

    test('should return BiometricFailure when device does not support biometrics', () async {
      // arrange
      when(() => mockLocalDataSource.isBiometricAvailable()).thenAnswer((_) async => false);

      // act
      final result = await repository.enableBiometricAuth();

      // assert
      expect(result, isA<Left<Failure, void>>());
      result.fold(
        (failure) {
          expect(failure, isA<BiometricFailure>());
          expect(failure.message, contains('not available'));
        },
        (_) => fail('Should not succeed'),
      );
    });

    test('should authenticate with biometrics when enabled', () async {
      // arrange
      const reason = 'Authenticate to access your account';
      when(() => mockLocalDataSource.isBiometricEnabled()).thenAnswer((_) async => true);
      when(() => mockLocalDataSource.authenticateWithBiometrics(reason))
          .thenAnswer((_) async => true);
      when(() => mockLocalDataSource.getBiometricCredentials())
          .thenAnswer((_) async => {'encrypted_token': 'encrypted-refresh-token'});
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.refreshToken('encrypted-refresh-token'))
          .thenAnswer((_) async => testTokensModel);
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});

      // act
      final result = await repository.authenticateWithBiometrics(reason);

      // assert
      expect(result, isA<Right<Failure, AuthTokens>>());
      verify(() => mockLocalDataSource.authenticateWithBiometrics(reason)).called(1);
      verify(() => mockRemoteDataSource.refreshToken('encrypted-refresh-token')).called(1);
    });

    test('should return BiometricFailure when biometric auth is not enabled', () async {
      // arrange
      const reason = 'Authenticate to access your account';
      when(() => mockLocalDataSource.isBiometricEnabled()).thenAnswer((_) async => false);

      // act
      final result = await repository.authenticateWithBiometrics(reason);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<BiometricFailure>());
          expect(failure.message, contains('not enabled'));
        },
        (_) => fail('Should not succeed'),
      );
    });

    test('should disable biometric auth successfully', () async {
      // arrange
      when(() => mockLocalDataSource.disableBiometric()).thenAnswer((_) async {});

      // act
      final result = await repository.disableBiometricAuth();

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.disableBiometric()).called(1);
    });
  });

  group('Password Management', () {
    test('should change password and logout successfully', () async {
      // arrange
      const currentPassword = 'currentPassword';
      const newPassword = 'newPassword';
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);
      when(() => mockRemoteDataSource.changePassword(
        currentPassword,
        newPassword,
        testTokensModel.accessToken,
      )).thenAnswer((_) async {});
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.changePassword(currentPassword, newPassword);

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockRemoteDataSource.changePassword(
        currentPassword,
        newPassword,
        testTokensModel.accessToken,
      )).called(1);
      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
    });

    test('should send password reset email successfully', () async {
      // arrange
      const email = 'test@example.com';
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.sendPasswordResetEmail(email))
          .thenAnswer((_) async {});

      // act
      final result = await repository.sendPasswordResetEmail(email);

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockRemoteDataSource.sendPasswordResetEmail(email)).called(1);
    });

    test('should reset password with token successfully', () async {
      // arrange
      const resetToken = 'reset-token';
      const newPassword = 'newPassword';
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.resetPasswordWithToken(resetToken, newPassword))
          .thenAnswer((_) async {});

      // act
      final result = await repository.resetPasswordWithToken(resetToken, newPassword);

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockRemoteDataSource.resetPasswordWithToken(resetToken, newPassword)).called(1);
    });
  });

  group('Session Management', () {
    test('should set auto-logout timer successfully', () async {
      // arrange
      const duration = Duration(hours: 8);
      when(() => mockLocalDataSource.storeSessionConfig(any())).thenAnswer((_) async {});

      // act
      final result = await repository.setAutoLogoutTimer(duration);

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.storeSessionConfig(any())).called(1);
    });

    test('should cancel auto-logout timer successfully', () async {
      // act
      final result = await repository.cancelAutoLogoutTimer();

      // assert
      expect(result, isA<Right<Failure, void>>());
    });

    test('should track user activity successfully', () async {
      // arrange
      when(() => mockLocalDataSource.getSessionConfig())
          .thenAnswer((_) async => {'auto_logout_duration': 8 * 60 * 60 * 1000});
      when(() => mockLocalDataSource.storeSessionConfig(any())).thenAnswer((_) async {});

      // act
      final result = await repository.trackUserActivity();

      // assert
      expect(result, isA<Right<Failure, void>>());
    });
  });

  group('Token Storage', () {
    test('should store tokens successfully', () async {
      // arrange
      when(() => mockLocalDataSource.storeTokens(any())).thenAnswer((_) async {});

      // act
      final result = await repository.storeTokens(testTokens);

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.storeTokens(any())).called(1);
    });

    test('should get stored tokens successfully', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenAnswer((_) async => testTokensModel);

      // act
      final result = await repository.getStoredTokens();

      // assert
      expect(result, isA<Right<Failure, AuthTokens?>>());
      result.fold(
        (failure) => fail('Should not return failure'),
        (tokens) {
          expect(tokens, isNotNull);
          expect(tokens!.accessToken, testTokens.accessToken);
        },
      );
    });

    test('should clear stored auth data successfully', () async {
      // arrange
      when(() => mockLocalDataSource.clearAllAuthData()).thenAnswer((_) async {});

      // act
      final result = await repository.clearStoredAuthData();

      // assert
      expect(result, isA<Right<Failure, void>>());
      verify(() => mockLocalDataSource.clearAllAuthData()).called(1);
    });
  });

  group('Error Handling', () {
    test('should handle unexpected exceptions gracefully', () async {
      // arrange
      when(() => mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(() => mockRemoteDataSource.login(any()))
          .thenThrow(Exception('Unexpected error'));

      // act
      final result = await repository.login(testCredentials);

      // assert
      expect(result, isA<Left<Failure, AuthTokens>>());
      result.fold(
        (failure) {
          expect(failure, isA<ServerFailure>());
          expect(failure.message, contains('Unexpected error during login'));
        },
        (tokens) => fail('Should not return tokens'),
      );
    });

    test('should handle cache exceptions properly', () async {
      // arrange
      when(() => mockLocalDataSource.getStoredTokens())
          .thenThrow(const CacheException('Cache error'));

      // act
      final result = await repository.getStoredTokens();

      // assert
      expect(result, isA<Left<Failure, AuthTokens?>>());
      result.fold(
        (failure) {
          expect(failure, isA<CacheFailure>());
          expect(failure.message, contains('Error retrieving stored tokens'));
        },
        (tokens) => fail('Should not return tokens'),
      );
    });
  });
}

/// Extension methods for testing
extension AuthTokensModelTestExt on AuthTokensModel {
  AuthTokensModel copyWith({
    String? accessToken,
    String? refreshToken,
    DateTime? expiresAt,
    String? tokenType,
  }) {
    return AuthTokensModel(
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      expiresAt: expiresAt ?? this.expiresAt,
      tokenType: tokenType ?? this.tokenType,
    );
  }
}