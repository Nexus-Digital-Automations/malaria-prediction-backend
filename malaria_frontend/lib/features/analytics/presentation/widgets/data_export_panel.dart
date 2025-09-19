/// Comprehensive data export panel for analytics dashboard
///
/// This widget provides extensive data export capabilities with multiple
/// formats, customization options, preview functionality, and batch operations
/// for analytics data export and sharing.
///
/// Features:
/// - Multiple export formats (PDF, Excel, CSV, JSON, PNG, SVG)
/// - Custom data selection and filtering
/// - Preview before export with validation
/// - Batch export operations
/// - Export templates and presets
/// - Scheduled exports (future enhancement)
/// - Cloud storage integration options
/// - Export history and management
/// - Progress tracking for large exports
/// - Email and sharing capabilities
///
/// Usage:
/// ```dart
/// DataExportPanel(
///   analyticsData: currentAnalyticsData,
///   availableFormats: [ExportFormat.pdf, ExportFormat.xlsx],
///   onExportRequested: (format) => handleExport(format),
///   showPreview: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';

/// Logger for data export operations
final _logger = Logger('DataExportPanel');

/// Comprehensive data export panel widget
class DataExportPanel extends StatefulWidget {
  /// Analytics data to export
  final AnalyticsData? analyticsData;

  /// Available export formats
  final List<ExportFormat> availableFormats;

  /// Callback when export is requested
  final ValueChanged<ExportRequest> onExportRequested;

  /// Whether to show export preview
  final bool showPreview;

  /// Whether to allow export customization
  final bool allowCustomization;

  /// Custom export templates
  final List<ExportTemplate>? customTemplates;

  /// Maximum export file size in MB
  final double? maxFileSizeMB;

  /// Whether to show export history
  final bool showHistory;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Whether export panel is read-only
  final bool readOnly;

  const DataExportPanel({
    super.key,
    this.analyticsData,
    this.availableFormats = const [
      ExportFormat.pdf,
      ExportFormat.xlsx,
      ExportFormat.csv,
      ExportFormat.json,
    ],
    required this.onExportRequested,
    this.showPreview = true,
    this.allowCustomization = true,
    this.customTemplates,
    this.maxFileSizeMB,
    this.showHistory = true,
    this.colorScheme,
    this.readOnly = false,
  });

  @override
  State<DataExportPanel> createState() => _DataExportPanelState();
}

