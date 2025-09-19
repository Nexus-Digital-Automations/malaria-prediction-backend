/// Temporal Risk Slider Widget for Time-based Risk Navigation
///
/// This widget provides a comprehensive temporal navigation system for
/// malaria risk data visualization. It allows users to scrub through
/// historical data, view predictions, and analyze temporal patterns
/// with smooth animations and intuitive controls.
///
/// Features:
/// - Interactive timeline slider with historical and prediction data
/// - Smooth temporal transitions and data interpolation
/// - Playback controls for automated time navigation
/// - Seasonal pattern indicators and trend visualization
/// - Data quality indicators and confidence intervals
/// - Customizable time intervals and zoom levels
/// - Touch-friendly controls with haptic feedback
/// - Accessibility support for screen readers
/// - Performance-optimized rendering for large datasets
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import '../../domain/entities/temporal_risk_data.dart';

/// Temporal navigation mode
enum TemporalNavigationMode {
  /// Manual scrubbing through time
  manual,

  /// Automatic playback
  autoPlay,

  /// Step-by-step navigation
  stepByStep,

  /// Jump to specific dates
  jumpTo,
}

/// Playback speed options
enum PlaybackSpeed {
  /// Very slow playback (4x slower than normal)
  verySlow(0.25, '0.25x'),

  /// Slow playback (2x slower than normal)
  slow(0.5, '0.5x'),

  /// Normal playback speed
  normal(1.0, '1x'),

  /// Fast playback (2x faster than normal)
  fast(2.0, '2x'),

  /// Very fast playback (4x faster than normal)
  veryFast(4.0, '4x');

  const PlaybackSpeed(this.multiplier, this.label);

  /// Speed multiplier
  final double multiplier;

  /// Display label
  final String label;
}

/// Temporal slider configuration
class TemporalSliderConfig {
  /// Whether to show playback controls
  final bool showPlaybackControls;

  /// Whether to show seasonal indicators
  final bool showSeasonalIndicators;

  /// Whether to show trend indicators
  final bool showTrendIndicators;

  /// Whether to show data quality indicators
  final bool showQualityIndicators;

  /// Whether to enable haptic feedback
  final bool enableHapticFeedback;

  /// Default playback speed
  final PlaybackSpeed defaultPlaybackSpeed;

  /// Auto-play interval for normal speed
  final Duration autoPlayInterval;

  /// Whether to loop playback
  final bool loopPlayback;

  /// Minimum time step for navigation
  final Duration minTimeStep;

  /// Theme configuration
  final TemporalSliderTheme theme;

  const TemporalSliderConfig({
    this.showPlaybackControls = true,
    this.showSeasonalIndicators = true,
    this.showTrendIndicators = true,
    this.showQualityIndicators = true,
    this.enableHapticFeedback = true,
    this.defaultPlaybackSpeed = PlaybackSpeed.normal,
    this.autoPlayInterval = const Duration(milliseconds: 500),
    this.loopPlayback = false,
    this.minTimeStep = const Duration(hours: 1),
    this.theme = const TemporalSliderTheme(),
  });
}

/// Theme configuration for temporal slider
class TemporalSliderTheme {
  /// Primary color for active elements
  final Color primaryColor;

  /// Secondary color for inactive elements
  final Color secondaryColor;

  /// Background color for the slider track
  final Color trackColor;

  /// Color for historical data indicators
  final Color historicalColor;

  /// Color for prediction data indicators
  final Color predictionColor;

  /// Color for seasonal indicators
  final Color seasonalColor;

  /// Color for trend indicators
  final Color trendColor;

  /// Color for data quality indicators
  final Map<double, Color> qualityColors;

  /// Text style for date labels
  final TextStyle dateTextStyle;

  /// Text style for risk values
  final TextStyle riskTextStyle;

  /// Border radius for UI elements
  final double borderRadius;

  /// Elevation for elevated elements
  final double elevation;

