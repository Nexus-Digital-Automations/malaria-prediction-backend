/// Export controls widget for analytics report generation
///
/// This widget provides controls for exporting analytics data
/// in various formats including PDF, CSV, Excel, and JSON.
///
/// Usage:
/// ```dart
/// ExportControls(
///   onExport: (format) => exportReport(format),
///   availableFormats: [ExportFormat.pdf, ExportFormat.csv],
/// );
/// ```

import 'package:flutter/material.dart';
import '../../domain/repositories/analytics_repository.dart';

/// Export controls widget
class ExportControls extends StatefulWidget {
  /// Callback when export is requested
  final ValueChanged<ExportFormat> onExport;

  /// Available export formats
  final List<ExportFormat> availableFormats;

  /// Whether to include charts in export
  final bool defaultIncludeCharts;

  /// Default report sections to include
  final List<ReportSection>? defaultSections;

  /// Constructor requiring export callback
  const ExportControls({
    super.key,
    required this.onExport,
    this.availableFormats = const [
      ExportFormat.pdf,
      ExportFormat.csv,
      ExportFormat.xlsx,
      ExportFormat.json,
    ],
    this.defaultIncludeCharts = true,
    this.defaultSections,
  });

  @override
  State<ExportControls> createState() => _ExportControlsState();
}

class _ExportControlsState extends State<ExportControls> {
  /// Currently selected export format
  ExportFormat _selectedFormat = ExportFormat.pdf;

  /// Whether to include charts in export
  bool _includeCharts = true;

  /// Selected report sections
  Set<ReportSection> _selectedSections = {
    ReportSection.summary,
    ReportSection.predictionAccuracy,
    ReportSection.environmentalTrends,
    ReportSection.riskAnalysis,
  };

  @override
  void initState() {
    super.initState();
    _selectedFormat = widget.availableFormats.first;
    _includeCharts = widget.defaultIncludeCharts;
    if (widget.defaultSections != null) {
      _selectedSections = widget.defaultSections!.toSet();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 16),
            _buildFormatSelector(),
            const SizedBox(height: 16),
            _buildOptionsSection(),
            const SizedBox(height: 16),
            _buildSectionsSelector(),
            const SizedBox(height: 20),
            _buildExportButton(),
          ],
        ),
      ),
    );
  }

  /// Builds the header
  Widget _buildHeader() {
    return Row(
      children: [
        Icon(
          Icons.file_download,
          color: Theme.of(context).colorScheme.primary,
          size: 24,
        ),
        const SizedBox(width: 8),
        Text(
          'Export Analytics Report',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  /// Builds format selector
  Widget _buildFormatSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Export Format',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: widget.availableFormats.map((format) {
            final isSelected = _selectedFormat == format;
            return ChoiceChip(
              label: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _getFormatIcon(format),
                    size: 16,
                    color: isSelected
                        ? Theme.of(context).colorScheme.onPrimary
                        : Theme.of(context).colorScheme.onSurface,
                  ),
                  const SizedBox(width: 4),
                  Text(_getFormatDisplayName(format)),
                ],
              ),
              selected: isSelected,
              onSelected: (selected) {
                if (selected) {
                  setState(() {
                    _selectedFormat = format;
                  });
                }
              },
              selectedColor: Theme.of(context).colorScheme.primary,
              labelStyle: TextStyle(
                color: isSelected
                    ? Theme.of(context).colorScheme.onPrimary
                    : Theme.of(context).colorScheme.onSurface,
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds export options
  Widget _buildOptionsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Export Options',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        CheckboxListTile(
          title: const Text('Include Charts'),
          subtitle: const Text('Embed visualizations in the report'),
          value: _includeCharts,
          onChanged: (value) {
            setState(() {
              _includeCharts = value ?? true;
            });
          },
          controlAffinity: ListTileControlAffinity.leading,
          contentPadding: EdgeInsets.zero,
        ),
      ],
    );
  }

  /// Builds report sections selector
  Widget _buildSectionsSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Report Sections',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: ReportSection.values.map((section) {
            final isSelected = _selectedSections.contains(section);
            return FilterChip(
              label: Text(_getSectionDisplayName(section)),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedSections.add(section);
                  } else {
                    _selectedSections.remove(section);
                  }
                });
              },
              selectedColor: Theme.of(context).colorScheme.primary.withOpacity(0.2),
              checkmarkColor: Theme.of(context).colorScheme.primary,
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds export button
  Widget _buildExportButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _selectedSections.isNotEmpty ? _handleExport : null,
        icon: const Icon(Icons.file_download),
        label: Text('Export ${_getFormatDisplayName(_selectedFormat)} Report'),
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }

  /// Handles export action
  void _handleExport() {
    if (_selectedSections.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select at least one report section'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    widget.onExport(_selectedFormat);

    // Show confirmation
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Exporting ${_getFormatDisplayName(_selectedFormat)} report...',
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  /// Gets icon for export format
  IconData _getFormatIcon(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return Icons.picture_as_pdf;
      case ExportFormat.csv:
        return Icons.table_chart;
      case ExportFormat.xlsx:
        return Icons.grid_on;
      case ExportFormat.json:
        return Icons.code;
      case ExportFormat.html:
        return Icons.web;
    }
  }

  /// Gets display name for export format
  String _getFormatDisplayName(ExportFormat format) {
    switch (format) {
      case ExportFormat.pdf:
        return 'PDF';
      case ExportFormat.csv:
        return 'CSV';
      case ExportFormat.xlsx:
        return 'Excel';
      case ExportFormat.json:
        return 'JSON';
      case ExportFormat.html:
        return 'HTML';
    }
  }

  /// Gets display name for report section
  String _getSectionDisplayName(ReportSection section) {
    switch (section) {
      case ReportSection.summary:
        return 'Summary';
      case ReportSection.predictionAccuracy:
        return 'Predictions';
      case ReportSection.environmentalTrends:
        return 'Environment';
      case ReportSection.riskAnalysis:
        return 'Risk Analysis';
      case ReportSection.alertPerformance:
        return 'Alerts';
      case ReportSection.dataQuality:
        return 'Data Quality';
      case ReportSection.recommendations:
        return 'Recommendations';
    }
  }
}