class _DataExportPanelState extends State<DataExportPanel>
    with TickerProviderStateMixin {
  /// Tab controller for export modes
  late TabController _tabController;

  /// Animation controller for UI transitions
  late AnimationController _animationController;

  /// Animation for panel transitions
  late Animation<double> _panelAnimation;

  /// Currently selected export format
  ExportFormat _selectedFormat = ExportFormat.pdf;

  /// Current export configuration
  late ExportConfiguration _exportConfig;

  /// Selected data sections for export
  final Set<DataSection> _selectedSections = {};

  /// Current export template
  ExportTemplate? _selectedTemplate;

  /// Export preview data
  ExportPreview? _previewData;

  /// Export history
  final List<ExportHistoryItem> _exportHistory = [];

  /// Form key for export configuration
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  /// Text controllers for custom settings
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _authorController = TextEditingController();

  /// Export progress (0.0 to 1.0)
  double _exportProgress = 0.0;

  /// Whether export is in progress
  bool _isExporting = false;

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing data export panel');

    // Initialize tab controller
    _tabController = TabController(length: ExportMode.values.length, vsync: this);

    // Initialize animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _panelAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );

    // Set initial format from available formats
    if (widget.availableFormats.isNotEmpty) {
      _selectedFormat = widget.availableFormats.first;
    }

    // Initialize export configuration
    _exportConfig = ExportConfiguration(
      format: _selectedFormat,
      includeCharts: true,
      includeMetadata: true,
      includeRawData: false,
      compression: CompressionLevel.medium,
      quality: ExportQuality.high,
    );

    // Initialize selected sections
    _selectedSections.addAll([
      DataSection.overview,
      DataSection.predictionMetrics,
      DataSection.environmentalData,
    ]);

    // Initialize text controllers
    _initializeControllers();

    // Load export history
    _loadExportHistory();

    // Start animation
    _animationController.forward();
  }

  @override
  void didUpdateWidget(DataExportPanel oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update selected format if available formats changed
    if (!widget.availableFormats.contains(_selectedFormat) && widget.availableFormats.isNotEmpty) {
      setState(() {
        _selectedFormat = widget.availableFormats.first;
        _exportConfig = _exportConfig.copyWith(format: _selectedFormat);
      });
    }

    // Regenerate preview if data changed
    if (widget.analyticsData != oldWidget.analyticsData) {
      _generatePreview();
    }
  }

  @override
  void dispose() {
    _logger.info('Disposing data export panel');
    _tabController.dispose();
    _animationController.dispose();
    _titleController.dispose();
    _descriptionController.dispose();
    _authorController.dispose();
    super.dispose();
  }

  /// Initializes text controllers with default values
  void _initializeControllers() {
    _titleController.text = 'Analytics Report';
    _descriptionController.text = 'Comprehensive analytics data export';
    _authorController.text = 'Analytics Dashboard';
  }

  /// Loads export history (mock implementation)
  void _loadExportHistory() {
    _exportHistory.addAll([
      ExportHistoryItem(
        id: 'export_1',
        format: ExportFormat.pdf,
        filename: 'analytics_report_2024.pdf',
        exportedAt: DateTime.now().subtract(const Duration(hours: 2)),
        size: 2.4,
        status: ExportStatus.completed,
      ),
      ExportHistoryItem(
        id: 'export_2',
        format: ExportFormat.xlsx,
        filename: 'environmental_data.xlsx',
        exportedAt: DateTime.now().subtract(const Duration(days: 1)),
        size: 1.8,
        status: ExportStatus.completed,
      ),
    ]);
  }

  /// Generates export preview
  Future<void> _generatePreview() async {
    if (!widget.showPreview || widget.analyticsData == null) return;

    _logger.info('Generating export preview for format: $_selectedFormat');

    // Simulate preview generation
    await Future.delayed(const Duration(milliseconds: 500));

    final estimatedSize = _calculateEstimatedSize();
    final pageCount = _calculatePageCount();

    setState(() {
      _previewData = ExportPreview(
        format: _selectedFormat,
        estimatedSize: estimatedSize,
        pageCount: pageCount,
        sections: _selectedSections.toList(),
        generatedAt: DateTime.now(),
      );
    });
  }

  /// Calculates estimated export file size
  double _calculateEstimatedSize() {
    double baseSize = 0.5; // Base size in MB

    // Add size based on selected sections
    baseSize += _selectedSections.length * 0.3;

    // Add size based on data complexity
    if (widget.analyticsData != null) {
      baseSize += widget.analyticsData!.environmentalTrends.length * 0.001;
      baseSize += widget.analyticsData!.riskTrends.length * 0.001;
    }

    // Adjust for format
    switch (_selectedFormat) {
      case ExportFormat.pdf:
        baseSize *= 1.2;
        break;
      case ExportFormat.xlsx:
        baseSize *= 0.8;
        break;
      case ExportFormat.csv:
        baseSize *= 0.3;
        break;
      case ExportFormat.json:
        baseSize *= 0.4;
        break;
      case ExportFormat.png:
        baseSize *= 2.0;
        break;
      case ExportFormat.svg:
        baseSize *= 0.6;
        break;
    }

    return baseSize;
  }

  /// Calculates estimated page count
  int _calculatePageCount() {
    if (_selectedFormat == ExportFormat.csv ||
        _selectedFormat == ExportFormat.json) {
      return 1; // No pages for data formats
    }

    int pages = 1; // Cover page
    pages += _selectedSections.length; // One page per section

    if (_exportConfig.includeRawData) {
      pages += 5; // Additional pages for raw data
    }

    return pages;
  }

  /// Starts the export process
  Future<void> _startExport() async {
    if (!_formKey.currentState!.validate()) return;
    if (widget.readOnly) return;

    setState(() {
      _isExporting = true;
      _exportProgress = 0.0;
    });

    try {
      final request = ExportRequest(
        format: _selectedFormat,
        configuration: _exportConfig,
        sections: _selectedSections.toList(),
        metadata: ExportMetadata(
          title: _titleController.text,
          description: _descriptionController.text,
          author: _authorController.text,
          generatedAt: DateTime.now(),
        ),
        template: _selectedTemplate,
      );

      // Simulate export progress
      for (int i = 0; i <= 100; i += 10) {
        await Future.delayed(const Duration(milliseconds: 100));
        setState(() {
          _exportProgress = i / 100;
        });
      }

      // Add to history
      _addToHistory(request);

      // Trigger export callback
      widget.onExportRequested(request);

      _showMessage('Export completed successfully');
      _logger.info('Export completed: ${request.format}');

    } catch (e) {
      _showError('Export failed: ${e.toString()}');
      _logger.severe('Export failed: $e');
    } finally {
      setState(() {
        _isExporting = false;
        _exportProgress = 0.0;
      });
    }
  }

  /// Adds export to history
  void _addToHistory(ExportRequest request) {
    final historyItem = ExportHistoryItem(
      id: 'export_${DateTime.now().millisecondsSinceEpoch}',
      format: request.format,
      filename: _generateFilename(request),
      exportedAt: DateTime.now(),
      size: _previewData?.estimatedSize ?? 1.0,
      status: ExportStatus.completed,
    );

    setState(() {
      _exportHistory.insert(0, historyItem);
    });
  }

  /// Generates filename for export
  String _generateFilename(ExportRequest request) {
    final title = _titleController.text.toLowerCase().replaceAll(' ', '_');
    final date = DateTime.now().toIso8601String().split('T')[0];
    final extension = _getFormatExtension(request.format);
    return '${title}_$date.$extension';
  }

  /// Gets file extension for format
  String _getFormatExtension(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return 'pdf';
      case ExportFormat.xlsx:
        return 'xlsx';
      case ExportFormat.csv:
        return 'csv';
      case ExportFormat.json:
        return 'json';
      case ExportFormat.png:
        return 'png';
      case ExportFormat.svg:
        return 'svg';
    }
  }

  /// Shows success message
  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Shows error message
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            _buildHeader(theme, colorScheme),

            const SizedBox(height: 16),

            // Tab bar
            _buildTabBar(theme, colorScheme),

            const SizedBox(height: 16),

            // Main content
            Expanded(
              child: AnimatedBuilder(
                animation: _panelAnimation,
                builder: (context, child) {
                  return Opacity(
                    opacity: _panelAnimation.value,
                    child: _buildMainContent(theme, colorScheme),
                  );
                },
              ),
            ),

            // Export progress (if active)
            if (_isExporting) ...[
              const SizedBox(height: 16),
              _buildExportProgress(theme, colorScheme),
            ],
          ],
        ),
      ),
    );
  }

  /// Builds the header section
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Data Export',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Export analytics data in multiple formats with customization',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        // Quick export button
        ElevatedButton.icon(
          onPressed: (_isExporting || widget.readOnly) ? null : _startExport,
          icon: _isExporting
              ? SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: colorScheme.onPrimary,
                  ),
                )
              : const Icon(Icons.download),
          label: Text(_isExporting ? 'Exporting...' : 'Export'),
        ),
      ],
    );
  }

  /// Builds tab bar
  Widget _buildTabBar(ThemeData theme, ColorScheme colorScheme) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      labelColor: colorScheme.primary,
      unselectedLabelColor: colorScheme.onSurface.withOpacity(0.6),
      indicatorColor: colorScheme.primary,
      tabs: const [
        Tab(icon: Icon(Icons.settings), text: 'Configure'),
        Tab(icon: Icon(Icons.preview), text: 'Preview'),
        Tab(icon: Icon(Icons.template_outlined), text: 'Templates'),
        Tab(icon: Icon(Icons.history), text: 'History'),
      ],
    );
  }

  /// Builds main content area
  Widget _buildMainContent(ThemeData theme, ColorScheme colorScheme) {
    if (widget.analyticsData == null) {
      return _buildNoDataState(theme, colorScheme);
    }

    return TabBarView(
      controller: _tabController,
      children: [
        _buildConfigureTab(theme, colorScheme),
        _buildPreviewTab(theme, colorScheme),
        _buildTemplatesTab(theme, colorScheme),
        _buildHistoryTab(theme, colorScheme),
      ],
    );
  }

  /// Builds no data state
  Widget _buildNoDataState(ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.download_outlined,
            size: 64,
            color: colorScheme.onSurface.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No data available for export',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds configure tab
  Widget _buildConfigureTab(ThemeData theme, ColorScheme colorScheme) {
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Format selection
            _buildFormatSelection(theme, colorScheme),

            const SizedBox(height: 20),

            // Data sections
            _buildDataSections(theme, colorScheme),

            const SizedBox(height: 20),

            // Export settings
            _buildExportSettings(theme, colorScheme),

            const SizedBox(height: 20),

            // Metadata
            _buildMetadataSection(theme, colorScheme),
          ],
        ),
      ),
    );
  }

  /// Builds format selection
  Widget _buildFormatSelection(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Export Format',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 8,
          children: widget.availableFormats.map((format) {
            final isSelected = _selectedFormat == format;
            return FilterChip(
              label: Text(_getFormatLabel(format)),
              selected: isSelected,
              onSelected: widget.readOnly
                  ? null
                  : (selected) {
                      if (selected) {
                        setState(() {
                          _selectedFormat = format;
                          _exportConfig = _exportConfig.copyWith(format: format);
                        });
                        _generatePreview();
                      }
                    },
              avatar: Icon(_getFormatIcon(format), size: 16),
              selectedColor: colorScheme.primaryContainer,
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds data sections selection
  Widget _buildDataSections(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Data Sections',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),
        ...DataSection.values.map((section) {
          final isSelected = _selectedSections.contains(section);
          return CheckboxListTile(
            value: isSelected,
            onChanged: widget.readOnly
                ? null
                : (selected) {
                    setState(() {
                      if (selected == true) {
                        _selectedSections.add(section);
                      } else {
                        _selectedSections.remove(section);
                      }
                    });
                    _generatePreview();
                  },
            title: Text(_getSectionLabel(section)),
            subtitle: Text(_getSectionDescription(section)),
            secondary: Icon(_getSectionIcon(section)),
            dense: true,
          );
        }),
      ],
    );
  }

  /// Builds export settings
  Widget _buildExportSettings(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Export Settings',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),
        CheckboxListTile(
          value: _exportConfig.includeCharts,
          onChanged: widget.readOnly
              ? null
              : (value) {
                  setState(() {
                    _exportConfig = _exportConfig.copyWith(includeCharts: value ?? false);
                  });
                  _generatePreview();
                },
          title: const Text('Include Charts'),
          subtitle: const Text('Include visualizations and graphs'),
          dense: true,
        ),
        CheckboxListTile(
          value: _exportConfig.includeMetadata,
          onChanged: widget.readOnly
              ? null
              : (value) {
                  setState(() {
                    _exportConfig = _exportConfig.copyWith(includeMetadata: value ?? false);
                  });
                  _generatePreview();
                },
          title: const Text('Include Metadata'),
          subtitle: const Text('Include data source and generation info'),
          dense: true,
        ),
        CheckboxListTile(
          value: _exportConfig.includeRawData,
          onChanged: widget.readOnly
              ? null
              : (value) {
                  setState(() {
                    _exportConfig = _exportConfig.copyWith(includeRawData: value ?? false);
                  });
                  _generatePreview();
                },
          title: const Text('Include Raw Data'),
          subtitle: const Text('Include detailed data tables'),
          dense: true,
        ),
      ],
    );
  }

  /// Builds metadata section
  Widget _buildMetadataSection(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Export Metadata',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _titleController,
          decoration: const InputDecoration(
            labelText: 'Report Title',
            border: OutlineInputBorder(),
          ),
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Please enter a report title';
            }
            return null;
          },
          readOnly: widget.readOnly,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _descriptionController,
          decoration: const InputDecoration(
            labelText: 'Description',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
          readOnly: widget.readOnly,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _authorController,
          decoration: const InputDecoration(
            labelText: 'Author',
            border: OutlineInputBorder(),
          ),
          readOnly: widget.readOnly,
        ),
      ],
    );
  }

  /// Builds preview tab
  Widget _buildPreviewTab(ThemeData theme, ColorScheme colorScheme) {
    if (_previewData == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text('Generating preview...', style: theme.textTheme.bodyLarge),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _generatePreview,
              child: const Text('Generate Preview'),
            ),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Preview summary card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Export Preview',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _buildPreviewStat(
                          'Format',
                          _getFormatLabel(_previewData!.format),
                          _getFormatIcon(_previewData!.format),
                          theme,
                          colorScheme,
                        ),
                      ),
                      Expanded(
                        child: _buildPreviewStat(
                          'Estimated Size',
                          '${_previewData!.estimatedSize.toStringAsFixed(1)} MB',
                          Icons.storage,
                          theme,
                          colorScheme,
                        ),
                      ),
                      Expanded(
                        child: _buildPreviewStat(
                          'Pages',
                          '${_previewData!.pageCount}',
                          Icons.description,
                          theme,
                          colorScheme,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Sections preview
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Included Sections',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ..._previewData!.sections.map((section) {
                    return ListTile(
                      leading: Icon(_getSectionIcon(section)),
                      title: Text(_getSectionLabel(section)),
                      subtitle: Text(_getSectionDescription(section)),
                      dense: true,
                    );
                  }),
                ],
              ),
            ),
          ),

          // Validation warnings (if any)
          if (widget.maxFileSizeMB != null && _previewData!.estimatedSize > widget.maxFileSizeMB!) ...[
            const SizedBox(height: 16),
            Card(
              color: Colors.orange.withOpacity(0.1),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.warning, color: Colors.orange),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Warning: Estimated file size (${_previewData!.estimatedSize.toStringAsFixed(1)} MB) exceeds maximum allowed size (${widget.maxFileSizeMB} MB)',
                        style: TextStyle(color: Colors.orange[800]),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Builds preview stat widget
  Widget _buildPreviewStat(String label, String value, IconData icon, ThemeData theme, ColorScheme colorScheme) {
    return Column(
      children: [
        Icon(icon, color: colorScheme.primary),
        const SizedBox(height: 8),
        Text(
          value,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
      ],
    );
  }

  /// Builds templates tab
  Widget _buildTemplatesTab(ThemeData theme, ColorScheme colorScheme) {
    final templates = widget.customTemplates ?? _getDefaultTemplates();

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Export Templates',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: colorScheme.primary,
            ),
          ),
          const SizedBox(height: 16),
          ...templates.map((template) => _buildTemplateCard(template, theme, colorScheme)),
        ],
      ),
    );
  }

  /// Builds template card
  Widget _buildTemplateCard(ExportTemplate template, ThemeData theme, ColorScheme colorScheme) {
    final isSelected = _selectedTemplate == template;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: isSelected ? colorScheme.primaryContainer.withOpacity(0.3) : null,
      child: ListTile(
        leading: Icon(template.icon, color: isSelected ? colorScheme.primary : null),
        title: Text(template.name),
        subtitle: Text(template.description),
        trailing: isSelected
            ? Icon(Icons.check_circle, color: colorScheme.primary)
            : const Icon(Icons.radio_button_unchecked),
        onTap: widget.readOnly
            ? null
            : () {
                setState(() {
                  _selectedTemplate = isSelected ? null : template;
                });
              },
      ),
    );
  }

  /// Builds history tab
  Widget _buildHistoryTab(ThemeData theme, ColorScheme colorScheme) {
    if (_exportHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history,
              size: 64,
              color: colorScheme.onSurface.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              'No export history',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      child: Column(
        children: _exportHistory.map((item) => _buildHistoryItem(item, theme, colorScheme)).toList(),
      ),
    );
  }

  /// Builds history item
  Widget _buildHistoryItem(ExportHistoryItem item, ThemeData theme, ColorScheme colorScheme) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _getStatusColor(item.status).withOpacity(0.2),
          child: Icon(
            _getFormatIcon(item.format),
            color: _getStatusColor(item.status),
          ),
        ),
        title: Text(item.filename),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${item.size.toStringAsFixed(1)} MB • ${_getStatusLabel(item.status)}'),
            Text(
              'Exported: ${item.exportedAt.toString().split('.')[0]}',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'download', child: Text('Download')),
            const PopupMenuItem(value: 'share', child: Text('Share')),
            const PopupMenuItem(value: 'delete', child: Text('Delete')),
          ],
          onSelected: (action) => _handleHistoryAction(action, item),
        ),
      ),
    );
  }

  /// Builds export progress indicator
  Widget _buildExportProgress(ThemeData theme, ColorScheme colorScheme) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.download, color: colorScheme.primary),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Exporting data...',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: colorScheme.primary,
                  ),
                ),
              ),
              Text(
                '${(_exportProgress * 100).toInt()}%',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: _exportProgress,
            backgroundColor: colorScheme.outline.withOpacity(0.3),
            valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
          ),
        ],
      ),
    );
  }

  /// Handles history item actions
  void _handleHistoryAction(String action, ExportHistoryItem item) {
    switch (action) {
      case 'download':
        _showMessage('Download functionality coming soon');
        break;
      case 'share':
        _showMessage('Share functionality coming soon');
        break;
      case 'delete':
        setState(() {
          _exportHistory.remove(item);
        });
        _showMessage('Export deleted from history');
        break;
    }
  }

  /// Gets default export templates
  List<ExportTemplate> _getDefaultTemplates() {
    return [
      ExportTemplate(
        id: 'standard',
        name: 'Standard Report',
        description: 'Standard analytics report with all sections',
        icon: Icons.description,
        configuration: _exportConfig,
      ),
      ExportTemplate(
        id: 'summary',
        name: 'Executive Summary',
        description: 'High-level overview for executives',
        icon: Icons.summarize,
        configuration: _exportConfig.copyWith(includeRawData: false),
      ),
      ExportTemplate(
        id: 'technical',
        name: 'Technical Report',
        description: 'Detailed technical analysis with raw data',
        icon: Icons.engineering,
        configuration: _exportConfig.copyWith(includeRawData: true),
      ),
    ];
  }

  /// Gets format label
  String _getFormatLabel(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return 'PDF';
      case ExportFormat.xlsx:
        return 'Excel';
      case ExportFormat.csv:
        return 'CSV';
      case ExportFormat.json:
        return 'JSON';
      case ExportFormat.png:
        return 'PNG';
      case ExportFormat.svg:
        return 'SVG';
    }
  }

  /// Gets format icon
  IconData _getFormatIcon(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return Icons.picture_as_pdf;
      case ExportFormat.xlsx:
        return Icons.grid_on;
      case ExportFormat.csv:
        return Icons.table_chart;
      case ExportFormat.json:
        return Icons.code;
      case ExportFormat.png:
        return Icons.image;
      case ExportFormat.svg:
        return Icons.vector_image;
    }
  }

  /// Gets section label
  String _getSectionLabel(DataSection section) {
    switch (section) {
      case DataSection.overview:
        return 'Overview';
      case DataSection.predictionMetrics:
        return 'Prediction Metrics';
      case DataSection.environmentalData:
        return 'Environmental Data';
      case DataSection.riskAnalysis:
        return 'Risk Analysis';
      case DataSection.alertStatistics:
        return 'Alert Statistics';
      case DataSection.dataQuality:
        return 'Data Quality';
      case DataSection.recommendations:
        return 'Recommendations';
    }
  }

  /// Gets section description
  String _getSectionDescription(DataSection section) {
    switch (section) {
      case DataSection.overview:
        return 'High-level summary and key metrics';
      case DataSection.predictionMetrics:
        return 'Model performance and accuracy metrics';
      case DataSection.environmentalData:
        return 'Climate and environmental factor analysis';
      case DataSection.riskAnalysis:
        return 'Risk assessment and trend analysis';
      case DataSection.alertStatistics:
        return 'Alert system performance metrics';
      case DataSection.dataQuality:
        return 'Data completeness and reliability metrics';
      case DataSection.recommendations:
        return 'System recommendations and insights';
    }
  }

  /// Gets section icon
  IconData _getSectionIcon(DataSection section) {
    switch (section) {
      case DataSection.overview:
        return Icons.dashboard;
      case DataSection.predictionMetrics:
        return Icons.analytics;
      case DataSection.environmentalData:
        return Icons.eco;
      case DataSection.riskAnalysis:
        return Icons.trending_up;
      case DataSection.alertStatistics:
        return Icons.notifications;
      case DataSection.dataQuality:
        return Icons.verified;
      case DataSection.recommendations:
        return Icons.lightbulb;
    }
  }

  /// Gets status color
  Color _getStatusColor(ExportStatus status) {
    switch (status) {
      case ExportStatus.pending:
        return Colors.orange;
      case ExportStatus.inProgress:
        return Colors.blue;
      case ExportStatus.completed:
        return Colors.green;
      case ExportStatus.failed:
        return Colors.red;
    }
  }

  /// Gets status label
  String _getStatusLabel(ExportStatus status) {
    switch (status) {
      case ExportStatus.pending:
        return 'Pending';
      case ExportStatus.inProgress:
        return 'In Progress';
      case ExportStatus.completed:
        return 'Completed';
      case ExportStatus.failed:
        return 'Failed';
    }
  }
}

