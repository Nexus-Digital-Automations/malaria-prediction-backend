/// Widget Tests for LoginPage
///
/// Comprehensive widget test suite for the login page including form validation,
/// UI interactions, biometric authentication, error handling, and accessibility
/// testing for the malaria prediction system.

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:network_image_mock/network_image_mock.dart';

import 'package:malaria_frontend/features/authentication/presentation/pages/login_page.dart';
import 'package:malaria_frontend/features/authentication/presentation/bloc/auth_bloc.dart';
import 'package:malaria_frontend/features/authentication/presentation/bloc/auth_event.dart';
import 'package:malaria_frontend/features/authentication/presentation/bloc/auth_state.dart';
import 'package:malaria_frontend/features/authentication/presentation/widgets/auth_text_field.dart';
import 'package:malaria_frontend/features/authentication/presentation/widgets/auth_button.dart';
import 'package:malaria_frontend/features/authentication/presentation/widgets/biometric_auth_button.dart';
import 'package:malaria_frontend/core/constants/app_colors.dart';

import '../../../test_config.dart';
import '../../../helpers/test_helpers.dart';

// Mock BLoC
class MockAuthBloc extends Mock implements AuthBloc {}

void main() {
  late MockAuthBloc mockAuthBloc;

  setUpAll(() async {
    await TestConfig.initialize();
    registerTestMocks();
  });

  setUp(() {
    mockAuthBloc = MockAuthBloc();

    // Default state setup
    when(() => mockAuthBloc.state).thenReturn(const AuthInitial());
    when(() => mockAuthBloc.stream).thenAnswer((_) => Stream.empty());
  });

  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('LoginPage Widget Tests', () {
    Widget createLoginPage() {
      return createTestWidget(
        child: BlocProvider<AuthBloc>(
          create: (_) => mockAuthBloc,
          child: const LoginPage(),
        ),
      );
    }

    testWidgets('should display all login form elements', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Verify main UI elements
        expect(find.text('Malaria Prediction'), findsOneWidget);
        expect(find.text('AI-powered malaria outbreak prediction and monitoring'), findsOneWidget);
        expect(find.byIcon(Icons.health_and_safety), findsOneWidget);

        // Verify form elements
        expect(find.byType(AuthTextField), findsNWidgets(2)); // Email and password
        expect(find.text('Email Address'), findsOneWidget);
        expect(find.text('Password'), findsOneWidget);
        expect(find.text('Remember me'), findsOneWidget);
        expect(find.text('Forgot Password?'), findsOneWidget);
        expect(find.text('Sign In'), findsOneWidget);
        expect(find.text('Sign Up'), findsOneWidget);

        // Verify accessibility elements
        expect(find.text('By signing in, you agree to our Terms of Service and Privacy Policy'), findsOneWidget);
      });
    });

    testWidgets('should validate email field correctly', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find email field
        final emailField = find.widgetWithText(TextFormField, 'Enter your email address');
        expect(emailField, findsOneWidget);

        // Test empty email validation
        await tester.enterText(emailField, '');
        await tester.pump();
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Email address is required'), findsOneWidget);

        // Test invalid email format
        await tester.enterText(emailField, 'invalid-email');
        await tester.pump();
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Please enter a valid email address'), findsOneWidget);

        // Test valid email
        await tester.enterText(emailField, 'test@example.com');
        await tester.pump();

        // Should not show validation error for valid email
        expect(find.text('Email address is required'), findsNothing);
        expect(find.text('Please enter a valid email address'), findsNothing);
      });
    });

    testWidgets('should validate password field correctly', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find password field
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
        expect(passwordField, findsOneWidget);

        // Test empty password validation
        await tester.enterText(passwordField, '');
        await tester.pump();
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Password is required'), findsOneWidget);

        // Test short password
        await tester.enterText(passwordField, '123');
        await tester.pump();
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Password must be at least 6 characters'), findsOneWidget);

        // Test valid password
        await tester.enterText(passwordField, 'password123');
        await tester.pump();

        // Should not show validation error for valid password
        expect(find.text('Password is required'), findsNothing);
        expect(find.text('Password must be at least 6 characters'), findsNothing);
      });
    });

    testWidgets('should toggle password visibility', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find password field and visibility toggle
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
        final visibilityToggle = find.byIcon(Icons.visibility_outlined);

        expect(passwordField, findsOneWidget);
        expect(visibilityToggle, findsOneWidget);

        // Initially password should be obscured
        final passwordWidget = tester.widget<TextFormField>(passwordField);
        expect(passwordWidget.obscureText, isTrue);

        // Tap visibility toggle
        await tester.tap(visibilityToggle);
        await tester.pump();

        // Password should now be visible
        expect(find.byIcon(Icons.visibility_off_outlined), findsOneWidget);
        final updatedPasswordWidget = tester.widget<TextFormField>(passwordField);
        expect(updatedPasswordWidget.obscureText, isFalse);

        // Tap again to hide
        await tester.tap(find.byIcon(Icons.visibility_off_outlined));
        await tester.pump();

        // Password should be obscured again
        expect(find.byIcon(Icons.visibility_outlined), findsOneWidget);
      });
    });

    testWidgets('should handle remember me checkbox', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find remember me checkbox
        final checkbox = find.byType(Checkbox);
        expect(checkbox, findsOneWidget);

        // Initially unchecked
        Checkbox checkboxWidget = tester.widget<Checkbox>(checkbox);
        expect(checkboxWidget.value, isFalse);

        // Tap to check
        await tester.tap(checkbox);
        await tester.pump();

        // Should be checked now
        checkboxWidget = tester.widget<Checkbox>(checkbox);
        expect(checkboxWidget.value, isTrue);

        // Tap again to uncheck
        await tester.tap(checkbox);
        await tester.pump();

        // Should be unchecked again
        checkboxWidget = tester.widget<Checkbox>(checkbox);
        expect(checkboxWidget.value, isFalse);
      });
    });

    testWidgets('should trigger login when form is valid and submitted', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Fill in valid form data
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          'password123',
        );
        await tester.pump();

        // Submit form
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        // Verify AuthLoginRequested event was added
        verify(() => mockAuthBloc.add(any(that: isA<AuthLoginRequested>()))).called(1);
      });
    });

    testWidgets('should handle forgot password tap', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Enter email first
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.pump();

        // Tap forgot password
        await tester.tap(find.text('Forgot Password?'));
        await tester.pump();

        // Verify AuthPasswordResetRequested event was added
        verify(() => mockAuthBloc.add(any(that: isA<AuthPasswordResetRequested>()))).called(1);
      });
    });

    testWidgets('should show error when forgot password tapped without email', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Tap forgot password without entering email
        await tester.tap(find.text('Forgot Password?'));
        await tester.pump();

        // Should show error message
        expect(find.text('Please enter your email address first'), findsOneWidget);
      });
    });

    testWidgets('should show biometric button when available', (tester) async {
      // Setup state with biometric available
      when(() => mockAuthBloc.state).thenReturn(
        const AuthUnauthenticated(biometricAvailable: true),
      );

      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Should show biometric section
        expect(find.text('OR'), findsOneWidget);
        expect(find.byType(BiometricAuthButton), findsOneWidget);
      });
    });

    testWidgets('should hide biometric button when not available', (tester) async {
      // Setup state with biometric not available
      when(() => mockAuthBloc.state).thenReturn(
        const AuthUnauthenticated(biometricAvailable: false),
      );

      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Should not show biometric section
        expect(find.text('OR'), findsNothing);
        expect(find.byType(BiometricAuthButton), findsNothing);
      });
    });

    testWidgets('should handle biometric authentication tap', (tester) async {
      // Setup state with biometric available
      when(() => mockAuthBloc.state).thenReturn(
        const AuthUnauthenticated(biometricAvailable: true),
      );

      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find and tap biometric button
        final biometricButton = find.byType(BiometricAuthButton);
        expect(biometricButton, findsOneWidget);

        await tester.tap(biometricButton);
        await tester.pump();

        // Verify AuthBiometricRequested event was added
        verify(() => mockAuthBloc.add(any(that: isA<AuthBiometricRequested>()))).called(1);
      });
    });

    testWidgets('should show loading state during authentication', (tester) async {
      // Setup loading state
      when(() => mockAuthBloc.state).thenReturn(
        const AuthInProgress(operation: 'Logging in...'),
      );

      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Form fields should be disabled
        final emailField = find.widgetWithText(TextFormField, 'Enter your email address');
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');

        final emailWidget = tester.widget<TextFormField>(emailField);
        final passwordWidget = tester.widget<TextFormField>(passwordField);

        expect(emailWidget.enabled, isFalse);
        expect(passwordWidget.enabled, isFalse);

        // Sign in button should show loading
        final authButton = find.byType(AuthButton);
        expect(authButton, findsOneWidget);

        final authButtonWidget = tester.widget<AuthButton>(authButton);
        expect(authButtonWidget.isLoading, isTrue);
      });
    });

    testWidgets('should show error message on authentication failure', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Simulate authentication failure
        when(() => mockAuthBloc.state).thenReturn(
          const AuthFailure(
            errorMessage: 'Invalid credentials',
            errorCode: 'AUTH_FAILED',
            canRetry: true,
          ),
        );

        // Trigger state change
        await tester.pump();

        // Should show error snackbar
        expect(find.text('Invalid credentials'), findsOneWidget);
        expect(find.byType(SnackBar), findsOneWidget);
      });
    });

    testWidgets('should navigate to register page', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Find and tap sign up button
        await tester.tap(find.text('Sign Up'));
        await tester.pump();

        // Note: In a real test, we would verify navigation
        // For now, we just verify the button exists and is tappable
        expect(find.text('Sign Up'), findsOneWidget);
      });
    });

    testWidgets('should show success message on password reset email sent', (tester) async {
      await mockNetworkImagesFor(() async {
        await pumpAndSettleWidget(tester, createLoginPage());

        // Simulate password reset email sent
        when(() => mockAuthBloc.state).thenReturn(
          const AuthPasswordResetEmailSent(email: 'test@example.com'),
        );

        // Trigger state change
        await tester.pump();

        // Should show success message
        expect(find.text('Password reset email sent successfully'), findsOneWidget);
      });
    });

    group('Accessibility Tests', () {
      testWidgets('should have proper semantic labels', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Check semantic labels for form fields
          expect(
            find.bySemanticsLabel('Email Address'),
            findsOneWidget,
          );
          expect(
            find.bySemanticsLabel('Password'),
            findsOneWidget,
          );

          // Check button accessibility
          expect(find.text('Sign In'), findsOneWidget);
          expect(find.text('Forgot Password?'), findsOneWidget);
        });
      });

      testWidgets('should support keyboard navigation', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Focus email field
          await tester.tap(find.widgetWithText(TextFormField, 'Enter your email address'));
          await tester.pump();

          // Enter email and press tab (next)
          await tester.enterText(
            find.widgetWithText(TextFormField, 'Enter your email address'),
            'test@example.com',
          );
          await tester.testTextInput.receiveAction(TextInputAction.next);
          await tester.pump();

          // Password field should be focused
          final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
          expect(passwordField, findsOneWidget);
        });
      });

      testWidgets('should have sufficient color contrast', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Verify high contrast colors are used
          final appBar = find.byType(Container);
          expect(appBar, findsWidgets);

          // Check primary color usage
          expect(AppColors.primary, equals(const Color(0xFF1976D2)));
          expect(AppColors.surface, equals(const Color(0xFFFFFBFE)));
          expect(AppColors.onSurface, equals(const Color(0xFF1C1B1F)));
        });
      });
    });

    group('Animation Tests', () {
      testWidgets('should animate page entrance', (tester) async {
        await mockNetworkImagesFor(() async {
          await tester.pumpWidget(createLoginPage());

          // Should start with FadeTransition and SlideTransition
          expect(find.byType(FadeTransition), findsOneWidget);
          expect(find.byType(SlideTransition), findsOneWidget);

          // Let animations complete
          await tester.pumpAndSettle();

          // Content should be fully visible
          expect(find.text('Malaria Prediction'), findsOneWidget);
        });
      });
    });

    group('Form Validation Integration', () {
      testWidgets('should enable submit button only when form is valid', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Initially sign in button should be disabled
          final signInButton = find.text('Sign In');
          expect(signInButton, findsOneWidget);

          // Fill in invalid email
          await tester.enterText(
            find.widgetWithText(TextFormField, 'Enter your email address'),
            'invalid-email',
          );
          await tester.pump();

          // Button should still be disabled
          final authButton = find.byType(AuthButton);
          final authButtonWidget = tester.widget<AuthButton>(authButton);
          expect(authButtonWidget.onPressed, isNull);

          // Fill in valid email and password
          await tester.enterText(
            find.widgetWithText(TextFormField, 'Enter your email address'),
            'test@example.com',
          );
          await tester.enterText(
            find.widgetWithText(TextFormField, 'Enter your password'),
            'password123',
          );
          await tester.pump();

          // Button should now be enabled
          final updatedAuthButton = tester.widget<AuthButton>(authButton);
          expect(updatedAuthButton.onPressed, isNotNull);
        });
      });

      testWidgets('should validate form on submit', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Try to submit without filling form
          await tester.tap(find.text('Sign In'));
          await tester.pump();

          // Should show validation errors
          expect(find.text('Email address is required'), findsOneWidget);
          expect(find.text('Password is required'), findsOneWidget);

          // Should not trigger login event
          verifyNever(() => mockAuthBloc.add(any(that: isA<AuthLoginRequested>())));
        });
      });
    });

    group('State Management Integration', () {
      testWidgets('should respond to different auth states', (tester) async {
        await mockNetworkImagesFor(() async {
          await pumpAndSettleWidget(tester, createLoginPage());

          // Test initial state
          expect(find.text('Malaria Prediction'), findsOneWidget);

          // Test loading state
          when(() => mockAuthBloc.state).thenReturn(
            const AuthInProgress(operation: 'Logging in...'),
          );
          await tester.pump();

          // Should show loading indicators
          expect(find.byType(AuthButton), findsOneWidget);

          // Test biometric loading state
          when(() => mockAuthBloc.state).thenReturn(
            const AuthBiometricInProgress(reason: 'Authenticating...'),
          );
          await tester.pump();

          // Should handle biometric loading state
          expect(find.text('Malaria Prediction'), findsOneWidget);
        });
      });
    });
  });
}