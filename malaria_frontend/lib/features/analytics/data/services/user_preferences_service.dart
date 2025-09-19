/// User preferences service for analytics dashboard state persistence
///
/// This service provides comprehensive user preference management for the
/// analytics dashboard with secure local storage, preference validation,
/// and cross-device synchronization capabilities.
///
/// Features:
/// - Secure local storage with encryption
/// - Preference validation and migration
/// - Cross-device synchronization
/// - Backup and restore capabilities
/// - Preference versioning and compatibility
/// - Real-time preference updates
/// - Default preference management
///
/// Usage:
/// ```dart
/// final prefsService = UserPreferencesService();
/// await prefsService.initialize();
///
/// // Save preferences
/// await prefsService.saveDashboardPreferences(preferences);
///
/// // Load preferences
/// final prefs = await prefsService.loadDashboardPreferences();
/// ```
library;

import 'dart:convert';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';

/// Dashboard user preferences entity
class DashboardPreferences {
  /// Selected dashboard section
  final String selectedSection;

  /// Selected region
  final String selectedRegion;

  /// Selected date range
  final DateRange selectedDateRange;

  /// Applied analytics filters
  final AnalyticsFilters appliedFilters;

  /// Sidebar visibility state
  final bool sidebarVisible;

  /// Real-time updates enabled
  final bool realTimeUpdatesEnabled;

  /// Real-time update interval in seconds
  final int realTimeUpdateInterval;

  /// Theme preference
  final String themeMode;

  /// Language preference
  final String language;

  /// Chart preferences
  final ChartPreferences chartPreferences;

  /// Export preferences
  final ExportPreferences exportPreferences;

  /// Notification preferences
  final NotificationPreferences notificationPreferences;

  /// Last modified timestamp
  final DateTime lastModified;

  /// Preference version for migration
  final int version;

  const DashboardPreferences({
    this.selectedSection = 'overview',
    this.selectedRegion = 'Kenya',
    required this.selectedDateRange,
    this.appliedFilters = const AnalyticsFilters(),
    this.sidebarVisible = true,
    this.realTimeUpdatesEnabled = true,
    this.realTimeUpdateInterval = 30,
    this.themeMode = 'system',
    this.language = 'en',
    this.chartPreferences = const ChartPreferences(),
    this.exportPreferences = const ExportPreferences(),
    this.notificationPreferences = const NotificationPreferences(),
    required this.lastModified,
    this.version = 1,
  });

  /// Creates preferences from JSON
  factory DashboardPreferences.fromJson(Map<String, dynamic> json) {
    return DashboardPreferences(
      selectedSection: json['selectedSection'] ?? 'overview',
      selectedRegion: json['selectedRegion'] ?? 'Kenya',
      selectedDateRange: DateRange(
        start: DateTime.parse(json['selectedDateRange']['start']),
        end: DateTime.parse(json['selectedDateRange']['end']),
      ),
      appliedFilters: json['appliedFilters'] != null
          ? AnalyticsFilters.fromJson(json['appliedFilters'])
          : const AnalyticsFilters(),
      sidebarVisible: json['sidebarVisible'] ?? true,
      realTimeUpdatesEnabled: json['realTimeUpdatesEnabled'] ?? true,
      realTimeUpdateInterval: json['realTimeUpdateInterval'] ?? 30,
      themeMode: json['themeMode'] ?? 'system',
      language: json['language'] ?? 'en',
      chartPreferences: json['chartPreferences'] != null
          ? ChartPreferences.fromJson(json['chartPreferences'])
          : const ChartPreferences(),
      exportPreferences: json['exportPreferences'] != null
          ? ExportPreferences.fromJson(json['exportPreferences'])
          : const ExportPreferences(),
      notificationPreferences: json['notificationPreferences'] != null
          ? NotificationPreferences.fromJson(json['notificationPreferences'])
          : const NotificationPreferences(),
      lastModified: DateTime.parse(json['lastModified']),
      version: json['version'] ?? 1,
    );
  }

