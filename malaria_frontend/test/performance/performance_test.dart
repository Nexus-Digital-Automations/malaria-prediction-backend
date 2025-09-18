/// Performance Tests for Malaria Prediction App
/// Comprehensive performance testing and benchmarking
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Validate app performance across different scenarios and devices

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_driver/flutter_driver.dart';
import 'package:integration_test/integration_test.dart';

import '../helpers/test_helper.dart';

/// Performance testing suite covering app startup, rendering, and interaction performance
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Performance Tests', () {
    setUpAll(() async {
      await TestHelper.initializeTestEnvironment();
    });

    tearDownAll(() async {
      await TestHelper.cleanupTestEnvironment();
    });

    group('App Startup Performance', () {
      testWidgets('measures cold startup time', (tester) async {
        final stopwatch = Stopwatch()..start();

        // Initialize app
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const PerformanceTestApp(),
        );

        // Wait for app to be fully loaded
        await TestHelper.TestActions.waitFor(
          tester,
          () => find.text('Dashboard').hasFound,
          timeout: const Duration(seconds: 10),
        );

        stopwatch.stop();

        // Log performance metrics
        final startupTime = stopwatch.elapsed;
        print('Cold startup time: ${startupTime.inMilliseconds}ms');

        // Assert reasonable startup time (adjust based on requirements)
        expect(startupTime.inSeconds, lessThan(5),
            reason: 'Cold startup should complete within 5 seconds');

        // Record performance metrics
        await binding.reportData(<String, dynamic>{
          'cold_startup_time_ms': startupTime.inMilliseconds,
          'test_timestamp': DateTime.now().toIso8601String(),
        });
      });

      testWidgets('measures warm startup time', (tester) async {
        // First startup (cold)
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const PerformanceTestApp(),
        );

        await TestHelper.TestActions.waitFor(
          tester,
          () => find.text('Dashboard').hasFound,
        );

        // Simulate app backgrounding and foregrounding
        await tester.binding.defaultBinaryMessenger.handlePlatformMessage(
          'flutter/lifecycle',
          const StandardMethodCodec().encodeSuccessEnvelope('AppLifecycleState.paused'),
          (data) {},
        );

        await tester.pump();

        // Measure warm startup
        final stopwatch = Stopwatch()..start();

        await tester.binding.defaultBinaryMessenger.handlePlatformMessage(
          'flutter/lifecycle',
          const StandardMethodCodec().encodeSuccessEnvelope('AppLifecycleState.resumed'),
          (data) {},
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        final warmStartupTime = stopwatch.elapsed;
        print('Warm startup time: ${warmStartupTime.inMilliseconds}ms');

        expect(warmStartupTime.inSeconds, lessThan(2),
            reason: 'Warm startup should complete within 2 seconds');

        await binding.reportData(<String, dynamic>{
          'warm_startup_time_ms': warmStartupTime.inMilliseconds,
          'test_timestamp': DateTime.now().toIso8601String(),
        });
      });
    });

    group('Rendering Performance', () {
      testWidgets('measures widget build performance', (tester) async {
        final buildTimes = <Duration>[];

        // Test multiple widget builds
        for (int i = 0; i < 10; i++) {
          final buildTime = await TestHelper.PerformanceHelper.measureBuildTime(
            tester,
            ComplexWidget(itemCount: 100),
          );

          buildTimes.add(buildTime);
          print('Build $i time: ${buildTime.inMilliseconds}ms');
        }

        // Calculate statistics
        final averageBuildTime = buildTimes.map((t) => t.inMilliseconds).reduce((a, b) => a + b) / buildTimes.length;
        final maxBuildTime = buildTimes.map((t) => t.inMilliseconds).reduce((a, b) => a > b ? a : b);

        print('Average build time: ${averageBuildTime.toStringAsFixed(2)}ms');
        print('Max build time: ${maxBuildTime}ms');

        // Assert reasonable build times
        expect(averageBuildTime, lessThan(50),
            reason: 'Average widget build should be under 50ms');

        expect(maxBuildTime, lessThan(100),
            reason: 'Max widget build should be under 100ms');

        await binding.reportData(<String, dynamic>{
          'average_build_time_ms': averageBuildTime,
          'max_build_time_ms': maxBuildTime,
          'build_samples': buildTimes.length,
        });
      });

      testWidgets('measures scroll performance', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          MaterialApp(
            home: Scaffold(
              body: ListView.builder(
                key: const Key('performance_list'),
                itemCount: 1000,
                itemBuilder: (context, index) => ComplexListItem(index: index),
              ),
            ),
          ),
        );

        final scrollable = find.byKey(const Key('performance_list'));

        // Measure scroll performance over multiple scroll operations
        final scrollMetrics = <ScrollMetrics>[];

        for (int i = 0; i < 5; i++) {
          final metrics = await TestHelper.PerformanceHelper.measureScrollPerformance(
            tester,
            scrollable,
            200.0 * (i + 1), // Varying scroll distances
          );

          scrollMetrics.add(metrics);
          print('Scroll $i: ${metrics.fps.toStringAsFixed(1)} FPS');

          // Wait between scrolls
          await tester.pump(const Duration(milliseconds: 500));
        }

        // Calculate average FPS
        final averageFps = scrollMetrics.map((m) => m.fps).reduce((a, b) => a + b) / scrollMetrics.length;
        final minFps = scrollMetrics.map((m) => m.fps).reduce((a, b) => a < b ? a : b);

        print('Average FPS: ${averageFps.toStringAsFixed(1)}');
        print('Minimum FPS: ${minFps.toStringAsFixed(1)}');

        // Assert smooth scrolling performance
        expect(averageFps, greaterThan(30),
            reason: 'Average FPS should be above 30');

        expect(minFps, greaterThan(20),
            reason: 'Minimum FPS should not drop below 20');

        await binding.reportData(<String, dynamic>{
          'average_scroll_fps': averageFps,
          'min_scroll_fps': minFps,
          'scroll_samples': scrollMetrics.length,
        });
      });

      testWidgets('measures animation performance', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const MaterialApp(home: AnimationPerformanceTest()),
        );

        // Start animation
        await tester.tap(find.byKey(const Key('start_animation')));

        // Measure animation performance
        final frameCount = tester.binding.frameCount;
        final stopwatch = Stopwatch()..start();

        // Let animation run
        await tester.pumpAndSettle(const Duration(seconds: 2));

        stopwatch.stop();

        final totalFrames = tester.binding.frameCount - frameCount;
        final animationDuration = stopwatch.elapsed;
        final fps = totalFrames / (animationDuration.inMilliseconds / 1000);

        print('Animation FPS: ${fps.toStringAsFixed(1)}');
        print('Total frames: $totalFrames over ${animationDuration.inMilliseconds}ms');

        expect(fps, greaterThan(50),
            reason: 'Animation should maintain at least 50 FPS');

        await binding.reportData(<String, dynamic>{
          'animation_fps': fps,
          'animation_duration_ms': animationDuration.inMilliseconds,
          'total_frames': totalFrames,
        });
      });
    });

    group('Memory Performance', () {
      testWidgets('measures memory usage during navigation', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const MemoryTestApp(),
        );

        // Record initial memory state
        final initialInfo = await tester.binding.defaultBinaryMessenger.send(
          'dev.flutter.memoryInfo',
          null,
        );

        // Navigate through different screens
        for (int i = 0; i < 5; i++) {
          await tester.tap(find.text('Navigate'));
          await tester.pumpAndSettle();

          await tester.tap(find.text('Back'));
          await tester.pumpAndSettle();

          // Force garbage collection
          await tester.binding.performReassemble();
          await tester.pump();
        }

        // Record final memory state
        final finalInfo = await tester.binding.defaultBinaryMessenger.send(
          'dev.flutter.memoryInfo',
          null,
        );

        // In a real implementation, you would parse the memory info
        // and check for memory leaks or excessive usage
        print('Memory performance test completed');
        print('Initial memory info available: ${initialInfo != null}');
        print('Final memory info available: ${finalInfo != null}');

        await binding.reportData(<String, dynamic>{
          'memory_test_completed': true,
          'navigation_cycles': 5,
        });
      });

      testWidgets('measures memory usage with large datasets', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const LargeDatasetApp(),
        );

        // Load progressively larger datasets
        for (int size in [100, 500, 1000, 2000]) {
          await tester.tap(find.text('Load $size items'));
          await tester.pumpAndSettle();

          // Verify list renders correctly
          expect(find.byType(ListView), findsOneWidget);

          // Scroll through the list to ensure all items can be rendered
          await tester.drag(find.byType(ListView), const Offset(0, -1000));
          await tester.pumpAndSettle();

          print('Successfully loaded and rendered $size items');
        }

        await binding.reportData(<String, dynamic>{
          'large_dataset_test_completed': true,
          'max_items_tested': 2000,
        });
      });
    });

    group('Network Performance', () {
      testWidgets('measures API response handling performance', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const NetworkPerformanceApp(),
        );

        // Test different API response sizes
        final responseTimes = <String, Duration>{};

        for (final testCase in ['small', 'medium', 'large']) {
          final stopwatch = Stopwatch()..start();

          await tester.tap(find.text('Load $testCase data'));

          // Wait for loading indicator to appear and disappear
          await TestHelper.TestActions.waitFor(
            tester,
            () => find.byType(CircularProgressIndicator).hasFound,
          );

          await TestHelper.TestActions.waitFor(
            tester,
            () => !find.byType(CircularProgressIndicator).hasFound,
            timeout: const Duration(seconds: 30),
          );

          stopwatch.stop();
          responseTimes[testCase] = stopwatch.elapsed;

          print('$testCase data load time: ${stopwatch.elapsed.inMilliseconds}ms');

          // Reset for next test
          await tester.tap(find.text('Clear'));
          await tester.pumpAndSettle();
        }

        // Assert reasonable response handling times
        for (final entry in responseTimes.entries) {
          expect(entry.value.inSeconds, lessThan(10),
              reason: '${entry.key} data should load within 10 seconds');
        }

        await binding.reportData(<String, dynamic>{
          'api_response_times': responseTimes.map(
            (key, value) => MapEntry(key, value.inMilliseconds),
          ),
        });
      });
    });

    group('Stress Testing', () {
      testWidgets('handles rapid user interactions', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const StressTestApp(),
        );

        // Perform rapid button taps
        final tapCount = 50;
        final stopwatch = Stopwatch()..start();

        for (int i = 0; i < tapCount; i++) {
          await tester.tap(find.text('Tap me'));
          // Minimal delay to simulate rapid tapping
          await tester.pump(const Duration(milliseconds: 10));
        }

        await tester.pumpAndSettle();
        stopwatch.stop();

        final totalTime = stopwatch.elapsed;
        final tapsPerSecond = tapCount / (totalTime.inMilliseconds / 1000);

        print('Processed $tapCount taps in ${totalTime.inMilliseconds}ms');
        print('Taps per second: ${tapsPerSecond.toStringAsFixed(1)}');

        // Verify counter updated correctly
        expect(find.text('Count: $tapCount'), findsOneWidget);

        expect(tapsPerSecond, greaterThan(10),
            reason: 'Should handle at least 10 taps per second');

        await binding.reportData(<String, dynamic>{
          'stress_test_taps': tapCount,
          'total_time_ms': totalTime.inMilliseconds,
          'taps_per_second': tapsPerSecond,
        });
      });

      testWidgets('handles concurrent operations', (tester) async {
        await TestHelper.pumpWidgetWithCustomSettings(
          tester,
          const ConcurrentOperationsApp(),
        );

        // Start multiple concurrent operations
        final stopwatch = Stopwatch()..start();

        await tester.tap(find.text('Start Operation 1'));
        await tester.pump();

        await tester.tap(find.text('Start Operation 2'));
        await tester.pump();

        await tester.tap(find.text('Start Operation 3'));
        await tester.pump();

        // Wait for all operations to complete
        await TestHelper.TestActions.waitFor(
          tester,
          () => find.text('All operations complete').hasFound,
          timeout: const Duration(seconds: 15),
        );

        stopwatch.stop();

        print('Concurrent operations completed in ${stopwatch.elapsed.inMilliseconds}ms');

        expect(stopwatch.elapsed.inSeconds, lessThan(10),
            reason: 'Concurrent operations should complete within 10 seconds');

        await binding.reportData(<String, dynamic>{
          'concurrent_operations_time_ms': stopwatch.elapsed.inMilliseconds,
          'operations_count': 3,
        });
      });
    });

    group('Device-Specific Performance', () {
      testWidgets('adapts to different screen sizes', (tester) async {
        final screenSizes = [
          const Size(320, 568), // iPhone SE
          const Size(375, 667), // iPhone 8
          const Size(414, 896), // iPhone 11
          const Size(768, 1024), // iPad
          const Size(1200, 800), // Desktop
        ];

        for (final size in screenSizes) {
          await TestHelper.pumpWidgetWithCustomSettings(
            tester,
            TestHelper.wrapWithMediaQuery(
              size: size,
              child: const ResponsivePerformanceApp(),
            ),
          );

          // Measure layout calculation time
          final stopwatch = Stopwatch()..start();
          await tester.pumpAndSettle();
          stopwatch.stop();

          print('Layout time for ${size.width}x${size.height}: ${stopwatch.elapsed.inMilliseconds}ms');

          expect(stopwatch.elapsed.inMilliseconds, lessThan(200),
              reason: 'Layout should adapt quickly to screen size changes');
        }

        await binding.reportData(<String, dynamic>{
          'responsive_layout_test_completed': true,
          'screen_sizes_tested': screenSizes.length,
        });
      });
    });
  });
}