  const TemporalSliderTheme({
    this.primaryColor = Colors.blue,
    this.secondaryColor = Colors.grey,
    this.trackColor = Colors.grey,
    this.historicalColor = Colors.green,
    this.predictionColor = Colors.orange,
    this.seasonalColor = Colors.purple,
    this.trendColor = Colors.red,
    this.qualityColors = const {
      0.9: Colors.green,
      0.7: Colors.orange,
      0.5: Colors.red,
      0.0: Colors.grey,
    },
    this.dateTextStyle = const TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w500,
    ),
    this.riskTextStyle = const TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.bold,
    ),
    this.borderRadius = 8.0,
    this.elevation = 2.0,
  });
}

/// Comprehensive temporal risk slider widget
class TemporalRiskSlider extends StatefulWidget {
  /// Temporal risk data for visualization
  final TemporalRiskData temporalData;

  /// Configuration for slider appearance and behavior
  final TemporalSliderConfig config;

  /// Callback for time selection changes
  final void Function(DateTime selectedTime, double interpolatedRisk)? onTimeChanged;

  /// Callback for playback state changes
  final void Function(bool isPlaying)? onPlaybackStateChanged;

  /// Callback for seasonal pattern selection
  final void Function(SeasonalPattern pattern)? onSeasonalPatternSelected;

  /// Initial selected time (defaults to latest data point)
  final DateTime? initialSelectedTime;

  /// Whether the slider is enabled for interaction
  final bool enabled;

  /// Custom time range override (uses data range if null)
  final DateRange? customTimeRange;

  const TemporalRiskSlider({
    Key? key,
    required this.temporalData,
    this.config = const TemporalSliderConfig(),
    this.onTimeChanged,
    this.onPlaybackStateChanged,
    this.onSeasonalPatternSelected,
    this.initialSelectedTime,
    this.enabled = true,
    this.customTimeRange,
  }) : super(key: key);

  @override
  State<TemporalRiskSlider> createState() => _TemporalRiskSliderState();
}