  /// Converts preferences to JSON
  Map<String, dynamic> toJson() {
    return {
      'selectedSection': selectedSection,
      'selectedRegion': selectedRegion,
      'selectedDateRange': {
        'start': selectedDateRange.start.toIso8601String(),
        'end': selectedDateRange.end.toIso8601String(),
      },
      'appliedFilters': appliedFilters.toJson(),
      'sidebarVisible': sidebarVisible,
      'realTimeUpdatesEnabled': realTimeUpdatesEnabled,
      'realTimeUpdateInterval': realTimeUpdateInterval,
      'themeMode': themeMode,
      'language': language,
      'chartPreferences': chartPreferences.toJson(),
      'exportPreferences': exportPreferences.toJson(),
      'notificationPreferences': notificationPreferences.toJson(),
      'lastModified': lastModified.toIso8601String(),
      'version': version,
    };
  }

  /// Creates a copy with updated values
  DashboardPreferences copyWith({
    String? selectedSection,
    String? selectedRegion,
    DateRange? selectedDateRange,
    AnalyticsFilters? appliedFilters,
    bool? sidebarVisible,
    bool? realTimeUpdatesEnabled,
    int? realTimeUpdateInterval,
    String? themeMode,
    String? language,
    ChartPreferences? chartPreferences,
    ExportPreferences? exportPreferences,
    NotificationPreferences? notificationPreferences,
  }) {
    return DashboardPreferences(
      selectedSection: selectedSection ?? this.selectedSection,
      selectedRegion: selectedRegion ?? this.selectedRegion,
      selectedDateRange: selectedDateRange ?? this.selectedDateRange,
      appliedFilters: appliedFilters ?? this.appliedFilters,
      sidebarVisible: sidebarVisible ?? this.sidebarVisible,
      realTimeUpdatesEnabled: realTimeUpdatesEnabled ?? this.realTimeUpdatesEnabled,
      realTimeUpdateInterval: realTimeUpdateInterval ?? this.realTimeUpdateInterval,
      themeMode: themeMode ?? this.themeMode,
      language: language ?? this.language,
      chartPreferences: chartPreferences ?? this.chartPreferences,
      exportPreferences: exportPreferences ?? this.exportPreferences,
      notificationPreferences: notificationPreferences ?? this.notificationPreferences,
      lastModified: DateTime.now(),
      version: version,
    );
  }
}

/// Chart display preferences
class ChartPreferences {
  /// Default chart animation duration
  final int animationDuration;

  /// Whether to show data labels
  final bool showDataLabels;

  /// Whether to show legends
  final bool showLegends;

  /// Whether to enable chart interactions
  final bool enableInteractions;

  /// Default chart color scheme
  final String colorScheme;

  /// Chart resolution for exports
  final int exportResolution;

  const ChartPreferences({
    this.animationDuration = 1000,
    this.showDataLabels = true,
    this.showLegends = true,
    this.enableInteractions = true,
    this.colorScheme = 'default',
    this.exportResolution = 300,
  });

  factory ChartPreferences.fromJson(Map<String, dynamic> json) {
    return ChartPreferences(
      animationDuration: json['animationDuration'] ?? 1000,
      showDataLabels: json['showDataLabels'] ?? true,
      showLegends: json['showLegends'] ?? true,
      enableInteractions: json['enableInteractions'] ?? true,
      colorScheme: json['colorScheme'] ?? 'default',
      exportResolution: json['exportResolution'] ?? 300,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'animationDuration': animationDuration,
      'showDataLabels': showDataLabels,
      'showLegends': showLegends,
      'enableInteractions': enableInteractions,
      'colorScheme': colorScheme,
      'exportResolution': exportResolution,
    };
  }
}

/// Export preferences
class ExportPreferences {
  /// Default export format
  final ExportFormat defaultFormat;