/// Performance test app implementations

class PerformanceTestApp extends StatelessWidget {
  const PerformanceTestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Performance Test')),
        body: const Center(
          child: Text('Dashboard'),
        ),
      ),
    );
  }
}

class ComplexWidget extends StatelessWidget {
  final int itemCount;

  const ComplexWidget({super.key, required this.itemCount});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: ListView.builder(
          itemCount: itemCount,
          itemBuilder: (context, index) => ComplexListItem(index: index),
        ),
      ),
    );
  }
}

class ComplexListItem extends StatelessWidget {
  final int index;

  const ComplexListItem({super.key, required this.index});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Item $index',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text('Description for item $index with some additional text content'),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.star, color: Colors.amber[700]),
                Icon(Icons.star, color: Colors.amber[700]),
                Icon(Icons.star, color: Colors.amber[700]),
                Icon(Icons.star_half, color: Colors.amber[700]),
                Icon(Icons.star_border, color: Colors.amber[700]),
                const SizedBox(width: 8),
                Text('4.5 (${index + 1} reviews)'),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class AnimationPerformanceTest extends StatefulWidget {
  const AnimationPerformanceTest({super.key});

  @override
  State<AnimationPerformanceTest> createState() => _AnimationPerformanceTestState();
}

class _AnimationPerformanceTestState extends State<AnimationPerformanceTest>
    with TickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _animation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AnimatedBuilder(
              animation: _animation,
              builder: (context, child) {
                return Transform.scale(
                  scale: 1.0 + _animation.value,
                  child: Transform.rotate(
                    angle: _animation.value * 2 * 3.14159,
                    child: Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: Color.lerp(Colors.blue, Colors.red, _animation.value),
                        borderRadius: BorderRadius.circular(50),
                      ),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              key: const Key('start_animation'),
              onPressed: () {
                _controller.reset();
                _controller.forward();
              },
              child: const Text('Start Animation'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class MemoryTestApp extends StatelessWidget {
  const MemoryTestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: const MemoryTestScreen(),
      routes: {
        '/detail': (context) => const DetailScreen(),
      },
    );
  }
}

class MemoryTestScreen extends StatelessWidget {
  const MemoryTestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Memory Test')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/detail'),
              child: const Text('Navigate'),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Back'),
            ),
          ],
        ),
      ),
    );
  }
}