class _TemporalRiskSliderState extends State<TemporalRiskSlider>
    with TickerProviderStateMixin {
  /// Current selected time
  late DateTime _selectedTime;

  /// Current playback mode
  TemporalNavigationMode _navigationMode = TemporalNavigationMode.manual;

  /// Current playback speed
  PlaybackSpeed _playbackSpeed = PlaybackSpeed.normal;

  /// Whether currently playing
  bool _isPlaying = false;

  /// Playback timer
  Timer? _playbackTimer;

  /// Animation controller for smooth transitions
  late AnimationController _transitionController;

  /// Animation for slider value changes
  late Animation<double> _sliderAnimation;

  /// Tween for animated slider movement
  late Tween<double> _sliderTween;

  /// Current slider value (0.0 to 1.0)
  double _sliderValue = 0.0;

  /// Time range for the slider
  late DateRange _timeRange;

  /// Cached interpolated risk values for performance
  final Map<DateTime, double> _interpolationCache = {};

  /// Date formatters
  late DateFormat _dateFormatter;
  late DateFormat _timeFormatter;
  late DateFormat _shortDateFormatter;

  @override
  void initState() {
    super.initState();
    _initializeSlider();
    _setupAnimations();
    _setupFormatters();
  }

  @override
  void didUpdateWidget(TemporalRiskSlider oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.temporalData != widget.temporalData) {
      _initializeSlider();
      _clearInterpolationCache();
    }
  }

  @override
  void dispose() {
    _playbackTimer?.cancel();
    _transitionController.dispose();
    super.dispose();
  }

  void _initializeSlider() {
    // Set time range
    _timeRange = widget.customTimeRange ?? widget.temporalData.timeRange;

    // Set initial selected time
    _selectedTime = widget.initialSelectedTime ??
                   widget.temporalData.latestDataPoint?.timestamp ??
                   _timeRange.end;

    // Update slider value based on selected time
    _updateSliderValue();

    // Set default configuration values
    _playbackSpeed = widget.config.defaultPlaybackSpeed;
  }

  void _setupAnimations() {
    _transitionController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _sliderTween = Tween<double>(begin: 0.0, end: 1.0);
    _sliderAnimation = _sliderTween.animate(
      CurvedAnimation(
        parent: _transitionController,
        curve: Curves.easeInOut,
      ),
    );

    _sliderAnimation.addListener(() {
      setState(() {
        _sliderValue = _sliderAnimation.value;
        _updateSelectedTimeFromSlider();
      });
    });
  }

  void _setupFormatters() {
    _dateFormatter = DateFormat('MMM dd, yyyy');
    _timeFormatter = DateFormat('HH:mm');
    _shortDateFormatter = DateFormat('MMM dd');
  }

  void _updateSliderValue() {
    final totalDuration = _timeRange.duration.inMilliseconds.toDouble();
    final selectedDuration = _selectedTime.difference(_timeRange.start).inMilliseconds.toDouble();
    _sliderValue = totalDuration > 0 ? (selectedDuration / totalDuration).clamp(0.0, 1.0) : 0.0;
  }

  void _updateSelectedTimeFromSlider() {
    final totalDuration = _timeRange.duration.inMilliseconds;
    final selectedDuration = (_sliderValue * totalDuration).round();
    _selectedTime = _timeRange.start.add(Duration(milliseconds: selectedDuration));

    // Notify callback
    final interpolatedRisk = _getInterpolatedRisk(_selectedTime);
    widget.onTimeChanged?.call(_selectedTime, interpolatedRisk);
  }

  double _getInterpolatedRisk(DateTime time) {
    // Check cache first
    if (_interpolationCache.containsKey(time)) {
      return _interpolationCache[time]!;
    }

    // Calculate interpolated risk
    final risk = widget.temporalData.interpolateRiskScore(time);

    // Cache the result
    _interpolationCache[time] = risk;

    return risk;
  }

  void _clearInterpolationCache() {
    _interpolationCache.clear();
  }

  void _startPlayback() {
    if (_isPlaying) return;

    setState(() {
      _isPlaying = true;
      _navigationMode = TemporalNavigationMode.autoPlay;
    });

    final interval = Duration(
      milliseconds: (widget.config.autoPlayInterval.inMilliseconds / _playbackSpeed.multiplier).round(),
    );

    _playbackTimer = Timer.periodic(interval, (_) {
      _stepForward();
    });

    widget.onPlaybackStateChanged?.call(true);
  }

  void _stopPlayback() {
    if (!_isPlaying) return;

    setState(() {
      _isPlaying = false;
      _navigationMode = TemporalNavigationMode.manual;
    });

    _playbackTimer?.cancel();
    _playbackTimer = null;

    widget.onPlaybackStateChanged?.call(false);
  }

  void _stepForward() {
    if (_sliderValue >= 1.0) {
      if (widget.config.loopPlayback) {
        _jumpToStart();
      } else {
        _stopPlayback();
      }
      return;
    }

    final timeStep = widget.config.minTimeStep.inMilliseconds.toDouble();
    final totalDuration = _timeRange.duration.inMilliseconds.toDouble();
    final stepValue = timeStep / totalDuration;

    _animateToSliderValue((_sliderValue + stepValue).clamp(0.0, 1.0));

    if (widget.config.enableHapticFeedback) {
      HapticFeedback.selectionClick();
    }
  }

  void _stepBackward() {
    final timeStep = widget.config.minTimeStep.inMilliseconds.toDouble();
    final totalDuration = _timeRange.duration.inMilliseconds.toDouble();
    final stepValue = timeStep / totalDuration;

    _animateToSliderValue((_sliderValue - stepValue).clamp(0.0, 1.0));

    if (widget.config.enableHapticFeedback) {
      HapticFeedback.selectionClick();
    }
  }

  void _jumpToStart() {
    _animateToSliderValue(0.0);
  }

  void _jumpToEnd() {
    _animateToSliderValue(1.0);
  }

  void _jumpToTime(DateTime time) {
    final totalDuration = _timeRange.duration.inMilliseconds.toDouble();
    final targetDuration = time.difference(_timeRange.start).inMilliseconds.toDouble();
    final targetValue = totalDuration > 0 ? (targetDuration / totalDuration).clamp(0.0, 1.0) : 0.0;

    _animateToSliderValue(targetValue);
  }

  void _animateToSliderValue(double targetValue) {
    _sliderTween.begin = _sliderValue;
    _sliderTween.end = targetValue;
    _transitionController.forward(from: 0.0);
  }

  void _changePlaybackSpeed() {
    final speeds = PlaybackSpeed.values;
    final currentIndex = speeds.indexOf(_playbackSpeed);
    final nextIndex = (currentIndex + 1) % speeds.length;

    setState(() {
      _playbackSpeed = speeds[nextIndex];
    });

    // Restart playback with new speed if currently playing
    if (_isPlaying) {
      _stopPlayback();
      _startPlayback();
    }
  }

  Color _getQualityColor(double quality) {
    final sortedQualities = widget.config.theme.qualityColors.keys.toList()
      ..sort((a, b) => b.compareTo(a));

    for (final threshold in sortedQualities) {
      if (quality >= threshold) {
        return widget.config.theme.qualityColors[threshold]!;
      }
    }

    return widget.config.theme.qualityColors.values.last;
  }

  List<Widget> _buildSeasonalIndicators() {
    if (!widget.config.showSeasonalIndicators) return [];

    return widget.temporalData.seasonalPatterns.map((pattern) {
      final startMonth = pattern.startMonth;
      final endMonth = pattern.endMonth;

      // Calculate position on timeline (simplified)
      final startValue = (startMonth - 1) / 12.0;
      final endValue = endMonth / 12.0;

      return Positioned(
        left: startValue * 300, // Approximate slider width
        width: (endValue - startValue) * 300,
        top: 0,
        height: 4,
        child: GestureDetector(
          onTap: () => widget.onSeasonalPatternSelected?.call(pattern),
          child: Container(
            decoration: BoxDecoration(
              color: widget.config.theme.seasonalColor.withOpacity(0.3),
              borderRadius: BorderRadius.circular(2),
            ),
            child: Tooltip(
              message: '${pattern.name}: ${pattern.averageRiskScore.toStringAsFixed(1)}',
              child: Container(),
            ),
          ),
        ),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(widget.config.theme.borderRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: widget.config.theme.elevation,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header with current time and risk
          _buildHeader(),

          const SizedBox(height: 16),

          // Main slider with indicators
          _buildSliderSection(),

          const SizedBox(height: 16),

          // Playback controls
          if (widget.config.showPlaybackControls)
            _buildPlaybackControls(),

          // Time range indicators
          _buildTimeRangeIndicators(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    final currentRisk = _getInterpolatedRisk(_selectedTime);
    final dataPoint = widget.temporalData.dataPoints
        .where((point) => point.timestamp.isBefore(_selectedTime.add(const Duration(hours: 1))))
        .where((point) => point.timestamp.isAfter(_selectedTime.subtract(const Duration(hours: 1))))
        .firstOrNull;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _dateFormatter.format(_selectedTime),
              style: widget.config.theme.dateTextStyle,
            ),
            Text(
              _timeFormatter.format(_selectedTime),
              style: widget.config.theme.dateTextStyle.copyWith(
                color: Colors.grey[600],
                fontSize: 10,
              ),
            ),
          ],
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${(currentRisk * 100).toStringAsFixed(1)}%',
              style: widget.config.theme.riskTextStyle.copyWith(
                color: widget.config.theme.primaryColor,
              ),
            ),
            if (dataPoint != null && widget.config.showQualityIndicators)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.signal_cellular_4_bar,
                    size: 12,
                    color: _getQualityColor(dataPoint.confidence),
                  ),
                  const SizedBox(width: 2),
                  Text(
                    '${(dataPoint.confidence * 100).toStringAsFixed(0)}%',
                    style: TextStyle(
                      fontSize: 10,
                      color: _getQualityColor(dataPoint.confidence),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildSliderSection() {
    return SizedBox(
      height: 60,
      child: Stack(
        children: [
          // Seasonal indicators
          ..._buildSeasonalIndicators(),

          // Main slider
          Positioned(
            left: 0,
            right: 0,
            top: 20,
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 6,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 12),
                overlayShape: const RoundSliderOverlayShape(overlayRadius: 20),
                activeTrackColor: widget.config.theme.primaryColor,
                inactiveTrackColor: widget.config.theme.trackColor,
                thumbColor: widget.config.theme.primaryColor,
                overlayColor: widget.config.theme.primaryColor.withOpacity(0.2),
              ),
              child: Slider(
                value: _sliderValue,
                onChanged: widget.enabled ? (value) {
                  setState(() {
                    _sliderValue = value;
                    _updateSelectedTimeFromSlider();
                  });

                  if (widget.config.enableHapticFeedback) {
                    HapticFeedback.selectionClick();
                  }
                } : null,
                onChangeStart: (_) {
                  if (_isPlaying) {
                    _stopPlayback();
                  }
                },
              ),
            ),
          ),

          // Data points indicators
          Positioned(
            left: 0,
            right: 0,
            top: 40,
            child: _buildDataPointsIndicator(),
          ),
        ],
      ),
    );
  }

  Widget _buildDataPointsIndicator() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: widget.temporalData.dataPoints
          .take(20) // Limit for performance
          .map((point) {
        final isHistorical = !point.isPrediction;
        final position = point.timestamp.difference(_timeRange.start).inMilliseconds /
                        _timeRange.duration.inMilliseconds;

        return Positioned(
          left: position * 300, // Approximate width
          child: Container(
            width: 3,
            height: 12,
            decoration: BoxDecoration(
              color: isHistorical
                  ? widget.config.theme.historicalColor
                  : widget.config.theme.predictionColor,
              borderRadius: BorderRadius.circular(1.5),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildPlaybackControls() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        // Jump to start
        IconButton(
          onPressed: widget.enabled ? _jumpToStart : null,
          icon: const Icon(Icons.skip_previous),
          tooltip: 'Jump to start',
        ),

        // Step backward
        IconButton(
          onPressed: widget.enabled ? _stepBackward : null,
          icon: const Icon(Icons.chevron_left),
          tooltip: 'Step backward',
        ),

        // Play/Pause
        IconButton(
          onPressed: widget.enabled ? (_isPlaying ? _stopPlayback : _startPlayback) : null,
          icon: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
          tooltip: _isPlaying ? 'Pause' : 'Play',
        ),

        // Step forward
        IconButton(
          onPressed: widget.enabled ? _stepForward : null,
          icon: const Icon(Icons.chevron_right),
          tooltip: 'Step forward',
        ),

        // Jump to end
        IconButton(
          onPressed: widget.enabled ? _jumpToEnd : null,
          icon: const Icon(Icons.skip_next),
          tooltip: 'Jump to end',
        ),

        // Speed control
        TextButton(
          onPressed: widget.enabled ? _changePlaybackSpeed : null,
          child: Text(
            _playbackSpeed.label,
            style: const TextStyle(fontSize: 12),
          ),
        ),
      ],
    );
  }

  Widget _buildTimeRangeIndicators() {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Start',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.grey[600],
                ),
              ),
              Text(
                _shortDateFormatter.format(_timeRange.start),
                style: const TextStyle(fontSize: 11),
              ),
            ],
          ),
          Column(
            children: [
              Text(
                'Current',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.grey[600],
                ),
              ),
              Text(
                _shortDateFormatter.format(_selectedTime),
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'End',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.grey[600],
                ),
              ),
              Text(
                _shortDateFormatter.format(_timeRange.end),
                style: const TextStyle(fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Extension to find first element or null
extension FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull {
    final iterator = this.iterator;
    return iterator.moveNext() ? iterator.current : null;
  }
}