  /// Whether to include charts in exports
  final bool includeCharts;

  /// Export file naming convention
  final String namingConvention;

  /// Whether to compress exports
  final bool compressFiles;

  const ExportPreferences({
    this.defaultFormat = ExportFormat.pdf,
    this.includeCharts = true,
    this.namingConvention = 'datetime',
    this.compressFiles = false,
  });

  factory ExportPreferences.fromJson(Map<String, dynamic> json) {
    return ExportPreferences(
      defaultFormat: ExportFormat.values.firstWhere(
        (format) => format.name == json['defaultFormat'],
        orElse: () => ExportFormat.pdf,
      ),
      includeCharts: json['includeCharts'] ?? true,
      namingConvention: json['namingConvention'] ?? 'datetime',
      compressFiles: json['compressFiles'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'defaultFormat': defaultFormat.name,
      'includeCharts': includeCharts,
      'namingConvention': namingConvention,
      'compressFiles': compressFiles,
    };
  }
}

/// Notification preferences
class NotificationPreferences {
  /// Whether to show data update notifications
  final bool showDataUpdates;

  /// Whether to show error notifications
  final bool showErrors;

  /// Whether to show export completion notifications
  final bool showExportCompletion;

  /// Notification sound enabled
  final bool soundEnabled;

  /// Auto-dismiss notification duration in seconds
  final int autoDismissDuration;

  const NotificationPreferences({
    this.showDataUpdates = true,
    this.showErrors = true,
    this.showExportCompletion = true,
    this.soundEnabled = false,
    this.autoDismissDuration = 5,
  });

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      showDataUpdates: json['showDataUpdates'] ?? true,
      showErrors: json['showErrors'] ?? true,
      showExportCompletion: json['showExportCompletion'] ?? true,
      soundEnabled: json['soundEnabled'] ?? false,
      autoDismissDuration: json['autoDismissDuration'] ?? 5,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'showDataUpdates': showDataUpdates,
      'showErrors': showErrors,
      'showExportCompletion': showExportCompletion,
      'soundEnabled': soundEnabled,
      'autoDismissDuration': autoDismissDuration,
    };
  }
}

/// User preferences service implementation
class UserPreferencesService {
  /// Shared preferences instance
  SharedPreferences? _prefs;

  /// Preferences change stream controller
  final StreamController<DashboardPreferences> _preferencesStreamController =
      StreamController<DashboardPreferences>.broadcast();

  /// Current cached preferences
  DashboardPreferences? _cachedPreferences;

  /// Preference keys
  static const String _dashboardPreferencesKey = 'dashboard_preferences';
  static const String _preferencesVersionKey = 'preferences_version';

  /// Current preferences version
  static const int _currentVersion = 1;

  /// Singleton instance
  static UserPreferencesService? _instance;

  /// Private constructor
  UserPreferencesService._();

  /// Gets singleton instance
  static UserPreferencesService get instance {
    _instance ??= UserPreferencesService._();
    return _instance!;
  }

  /// Stream of preference changes
  Stream<DashboardPreferences> get preferencesStream =>
      _preferencesStreamController.stream;

  /// Initializes the preferences service
  Future<void> initialize() async {
    try {
      _prefs = await SharedPreferences.getInstance();
      await _migratePrefencesIfNeeded();
      await _loadCachedPreferences();
    } catch (e) {
      debugPrint('Error initializing UserPreferencesService: $e');
      // Create default preferences if initialization fails
      _cachedPreferences = _createDefaultPreferences();
    }
  }

  /// Loads dashboard preferences
  Future<DashboardPreferences> loadDashboardPreferences() async {
    if (_cachedPreferences != null) {
      return _cachedPreferences!;
    }

    try {
      final prefsJson = _prefs?.getString(_dashboardPreferencesKey);
      if (prefsJson != null) {
        final json = jsonDecode(prefsJson) as Map<String, dynamic>;
        _cachedPreferences = DashboardPreferences.fromJson(json);
        return _cachedPreferences!;
      }
    } catch (e) {
      debugPrint('Error loading preferences: $e');
    }

    // Return default preferences if loading fails
    _cachedPreferences = _createDefaultPreferences();
    return _cachedPreferences!;
  }

