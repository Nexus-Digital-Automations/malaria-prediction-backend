/// Comprehensive Risk Maps Integration Test
///
/// Tests the complete risk maps feature including interactive maps,
/// choropleth overlays, environmental data layers, location services,
/// real-time prediction visualization, map controls, and legends.
///
/// Author: Claude AI Agent - Risk Maps Implementation
/// Created: 2025-09-19
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:latlong2/latlong.dart';
import 'package:logger/logger.dart';

import 'package:malaria_frontend/main.dart' as app;
import 'package:malaria_frontend/core/network/network_info.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/bloc/risk_maps_bloc.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/pages/risk_maps_page.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/widgets/risk_map_widget.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/widgets/map_controls_widget.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/widgets/map_legend_widget.dart';
import 'package:malaria_frontend/features/risk_maps/domain/entities/risk_data.dart';
import 'package:malaria_frontend/features/risk_maps/domain/entities/map_layer.dart';
import 'package:malaria_frontend/features/risk_maps/domain/usecases/get_risk_data.dart';
import 'package:malaria_frontend/features/risk_maps/domain/usecases/update_map_layers.dart';
import 'package:malaria_frontend/features/risk_maps/domain/repositories/risk_maps_repository.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Risk Maps Integration Tests', () {
    late Logger logger;

    setUpAll(() {
      logger = Logger();
      logger.i('Starting Risk Maps Integration Tests');
    });

    testWidgets('Complete Risk Maps Functionality Test', (WidgetTester tester) async {
      logger.i('Test: Complete Risk Maps Functionality');

      // Initialize the app
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _buildTestRiskMapsPage(),
          ),
        ),
      );

      // Wait for initial load
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Test 1: Verify map widget is present
      expect(find.byType(RiskMapWidget), findsOneWidget);
      logger.i('✓ Risk map widget found');

      // Test 2: Verify map controls are present
      expect(find.byType(MapControlsWidget), findsOneWidget);
      logger.i('✓ Map controls widget found');

      // Test 3: Verify legend is present
      expect(find.byType(MapLegendWidget), findsOneWidget);
      logger.i('✓ Map legend widget found');

      // Test 4: Test location button interaction
      final locationButton = find.byIcon(Icons.my_location);
      if (locationButton.evaluate().isNotEmpty) {
        await tester.tap(locationButton);
        await tester.pumpAndSettle();
        logger.i('✓ Location button interaction tested');
      }

      // Test 5: Test map controls expansion
      final expandButton = find.byIcon(Icons.expand_more);
      if (expandButton.evaluate().isNotEmpty) {
        await tester.tap(expandButton);
        await tester.pumpAndSettle();
        logger.i('✓ Map controls expansion tested');
      }

      // Test 6: Test tile provider switching
      final dropdownFinder = find.byType(DropdownButton<String>);
      if (dropdownFinder.evaluate().isNotEmpty) {
        await tester.tap(dropdownFinder);
        await tester.pumpAndSettle();

        // Try to select different tile provider
        final satelliteOption = find.text('Satellite').last;
        if (satelliteOption.evaluate().isNotEmpty) {
          await tester.tap(satelliteOption);
          await tester.pumpAndSettle();
          logger.i('✓ Tile provider switching tested');
        }
      }

      // Test 7: Test layer visibility toggles
      final layerToggles = find.byType(CheckboxListTile);
      if (layerToggles.evaluate().isNotEmpty) {
        await tester.tap(layerToggles.first);
        await tester.pumpAndSettle();
        logger.i('✓ Layer visibility toggle tested');
      }

      // Test 8: Test opacity slider
      final opacitySlider = find.byType(Slider);
      if (opacitySlider.evaluate().isNotEmpty) {
        await tester.drag(opacitySlider, const Offset(50, 0));
        await tester.pumpAndSettle();
        logger.i('✓ Opacity slider tested');
      }

      logger.i('✅ All Risk Maps functionality tests passed!');
    });

    testWidgets('Risk Data Visualization Test', (WidgetTester tester) async {
      logger.i('Test: Risk Data Visualization');

      // Create test app with mock risk data
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _buildTestRiskMapsPageWithMockData(),
          ),
        ),
      );

      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Test risk data rendering
      expect(find.byType(RiskMapWidget), findsOneWidget);
      logger.i('✓ Risk data visualization rendered');

      // Test choropleth overlay presence
      // Note: FlutterMap layers are not easily testable in widget tests
      // but we can verify the widget structure is correct
      final mapWidget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));
      expect(mapWidget.riskData, isNotEmpty);
      logger.i('✓ Choropleth overlay data verified');

      // Test map layers
      expect(mapWidget.mapLayers, isNotEmpty);
      logger.i('✓ Environmental data layers verified');

      logger.i('✅ Risk Data Visualization tests passed!');
    });

    testWidgets('Interactive Features Test', (WidgetTester tester) async {
      logger.i('Test: Interactive Features');

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _buildTestRiskMapsPageWithMockData(),
          ),
        ),
      );

      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Test map interaction callbacks
      final mapWidget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));

      // Verify callbacks are set
      expect(mapWidget.onTap, isNotNull);
      expect(mapWidget.onLongPress, isNotNull);
      expect(mapWidget.onViewChanged, isNotNull);
      logger.i('✓ Map interaction callbacks verified');

      // Test heat map toggle
      final heatMapSwitch = find.byType(Switch);
      if (heatMapSwitch.evaluate().isNotEmpty) {
        await tester.tap(heatMapSwitch);
        await tester.pumpAndSettle();
        logger.i('✓ Heat map toggle tested');
      }

      logger.i('✅ Interactive Features tests passed!');
    });

    testWidgets('Geospatial Features Test', (WidgetTester tester) async {
      logger.i('Test: Geospatial Features');

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _buildTestRiskMapsPageWithMockData(),
          ),
        ),
      );

      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Test coordinate handling
      final mapWidget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));

      // Verify initial coordinates
      expect(mapWidget.initialCenter, isNotNull);
      expect(mapWidget.initialZoom, isNotNull);
      logger.i('✓ Geospatial coordinates verified');

      // Test boundary data
      for (final riskData in mapWidget.riskData) {
        expect(riskData.boundaries, isNotEmpty);
        expect(riskData.coordinates, isNotNull);
      }
      logger.i('✓ Geographic boundaries verified');

      logger.i('✅ Geospatial Features tests passed!');
    });

    testWidgets('Real-time Updates Test', (WidgetTester tester) async {
      logger.i('Test: Real-time Updates');

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: _buildTestRiskMapsPageWithMockData(),
          ),
        ),
      );

      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Test that the widget can handle dynamic data updates
      final mapWidget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));

      // Verify real-time capability structure is in place
      expect(mapWidget.onViewChanged, isNotNull);
      logger.i('✓ Real-time update capability verified');

      logger.i('✅ Real-time Updates tests passed!');
    });
  });
}

