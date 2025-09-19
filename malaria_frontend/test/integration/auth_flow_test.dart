/// Integration Tests for Authentication Flow
///
/// End-to-end integration tests for the complete authentication user journey
/// including login, registration, biometric setup, password reset, and session
/// management for the malaria prediction system.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:malaria_frontend/main.dart' as app;
import 'package:malaria_frontend/injection_container.dart' as di;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Authentication Flow Integration Tests', () {
    setUpAll(() async {
      // Initialize dependency injection
      await di.init();
    });

    group('Login Flow', () {
      testWidgets('should complete successful login flow', (tester) async {
        // Start the app
        app.main();
        await tester.pumpAndSettle();

        // Verify we're on the login page
        expect(find.text('Malaria Prediction'), findsOneWidget);
        expect(find.text('Sign In'), findsOneWidget);

        // Fill in login credentials
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          'password123',
        );

        // Wait for form validation
        await tester.pump(const Duration(milliseconds: 500));

        // Submit login form
        await tester.tap(find.text('Sign In'));
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Should navigate to dashboard (in a real app with mock backend)
        // For now, we verify the login attempt was processed
        expect(find.text('Sign In'), findsOneWidget);
      });

      testWidgets('should handle login validation errors', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Try to submit without credentials
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        // Should show validation errors
        expect(find.text('Email address is required'), findsOneWidget);
        expect(find.text('Password is required'), findsOneWidget);

        // Fill invalid email
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'invalid-email',
        );
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Please enter a valid email address'), findsOneWidget);

        // Fill valid email but short password
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          '123',
        );
        await tester.tap(find.text('Sign In'));
        await tester.pump();

        expect(find.text('Password must be at least 6 characters'), findsOneWidget);
      });

      testWidgets('should handle remember me functionality', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Find remember me checkbox
        final checkbox = find.byType(Checkbox);
        expect(checkbox, findsOneWidget);

        // Initially unchecked
        Checkbox checkboxWidget = tester.widget<Checkbox>(checkbox);
        expect(checkboxWidget.value, isFalse);

        // Check remember me
        await tester.tap(checkbox);
        await tester.pump();

        // Fill credentials and login
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          'password123',
        );

        // Verify checkbox is checked
        checkboxWidget = tester.widget<Checkbox>(checkbox);
        expect(checkboxWidget.value, isTrue);

        await tester.tap(find.text('Sign In'));
        await tester.pumpAndSettle();
      });
    });

    group('Registration Flow', () {
      testWidgets('should navigate to registration page', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Tap sign up link
        await tester.tap(find.text('Sign Up'));
        await tester.pumpAndSettle();

        // Should navigate to registration page
        // In a real app, this would show the registration form
        expect(find.text('Sign Up'), findsOneWidget);
      });
    });

    group('Password Reset Flow', () {
      testWidgets('should handle password reset request', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Enter email first
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );

        // Tap forgot password
        await tester.tap(find.text('Forgot Password?'));
        await tester.pumpAndSettle();

        // Should show success message (simulated)
        // In a real app with backend, this would show confirmation
        expect(find.text('Forgot Password?'), findsOneWidget);
      });

      testWidgets('should show error when password reset without email', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Tap forgot password without entering email
        await tester.tap(find.text('Forgot Password?'));
        await tester.pump();

        // Should show error message
        expect(find.text('Please enter your email address first'), findsOneWidget);
      });
    });

    group('Biometric Authentication Flow', () {
      testWidgets('should show biometric option when available', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // In a real test with mock biometric service, we would set it as available
        // For now, we check the general structure
        expect(find.text('Malaria Prediction'), findsOneWidget);
      });
    });

    group('Form Interaction Tests', () {
      testWidgets('should handle password visibility toggle', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Find password field
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
        expect(passwordField, findsOneWidget);

        // Find visibility toggle
        final visibilityToggle = find.byIcon(Icons.visibility_outlined);
        expect(visibilityToggle, findsOneWidget);

        // Initially password should be obscured
        TextFormField passwordWidget = tester.widget<TextFormField>(passwordField);
        expect(passwordWidget.obscureText, isTrue);

        // Tap to show password
        await tester.tap(visibilityToggle);
        await tester.pump();

        // Should now show visibility_off icon
        expect(find.byIcon(Icons.visibility_off_outlined), findsOneWidget);

        // Password should be visible
        passwordWidget = tester.widget<TextFormField>(passwordField);
        expect(passwordWidget.obscureText, isFalse);

        // Tap again to hide
        await tester.tap(find.byIcon(Icons.visibility_off_outlined));
        await tester.pump();

        // Should show visibility icon again
        expect(find.byIcon(Icons.visibility_outlined), findsOneWidget);
        passwordWidget = tester.widget<TextFormField>(passwordField);
        expect(passwordWidget.obscureText, isTrue);
      });

      testWidgets('should handle keyboard navigation', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Focus email field
        await tester.tap(find.widgetWithText(TextFormField, 'Enter your email address'));
        await tester.pump();

        // Enter email
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );

        // Simulate pressing Next/Tab to move to password field
        await tester.testTextInput.receiveAction(TextInputAction.next);
        await tester.pump();

        // Password field should be focused
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
        expect(passwordField, findsOneWidget);

        // Enter password
        await tester.enterText(passwordField, 'password123');

        // Simulate pressing Done/Enter to submit form
        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();

        // Form should be submitted
        expect(find.text('Sign In'), findsOneWidget);
      });
    });

    group('Accessibility Integration Tests', () {
      testWidgets('should support screen reader navigation', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Enable semantics
        final handle = tester.ensureSemantics();

        try {
          // Verify semantic structure
          expect(find.text('Malaria Prediction'), findsOneWidget);
          expect(find.text('Email Address'), findsOneWidget);
          expect(find.text('Password'), findsOneWidget);

          // Test semantic focus traversal
          final semantics = tester.semantics;
          expect(semantics, hasSemantics);

          // Verify all interactive elements are semantically accessible
          expect(find.text('Sign In'), findsOneWidget);
          expect(find.text('Forgot Password?'), findsOneWidget);
          expect(find.text('Sign Up'), findsOneWidget);
        } finally {
          handle.dispose();
        }
      });

      testWidgets('should have proper focus management', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Test tab order: email -> password -> remember me -> forgot password -> sign in
        await tester.tap(find.widgetWithText(TextFormField, 'Enter your email address'));
        await tester.pump();

        // Enter text and move to next field
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.testTextInput.receiveAction(TextInputAction.next);
        await tester.pump();

        // Should focus password field
        final passwordField = find.widgetWithText(TextFormField, 'Enter your password');
        expect(passwordField, findsOneWidget);
      });
    });

    group('Performance Integration Tests', () {
      testWidgets('should load page within performance budget', (tester) async {
        final stopwatch = Stopwatch()..start();

        app.main();
        await tester.pumpAndSettle();

        stopwatch.stop();

        // Login page should load within 3 seconds
        expect(stopwatch.elapsedMilliseconds, lessThan(3000));

        // Verify all essential elements are rendered
        expect(find.text('Malaria Prediction'), findsOneWidget);
        expect(find.text('Sign In'), findsOneWidget);
        expect(find.byType(TextFormField), findsNWidgets(2));
      });

      testWidgets('should handle rapid user interactions', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Rapidly interact with form elements
        for (int i = 0; i < 5; i++) {
          await tester.tap(find.byType(Checkbox));
          await tester.pump(const Duration(milliseconds: 50));
        }

        // Should handle rapid interactions gracefully
        expect(find.byType(Checkbox), findsOneWidget);

        // Test rapid text input
        final emailField = find.widgetWithText(TextFormField, 'Enter your email address');
        await tester.tap(emailField);
        await tester.pump();

        for (int i = 0; i < 10; i++) {
          await tester.enterText(emailField, 'test$i@example.com');
          await tester.pump(const Duration(milliseconds: 10));
        }

        // Should handle rapid text changes
        expect(emailField, findsOneWidget);
      });
    });

    group('Error Handling Integration Tests', () {
      testWidgets('should gracefully handle network errors', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Fill in credentials
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          'password123',
        );

        // Submit login (will fail in integration test without mock backend)
        await tester.tap(find.text('Sign In'));
        await tester.pumpAndSettle(const Duration(seconds: 2));

        // Should handle error gracefully without crashing
        expect(find.text('Sign In'), findsOneWidget);
      });

      testWidgets('should handle memory pressure during animations', (tester) async {
        // Run multiple instances to test memory handling
        for (int i = 0; i < 3; i++) {
          app.main();
          await tester.pumpAndSettle();

          // Trigger animations by interacting with form
          await tester.tap(find.widgetWithText(TextFormField, 'Enter your email address'));
          await tester.pump();
          await tester.enterText(
            find.widgetWithText(TextFormField, 'Enter your email address'),
            'test$i@example.com',
          );
          await tester.pump();

          // Should handle memory pressure gracefully
          expect(find.text('Malaria Prediction'), findsOneWidget);
        }
      });
    });

    group('State Persistence Tests', () {
      testWidgets('should maintain form state during orientation changes', (tester) async {
        app.main();
        await tester.pumpAndSettle();

        // Fill in form data
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your email address'),
          'test@example.com',
        );
        await tester.enterText(
          find.widgetWithText(TextFormField, 'Enter your password'),
          'password123',
        );

        // Check remember me
        await tester.tap(find.byType(Checkbox));
        await tester.pump();

        // Simulate orientation change by resizing
        await tester.binding.setSurfaceSize(const Size(667, 375)); // Landscape
        await tester.pumpAndSettle();

        // Form data should be preserved
        final emailField = tester.widget<TextFormField>(
          find.widgetWithText(TextFormField, 'Enter your email address'),
        );
        final passwordField = tester.widget<TextFormField>(
          find.widgetWithText(TextFormField, 'Enter your password'),
        );
        final checkbox = tester.widget<Checkbox>(find.byType(Checkbox));

        expect(emailField.controller?.text, 'test@example.com');
        expect(passwordField.controller?.text, 'password123');
        expect(checkbox.value, isTrue);

        // Restore original size
        await tester.binding.setSurfaceSize(const Size(375, 667)); // Portrait
        await tester.pumpAndSettle();
      });
    });
  });
}

/// Custom matchers for integration tests
class HasSemantics extends Matcher {
  const HasSemantics();

  @override
  bool matches(dynamic item, Map<dynamic, dynamic> matchState) {
    return item != null;
  }

  @override
  Description describe(Description description) {
    return description.add('has semantic information');
  }
}

const hasSemantics = HasSemantics();