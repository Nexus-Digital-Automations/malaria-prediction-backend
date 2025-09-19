/// Layer Opacity Slider Widget for Multi-Layer Mapping System
///
/// Specialized widget for controlling layer opacity and blending modes
/// in the multi-layer mapping system. Provides intuitive controls for
/// transparency, blending effects, and visual layer mixing.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System
/// Created: 2025-09-19
library;

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Comprehensive opacity slider with advanced blending controls
class LayerOpacitySlider extends StatefulWidget {
  /// Layer identifier for tracking changes
  final String layerId;

  /// Initial opacity value (0.0 to 1.0)
  final double initialOpacity;

  /// Callback when opacity changes
  final void Function(double opacity)? onOpacityChanged;

  /// Callback when blending mode changes
  final void Function(BlendMode blendMode)? onBlendModeChanged;

  /// Whether to show advanced blending controls
  final bool showAdvancedControls;

  /// Whether to show opacity percentage label
  final bool showPercentageLabel;

  /// Whether to enable haptic feedback
  final bool enableHapticFeedback;

  /// Custom slider theme
  final LayerOpacitySliderTheme? theme;

  /// Minimum opacity value
  final double minOpacity;

  /// Maximum opacity value
  final double maxOpacity;

  /// Opacity step size for discrete values
  final double? step;

  /// Initial blending mode
  final BlendMode initialBlendMode;

  /// Available blending modes
  final List<BlendMode> availableBlendModes;

  /// Whether slider is enabled
  final bool enabled;

  /// Custom label text
  final String? label;

  /// Whether to animate opacity changes
  final bool animateChanges;

  /// Animation duration for opacity changes
  final Duration animationDuration;

  const LayerOpacitySlider({
    super.key,
    required this.layerId,
    required this.initialOpacity,
    this.onOpacityChanged,
    this.onBlendModeChanged,
    this.showAdvancedControls = false,
    this.showPercentageLabel = true,
    this.enableHapticFeedback = true,
    this.theme,
    this.minOpacity = 0.0,
    this.maxOpacity = 1.0,
    this.step,
    this.initialBlendMode = BlendMode.srcOver,
    this.availableBlendModes = const [
      BlendMode.srcOver,
      BlendMode.multiply,
      BlendMode.screen,
      BlendMode.overlay,
      BlendMode.softLight,
      BlendMode.hardLight,
    ],
    this.enabled = true,
    this.label,
    this.animateChanges = false,
    this.animationDuration = const Duration(milliseconds: 200),
  });

  @override
  State<LayerOpacitySlider> createState() => _LayerOpacitySliderState();
}

