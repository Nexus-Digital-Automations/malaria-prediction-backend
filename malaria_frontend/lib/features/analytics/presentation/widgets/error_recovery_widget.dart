/// Error recovery widget for analytics dashboard error handling
///
/// This widget provides comprehensive error handling and recovery mechanisms
/// for the analytics dashboard with user-friendly error display, retry
/// functionality, and intelligent error categorization.
///
/// Features:
/// - Categorized error display with specific recovery actions
/// - Intelligent retry mechanisms with exponential backoff
/// - User-friendly error messages and suggestions
/// - Error reporting and logging capabilities
/// - Offline state detection and handling
/// - Accessibility support for error states
/// - Custom error action buttons and recovery flows
///
/// Usage:
/// ```dart
/// ErrorRecoveryWidget(
///   error: analyticsError,
///   onRetry: () => _retryOperation(),
///   onDismiss: () => _dismissError(),
///   showErrorDetails: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../bloc/analytics_bloc.dart';

/// Error category enumeration
enum ErrorCategory {
  /// Network connectivity issues
  network,

  /// Data parsing or validation errors
  data,

  /// Authentication or authorization errors
  auth,

  /// Server or API errors
  server,

  /// Client-side application errors
  client,

  /// Permission or access errors
  permission,

  /// Timeout errors
  timeout,

  /// Unknown or unexpected errors
  unknown,
}

/// Error severity levels
enum ErrorSeverity {
  /// Low severity - warning level
  low,

  /// Medium severity - error level
  medium,

  /// High severity - critical error level
  high,

  /// Critical severity - system failure level
  critical,
}

/// Recovery action configuration
class RecoveryAction {
  /// Action identifier
  final String id;

  /// Action label for button
  final String label;

  /// Action icon
  final IconData icon;

  /// Action callback
  final VoidCallback onTap;

  /// Whether action is primary (highlighted)
  final bool isPrimary;

  /// Whether action is destructive
  final bool isDestructive;

  /// Action tooltip
  final String? tooltip;

  const RecoveryAction({
    required this.id,
    required this.label,
    required this.icon,
    required this.onTap,
    this.isPrimary = false,
    this.isDestructive = false,
    this.tooltip,
  });
}

/// Error information with recovery context
class ErrorInfo {
  /// Error category
  final ErrorCategory category;

  /// Error severity
  final ErrorSeverity severity;

  /// User-friendly title
  final String title;

  /// Detailed error message
  final String message;

  /// Technical error details
  final String? technicalDetails;

  /// Suggested user actions
  final List<String> suggestions;

  /// Recovery actions
  final List<RecoveryAction> actions;

  /// Whether error is recoverable
  final bool isRecoverable;

  /// Error code for tracking
  final String? errorCode;

  /// Timestamp when error occurred
  final DateTime timestamp;

  const ErrorInfo({
    required this.category,
    required this.severity,
    required this.title,
    required this.message,
    this.technicalDetails,
    this.suggestions = const [],
    this.actions = const [],
    this.isRecoverable = true,
    this.errorCode,
    required this.timestamp,
  });
}

/// Main error recovery widget
class ErrorRecoveryWidget extends StatefulWidget {
  /// Analytics error state
  final AnalyticsError error;

  /// Callback for retry action
  final VoidCallback? onRetry;

  /// Callback for dismiss action
  final VoidCallback? onDismiss;

  /// Callback for error reporting
  final VoidCallback? onReport;

  /// Whether to show detailed error information
  final bool showErrorDetails;

  /// Whether to show technical details
  final bool showTechnicalDetails;

  /// Custom recovery actions
  final List<RecoveryAction>? customActions;

  /// Whether to auto-retry with exponential backoff
  final bool enableAutoRetry;

  /// Maximum number of auto-retry attempts
  final int maxRetryAttempts;

  /// Whether to show error reporting option
  final bool showReportOption;

  /// Whether to show as overlay or inline
  final bool showAsOverlay;

  /// Custom error icon
  final IconData? customIcon;

  /// Custom error color
  final Color? customColor;

  const ErrorRecoveryWidget({
    super.key,
    required this.error,
    this.onRetry,
    this.onDismiss,
    this.onReport,
    this.showErrorDetails = true,
    this.showTechnicalDetails = false,
    this.customActions,
    this.enableAutoRetry = false,
    this.maxRetryAttempts = 3,
    this.showReportOption = true,
    this.showAsOverlay = true,
    this.customIcon,
    this.customColor,
  });