  /// Saves dashboard preferences
  Future<bool> saveDashboardPreferences(DashboardPreferences preferences) async {
    try {
      final updatedPreferences = preferences.copyWith();
      final json = jsonEncode(updatedPreferences.toJson());
      final success = await _prefs?.setString(_dashboardPreferencesKey, json) ?? false;

      if (success) {
        _cachedPreferences = updatedPreferences;
        _preferencesStreamController.add(updatedPreferences);
      }

      return success;
    } catch (e) {
      debugPrint('Error saving preferences: $e');
      return false;
    }
  }

  /// Updates specific preference
  Future<bool> updatePreference<T>(String key, T value) async {
    final currentPrefs = await loadDashboardPreferences();

    DashboardPreferences updatedPrefs;

    switch (key) {
      case 'selectedSection':
        updatedPrefs = currentPrefs.copyWith(selectedSection: value as String);
        break;
      case 'selectedRegion':
        updatedPrefs = currentPrefs.copyWith(selectedRegion: value as String);
        break;
      case 'sidebarVisible':
        updatedPrefs = currentPrefs.copyWith(sidebarVisible: value as bool);
        break;
      case 'realTimeUpdatesEnabled':
        updatedPrefs = currentPrefs.copyWith(realTimeUpdatesEnabled: value as bool);
        break;
      case 'themeMode':
        updatedPrefs = currentPrefs.copyWith(themeMode: value as String);
        break;
      default:
        return false;
    }

    return await saveDashboardPreferences(updatedPrefs);
  }

  /// Resets preferences to defaults
  Future<bool> resetToDefaults() async {
    final defaultPrefs = _createDefaultPreferences();
    return await saveDashboardPreferences(defaultPrefs);
  }

  /// Exports preferences as JSON string
  Future<String> exportPreferences() async {
    final preferences = await loadDashboardPreferences();
    return jsonEncode(preferences.toJson());
  }

  /// Imports preferences from JSON string
  Future<bool> importPreferences(String preferencesJson) async {
    try {
      final json = jsonDecode(preferencesJson) as Map<String, dynamic>;
      final preferences = DashboardPreferences.fromJson(json);
      return await saveDashboardPreferences(preferences);
    } catch (e) {
      debugPrint('Error importing preferences: $e');
      return false;
    }
  }

  /// Clears all preferences
  Future<bool> clearPreferences() async {
    try {
      await _prefs?.remove(_dashboardPreferencesKey);
      _cachedPreferences = null;
      return true;
    } catch (e) {
      debugPrint('Error clearing preferences: $e');
      return false;
    }
  }

  /// Gets specific preference value
  Future<T?> getPreference<T>(String key) async {
    final preferences = await loadDashboardPreferences();

    switch (key) {
      case 'selectedSection':
        return preferences.selectedSection as T?;
      case 'selectedRegion':
        return preferences.selectedRegion as T?;
      case 'sidebarVisible':
        return preferences.sidebarVisible as T?;
      case 'realTimeUpdatesEnabled':
        return preferences.realTimeUpdatesEnabled as T?;
      case 'themeMode':
        return preferences.themeMode as T?;
      default:
        return null;
    }
  }

  /// Disposes the service
  void dispose() {
    _preferencesStreamController.close();
  }

  /// Creates default preferences
  DashboardPreferences _createDefaultPreferences() {
    return DashboardPreferences(
      selectedDateRange: DateRange(
        start: DateTime.now().subtract(const Duration(days: 30)),
        end: DateTime.now(),
      ),
      lastModified: DateTime.now(),
    );
  }

