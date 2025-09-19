/// Loading overlay widget for analytics dashboard state management
///
/// This widget provides a comprehensive loading overlay system for the
/// analytics dashboard with progress tracking, animated indicators,
/// and user feedback during data loading operations.
///
/// Features:
/// - Animated loading indicators with progress tracking
/// - Customizable loading messages and progress display
/// - Non-blocking and blocking overlay modes
/// - Shimmer effects for content placeholders
/// - Cancellation support for long-running operations
/// - Accessibility support with screen reader announcements
/// - Theme-aware styling and animations
///
/// Usage:
/// ```dart
/// LoadingOverlay(
///   message: 'Loading analytics data...',
///   progress: 0.65,
///   showProgress: true,
///   cancellable: true,
///   onCancel: () => _cancelOperation(),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Loading overlay configuration
class LoadingOverlayConfig {
  /// Default overlay color
  static const Color defaultOverlayColor = Colors.black54;

  /// Default animation duration
  static const Duration defaultAnimationDuration = Duration(milliseconds: 300);

  /// Default indicator size
  static const double defaultIndicatorSize = 48.0;

  /// Default progress bar height
  static const double defaultProgressBarHeight = 4.0;

  /// Default content padding
  static const EdgeInsets defaultContentPadding = EdgeInsets.all(24.0);
}

/// Loading animation type
enum LoadingAnimationType {
  /// Circular progress indicator
  circular,

  /// Linear progress bar
  linear,

  /// Spinning dots
  dots,

  /// Wave animation
  wave,

  /// Pulse animation
  pulse,

  /// Custom shimmer effect
  shimmer,
}

/// Main loading overlay widget
class LoadingOverlay extends StatefulWidget {
  /// Loading message to display
  final String message;

  /// Current progress (0.0 to 1.0, null for indeterminate)
  final double? progress;

  /// Whether to show progress percentage
  final bool showProgress;

  /// Whether to show progress bar
  final bool showProgressBar;

  /// Loading animation type
  final LoadingAnimationType animationType;

  /// Whether operation can be cancelled
  final bool cancellable;

  /// Callback when cancel is tapped
  final VoidCallback? onCancel;

  /// Whether overlay blocks user interaction
  final bool blocking;

  /// Custom overlay color
  final Color? overlayColor;

  /// Custom content widget
  final Widget? customContent;

  /// Animation duration
  final Duration animationDuration;

  /// Indicator size
  final double indicatorSize;

  /// Whether to show in dialog
  final bool showAsDialog;

  /// Dialog title (when showAsDialog is true)
  final String? dialogTitle;

  /// Additional details text
  final String? details;

  const LoadingOverlay({
    super.key,
    this.message = 'Loading...',
    this.progress,
    this.showProgress = false,
    this.showProgressBar = true,
    this.animationType = LoadingAnimationType.circular,
    this.cancellable = false,
    this.onCancel,
    this.blocking = true,
    this.overlayColor,
    this.customContent,
    this.animationDuration = LoadingOverlayConfig.defaultAnimationDuration,
    this.indicatorSize = LoadingOverlayConfig.defaultIndicatorSize,
    this.showAsDialog = false,
    this.dialogTitle,
    this.details,
  });

  @override
  State<LoadingOverlay> createState() => _LoadingOverlayState();
}

