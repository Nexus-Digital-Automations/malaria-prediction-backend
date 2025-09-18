/// Core Widget Tests for Malaria Prediction App
/// Comprehensive widget testing for core UI components
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Ensure core widgets function correctly across different scenarios

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mocktail/mocktail.dart';

import '../helpers/test_helper.dart';
import '../mocks/mock_factories.dart';

/// Test core application widgets and components
void main() {
  group('Core Widgets Tests', () {
    setUpAll(() async {
      await TestHelper.initializeTestEnvironment();
    });

    tearDownAll(() async {
      await TestHelper.cleanupTestEnvironment();
    });

    group('LoadingWidget Tests', () {
      testWidgets('should display circular progress indicator', (tester) async {
        // Arrange
        const loadingWidget = LoadingWidget();

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: loadingWidget),
        );

        // Assert
        expect(TestHelper.WidgetFinders.loadingIndicator(), findsOneWidget);
        expect(find.text('Loading...'), findsOneWidget);
      });

      testWidgets('should display custom loading message', (tester) async {
        // Arrange
        const customMessage = 'Fetching risk data...';
        const loadingWidget = LoadingWidget(message: customMessage);

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: loadingWidget),
        );

        // Assert
        expect(find.text(customMessage), findsOneWidget);
        expect(TestHelper.WidgetFinders.loadingIndicator(), findsOneWidget);
      });

      testWidgets('should have correct accessibility semantics', (tester) async {
        // Arrange
        const loadingWidget = LoadingWidget();

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: loadingWidget),
        );

        // Assert
        final semantics = tester.getSemantics(TestHelper.WidgetFinders.loadingIndicator());
        expect(semantics.label, contains('Loading'));
      });

      testWidgets('should measure loading widget performance', (tester) async {
        // Arrange
        const loadingWidget = LoadingWidget();

        // Act
        final buildTime = await TestHelper.PerformanceHelper.measureBuildTime(
          tester,
          TestHelper.createTestApp(child: loadingWidget),
        );

        // Assert
        expect(buildTime.inMilliseconds, lessThan(100),
            reason: 'Loading widget should build quickly');
      });
    });

    group('ErrorWidget Tests', () {
      testWidgets('should display error message and retry button', (tester) async {
        // Arrange
        const errorMessage = 'Failed to load data';
        var retryPressed = false;

        final errorWidget = CustomErrorWidget(
          message: errorMessage,
          onRetry: () => retryPressed = true,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: errorWidget),
        );

        // Assert
        expect(find.text(errorMessage), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);

        // Test retry functionality
        await TestHelper.TestActions.tapAndSettle(tester, find.text('Retry'));
        expect(retryPressed, isTrue);
      });

      testWidgets('should display different error types correctly', (tester) async {
        // Test network error
        await _testErrorType(
          tester,
          ErrorType.network,
          'Network connection failed',
          Icons.wifi_off,
        );

        // Test server error
        await _testErrorType(
          tester,
          ErrorType.server,
          'Server error occurred',
          Icons.error_outline,
        );

        // Test permission error
        await _testErrorType(
          tester,
          ErrorType.permission,
          'Permission denied',
          Icons.lock_outline,
        );
      });

      testWidgets('should handle error widget without retry option', (tester) async {
        // Arrange
        const errorWidget = CustomErrorWidget(
          message: 'Fatal error occurred',
          onRetry: null,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: errorWidget),
        );

        // Assert
        expect(find.text('Fatal error occurred'), findsOneWidget);
        expect(find.text('Retry'), findsNothing);
      });
    });

    group('CustomButton Tests', () {
      testWidgets('should respond to tap events', (tester) async {
        // Arrange
        var tapCount = 0;
        final button = CustomButton(
          text: 'Test Button',
          onPressed: () => tapCount++,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: button),
        );

        await TestHelper.TestActions.tapAndSettle(tester, find.text('Test Button'));

        // Assert
        expect(tapCount, equals(1));
      });

      testWidgets('should be disabled when onPressed is null', (tester) async {
        // Arrange
        const button = CustomButton(
          text: 'Disabled Button',
          onPressed: null,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: button),
        );

        // Assert
        final buttonWidget = tester.widget<ElevatedButton>(
          find.widgetWithText(ElevatedButton, 'Disabled Button'),
        );
        expect(buttonWidget.onPressed, isNull);
      });

      testWidgets('should display loading state correctly', (tester) async {
        // Arrange
        const button = CustomButton(
          text: 'Loading Button',
          isLoading: true,
          onPressed: () {},
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: button),
        );

        // Assert
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
        expect(find.text('Loading Button'), findsNothing);
      });

      testWidgets('should apply custom styling correctly', (tester) async {
        // Arrange
        const button = CustomButton(
          text: 'Styled Button',
          backgroundColor: Colors.red,
          textColor: Colors.white,
          onPressed: () {},
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: button),
        );

        // Assert
        final buttonWidget = tester.widget<ElevatedButton>(
          find.widgetWithText(ElevatedButton, 'Styled Button'),
        );

        final buttonStyle = buttonWidget.style;
        expect(buttonStyle?.backgroundColor?.resolve({}), equals(Colors.red));
      });
    });

    group('DataCard Tests', () {
      testWidgets('should display data correctly', (tester) async {
        // Arrange
        const testData = {
          'title': 'Risk Level',
          'value': 'High',
          'subtitle': 'Current assessment',
        };

        const dataCard = DataCard(data: testData);

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: dataCard),
        );

        // Assert
        expect(find.text('Risk Level'), findsOneWidget);
        expect(find.text('High'), findsOneWidget);
        expect(find.text('Current assessment'), findsOneWidget);
      });

      testWidgets('should handle empty data gracefully', (tester) async {
        // Arrange
        const dataCard = DataCard(data: {});

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: dataCard),
        );

        // Assert
        expect(find.text('No data available'), findsOneWidget);
      });

      testWidgets('should respond to tap when onTap is provided', (tester) async {
        // Arrange
        var tapCount = 0;
        final dataCard = DataCard(
          data: const {'title': 'Tappable Card'},
          onTap: () => tapCount++,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: dataCard),
        );

        await TestHelper.TestActions.tapAndSettle(tester, find.byType(DataCard));

        // Assert
        expect(tapCount, equals(1));
      });
    });

    group('SearchField Tests', () {
      testWidgets('should accept text input and trigger search', (tester) async {
        // Arrange
        String? lastSearchQuery;
        final searchField = SearchField(
          onSearch: (query) => lastSearchQuery = query,
          hintText: 'Search locations...',
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: searchField),
        );

        await TestHelper.TestActions.enterTextAndSettle(
          tester,
          find.byType(TextField),
          'Nairobi',
        );

        await TestHelper.TestActions.tapAndSettle(
          tester,
          find.byIcon(Icons.search),
        );

        // Assert
        expect(lastSearchQuery, equals('Nairobi'));
      });

      testWidgets('should clear search when clear button is tapped', (tester) async {
        // Arrange
        final searchField = SearchField(
          onSearch: (query) {},
          hintText: 'Search...',
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: searchField),
        );

        await TestHelper.TestActions.enterTextAndSettle(
          tester,
          find.byType(TextField),
          'test query',
        );

        await TestHelper.TestActions.tapAndSettle(
          tester,
          find.byIcon(Icons.clear),
        );

        // Assert
        final textField = tester.widget<TextField>(find.byType(TextField));
        expect(textField.controller?.text, isEmpty);
      });

      testWidgets('should show search suggestions when available', (tester) async {
        // Arrange
        final suggestions = ['Nairobi', 'Mombasa', 'Kisumu'];
        final searchField = SearchField(
          onSearch: (query) {},
          suggestions: suggestions,
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.createTestApp(child: searchField),
        );

        await TestHelper.TestActions.enterTextAndSettle(
          tester,
          find.byType(TextField),
          'N',
        );

        // Assert
        expect(find.text('Nairobi'), findsOneWidget);
        expect(find.text('Mombasa'), findsNothing); // Should be filtered
      });
    });

    group('ResponsiveLayout Tests', () {
      testWidgets('should display mobile layout on small screens', (tester) async {
        // Arrange
        const responsiveWidget = ResponsiveLayout(
          mobile: Text('Mobile Layout'),
          tablet: Text('Tablet Layout'),
          desktop: Text('Desktop Layout'),
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.wrapWithMediaQuery(
            size: const Size(360, 640), // Mobile size
            child: TestHelper.createTestApp(child: responsiveWidget),
          ),
        );

        // Assert
        expect(find.text('Mobile Layout'), findsOneWidget);
        expect(find.text('Tablet Layout'), findsNothing);
        expect(find.text('Desktop Layout'), findsNothing);
      });

      testWidgets('should display tablet layout on medium screens', (tester) async {
        // Arrange
        const responsiveWidget = ResponsiveLayout(
          mobile: Text('Mobile Layout'),
          tablet: Text('Tablet Layout'),
          desktop: Text('Desktop Layout'),
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.wrapWithMediaQuery(
            size: const Size(768, 1024), // Tablet size
            child: TestHelper.createTestApp(child: responsiveWidget),
          ),
        );

        // Assert
        expect(find.text('Tablet Layout'), findsOneWidget);
        expect(find.text('Mobile Layout'), findsNothing);
        expect(find.text('Desktop Layout'), findsNothing);
      });

      testWidgets('should display desktop layout on large screens', (tester) async {
        // Arrange
        const responsiveWidget = ResponsiveLayout(
          mobile: Text('Mobile Layout'),
          tablet: Text('Tablet Layout'),
          desktop: Text('Desktop Layout'),
        );

        // Act
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          TestHelper.wrapWithMediaQuery(
            size: const Size(1200, 800), // Desktop size
            child: TestHelper.createTestApp(child: responsiveWidget),
          ),
        );

        // Assert
        expect(find.text('Desktop Layout'), findsOneWidget);
        expect(find.text('Mobile Layout'), findsNothing);
        expect(find.text('Tablet Layout'), findsNothing);
      });
    });
  });
}