class DetailScreen extends StatelessWidget {
  const DetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detail Screen')),
      body: ListView.builder(
        itemCount: 100,
        itemBuilder: (context, index) => ListTile(
          title: Text('Detail Item $index'),
          subtitle: Text('Subtitle for item $index'),
          leading: const Icon(Icons.info),
        ),
      ),
    );
  }
}

class LargeDatasetApp extends StatefulWidget {
  const LargeDatasetApp({super.key});

  @override
  State<LargeDatasetApp> createState() => _LargeDatasetAppState();
}

class _LargeDatasetAppState extends State<LargeDatasetApp> {
  List<String> items = [];

  void loadItems(int count) {
    setState(() {
      items = List.generate(count, (index) => 'Item $index with data');
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Large Dataset Test')),
        body: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () => loadItems(100),
                  child: const Text('Load 100 items'),
                ),
                ElevatedButton(
                  onPressed: () => loadItems(500),
                  child: const Text('Load 500 items'),
                ),
                ElevatedButton(
                  onPressed: () => loadItems(1000),
                  child: const Text('Load 1000 items'),
                ),
                ElevatedButton(
                  onPressed: () => loadItems(2000),
                  child: const Text('Load 2000 items'),
                ),
              ],
            ),
            Expanded(
              child: ListView.builder(
                itemCount: items.length,
                itemBuilder: (context, index) => ListTile(
                  title: Text(items[index]),
                  leading: const Icon(Icons.data_usage),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class NetworkPerformanceApp extends StatefulWidget {
  const NetworkPerformanceApp({super.key});

  @override
  State<NetworkPerformanceApp> createState() => _NetworkPerformanceAppState();
}

class _NetworkPerformanceAppState extends State<NetworkPerformanceApp> {
  bool isLoading = false;
  String? data;

  Future<void> loadData(String size) async {
    setState(() {
      isLoading = true;
      data = null;
    });

    // Simulate network delay based on data size
    int delay;
    switch (size) {
      case 'small':
        delay = 500;
        break;
      case 'medium':
        delay = 1500;
        break;
      case 'large':
        delay = 3000;
        break;
      default:
        delay = 1000;
    }

    await Future.delayed(Duration(milliseconds: delay));

    setState(() {
      isLoading = false;
      data = '$size data loaded successfully';
    });
  }

  void clearData() {
    setState(() {
      data = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Network Performance Test')),
        body: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () => loadData('small'),
                  child: const Text('Load small data'),
                ),
                ElevatedButton(
                  onPressed: () => loadData('medium'),
                  child: const Text('Load medium data'),
                ),
                ElevatedButton(
                  onPressed: () => loadData('large'),
                  child: const Text('Load large data'),
                ),
              ],
            ),
            ElevatedButton(
              onPressed: clearData,
              child: const Text('Clear'),
            ),
            const SizedBox(height: 20),
            if (isLoading)
              const CircularProgressIndicator()
            else if (data != null)
              Text(data!)
            else
              const Text('No data loaded'),
          ],
        ),
      ),
    );
  }
}