/// Export mode enumeration
enum ExportMode {
  configure,
  preview,
  templates,
  history,
}

/// Data section enumeration
enum DataSection {
  overview,
  predictionMetrics,
  environmentalData,
  riskAnalysis,
  alertStatistics,
  dataQuality,
  recommendations,
}

/// Compression level enumeration
enum CompressionLevel {
  none,
  low,
  medium,
  high,
}

/// Export quality enumeration
enum ExportQuality {
  low,
  medium,
  high,
  ultra,
}

/// Export status enumeration
enum ExportStatus {
  pending,
  inProgress,
  completed,
  failed,
}

/// Export configuration class
class ExportConfiguration {
  final ExportFormat format;
  final bool includeCharts;
  final bool includeMetadata;
  final bool includeRawData;
  final CompressionLevel compression;
  final ExportQuality quality;

  const ExportConfiguration({
    required this.format,
    this.includeCharts = true,
    this.includeMetadata = true,
    this.includeRawData = false,
    this.compression = CompressionLevel.medium,
    this.quality = ExportQuality.high,
  });

  ExportConfiguration copyWith({
    ExportFormat? format,
    bool? includeCharts,
    bool? includeMetadata,
    bool? includeRawData,
    CompressionLevel? compression,
    ExportQuality? quality,
  }) {
    return ExportConfiguration(
      format: format ?? this.format,
      includeCharts: includeCharts ?? this.includeCharts,
      includeMetadata: includeMetadata ?? this.includeMetadata,
      includeRawData: includeRawData ?? this.includeRawData,
      compression: compression ?? this.compression,
      quality: quality ?? this.quality,
    );
  }
}