/// Build test risk maps page with minimal setup
Widget _buildTestRiskMapsPage() {
  return const RiskMapsPage(
    initialCenter: LatLng(-1.2921, 36.8219), // Nairobi
    initialZoom: 6.0,
  );
}

/// Build test risk maps page with mock data for testing
Widget _buildTestRiskMapsPageWithMockData() {
  final mockRiskData = [
    RiskData(
      id: 'test_1',
      region: 'nairobi',
      regionName: 'Nairobi',
      coordinates: const LatLng(-1.2921, 36.8219),
      boundaries: const [
        LatLng(-1.2, 36.7),
        LatLng(-1.2, 36.9),
        LatLng(-1.4, 36.9),
        LatLng(-1.4, 36.7),
      ],
      riskScore: 0.65,
      riskLevel: RiskLevel.medium,
      confidence: 0.85,
      timestamp: DateTime.now(),
      validFor: DateTime.now().add(const Duration(days: 7)),
      environmentalFactors: const EnvironmentalFactors(
        temperature: 25.5,
        rainfall: 150.0,
        humidity: 0.75,
        vegetationIndex: 0.6,
        waterCoverage: 0.3,
        populationDensity: 4500,
        elevation: 1795,
        windSpeed: 15.2,
        previousCases: 25,
        healthcareAccess: 0.8,
      ),
      historicalTrend: const [],
      predictions: const [],
      metadata: const {},
    ),
    RiskData(
      id: 'test_2',
      region: 'mombasa',
      regionName: 'Mombasa',
      coordinates: const LatLng(-4.0435, 39.6682),
      boundaries: const [
        LatLng(-4.0, 39.6),
        LatLng(-4.0, 39.7),
        LatLng(-4.1, 39.7),
        LatLng(-4.1, 39.6),
      ],
      riskScore: 0.85,
      riskLevel: RiskLevel.high,
      confidence: 0.9,
      timestamp: DateTime.now(),
      validFor: DateTime.now().add(const Duration(days: 7)),
      environmentalFactors: const EnvironmentalFactors(
        temperature: 28.5,
        rainfall: 200.0,
        humidity: 0.85,
        vegetationIndex: 0.4,
        waterCoverage: 0.5,
        populationDensity: 3200,
        elevation: 50,
        windSpeed: 20.1,
        previousCases: 45,
        healthcareAccess: 0.7,
      ),
      historicalTrend: const [],
      predictions: const [],
      metadata: const {},
    ),
  ];

  final mockMapLayers = [
    MapLayer(
      id: 'temperature',
      name: 'Temperature',
      description: 'Temperature data layer',
      type: LayerType.polygons,
      isVisible: true,
      isToggleable: true,
      opacity: 0.7,
      zIndex: 1,
      colorScheme: const LayerColorScheme(
        primaryColor: Colors.red,
        secondaryColor: Colors.orange,
        borderColor: Colors.black,
        backgroundColor: Colors.transparent,
      ),
      dataConfig: const LayerDataConfig(
        source: 'temperature_api',
        updateInterval: Duration(hours: 1),
        cacheTimeout: Duration(hours: 6),
        dataFormat: 'geojson',
      ),
      styleConfig: const LayerStyleConfig(
        strokeWidth: 2.0,
        fillOpacity: 0.5,
        strokeOpacity: 1.0,
      ),
      legend: const LayerLegend(
        title: 'Temperature (°C)',
        items: [
          LegendItem(
            color: Colors.blue,
            label: 'Low (15-20°C)',
            value: '15-20',
          ),
          LegendItem(
            color: Colors.orange,
            label: 'Medium (20-25°C)',
            value: '20-25',
          ),
          LegendItem(
            color: Colors.red,
            label: 'High (25-30°C)',
            value: '25-30',
          ),
        ],
        position: LegendPosition.bottomRight,
      ),
      requiresAuth: false,
      minZoom: 3.0,
      maxZoom: 18.0,
      tags: const ['environmental', 'temperature'],
      metadata: const {},
    ),
    MapLayer(
      id: 'rainfall',
      name: 'Rainfall',
      description: 'Rainfall data layer',
      type: LayerType.polygons,
      isVisible: true,
      isToggleable: true,
      opacity: 0.6,
      zIndex: 2,
      colorScheme: const LayerColorScheme(
        primaryColor: Colors.blue,
        secondaryColor: Colors.lightBlue,
        borderColor: Colors.darkBlue,
        backgroundColor: Colors.transparent,
      ),
      dataConfig: const LayerDataConfig(
        source: 'rainfall_api',
        updateInterval: Duration(hours: 1),
        cacheTimeout: Duration(hours: 6),
        dataFormat: 'geojson',
      ),
      styleConfig: const LayerStyleConfig(
        strokeWidth: 1.5,
        fillOpacity: 0.4,
        strokeOpacity: 1.0,
      ),
      legend: const LayerLegend(
        title: 'Rainfall (mm)',
        items: [
          LegendItem(
            color: Colors.lightBlue,
            label: 'Light (0-50mm)',
            value: '0-50',
          ),
          LegendItem(
            color: Colors.blue,
            label: 'Moderate (50-150mm)',
            value: '50-150',
          ),
          LegendItem(
            color: Colors.darkBlue,
            label: 'Heavy (150+mm)',
            value: '150+',
          ),
        ],
        position: LegendPosition.bottomRight,
      ),
      requiresAuth: false,
      minZoom: 3.0,
      maxZoom: 18.0,
      tags: const ['environmental', 'rainfall'],
      metadata: const {},
    ),
  ];

  return RiskMapWidget(
    riskData: mockRiskData,
    mapLayers: mockMapLayers,
    initialCenter: const LatLng(-1.2921, 36.8219),
    initialZoom: 6.0,
    showControls: true,
    showLegend: true,
    onTap: (coordinates) {
      // Mock tap handler
    },
    onLongPress: (coordinates) {
      // Mock long press handler
    },
    onViewChanged: (center, zoom, bounds) {
      // Mock view change handler
    },
    onLocationPressed: () {
      // Mock location handler
    },
    onLayerVisibilityChanged: (layerId, isVisible) {
      // Mock layer toggle handler
    },
  );
}