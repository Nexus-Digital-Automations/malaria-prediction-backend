/// Risk Legend Widget for Map Visualization
///
/// Displays a legend showing risk level colors and descriptions
/// for the choropleth map overlay.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:flutter/material.dart';
import '../../domain/entities/risk_data.dart';

/// Risk legend widget for displaying risk level colors
class RiskLegendWidget extends StatelessWidget {
  /// Whether the legend is visible
  final bool isVisible;

  /// Callback when legend visibility is toggled
  final VoidCallback? onToggle;

  /// Custom title for the legend
  final String title;

  /// Whether to show the toggle button
  final bool showToggle;

  const RiskLegendWidget({
    super.key,
    this.isVisible = true,
    this.onToggle,
    this.title = 'Malaria Risk',
    this.showToggle = true,
  });

  @override
  Widget build(BuildContext context) {
    if (!isVisible) {
      return _buildMinimizedLegend();
    }

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      child: Container(
        padding: const EdgeInsets.all(12),
        constraints: const BoxConstraints(
          minWidth: 140,
          maxWidth: 180,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            const SizedBox(height: 8),
            const Divider(height: 1),
            const SizedBox(height: 8),
            ...RiskLevel.values.reversed.map(_buildLegendItem),
          ],
        ),
      ),
    );
  }

  Widget _buildMinimizedLegend() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      child: InkWell(
        onTap: onToggle,
        borderRadius: BorderRadius.circular(8),
        child: const Padding(
          padding: EdgeInsets.all(8),
          child: Icon(Icons.legend_toggle, size: 24),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        if (showToggle)
          InkWell(
            onTap: onToggle,
            borderRadius: BorderRadius.circular(4),
            child: const Padding(
              padding: EdgeInsets.all(4),
              child: Icon(Icons.close, size: 16),
            ),
          ),
      ],
    );
  }

  Widget _buildLegendItem(RiskLevel level) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 20,
            height: 20,
            decoration: BoxDecoration(
              color: level.fillColor,
              border: Border.all(color: level.borderColor, width: 1.5),
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  level.displayName,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  _getRiskRange(level),
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey.shade600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getRiskRange(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return '< 30%';
      case RiskLevel.medium:
        return '30-60%';
      case RiskLevel.high:
        return '60-80%';
      case RiskLevel.critical:
        return '> 80%';
    }
  }
}