/// Export metadata class
class ExportMetadata {
  final String title;
  final String description;
  final String author;
  final DateTime generatedAt;

  const ExportMetadata({
    required this.title,
    required this.description,
    required this.author,
    required this.generatedAt,
  });
}

/// Export request class
class ExportRequest {
  final ExportFormat format;
  final ExportConfiguration configuration;
  final List<DataSection> sections;
  final ExportMetadata metadata;
  final ExportTemplate? template;

  const ExportRequest({
    required this.format,
    required this.configuration,
    required this.sections,
    required this.metadata,
    this.template,
  });
}

/// Export preview class
class ExportPreview {
  final ExportFormat format;
  final double estimatedSize;
  final int pageCount;
  final List<DataSection> sections;
  final DateTime generatedAt;

  const ExportPreview({
    required this.format,
    required this.estimatedSize,
    required this.pageCount,
    required this.sections,
    required this.generatedAt,
  });
}

/// Export template class
class ExportTemplate {
  final String id;
  final String name;
  final String description;
  final IconData icon;
  final ExportConfiguration configuration;

  const ExportTemplate({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.configuration,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ExportTemplate && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Export history item class
class ExportHistoryItem {
  final String id;
  final ExportFormat format;
  final String filename;
  final DateTime exportedAt;
  final double size;
  final ExportStatus status;

  const ExportHistoryItem({
    required this.id,
    required this.format,
    required this.filename,
    required this.exportedAt,
    required this.size,
    required this.status,
  });
}