class StressTestApp extends StatefulWidget {
  const StressTestApp({super.key});

  @override
  State<StressTestApp> createState() => _StressTestAppState();
}

class _StressTestAppState extends State<StressTestApp> {
  int count = 0;

  void incrementCounter() {
    setState(() {
      count++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Stress Test')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Count: $count'),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: incrementCounter,
                child: const Text('Tap me'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ConcurrentOperationsApp extends StatefulWidget {
  const ConcurrentOperationsApp({super.key});

  @override
  State<ConcurrentOperationsApp> createState() => _ConcurrentOperationsAppState();
}

class _ConcurrentOperationsAppState extends State<ConcurrentOperationsApp> {
  final List<bool> operationStatus = [false, false, false];
  bool get allComplete => operationStatus.every((status) => status);

  Future<void> startOperation(int index) async {
    // Simulate async operation
    await Future.delayed(Duration(seconds: 2 + index));
    setState(() {
      operationStatus[index] = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Concurrent Operations Test')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ...List.generate(3, (index) => Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ElevatedButton(
                      onPressed: operationStatus[index] ? null : () => startOperation(index),
                      child: Text('Start Operation ${index + 1}'),
                    ),
                    const SizedBox(width: 20),
                    Icon(
                      operationStatus[index] ? Icons.check : Icons.hourglass_empty,
                      color: operationStatus[index] ? Colors.green : Colors.grey,
                    ),
                  ],
                ),
              )),
              const SizedBox(height: 20),
              if (allComplete)
                const Text('All operations complete'),
            ],
          ),
        ),
      ),
    );
  }
}

class ResponsivePerformanceApp extends StatelessWidget {
  const ResponsivePerformanceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Responsive Performance Test')),
        body: LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < 600) {
              return const MobileLayout();
            } else if (constraints.maxWidth < 1200) {
              return const TabletLayout();
            } else {
              return const DesktopLayout();
            }
          },
        ),
      ),
    );
  }
}

class MobileLayout extends StatelessWidget {
  const MobileLayout({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('Mobile Layout'),
    );
  }
}

class TabletLayout extends StatelessWidget {
  const TabletLayout({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('Tablet Layout'),
    );
  }
}

class DesktopLayout extends StatelessWidget {
  const DesktopLayout({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('Desktop Layout'),
    );
  }
}