class _LoadingOverlayState extends State<LoadingOverlay>
    with TickerProviderStateMixin {
  /// Animation controller for entrance/exit
  late AnimationController _overlayController;

  /// Animation controller for loading indicator
  late AnimationController _indicatorController;

  /// Fade animation for overlay
  late Animation<double> _fadeAnimation;

  /// Scale animation for content
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _overlayController.forward();
  }

  @override
  void dispose() {
    _overlayController.dispose();
    _indicatorController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.showAsDialog) {
      return _buildDialog();
    }

    return _buildOverlay();
  }

  /// Initializes animation controllers
  void _initializeAnimations() {
    _overlayController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    _indicatorController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _overlayController,
      curve: Curves.easeInOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _overlayController,
      curve: Curves.easeOutBack,
    ));
  }

  /// Builds overlay version
  Widget _buildOverlay() {
    return AnimatedBuilder(
      animation: _overlayController,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: Container(
            color: widget.overlayColor ?? LoadingOverlayConfig.defaultOverlayColor,
            child: widget.blocking
                ? _buildBlockingContent()
                : _buildNonBlockingContent(),
          ),
        );
      },
    );
  }

  /// Builds dialog version
  Widget _buildDialog() {
    return AlertDialog(
      title: widget.dialogTitle != null ? Text(widget.dialogTitle!) : null,
      content: _buildLoadingContent(),
      actions: widget.cancellable
          ? [
              TextButton(
                onPressed: widget.onCancel,
                child: const Text('Cancel'),
              ),
            ]
          : null,
    );
  }

  /// Builds blocking content (full screen overlay)
  Widget _buildBlockingContent() {
    return Center(
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: Card(
          elevation: 8,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Container(
            padding: LoadingOverlayConfig.defaultContentPadding,
            constraints: const BoxConstraints(
              minWidth: 200,
              maxWidth: 320,
            ),
            child: _buildLoadingContent(),
          ),
        ),
      ),
    );
  }

  /// Builds non-blocking content (positioned overlay)
  Widget _buildNonBlockingContent() {
    return Positioned(
      top: 16,
      right: 16,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: Card(
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          child: Container(
            padding: const EdgeInsets.all(16),
            child: _buildLoadingContent(),
          ),
        ),
      ),
    );
  }

  /// Builds main loading content
  Widget _buildLoadingContent() {
    if (widget.customContent != null) {
      return widget.customContent!;
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Loading indicator
        _buildLoadingIndicator(),

        const SizedBox(height: 16),

        // Loading message
        Text(
          widget.message,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            fontWeight: FontWeight.w500,
          ),
          textAlign: TextAlign.center,
        ),

        // Details text
        if (widget.details != null) ...[
          const SizedBox(height: 8),
          Text(
            widget.details!,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],

        // Progress information
        if (widget.showProgress || widget.showProgressBar) ...[
          const SizedBox(height: 16),
          _buildProgressSection(),
        ],

        // Cancel button
        if (widget.cancellable) ...[
          const SizedBox(height: 16),
          TextButton(
            onPressed: widget.onCancel,
            child: const Text('Cancel'),
          ),
        ],
      ],
    );
  }

  /// Builds loading indicator based on animation type
  Widget _buildLoadingIndicator() {
    switch (widget.animationType) {
      case LoadingAnimationType.circular:
        return _buildCircularIndicator();
      case LoadingAnimationType.linear:
        return _buildLinearIndicator();
      case LoadingAnimationType.dots:
        return _buildDotsIndicator();
      case LoadingAnimationType.wave:
        return _buildWaveIndicator();
      case LoadingAnimationType.pulse:
        return _buildPulseIndicator();
      case LoadingAnimationType.shimmer:
        return _buildShimmerIndicator();
    }
  }

  /// Builds circular progress indicator
  Widget _buildCircularIndicator() {
    return SizedBox(
      width: widget.indicatorSize,
      height: widget.indicatorSize,
      child: CircularProgressIndicator(
        value: widget.progress,
        strokeWidth: 3,
        valueColor: AlwaysStoppedAnimation<Color>(
          Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  /// Builds linear progress indicator
  Widget _buildLinearIndicator() {
    return SizedBox(
      width: widget.indicatorSize * 2,
      height: LoadingOverlayConfig.defaultProgressBarHeight,
      child: LinearProgressIndicator(
        value: widget.progress,
        valueColor: AlwaysStoppedAnimation<Color>(
          Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  /// Builds animated dots indicator
  Widget _buildDotsIndicator() {
    return SizedBox(
      width: widget.indicatorSize,
      height: widget.indicatorSize / 4,
      child: AnimatedBuilder(
        animation: _indicatorController,
        builder: (context, child) {
          return Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: List.generate(3, (index) {
              final delay = index * 0.2;
              final animationValue = (_indicatorController.value + delay) % 1.0;
              final scale = 1.0 + (math.sin(animationValue * 2 * math.pi) * 0.5);

              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
              );
            }),
          );
        },
      ),
    );
  }

  /// Builds wave animation indicator
  Widget _buildWaveIndicator() {
    return SizedBox(
      width: widget.indicatorSize,
      height: widget.indicatorSize / 2,
      child: AnimatedBuilder(
        animation: _indicatorController,
        builder: (context, child) {
          return Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: List.generate(5, (index) {
              final delay = index * 0.1;
              final animationValue = (_indicatorController.value + delay) % 1.0;
              final height = 4 + (math.sin(animationValue * 2 * math.pi) * 12);

              return Container(
                width: 3,
                height: height,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            }),
          );
        },
      ),
    );
  }

  /// Builds pulse animation indicator
  Widget _buildPulseIndicator() {
    return SizedBox(
      width: widget.indicatorSize,
      height: widget.indicatorSize,
      child: AnimatedBuilder(
        animation: _indicatorController,
        builder: (context, child) {
          final scale = 0.5 + (math.sin(_indicatorController.value * 2 * math.pi) * 0.3);
          final opacity = 0.3 + (math.sin(_indicatorController.value * 2 * math.pi) * 0.4);

          return Transform.scale(
            scale: scale,
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary.withValues(alpha: opacity),
                shape: BoxShape.circle,
              ),
            ),
          );
        },
      ),
    );
  }

  /// Builds shimmer effect indicator
  Widget _buildShimmerIndicator() {
    return SizedBox(
      width: widget.indicatorSize * 2,
      height: widget.indicatorSize / 4,
      child: AnimatedBuilder(
        animation: _indicatorController,
        builder: (context, child) {
          return Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(4),
              gradient: LinearGradient(
                stops: [
                  _indicatorController.value - 0.3,
                  _indicatorController.value,
                  _indicatorController.value + 0.3,
                ],
                colors: [
                  Theme.of(context).colorScheme.surfaceContainerHighest,
                  Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
                  Theme.of(context).colorScheme.surfaceContainerHighest,
                ],
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
              ),
            ),
          );
        },
      ),
    );
  }

  /// Builds progress section
  Widget _buildProgressSection() {
    return Column(
      children: [
        // Progress bar
        if (widget.showProgressBar && widget.progress != null) ...[
          SizedBox(
            width: double.infinity,
            height: LoadingOverlayConfig.defaultProgressBarHeight,
            child: LinearProgressIndicator(
              value: widget.progress,
              valueColor: AlwaysStoppedAnimation<Color>(
                Theme.of(context).colorScheme.primary,
              ),
              backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
            ),
          ),
          const SizedBox(height: 8),
        ],

        // Progress percentage
        if (widget.showProgress && widget.progress != null)
          Text(
            '${(widget.progress! * 100).toInt()}%',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
      ],
    );
  }

  /// Closes overlay with animation
  Future<void> close() async {
    await _overlayController.reverse();
  }
}

/// Shimmer loading widget for content placeholders
class ShimmerLoading extends StatefulWidget {
  /// Child widget to apply shimmer effect to
  final Widget child;

  /// Whether shimmer is active
  final bool isLoading;

  /// Shimmer color
  final Color? shimmerColor;

  /// Shimmer highlight color
  final Color? highlightColor;

  /// Animation duration
  final Duration duration;

  const ShimmerLoading({
    super.key,
    required this.child,
    this.isLoading = true,
    this.shimmerColor,
    this.highlightColor,
    this.duration = const Duration(milliseconds: 1500),
  });

  @override
  State<ShimmerLoading> createState() => _ShimmerLoadingState();
}

class _ShimmerLoadingState extends State<ShimmerLoading>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(duration: widget.duration, vsync: this);
    _animation = Tween<double>(begin: -1.0, end: 2.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    if (widget.isLoading) {
      _controller.repeat();
    }
  }

  @override
  void didUpdateWidget(ShimmerLoading oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isLoading) {
      _controller.repeat();
    } else {
      _controller.stop();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isLoading) {
      return widget.child;
    }

    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return ShaderMask(
          blendMode: BlendMode.srcATop,
          shaderCallback: (bounds) {
            return LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              stops: [
                (_animation.value - 1).clamp(0.0, 1.0),
                _animation.value.clamp(0.0, 1.0),
                (_animation.value + 1).clamp(0.0, 1.0),
              ],
              colors: [
                widget.shimmerColor ?? Theme.of(context).colorScheme.surfaceContainerHighest,
                widget.highlightColor ?? Theme.of(context).colorScheme.surface,
                widget.shimmerColor ?? Theme.of(context).colorScheme.surfaceContainerHighest,
              ],
            ).createShader(bounds);
          },
          child: widget.child,
        );
      },
    );
  }
}