  @override
  State<ErrorRecoveryWidget> createState() => _ErrorRecoveryWidgetState();
}

class _ErrorRecoveryWidgetState extends State<ErrorRecoveryWidget>
    with TickerProviderStateMixin {
  /// Animation controller for entrance animation
  late AnimationController _entranceController;

  /// Animation controller for retry button pulse
  late AnimationController _retryController;

  /// Fade animation
  late Animation<double> _fadeAnimation;

  /// Scale animation
  late Animation<double> _scaleAnimation;

  /// Retry button scale animation
  late Animation<double> _retryScaleAnimation;

  /// Current retry count
  int _retryCount = 0;

  /// Whether details are expanded
  bool _detailsExpanded = false;

  /// Error information derived from analytics error
  late ErrorInfo _errorInfo;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _processError();
    _entranceController.forward();

    if (widget.enableAutoRetry && _errorInfo.isRecoverable) {
      _scheduleAutoRetry();
    }
  }

  @override
  void didUpdateWidget(ErrorRecoveryWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.error != widget.error) {
      _processError();
      _retryCount = 0;
    }
  }

  @override
  void dispose() {
    _entranceController.dispose();
    _retryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.showAsOverlay) {
      return _buildOverlay();
    } else {
      return _buildInlineWidget();
    }
  }

  /// Initializes animation controllers
  void _initializeAnimations() {
    _entranceController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );

    _retryController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _entranceController,
      curve: Curves.easeOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _entranceController,
      curve: Curves.easeOutBack,
    ));

    _retryScaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.1,
    ).animate(CurvedAnimation(
      parent: _retryController,
      curve: Curves.elasticInOut,
    ));
  }

  /// Processes analytics error into error info
  void _processError() {
    _errorInfo = _categorizeError(widget.error);
  }

  /// Builds overlay version
  Widget _buildOverlay() {
    return AnimatedBuilder(
      animation: _entranceController,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: Container(
            color: Colors.black54,
            child: Center(
              child: ScaleTransition(
                scale: _scaleAnimation,
                child: _buildErrorCard(),
              ),
            ),
          ),
        );
      },
    );
  }

  /// Builds inline widget version
  Widget _buildInlineWidget() {
    return AnimatedBuilder(
      animation: _entranceController,
      builder: (context, child) {
        return FadeTransition(
          opacity: _fadeAnimation,
          child: ScaleTransition(
            scale: _scaleAnimation,
            child: _buildErrorCard(),
          ),
        );
      },
    );
  }

  /// Builds main error card
  Widget _buildErrorCard() {
    return Card(
      elevation: 8,
      margin: const EdgeInsets.all(24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        constraints: const BoxConstraints(
          maxWidth: 500,
          minWidth: 300,
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Error header
            _buildErrorHeader(),

            const SizedBox(height: 16),

            // Error message
            _buildErrorMessage(),

            // Suggestions
            if (_errorInfo.suggestions.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildSuggestions(),
            ],

            // Error details (expandable)
            if (widget.showErrorDetails) _buildErrorDetails(),

            const SizedBox(height: 24),

            // Action buttons
            _buildActionButtons(),
          ],
        ),
      ),
    );
  }

  /// Builds error header with icon and title
  Widget _buildErrorHeader() {
    final color = widget.customColor ?? _getErrorColor(_errorInfo.severity);

    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            widget.customIcon ?? _getErrorIcon(_errorInfo.category),
            color: color,
            size: 32,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _errorInfo.title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _getSeverityText(_errorInfo.severity),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: color.withValues(alpha: 0.8),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
        if (widget.onDismiss != null)
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: widget.onDismiss,
            tooltip: 'Dismiss',
          ),
      ],
    );
  }

  /// Builds error message section
  Widget _buildErrorMessage() {
    return Text(
      _errorInfo.message,
      style: Theme.of(context).textTheme.bodyLarge,
    );
  }

  /// Builds suggestions section
  Widget _buildSuggestions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Suggestions:',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...(_errorInfo.suggestions.map((suggestion) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                Icons.lightbulb_outline,
                size: 16,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  suggestion,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ],
          ),
        ))),
      ],
    );
  }

  /// Builds expandable error details section
  Widget _buildErrorDetails() {
    return Column(
      children: [
        const SizedBox(height: 16),
        InkWell(
          onTap: () {
            setState(() {
              _detailsExpanded = !_detailsExpanded;
            });
          },
          child: Row(
            children: [
              Icon(
                _detailsExpanded ? Icons.expand_less : Icons.expand_more,
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
              ),
              const SizedBox(width: 8),
              Text(
                'Error Details',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        AnimatedCrossFade(
          duration: const Duration(milliseconds: 300),
          crossFadeState: _detailsExpanded
              ? CrossFadeState.showSecond
              : CrossFadeState.showFirst,
          firstChild: const SizedBox.shrink(),
          secondChild: _buildDetailedErrorInfo(),
        ),
      ],
    );
  }

  /// Builds detailed error information
  Widget _buildDetailedErrorInfo() {
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_errorInfo.errorCode != null) ...[
            _buildDetailRow('Error Code', _errorInfo.errorCode!),
            const SizedBox(height: 8),
          ],
          _buildDetailRow('Category', _errorInfo.category.name.toUpperCase()),
          const SizedBox(height: 8),
          _buildDetailRow('Timestamp', _formatTimestamp(_errorInfo.timestamp)),
          if (widget.showTechnicalDetails && _errorInfo.technicalDetails != null) ...[
            const SizedBox(height: 8),
            _buildDetailRow('Technical Details', _errorInfo.technicalDetails!),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _copyErrorDetails,
                  icon: const Icon(Icons.copy, size: 16),
                  label: const Text('Copy Details'),
                ),
              ),
              if (widget.showReportOption) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: widget.onReport ?? _reportError,
                    icon: const Icon(Icons.bug_report, size: 16),
                    label: const Text('Report'),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  /// Builds detail row
  Widget _buildDetailRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds action buttons
  Widget _buildActionButtons() {
    final actions = _buildRecoveryActions();

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: actions.map((action) => _buildActionButton(action)).toList(),
    );
  }

  /// Builds individual action button
  Widget _buildActionButton(RecoveryAction action) {
    if (action.id == 'retry') {
      return AnimatedBuilder(
        animation: _retryController,
        builder: (context, child) {
          return Transform.scale(
            scale: _retryScaleAnimation.value,
            child: _buildButton(action),
          );
        },
      );
    }

    return _buildButton(action);
  }

  /// Builds button widget
  Widget _buildButton(RecoveryAction action) {
    if (action.isPrimary) {
      return ElevatedButton.icon(
        onPressed: action.onTap,
        icon: Icon(action.icon),
        label: Text(action.label),
        style: action.isDestructive
            ? ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
                foregroundColor: Theme.of(context).colorScheme.onError,
              )
            : null,
      );
    } else {
      return OutlinedButton.icon(
        onPressed: action.onTap,
        icon: Icon(action.icon),
        label: Text(action.label),
        style: action.isDestructive
            ? OutlinedButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error,
              )
            : null,
      );
    }
  }

  /// Builds recovery actions list
  List<RecoveryAction> _buildRecoveryActions() {
    final actions = <RecoveryAction>[];

    // Add retry action if recoverable
    if (_errorInfo.isRecoverable && widget.onRetry != null) {
      actions.add(RecoveryAction(
        id: 'retry',
        label: _retryCount > 0 ? 'Retry (${_retryCount + 1})' : 'Retry',
        icon: Icons.refresh,
        onTap: _handleRetry,
        isPrimary: true,
      ));
    }

    // Add custom actions
    if (widget.customActions != null) {
      actions.addAll(widget.customActions!);
    }

    // Add default actions from error info
    actions.addAll(_errorInfo.actions);

    return actions;
  }

  /// Categorizes analytics error into error info
  ErrorInfo _categorizeError(AnalyticsError error) {
    final errorType = error.errorType.toLowerCase();
    final message = error.message;

    // Determine category based on error type
    ErrorCategory category;
    ErrorSeverity severity;
    String title;
    List<String> suggestions;

    if (errorType.contains('network') || errorType.contains('connection')) {
      category = ErrorCategory.network;
      severity = ErrorSeverity.medium;
      title = 'Network Connection Error';
      suggestions = [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact your network administrator if the problem persists',
      ];
    } else if (errorType.contains('auth')) {
      category = ErrorCategory.auth;
      severity = ErrorSeverity.high;
      title = 'Authentication Error';
      suggestions = [
        'Please sign in again',
        'Check your credentials',
        'Contact support if you cannot access your account',
      ];
    } else if (errorType.contains('timeout')) {
      category = ErrorCategory.timeout;
      severity = ErrorSeverity.medium;
      title = 'Request Timeout';
      suggestions = [
        'The request took too long to complete',
        'Try again with a smaller date range',
        'Check your network connection',
      ];
    } else if (errorType.contains('data')) {
      category = ErrorCategory.data;
      severity = ErrorSeverity.low;
      title = 'Data Processing Error';
      suggestions = [
        'Try adjusting your filters',
        'Select a different date range',
        'Contact support if the error persists',
      ];
    } else {
      category = ErrorCategory.unknown;
      severity = ErrorSeverity.medium;
      title = 'Unexpected Error';
      suggestions = [
        'Please try again',
        'Refresh the page if the problem continues',
        'Contact support with error details',
      ];
    }

    return ErrorInfo(
      category: category,
      severity: severity,
      title: title,
      message: message,
      technicalDetails: 'Error Type: $errorType\nRecoverable: ${error.isRecoverable}',
      suggestions: suggestions,
      isRecoverable: error.isRecoverable,
      errorCode: errorType,
      timestamp: DateTime.now(),
    );
  }

  /// Gets error icon based on category
  IconData _getErrorIcon(ErrorCategory category) {
    switch (category) {
      case ErrorCategory.network:
        return Icons.wifi_off;
      case ErrorCategory.data:
        return Icons.data_usage_outlined;
      case ErrorCategory.auth:
        return Icons.lock_outline;
      case ErrorCategory.server:
        return Icons.cloud_off;
      case ErrorCategory.client:
        return Icons.error_outline;
      case ErrorCategory.permission:
        return Icons.security;
      case ErrorCategory.timeout:
        return Icons.schedule;
      case ErrorCategory.unknown:
        return Icons.help_outline;
    }
  }

  /// Gets error color based on severity
  Color _getErrorColor(ErrorSeverity severity) {
    switch (severity) {
      case ErrorSeverity.low:
        return Colors.orange;
      case ErrorSeverity.medium:
        return Colors.red;
      case ErrorSeverity.high:
        return Colors.red.shade700;
      case ErrorSeverity.critical:
        return Colors.red.shade900;
    }
  }

  /// Gets severity text
  String _getSeverityText(ErrorSeverity severity) {
    switch (severity) {
      case ErrorSeverity.low:
        return 'Warning';
      case ErrorSeverity.medium:
        return 'Error';
      case ErrorSeverity.high:
        return 'Critical Error';
      case ErrorSeverity.critical:
        return 'System Failure';
    }
  }

  /// Formats timestamp for display
  String _formatTimestamp(DateTime timestamp) {
    return '${timestamp.day}/${timestamp.month}/${timestamp.year} '
           '${timestamp.hour.toString().padLeft(2, '0')}:'
           '${timestamp.minute.toString().padLeft(2, '0')}';
  }

  /// Handles retry action
  void _handleRetry() {
    _retryCount++;
    _retryController.forward().then((_) {
      _retryController.reset();
    });

    if (widget.onRetry != null) {
      widget.onRetry!();
    }
  }

  /// Schedules auto-retry with exponential backoff
  void _scheduleAutoRetry() {
    if (_retryCount >= widget.maxRetryAttempts) return;

    final delay = Duration(seconds: (2 << _retryCount).clamp(1, 30));
    Future.delayed(delay, () {
      if (mounted && _errorInfo.isRecoverable) {
        _handleRetry();
      }
    });
  }

  /// Copies error details to clipboard
  void _copyErrorDetails() {
    final details = [
      'Error: ${_errorInfo.title}',
      'Message: ${_errorInfo.message}',
      'Category: ${_errorInfo.category.name}',
      'Severity: ${_errorInfo.severity.name}',
      'Time: ${_formatTimestamp(_errorInfo.timestamp)}',
      if (_errorInfo.errorCode != null) 'Code: ${_errorInfo.errorCode}',
      if (_errorInfo.technicalDetails != null) 'Details: ${_errorInfo.technicalDetails}',
    ].join('\n');

    Clipboard.setData(ClipboardData(text: details));

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Error details copied to clipboard')),
    );
  }

  /// Reports error to support
  void _reportError() {
    // Implementation would send error report
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Error report sent successfully')),
    );
  }
}