class _LayerOpacitySliderState extends State<LayerOpacitySlider>
    with TickerProviderStateMixin {
  late double _currentOpacity;
  late BlendMode _currentBlendMode;
  late AnimationController _animationController;
  late Animation<double> _opacityAnimation;

  bool _isSliding = false;
  bool _showAdvancedPanel = false;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    const String methodName = 'initState';
    debugPrint('[$methodName] Initializing LayerOpacitySlider for layer: ${widget.layerId}');

    _currentOpacity = widget.initialOpacity.clamp(widget.minOpacity, widget.maxOpacity);
    _currentBlendMode = widget.initialBlendMode;

    _animationController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    _opacityAnimation = Tween<double>(
      begin: _currentOpacity,
      end: _currentOpacity,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void didUpdateWidget(LayerOpacitySlider oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.initialOpacity != widget.initialOpacity) {
      _updateOpacity(widget.initialOpacity, fromWidget: true);
    }

    if (oldWidget.initialBlendMode != widget.initialBlendMode) {
      setState(() {
        _currentBlendMode = widget.initialBlendMode;
      });
    }
  }

  @override
  void dispose() {
    const String methodName = 'dispose';
    debugPrint('[$methodName] Disposing LayerOpacitySlider');

    _animationController.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    debugPrint('[$methodName] Building LayerOpacitySlider widget');

    final theme = widget.theme ?? LayerOpacitySliderTheme.defaultTheme(context);

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.backgroundColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.borderColor),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildMainSlider(theme),
          if (widget.showAdvancedControls) ...[
            const SizedBox(height: 8),
            _buildAdvancedToggle(theme),
            if (_showAdvancedPanel) ...[
              const SizedBox(height: 8),
              _buildAdvancedPanel(theme),
            ],
          ],
        ],
      ),
    );
  }

  /// Build the main opacity slider
  Widget _buildMainSlider(LayerOpacitySliderTheme theme) {
    return Column(
      children: [
        if (widget.label != null || widget.showPercentageLabel)
          _buildSliderHeader(theme),
        const SizedBox(height: 4),
        _buildSliderTrack(theme),
        const SizedBox(height: 4),
        _buildSliderControls(theme),
      ],
    );
  }

  /// Build slider header with label and percentage
  Widget _buildSliderHeader(LayerOpacitySliderTheme theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        if (widget.label != null)
          Text(
            widget.label!,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: theme.labelColor,
            ),
          ),
        if (widget.showPercentageLabel)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: theme.percentageBadgeColor,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              '${(_currentOpacity * 100).round()}%',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: theme.percentageTextColor,
              ),
            ),
          ),
      ],
    );
  }

  /// Build custom slider track with gradient preview
  Widget _buildSliderTrack(LayerOpacitySliderTheme theme) {
    return SizedBox(
      height: 32,
      child: Stack(
        children: [
          // Background track with opacity visualization
          Positioned.fill(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(4),
                gradient: LinearGradient(
                  colors: [
                    theme.trackColor.withOpacity(0.0),
                    theme.trackColor.withOpacity(1.0),
                  ],
                ),
                border: Border.all(color: theme.borderColor),
              ),
              child: _buildCheckerboardPattern(),
            ),
          ),

          // Main slider
          Positioned.fill(
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 24,
                thumbShape: _CustomSliderThumbShape(
                  theme: theme,
                  opacity: _currentOpacity,
                ),
                trackShape: _CustomSliderTrackShape(),
                overlayShape: const RoundSliderOverlayShape(overlayRadius: 16),
                activeTrackColor: Colors.transparent,
                inactiveTrackColor: Colors.transparent,
                thumbColor: theme.thumbColor,
                overlayColor: theme.thumbColor.withOpacity(0.2),
              ),
              child: Slider(
                value: _currentOpacity,
                min: widget.minOpacity,
                max: widget.maxOpacity,
                divisions: widget.step != null
                    ? ((widget.maxOpacity - widget.minOpacity) / widget.step!).round()
                    : null,
                onChanged: widget.enabled ? _onSliderChanged : null,
                onChangeStart: _onSliderStart,
                onChangeEnd: _onSliderEnd,
              ),
            ),
          ),

          // Opacity preview overlay
          Positioned(
            left: 16 + (_currentOpacity * (MediaQuery.of(context).size.width - 80)),
            top: 0,
            child: _buildOpacityPreview(theme),
          ),
        ],
      ),
    );
  }

  /// Build checkerboard pattern for transparency visualization
  Widget _buildCheckerboardPattern() {
    return CustomPaint(
      painter: CheckerboardPainter(),
    );
  }

  /// Build opacity preview indicator
  Widget _buildOpacityPreview(LayerOpacitySliderTheme theme) {
    return AnimatedOpacity(
      opacity: _isSliding ? 1.0 : 0.0,
      duration: const Duration(milliseconds: 200),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        decoration: BoxDecoration(
          color: Colors.black87,
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          '${(_currentOpacity * 100).round()}%',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 10,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  /// Build slider control buttons
  Widget _buildSliderControls(LayerOpacitySliderTheme theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _buildQuickOpacityButton(theme, 0.0, 'Hidden'),
        _buildQuickOpacityButton(theme, 0.25, '25%'),
        _buildQuickOpacityButton(theme, 0.5, '50%'),
        _buildQuickOpacityButton(theme, 0.75, '75%'),
        _buildQuickOpacityButton(theme, 1.0, 'Full'),
      ],
    );
  }

  /// Build quick opacity button
  Widget _buildQuickOpacityButton(LayerOpacitySliderTheme theme, double opacity, String label) {
    final isSelected = (_currentOpacity - opacity).abs() < 0.05;

    return GestureDetector(
      onTap: widget.enabled ? () => _updateOpacity(opacity) : null,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isSelected ? theme.selectedButtonColor : theme.buttonColor,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: isSelected ? theme.selectedButtonBorderColor : theme.buttonBorderColor,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 10,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
            color: isSelected ? theme.selectedButtonTextColor : theme.buttonTextColor,
          ),
        ),
      ),
    );
  }

  /// Build advanced controls toggle
  Widget _buildAdvancedToggle(LayerOpacitySliderTheme theme) {
    return GestureDetector(
      onTap: () {
        setState(() {
          _showAdvancedPanel = !_showAdvancedPanel;
        });
      },
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            'Advanced Controls',
            style: TextStyle(
              fontSize: 12,
              color: theme.labelColor,
            ),
          ),
          const SizedBox(width: 4),
          AnimatedRotation(
            turns: _showAdvancedPanel ? 0.5 : 0.0,
            duration: const Duration(milliseconds: 200),
            child: Icon(
              Icons.expand_more,
              size: 16,
              color: theme.iconColor,
            ),
          ),
        ],
      ),
    );
  }

  /// Build advanced controls panel
  Widget _buildAdvancedPanel(LayerOpacitySliderTheme theme) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.advancedPanelColor,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: theme.borderColor),
      ),
      child: Column(
        children: [
          _buildBlendModeSelector(theme),
          const SizedBox(height: 8),
          _buildAdvancedSliders(theme),
        ],
      ),
    );
  }

  /// Build blend mode selector
  Widget _buildBlendModeSelector(LayerOpacitySliderTheme theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Blend Mode',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: theme.labelColor,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 4,
          runSpacing: 4,
          children: widget.availableBlendModes.map((blendMode) {
            final isSelected = _currentBlendMode == blendMode;
            return GestureDetector(
              onTap: () {
                setState(() {
                  _currentBlendMode = blendMode;
                });
                widget.onBlendModeChanged?.call(blendMode);

                if (widget.enableHapticFeedback) {
                  HapticFeedback.lightImpact();
                }
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isSelected ? theme.selectedButtonColor : theme.buttonColor,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: isSelected
                        ? theme.selectedButtonBorderColor
                        : theme.buttonBorderColor,
                  ),
                ),
                child: Text(
                  _getBlendModeDisplayName(blendMode),
                  style: TextStyle(
                    fontSize: 10,
                    color: isSelected
                        ? theme.selectedButtonTextColor
                        : theme.buttonTextColor,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Build additional advanced sliders
  Widget _buildAdvancedSliders(LayerOpacitySliderTheme theme) {
    return Column(
      children: [
        _buildAdvancedSlider(
          'Contrast',
          1.0,
          0.0,
          2.0,
          theme,
          (value) {
            // Handle contrast adjustment
          },
        ),
        const SizedBox(height: 8),
        _buildAdvancedSlider(
          'Brightness',
          0.0,
          -1.0,
          1.0,
          theme,
          (value) {
            // Handle brightness adjustment
          },
        ),
      ],
    );
  }

  /// Build individual advanced slider
  Widget _buildAdvancedSlider(
    String label,
    double value,
    double min,
    double max,
    LayerOpacitySliderTheme theme,
    void Function(double) onChanged,
  ) {
    return Row(
      children: [
        SizedBox(
          width: 60,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: theme.labelColor,
            ),
          ),
        ),
        Expanded(
          child: SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
            ),
            child: Slider(
              value: value,
              min: min,
              max: max,
              onChanged: onChanged,
              activeColor: theme.trackColor,
              inactiveColor: theme.trackColor.withOpacity(0.3),
            ),
          ),
        ),
        SizedBox(
          width: 40,
          child: Text(
            value.toStringAsFixed(1),
            style: TextStyle(
              fontSize: 10,
              color: theme.labelColor,
            ),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    );
  }

  // Event handlers

  void _onSliderChanged(double value) {
    _updateOpacity(value);
  }

  void _onSliderStart(double value) {
    setState(() {
      _isSliding = true;
    });

    if (widget.enableHapticFeedback) {
      HapticFeedback.lightImpact();
    }
  }

  void _onSliderEnd(double value) {
    setState(() {
      _isSliding = false;
    });

    _debouncedCallback(value);

    if (widget.enableHapticFeedback) {
      HapticFeedback.mediumImpact();
    }
  }

  void _updateOpacity(double opacity, {bool fromWidget = false}) {
    const String methodName = '_updateOpacity';
    final clampedOpacity = opacity.clamp(widget.minOpacity, widget.maxOpacity);

    debugPrint('[$methodName] Updating opacity for layer ${widget.layerId}: $clampedOpacity');

    if (!fromWidget && widget.animateChanges) {
      _opacityAnimation = Tween<double>(
        begin: _currentOpacity,
        end: clampedOpacity,
      ).animate(_animationController);

      _animationController.forward(from: 0.0).then((_) {
        setState(() {
          _currentOpacity = clampedOpacity;
        });
      });
    } else {
      setState(() {
        _currentOpacity = clampedOpacity;
      });
    }

    if (!fromWidget) {
      widget.onOpacityChanged?.call(clampedOpacity);
    }
  }

  void _debouncedCallback(double value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 100), () {
      // Final callback after debounce period
      widget.onOpacityChanged?.call(value);
    });
  }

  String _getBlendModeDisplayName(BlendMode blendMode) {
    switch (blendMode) {
      case BlendMode.srcOver:
        return 'Normal';
      case BlendMode.multiply:
        return 'Multiply';
      case BlendMode.screen:
        return 'Screen';
      case BlendMode.overlay:
        return 'Overlay';
      case BlendMode.softLight:
        return 'Soft Light';
      case BlendMode.hardLight:
        return 'Hard Light';
      case BlendMode.colorDodge:
        return 'Color Dodge';
      case BlendMode.colorBurn:
        return 'Color Burn';
      case BlendMode.darken:
        return 'Darken';
      case BlendMode.lighten:
        return 'Lighten';
      case BlendMode.difference:
        return 'Difference';
      case BlendMode.exclusion:
        return 'Exclusion';
      default:
        return blendMode.toString().split('.').last;
    }
  }
}

// Custom slider components

class _CustomSliderThumbShape extends SliderComponentShape {
  final LayerOpacitySliderTheme theme;
  final double opacity;

  const _CustomSliderThumbShape({
    required this.theme,
    required this.opacity,
  });

  @override
  Size getPreferredSize(bool isEnabled, bool isDiscrete) {
    return const Size(20, 20);
  }

  @override
  void paint(
    PaintingContext context,
    Offset center, {
    required Animation<double> activationAnimation,
    required Animation<double> enableAnimation,
    required bool isDiscrete,
    required TextPainter labelPainter,
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required TextDirection textDirection,
    required double value,
    required double textScaleFactor,
    required Size sizeWithOverflow,
  }) {
    final Canvas canvas = context.canvas;

    // Draw thumb shadow
    final shadowPaint = Paint()
      ..color = Colors.black.withOpacity(0.2)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2);
    canvas.drawCircle(center + const Offset(0, 1), 10, shadowPaint);

    // Draw thumb background
    final thumbPaint = Paint()
      ..color = theme.thumbColor
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 9, thumbPaint);

    // Draw opacity indicator
    final opacityPaint = Paint()
      ..color = Colors.white.withOpacity(opacity)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 6, opacityPaint);

    // Draw thumb border
    final borderPaint = Paint()
      ..color = theme.thumbBorderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawCircle(center, 9, borderPaint);
  }
}