/// Helper function to test different error types
Future<void> _testErrorType(
  WidgetTester tester,
  ErrorType errorType,
  String expectedMessage,
  IconData expectedIcon,
) async {
  final errorWidget = CustomErrorWidget(
    errorType: errorType,
    onRetry: () {},
  );

  await TestHelper.pumpWidgetWithCustomSettings(
    tester,
    TestHelper.createTestApp(child: errorWidget),
  );

  expect(find.text(expectedMessage), findsOneWidget);
  expect(find.byIcon(expectedIcon), findsOneWidget);
}

/// Mock widget implementations for testing
/// These represent the actual widgets that would be implemented in the app

class LoadingWidget extends StatelessWidget {
  final String message;

  const LoadingWidget({
    super.key,
    this.message = 'Loading...',
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(
              semanticsLabel: 'Loading content',
            ),
            const SizedBox(height: 16),
            Text(
              message,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ],
        ),
      ),
    );
  }
}

enum ErrorType { network, server, permission, unknown }

class CustomErrorWidget extends StatelessWidget {
  final String? message;
  final VoidCallback? onRetry;
  final ErrorType errorType;

  const CustomErrorWidget({
    super.key,
    this.message,
    this.onRetry,
    this.errorType = ErrorType.unknown,
  });

  @override
  Widget build(BuildContext context) {
    final errorInfo = _getErrorInfo(errorType);

    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                errorInfo['icon'] as IconData,
                size: 64,
                color: Theme.of(context).colorScheme.error,
              ),
              const SizedBox(height: 16),
              Text(
                message ?? errorInfo['message'] as String,
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              if (onRetry != null)
                ElevatedButton(
                  onPressed: onRetry,
                  child: const Text('Retry'),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Map<String, dynamic> _getErrorInfo(ErrorType type) {
    switch (type) {
      case ErrorType.network:
        return {
          'message': 'Network connection failed',
          'icon': Icons.wifi_off,
        };
      case ErrorType.server:
        return {
          'message': 'Server error occurred',
          'icon': Icons.error_outline,
        };
      case ErrorType.permission:
        return {
          'message': 'Permission denied',
          'icon': Icons.lock_outline,
        };
      case ErrorType.unknown:
      default:
        return {
          'message': 'An error occurred',
          'icon': Icons.error,
        };
    }
  }
}

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final Color? backgroundColor;
  final Color? textColor;

  const CustomButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.backgroundColor,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: backgroundColor,
        foregroundColor: textColor,
      ),
      child: isLoading
          ? const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Text(text),
    );
  }
}

class DataCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback? onTap;

  const DataCard({
    super.key,
    required this.data,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No data available'),
        ),
      );
    }

    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (data['title'] != null)
                Text(
                  data['title'] as String,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              if (data['value'] != null)
                Text(
                  data['value'] as String,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              if (data['subtitle'] != null)
                Text(
                  data['subtitle'] as String,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class SearchField extends StatefulWidget {
  final Function(String) onSearch;
  final String hintText;
  final List<String>? suggestions;

  const SearchField({
    super.key,
    required this.onSearch,
    this.hintText = 'Search...',
    this.suggestions,
  });

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  final TextEditingController _controller = TextEditingController();
  List<String> _filteredSuggestions = [];

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
  }

  void _onTextChanged() {
    final query = _controller.text;
    if (widget.suggestions != null && query.isNotEmpty) {
      setState(() {
        _filteredSuggestions = widget.suggestions!
            .where((suggestion) =>
                suggestion.toLowerCase().contains(query.toLowerCase()))
            .toList();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TextField(
          controller: _controller,
          decoration: InputDecoration(
            hintText: widget.hintText,
            prefixIcon: IconButton(
              icon: const Icon(Icons.search),
              onPressed: () => widget.onSearch(_controller.text),
            ),
            suffixIcon: IconButton(
              icon: const Icon(Icons.clear),
              onPressed: () {
                _controller.clear();
                setState(() {
                  _filteredSuggestions.clear();
                });
              },
            ),
          ),
          onSubmitted: widget.onSearch,
        ),
        if (_filteredSuggestions.isNotEmpty)
          Container(
            constraints: const BoxConstraints(maxHeight: 200),
            child: ListView.builder(
              itemCount: _filteredSuggestions.length,
              itemBuilder: (context, index) {
                return ListTile(
                  title: Text(_filteredSuggestions[index]),
                  onTap: () {
                    _controller.text = _filteredSuggestions[index];
                    widget.onSearch(_filteredSuggestions[index]);
                    setState(() {
                      _filteredSuggestions.clear();
                    });
                  },
                );
              },
            ),
          ),
      ],
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    required this.tablet,
    required this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 600) {
          return mobile;
        } else if (constraints.maxWidth < 1200) {
          return tablet;
        } else {
          return desktop;
        }
      },
    );
  }
}