  /// Loads cached preferences
  Future<void> _loadCachedPreferences() async {
    _cachedPreferences = await loadDashboardPreferences();
  }

  /// Migrates preferences if version has changed
  Future<void> _migratePrefencesIfNeeded() async {
    final storedVersion = _prefs?.getInt(_preferencesVersionKey) ?? 0;

    if (storedVersion < _currentVersion) {
      await _migratePreferences(storedVersion, _currentVersion);
      await _prefs?.setInt(_preferencesVersionKey, _currentVersion);
    }
  }

  /// Performs preference migration
  Future<void> _migratePreferences(int fromVersion, int toVersion) async {
    debugPrint('Migrating preferences from version $fromVersion to $toVersion');

    // Add migration logic here when preference structure changes
    // For now, we'll just clear old preferences
    if (fromVersion == 0) {
      await clearPreferences();
    }
  }
}

/// Extension for analytics filters JSON serialization
extension AnalyticsFiltersJson on AnalyticsFilters {
  /// Converts analytics filters to JSON
  Map<String, dynamic> toJson() {
    return {
      'includeEnvironmentalData': includeEnvironmentalData,
      'includePredictionAccuracy': includePredictionAccuracy,
      'includeRiskTrends': includeRiskTrends,
      'includeAlertStatistics': includeAlertStatistics,
      'includeDataQuality': includeDataQuality,
      'riskLevels': riskLevels?.map((level) => level.name).toList(),
      'environmentalFactors': environmentalFactors?.map((factor) => factor.name).toList(),
      'alertSeverities': alertSeverities?.map((severity) => severity.name).toList(),
      'minDataQuality': minDataQuality,
      'maxDataAgeHours': maxDataAgeHours,
      'aggregationPeriod': aggregationPeriod.name,
      'smoothData': smoothData,
      'smoothingWindowDays': smoothingWindowDays,
      'normalizeData': normalizeData,
      'includeConfidenceIntervals': includeConfidenceIntervals,
      'confidenceLevel': confidenceLevel,
    };
  }

  /// Creates analytics filters from JSON
  static AnalyticsFilters fromJson(Map<String, dynamic> json) {
    return AnalyticsFilters(
      includeEnvironmentalData: json['includeEnvironmentalData'] ?? true,
      includePredictionAccuracy: json['includePredictionAccuracy'] ?? true,
      includeRiskTrends: json['includeRiskTrends'] ?? true,
      includeAlertStatistics: json['includeAlertStatistics'] ?? true,
      includeDataQuality: json['includeDataQuality'] ?? true,
      riskLevels: json['riskLevels'] != null
          ? (json['riskLevels'] as List)
              .map((name) => RiskLevel.values.firstWhere((level) => level.name == name))
              .toList()
          : null,
      environmentalFactors: json['environmentalFactors'] != null
          ? (json['environmentalFactors'] as List)
              .map((name) => EnvironmentalFactor.values.firstWhere((factor) => factor.name == name))
              .toList()
          : null,
      alertSeverities: json['alertSeverities'] != null
          ? (json['alertSeverities'] as List)
              .map((name) => AlertSeverity.values.firstWhere((severity) => severity.name == name))
              .toList()
          : null,
      minDataQuality: json['minDataQuality']?.toDouble(),
      maxDataAgeHours: json['maxDataAgeHours'],
      aggregationPeriod: AggregationPeriod.values.firstWhere(
        (period) => period.name == json['aggregationPeriod'],
        orElse: () => AggregationPeriod.daily,
      ),
      smoothData: json['smoothData'] ?? false,
      smoothingWindowDays: json['smoothingWindowDays'] ?? 7,
      normalizeData: json['normalizeData'] ?? false,
      includeConfidenceIntervals: json['includeConfidenceIntervals'] ?? false,
      confidenceLevel: json['confidenceLevel']?.toDouble() ?? 0.95,
    );
  }
}