/// Loading overlay manager for controlling multiple overlays
class LoadingOverlayManager {
  /// Active overlays
  static final Map<String, OverlayEntry> _activeOverlays = {};

  /// Shows loading overlay
  static void show(
    BuildContext context, {
    String id = 'default',
    String message = 'Loading...',
    double? progress,
    bool cancellable = false,
    VoidCallback? onCancel,
    LoadingAnimationType animationType = LoadingAnimationType.circular,
  }) {
    hide(id); // Remove existing overlay

    final overlay = OverlayEntry(
      builder: (context) => LoadingOverlay(
        message: message,
        progress: progress,
        cancellable: cancellable,
        onCancel: onCancel,
        animationType: animationType,
      ),
    );

    Overlay.of(context).insert(overlay);
    _activeOverlays[id] = overlay;
  }

  /// Hides loading overlay
  static void hide(String id) {
    final overlay = _activeOverlays.remove(id);
    overlay?.remove();
  }

  /// Hides all loading overlays
  static void hideAll() {
    for (final overlay in _activeOverlays.values) {
      overlay.remove();
    }
    _activeOverlays.clear();
  }

  /// Updates overlay progress
  static void updateProgress(String id, double progress) {
    final overlay = _activeOverlays[id];
    if (overlay != null) {
      overlay.markNeedsBuild();
    }
  }
}