class _CustomSliderTrackShape extends SliderTrackShape {
  @override
  Rect getPreferredRect({
    required RenderBox parentBox,
    Offset offset = Offset.zero,
    required SliderThemeData sliderTheme,
    bool isEnabled = false,
    bool isDiscrete = false,
  }) {
    final double trackHeight = sliderTheme.trackHeight!;
    final double trackLeft = offset.dx;
    final double trackTop = offset.dy + (parentBox.size.height - trackHeight) / 2;
    final double trackWidth = parentBox.size.width;
    return Rect.fromLTWH(trackLeft, trackTop, trackWidth, trackHeight);
  }

  @override
  void paint(
    PaintingContext context,
    Offset offset, {
    required RenderBox parentBox,
    required SliderThemeData sliderTheme,
    required Animation<double> enableAnimation,
    required Offset thumbCenter,
    bool isEnabled = false,
    bool isDiscrete = false,
    required TextDirection textDirection,
  }) {
    // Custom track painting is handled by the background container
  }
}

class CheckerboardPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    const double squareSize = 4.0;
    final Paint lightPaint = Paint()..color = Colors.white;
    final Paint darkPaint = Paint()..color = Colors.grey.shade300;

    for (double x = 0; x < size.width; x += squareSize) {
      for (double y = 0; y < size.height; y += squareSize) {
        final bool isLight = ((x / squareSize).floor() + (y / squareSize).floor()) % 2 == 0;
        canvas.drawRect(
          Rect.fromLTWH(x, y, squareSize, squareSize),
          isLight ? lightPaint : darkPaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// Theme configuration

class LayerOpacitySliderTheme {
  final Color backgroundColor;
  final Color borderColor;
  final Color trackColor;
  final Color thumbColor;
  final Color thumbBorderColor;
  final Color labelColor;
  final Color iconColor;
  final Color buttonColor;
  final Color buttonBorderColor;
  final Color buttonTextColor;
  final Color selectedButtonColor;
  final Color selectedButtonBorderColor;
  final Color selectedButtonTextColor;
  final Color percentageBadgeColor;
  final Color percentageTextColor;
  final Color advancedPanelColor;

  const LayerOpacitySliderTheme({
    required this.backgroundColor,
    required this.borderColor,
    required this.trackColor,
    required this.thumbColor,
    required this.thumbBorderColor,
    required this.labelColor,
    required this.iconColor,
    required this.buttonColor,
    required this.buttonBorderColor,
    required this.buttonTextColor,
    required this.selectedButtonColor,
    required this.selectedButtonBorderColor,
    required this.selectedButtonTextColor,
    required this.percentageBadgeColor,
    required this.percentageTextColor,
    required this.advancedPanelColor,
  });

  static LayerOpacitySliderTheme defaultTheme(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return LayerOpacitySliderTheme(
      backgroundColor: theme.cardColor,
      borderColor: theme.dividerColor,
      trackColor: theme.primaryColor,
      thumbColor: Colors.white,
      thumbBorderColor: theme.primaryColor,
      labelColor: theme.textTheme.bodyMedium?.color ?? Colors.black87,
      iconColor: theme.iconTheme.color ?? Colors.grey,
      buttonColor: isDark ? Colors.grey.shade800 : Colors.grey.shade100,
      buttonBorderColor: theme.dividerColor,
      buttonTextColor: theme.textTheme.bodySmall?.color ?? Colors.grey.shade600,
      selectedButtonColor: theme.primaryColor,
      selectedButtonBorderColor: theme.primaryColor,
      selectedButtonTextColor: Colors.white,
      percentageBadgeColor: theme.primaryColor,
      percentageTextColor: Colors.white,
      advancedPanelColor: isDark ? Colors.grey.shade900 : Colors.grey.shade50,
    );
  }
}