/// Report configuration panel for malaria analytics custom reports
///
/// This widget provides comprehensive configuration options for report generation
/// including sections, charts, export formats, scheduling, and security settings.
///
/// Features:
/// - Customizable report sections and chart configurations
/// - Multiple export format options (PDF, CSV, Excel, JSON)
/// - Advanced layout and styling options
/// - Report scheduling configuration
/// - Security and sharing settings
/// - Real-time preview updates
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/report_template_model.dart';
import '../services/report_generation_service.dart';
import '../../domain/entities/analytics_filters.dart';

/// Report configuration panel with comprehensive customization options
class ReportConfigurationPanel extends StatefulWidget {
  /// Report template to configure
  final ReportTemplate template;

  /// Callback when configuration changes
  final ValueChanged<ReportGenerationConfig> onConfigurationChanged;

  /// Initial configuration
  final ReportGenerationConfig? initialConfiguration;

  /// Whether to show advanced options
  final bool showAdvancedOptions;

  /// Whether to enable scheduling options
  final bool enableScheduling;

  /// Whether to enable security options
  final bool enableSecurity;

  const ReportConfigurationPanel({
    super.key,
    required this.template,
    required this.onConfigurationChanged,
    this.initialConfiguration,
    this.showAdvancedOptions = true,
    this.enableScheduling = true,
    this.enableSecurity = true,
  });

  @override
  State<ReportConfigurationPanel> createState() => _ReportConfigurationPanelState();
}

