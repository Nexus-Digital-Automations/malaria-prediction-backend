/// Risk Maps Widget Test
///
/// Unit tests for the RiskMapWidget to verify interactive map functionality,
/// choropleth overlays, environmental data layers, and map controls.
///
/// Author: Claude AI Agent - Risk Maps Implementation
/// Created: 2025-09-19
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:latlong2/latlong.dart';

import 'package:malaria_frontend/features/risk_maps/presentation/widgets/risk_map_widget.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/widgets/map_controls_widget.dart';
import 'package:malaria_frontend/features/risk_maps/presentation/widgets/map_legend_widget.dart';
import 'package:malaria_frontend/features/risk_maps/domain/entities/risk_data.dart';
import 'package:malaria_frontend/features/risk_maps/domain/entities/map_layer.dart';

void main() {
  group('RiskMapWidget Tests', () {

    // Test data
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
          gradient: [Colors.blue, Colors.orange, Colors.red],
          steps: 10,
          noDataColor: Colors.grey,
          borderColor: Colors.black,
          highlightColor: Colors.yellow,
        ),
        dataConfig: const LayerDataConfig(
          sourceType: DataSourceType.api,
          enableCaching: true,
          cacheDuration: 3600,
          dataFormat: 'geojson',
          fieldMappings: {},
          filters: [],
          aggregations: {},
        ),
        styleConfig: const LayerStyleConfig(
          strokeWidth: 2.0,
          markerSize: 8.0,
          fontSize: 12.0,
          fontWeight: FontWeight.normal,
          textColor: Colors.black,
        ),
        legend: const LayerLegend(
          isVisible: true,
          title: 'Temperature (°C)',
          items: [
            LegendItem(
              color: Colors.blue,
              label: 'Low (15-20°C)',
              value: '15-20',
            ),
          ],
          position: LegendPosition.bottomRight,
          backgroundColor: Colors.white,
          textColor: Colors.black,
        ),
        requiresAuth: false,
        minZoom: 3.0,
        maxZoom: 18.0,
        tags: const ['environmental', 'temperature'],
        metadata: const {},
      ),
    ];

    testWidgets('RiskMapWidget displays correctly with data', (WidgetTester tester) async {
      // Build the widget
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskMapWidget(
              riskData: mockRiskData,
              mapLayers: mockMapLayers,
              initialCenter: const LatLng(-1.2921, 36.8219),
              initialZoom: 6.0,
              showControls: true,
              showLegend: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify the widget is created
      expect(find.byType(RiskMapWidget), findsOneWidget);
    });

    testWidgets('MapControlsWidget displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MapControlsWidget(
              availableTileProviders: const ['OpenStreetMap', 'Satellite', 'Terrain'],
              selectedTileProvider: 'OpenStreetMap',
              mapLayers: mockMapLayers,
              visibleLayerIds: {'temperature'},
              showHeatMap: false,
              mapOpacity: 1.0,
              isLocationLoading: false,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify the controls widget is created
      expect(find.byType(MapControlsWidget), findsOneWidget);

      // Verify location button exists
      expect(find.byIcon(Icons.my_location), findsOneWidget);

      // Verify expand button exists
      expect(find.byIcon(Icons.expand_more), findsOneWidget);
    });

    testWidgets('MapLegendWidget displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MapLegendWidget(
              riskData: mockRiskData,
              mapLayers: mockMapLayers,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify the legend widget is created
      expect(find.byType(MapLegendWidget), findsOneWidget);
    });

    testWidgets('Risk data entity properties work correctly', (WidgetTester tester) async {
      final riskData = mockRiskData.first;

      // Test risk data properties
      expect(riskData.riskScorePercentage, equals('65%'));
      expect(riskData.confidencePercentage, equals('85%'));
      expect(riskData.requiresAttention, isFalse); // Medium risk
      expect(riskData.isValid, isTrue);

      // Test environmental factors summary
      final summary = riskData.environmentalFactors.summary;
      expect(summary['Temperature'], equals('25.5°C'));
      expect(summary['Rainfall'], equals('150.0mm'));
      expect(summary['Humidity'], equals('75%'));
    });

    testWidgets('Risk levels display correctly', (WidgetTester tester) async {
      // Test all risk levels
      expect(RiskLevel.low.displayName, equals('Low Risk'));
      expect(RiskLevel.medium.displayName, equals('Medium Risk'));
      expect(RiskLevel.high.displayName, equals('High Risk'));
      expect(RiskLevel.critical.displayName, equals('Critical Risk'));

      // Test risk level from score
      expect(RiskLevel.fromScore(0.1), equals(RiskLevel.low));
      expect(RiskLevel.fromScore(0.4), equals(RiskLevel.medium));
      expect(RiskLevel.fromScore(0.7), equals(RiskLevel.high));
      expect(RiskLevel.fromScore(0.9), equals(RiskLevel.critical));
    });

    testWidgets('Map layer entity properties work correctly', (WidgetTester tester) async {
      final mapLayer = mockMapLayers.first;

      // Test map layer properties
      expect(mapLayer.id, equals('temperature'));
      expect(mapLayer.name, equals('Temperature'));
      expect(mapLayer.isVisible, isTrue);
      expect(mapLayer.isToggleable, isTrue);
      expect(mapLayer.opacity, equals(0.7));
      expect(mapLayer.type, equals(LayerType.polygons));

      // Test color scheme
      expect(mapLayer.colorScheme.primaryColor, equals(Colors.red));
      expect(mapLayer.colorScheme.secondaryColor, equals(Colors.orange));

      // Test style config
      expect(mapLayer.styleConfig.strokeWidth, equals(2.0));
      expect(mapLayer.styleConfig.markerSize, equals(8.0));

      // Test legend
      expect(mapLayer.legend.title, equals('Temperature (°C)'));
      expect(mapLayer.legend.items.length, equals(1));
      expect(mapLayer.legend.position, equals(LegendPosition.bottomRight));
    });

    testWidgets('Widget handles empty data gracefully', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskMapWidget(
              riskData: const [],
              mapLayers: const [],
              initialCenter: const LatLng(-1.2921, 36.8219),
              initialZoom: 6.0,
              showControls: true,
              showLegend: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Widget should still render without data
      expect(find.byType(RiskMapWidget), findsOneWidget);
    });

    testWidgets('Widget callback functions are set correctly', (WidgetTester tester) async {
      bool tapCalled = false;
      bool longPressCalled = false;
      bool viewChangedCalled = false;
      bool locationCalled = false;
      bool layerVisibilityCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskMapWidget(
              riskData: mockRiskData,
              mapLayers: mockMapLayers,
              onTap: (coordinates) {
                tapCalled = true;
              },
              onLongPress: (coordinates) {
                longPressCalled = true;
              },
              onViewChanged: (center, zoom, bounds) {
                viewChangedCalled = true;
              },
              onLocationPressed: () {
                locationCalled = true;
              },
              onLayerVisibilityChanged: (layerId, isVisible) {
                layerVisibilityCalled = true;
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify widget exists
      expect(find.byType(RiskMapWidget), findsOneWidget);

      // Get the widget to check callbacks are set
      final widget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));
      expect(widget.onTap, isNotNull);
      expect(widget.onLongPress, isNotNull);
      expect(widget.onViewChanged, isNotNull);
      expect(widget.onLocationPressed, isNotNull);
      expect(widget.onLayerVisibilityChanged, isNotNull);
    });

    testWidgets('Widget configuration options work correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskMapWidget(
              riskData: mockRiskData,
              mapLayers: mockMapLayers,
              initialCenter: const LatLng(-1.2921, 36.8219),
              initialZoom: 8.0,
              showControls: false,
              showLegend: false,
              enableOfflineSupport: false,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      final widget = tester.widget<RiskMapWidget>(find.byType(RiskMapWidget));
      expect(widget.initialZoom, equals(8.0));
      expect(widget.showControls, isFalse);
      expect(widget.showLegend, isFalse);
      expect(widget.enableOfflineSupport, isFalse);
    });
  });
}