class _ReportConfigurationPanelState extends State<ReportConfigurationPanel>
    with TickerProviderStateMixin {
  /// Tab controller for configuration sections
  late TabController _tabController;

  /// Export format selection
  ExportFormat _exportFormat = ExportFormat.pdf;

  /// Output filename
  late TextEditingController _filenameController;

  /// Whether to include charts
  bool _includeCharts = true;

  /// Chart quality setting
  int _chartQuality = 300;

  /// Whether to compress output
  bool _compressOutput = false;

  /// Selected report sections
  Set<ReportSection> _selectedSections = {};

  /// Chart configurations
  Map<ReportSection, List<ReportChartConfig>> _chartConfigurations = {};

  /// Layout configuration
  late ReportLayoutConfig _layoutConfig;

  /// Security configuration
  late SecurityConfig _securityConfig;

  /// Schedule configuration
  ScheduleConfig? _scheduleConfig;

  /// Custom metadata
  Map<String, dynamic> _customMetadata = {};

  /// Whether scheduling is enabled
  bool _schedulingEnabled = false;

  /// Whether to show all configuration tabs
  bool _showAllTabs = false;

  @override
  void initState() {
    super.initState();

    // Initialize tab controller
    _tabController = TabController(
      length: widget.showAdvancedOptions ? 5 : 3,
      vsync: this,
    );

    // Initialize controllers
    _filenameController = TextEditingController(
      text: 'malaria_analytics_report_${DateTime.now().millisecondsSinceEpoch}',
    );

    // Initialize configurations
    _initializeConfigurations();

    // Listen to tab changes
    _tabController.addListener(_onTabChanged);

    // Log initialization
    debugPrint('ReportConfigurationPanel initialized for template: ${widget.template.name}');
  }

  @override
  void dispose() {
    _tabController.dispose();
    _filenameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildHeader(),
        _buildTabBar(),
        Expanded(
          child: _buildTabView(),
        ),
      ],
    );
  }

  /// Builds the header section
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Icon(
            Icons.tune,
            color: Theme.of(context).colorScheme.primary,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Configure Report',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Template: ${widget.template.name}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(
              _showAllTabs ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
              color: Theme.of(context).colorScheme.primary,
            ),
            onPressed: () {
              setState(() {
                _showAllTabs = !_showAllTabs;
              });
            },
            tooltip: _showAllTabs ? 'Show fewer options' : 'Show all options',
          ),
        ],
      ),
    );
  }

  /// Builds the tab bar
  Widget _buildTabBar() {
    final tabs = [
      const Tab(icon: Icon(Icons.settings), text: 'Basic'),
      const Tab(icon: Icon(Icons.list_alt), text: 'Sections'),
      const Tab(icon: Icon(Icons.bar_chart), text: 'Charts'),
    ];

    if (widget.showAdvancedOptions && _showAllTabs) {
      tabs.addAll([
        const Tab(icon: Icon(Icons.design_services), text: 'Layout'),
        const Tab(icon: Icon(Icons.security), text: 'Security'),
      ]);
    }

    return TabBar(
      controller: _tabController,
      tabs: tabs,
      isScrollable: true,
      indicatorColor: Theme.of(context).colorScheme.primary,
      labelColor: Theme.of(context).colorScheme.primary,
      unselectedLabelColor: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
    );
  }

  /// Builds the tab view
  Widget _buildTabView() {
    final views = [
      _buildBasicConfigTab(),
      _buildSectionsTab(),
      _buildChartsTab(),
    ];

    if (widget.showAdvancedOptions && _showAllTabs) {
      views.addAll([
        _buildLayoutTab(),
        _buildSecurityTab(),
      ]);
    }

    return TabBarView(
      controller: _tabController,
      children: views,
    );
  }

  /// Builds basic configuration tab
  Widget _buildBasicConfigTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildExportFormatSection(),
          const SizedBox(height: 24),
          _buildFilenameSection(),
          const SizedBox(height: 24),
          _buildQualitySection(),
          const SizedBox(height: 24),
          _buildSchedulingSection(),
          const SizedBox(height: 24),
          _buildPreviewSection(),
        ],
      ),
    );
  }

  /// Builds export format selection section
  Widget _buildExportFormatSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Export Format',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 8,
              children: [
                _buildFormatChip(ExportFormat.pdf, 'PDF', Icons.picture_as_pdf),
                _buildFormatChip(ExportFormat.csv, 'CSV', Icons.table_chart),
                _buildFormatChip(ExportFormat.xlsx, 'Excel', Icons.grid_on),
                _buildFormatChip(ExportFormat.json, 'JSON', Icons.code),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _getFormatDescription(_exportFormat),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds format selection chip
  Widget _buildFormatChip(ExportFormat format, String label, IconData icon) {
    final isSelected = _exportFormat == format;

    return FilterChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16),
          const SizedBox(width: 4),
          Text(label),
        ],
      ),
      selected: isSelected,
      onSelected: (selected) {
        if (selected) {
          setState(() {
            _exportFormat = format;
          });
          _updateConfiguration();
        }
      },
      backgroundColor: Theme.of(context).colorScheme.surface,
      selectedColor: Theme.of(context).colorScheme.primaryContainer,
    );
  }

  /// Builds filename configuration section
  Widget _buildFilenameSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Output Filename',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _filenameController,
              decoration: InputDecoration(
                hintText: 'Enter filename without extension',
                prefixIcon: const Icon(Icons.file_present),
                suffixText: '.${_exportFormat.name}',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onChanged: (value) => _updateConfiguration(),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton.icon(
                  onPressed: _generateTimestampFilename,
                  icon: const Icon(Icons.schedule, size: 16),
                  label: const Text('Add Timestamp'),
                ),
                const SizedBox(width: 8),
                TextButton.icon(
                  onPressed: _generateTemplateFilename,
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: const Text('Auto Generate'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Builds quality and options section
  Widget _buildQualitySection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Quality & Options',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Include Charts'),
              subtitle: const Text('Embed charts in the report'),
              value: _includeCharts,
              onChanged: (value) {
                setState(() {
                  _includeCharts = value;
                });
                _updateConfiguration();
              },
            ),
            if (_includeCharts) ...[
              const SizedBox(height: 12),
              Text(
                'Chart Quality: ${_chartQuality} DPI',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              Slider(
                value: _chartQuality.toDouble(),
                min: 150,
                max: 600,
                divisions: 3,
                label: '${_chartQuality} DPI',
                onChanged: (value) {
                  setState(() {
                    _chartQuality = value.round();
                  });
                  _updateConfiguration();
                },
              ),
            ],
            const SizedBox(height: 8),
            SwitchListTile(
              title: const Text('Compress Output'),
              subtitle: const Text('Reduce file size for sharing'),
              value: _compressOutput,
              onChanged: (value) {
                setState(() {
                  _compressOutput = value;
                });
                _updateConfiguration();
              },
            ),
          ],
        ),
      ),
    );
  }

  /// Builds scheduling section
  Widget _buildSchedulingSection() {
    if (!widget.enableScheduling) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Scheduling',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              title: const Text('Enable Scheduling'),
              subtitle: const Text('Automatically generate reports'),
              value: _schedulingEnabled,
              onChanged: widget.template.supportsScheduling
                  ? (value) {
                      setState(() {
                        _schedulingEnabled = value;
                        if (!value) {
                          _scheduleConfig = null;
                        } else {
                          _scheduleConfig = _getDefaultScheduleConfig();
                        }
                      });
                      _updateConfiguration();
                    }
                  : null,
            ),
            if (!widget.template.supportsScheduling) ...[
              const SizedBox(height: 8),
              Text(
                'This template does not support scheduling',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
            if (_schedulingEnabled && _scheduleConfig != null) ...[
              const SizedBox(height: 16),
              _buildScheduleConfig(),
            ],
          ],
        ),
      ),
    );
  }

  /// Builds schedule configuration
  Widget _buildScheduleConfig() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownButtonFormField<ScheduleFrequency>(
          value: _scheduleConfig!.frequency,
          decoration: const InputDecoration(
            labelText: 'Frequency',
            border: OutlineInputBorder(),
          ),
          items: ScheduleFrequency.values.map((frequency) {
            return DropdownMenuItem(
              value: frequency,
              child: Text(frequency.name.toUpperCase()),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() {
                _scheduleConfig = _scheduleConfig!.copyWith(frequency: value);
              });
              _updateConfiguration();
            }
          },
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                initialValue: _scheduleConfig!.timeOfDay.hour.toString().padLeft(2, '0'),
                decoration: const InputDecoration(
                  labelText: 'Hour (24h)',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(2),
                ],
                onChanged: (value) {
                  final hour = int.tryParse(value);
                  if (hour != null && hour >= 0 && hour <= 23) {
                    setState(() {
                      _scheduleConfig = _scheduleConfig!.copyWith(
                        timeOfDay: TimeOfDay(
                          hour: hour,
                          minute: _scheduleConfig!.timeOfDay.minute,
                        ),
                      );
                    });
                    _updateConfiguration();
                  }
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextFormField(
                initialValue: _scheduleConfig!.timeOfDay.minute.toString().padLeft(2, '0'),
                decoration: const InputDecoration(
                  labelText: 'Minute',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(2),
                ],
                onChanged: (value) {
                  final minute = int.tryParse(value);
                  if (minute != null && minute >= 0 && minute <= 59) {
                    setState(() {
                      _scheduleConfig = _scheduleConfig!.copyWith(
                        timeOfDay: TimeOfDay(
                          hour: _scheduleConfig!.timeOfDay.hour,
                          minute: minute,
                        ),
                      );
                    });
                    _updateConfiguration();
                  }
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds preview section
  Widget _buildPreviewSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Preview Information',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _buildPreviewItem('Export Format', _exportFormat.name.toUpperCase()),
            _buildPreviewItem('Filename', '${_filenameController.text}.${_exportFormat.name}'),
            _buildPreviewItem('Sections', '${_selectedSections.length} of ${widget.template.sections.length}'),
            _buildPreviewItem('Charts', _includeCharts ? 'Included' : 'Excluded'),
            if (_schedulingEnabled)
              _buildPreviewItem('Scheduling', _scheduleConfig?.frequency.name.toUpperCase() ?? 'None'),
          ],
        ),
      ),
    );
  }

  /// Builds preview item
  Widget _buildPreviewItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds sections configuration tab
  Widget _buildSectionsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Select Report Sections',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Choose which sections to include in your report',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 16),
          ...widget.template.sections.map((section) => _buildSectionTile(section)),
          const SizedBox(height: 16),
          Row(
            children: [
              TextButton.icon(
                onPressed: _selectAllSections,
                icon: const Icon(Icons.select_all),
                label: const Text('Select All'),
              ),
              const SizedBox(width: 8),
              TextButton.icon(
                onPressed: _clearAllSections,
                icon: const Icon(Icons.clear_all),
                label: const Text('Clear All'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds section tile
  Widget _buildSectionTile(ReportSection section) {
    final isSelected = _selectedSections.contains(section);
    final chartCount = widget.template.chartConfigurations[section]?.length ?? 0;

    return Card(
      child: CheckboxListTile(
        title: Text(_getSectionTitle(section)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_getSectionDescription(section)),
            if (chartCount > 0) ...[
              const SizedBox(height: 4),
              Text(
                '$chartCount chart${chartCount > 1 ? 's' : ''} included',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.primary,
                  fontSize: 12,
                ),
              ),
            ],
          ],
        ),
        value: isSelected,
        onChanged: (value) {
          setState(() {
            if (value == true) {
              _selectedSections.add(section);
            } else {
              _selectedSections.remove(section);
            }
          });
          _updateConfiguration();
        },
        secondary: Icon(_getSectionIcon(section)),
      ),
    );
  }

  /// Builds charts configuration tab
  Widget _buildChartsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Chart Configuration',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Configure charts for each section',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 16),
          ..._selectedSections.map((section) => _buildChartSection(section)),
        ],
      ),
    );
  }

  /// Builds chart section
  Widget _buildChartSection(ReportSection section) {
    final charts = _chartConfigurations[section] ?? [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_getSectionIcon(section)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _getSectionTitle(section),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Chip(
                  label: Text('${charts.length} charts'),
                  backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (charts.isEmpty)
              Text(
                'No charts configured for this section',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
              )
            else
              ...charts.map((chart) => _buildChartTile(chart)),
          ],
        ),
      ),
    );
  }

  /// Builds chart tile
  Widget _buildChartTile(ReportChartConfig chart) {
    return ListTile(
      leading: Icon(_getChartIcon(chart.chartType)),
      title: Text(chart.title),
      subtitle: Text(chart.description),
      trailing: Chip(
        label: Text(chart.chartType.name),
        backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
      ),
      contentPadding: EdgeInsets.zero,
    );
  }

  /// Builds layout configuration tab
  Widget _buildLayoutTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Layout & Styling',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Layout configuration options will be implemented here',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds security configuration tab
  Widget _buildSecurityTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Security & Sharing',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Security and sharing options will be implemented here',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ],
      ),
    );
  }

  /// Initializes configurations from template
  void _initializeConfigurations() {
    // Initialize selected sections
    _selectedSections = Set.from(widget.template.sections);

    // Initialize chart configurations
    _chartConfigurations = Map.from(widget.template.chartConfigurations);

    // Initialize layout configuration
    _layoutConfig = widget.template.layoutConfig;

    // Initialize security configuration
    _securityConfig = widget.template.securityConfig;

    // Initialize from initial configuration if provided
    if (widget.initialConfiguration != null) {
      _exportFormat = widget.initialConfiguration!.exportFormat;
      _filenameController.text = widget.initialConfiguration!.outputFileName;
      _includeCharts = widget.initialConfiguration!.includeCharts;
      _chartQuality = widget.initialConfiguration!.chartQuality;
      _compressOutput = widget.initialConfiguration!.compressOutput;
    }

    // Trigger initial update
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateConfiguration();
    });
  }

  /// Handles tab changes
  void _onTabChanged() {
    // Haptic feedback on tab change
    HapticFeedback.selectionClick();
  }

  /// Updates configuration and notifies parent
  void _updateConfiguration() {
    final config = ReportGenerationConfig(
      exportFormat: _exportFormat,
      outputFileName: _filenameController.text.isNotEmpty
          ? _filenameController.text
          : 'malaria_analytics_report',
      includeCharts: _includeCharts,
      chartQuality: _chartQuality,
      compressOutput: _compressOutput,
      customStyling: {},
      metadata: {
        'selectedSections': _selectedSections.map((s) => s.name).toList(),
        'schedulingEnabled': _schedulingEnabled,
        'scheduleConfig': _scheduleConfig?.toJson(),
      },
    );

    widget.onConfigurationChanged(config);
  }

  /// Generates timestamp filename
  void _generateTimestampFilename() {
    final now = DateTime.now();
    final timestamp = '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}_${now.hour.toString().padLeft(2, '0')}${now.minute.toString().padLeft(2, '0')}';

    setState(() {
      _filenameController.text = 'malaria_analytics_report_$timestamp';
    });
    _updateConfiguration();
  }

  /// Generates template-based filename
  void _generateTemplateFilename() {
    final templateName = widget.template.name.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '_');

    setState(() {
      _filenameController.text = 'report_$templateName';
    });
    _updateConfiguration();
  }

  /// Selects all sections
  void _selectAllSections() {
    setState(() {
      _selectedSections = Set.from(widget.template.sections);
    });
    _updateConfiguration();
  }

  /// Clears all sections
  void _clearAllSections() {
    setState(() {
      _selectedSections.clear();
    });
    _updateConfiguration();
  }

  /// Gets default schedule configuration
  ScheduleConfig _getDefaultScheduleConfig() {
    return const ScheduleConfig(
      frequency: ScheduleFrequency.weekly,
      timeOfDay: TimeOfDay(hour: 9, minute: 0),
    );
  }

  /// Gets format description
  String _getFormatDescription(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return 'Professional document format with charts and formatting';
      case ExportFormat.csv:
        return 'Spreadsheet format for data analysis';
      case ExportFormat.xlsx:
        return 'Excel format with multiple sheets and charts';
      case ExportFormat.json:
        return 'Structured data format for integration';
      default:
        return 'Selected export format';
    }
  }

  /// Gets section title
  String _getSectionTitle(ReportSection section) {
    switch (section) {
      case ReportSection.overview:
        return 'Executive Overview';
      case ReportSection.predictionMetrics:
        return 'Prediction Metrics';
      case ReportSection.environmentalAnalysis:
        return 'Environmental Analysis';
      case ReportSection.riskAssessment:
        return 'Risk Assessment';
      case ReportSection.alertPerformance:
        return 'Alert Performance';
      case ReportSection.dataQuality:
        return 'Data Quality';
      case ReportSection.recommendations:
        return 'Recommendations';
      case ReportSection.appendix:
        return 'Appendix';
    }
  }

  /// Gets section description
  String _getSectionDescription(ReportSection section) {
    switch (section) {
      case ReportSection.overview:
        return 'High-level summary and key metrics';
      case ReportSection.predictionMetrics:
        return 'Model accuracy and performance metrics';
      case ReportSection.environmentalAnalysis:
        return 'Environmental factors and trends';
      case ReportSection.riskAssessment:
        return 'Risk levels and geographic distribution';
      case ReportSection.alertPerformance:
        return 'Alert system effectiveness metrics';
      case ReportSection.dataQuality:
        return 'Data completeness and accuracy assessment';
      case ReportSection.recommendations:
        return 'Actionable insights and suggestions';
      case ReportSection.appendix:
        return 'Technical details and methodology';
    }
  }

  /// Gets section icon
  IconData _getSectionIcon(ReportSection section) {
    switch (section) {
      case ReportSection.overview:
        return Icons.dashboard;
      case ReportSection.predictionMetrics:
        return Icons.analytics;
      case ReportSection.environmentalAnalysis:
        return Icons.eco;
      case ReportSection.riskAssessment:
        return Icons.warning;
      case ReportSection.alertPerformance:
        return Icons.notifications;
      case ReportSection.dataQuality:
        return Icons.verified;
      case ReportSection.recommendations:
        return Icons.lightbulb;
      case ReportSection.appendix:
        return Icons.library_books;
    }
  }

  /// Gets chart icon
  IconData _getChartIcon(ChartType chartType) {
    switch (chartType) {
      case ChartType.lineChart:
        return Icons.show_chart;
      case ChartType.barChart:
        return Icons.bar_chart;
      case ChartType.pieChart:
        return Icons.pie_chart;
      case ChartType.scatterPlot:
        return Icons.scatter_plot;
      case ChartType.areaChart:
        return Icons.area_chart;
      case ChartType.histogram:
        return Icons.equalizer;
      case ChartType.heatmap:
        return Icons.grid_on;
      case ChartType.radar:
        return Icons.radar;
      case ChartType.gauge:
        return Icons.speed;
    }
  }
}

/// Extension for ScheduleConfig to add JSON conversion
extension ScheduleConfigExtension on ScheduleConfig {
  Map<String, dynamic> toJson() {
    return {
      'frequency': frequency.name,
      'interval': interval,
      'timeOfDay': {
        'hour': timeOfDay.hour,
        'minute': timeOfDay.minute,
      },
      'timezone': timezone,
      'isActive': isActive,
    };
  }
}