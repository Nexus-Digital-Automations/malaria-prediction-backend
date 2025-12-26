/// Region Info Popup Widget for Risk Map
///
/// Displays detailed information about a selected region including
/// risk score, environmental factors, and prediction details.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/risk_data.dart';

/// Region info popup widget
class RegionInfoPopup extends StatelessWidget {
  /// Risk data for the selected region
  final RiskData riskData;

  /// Callback when popup is closed
  final VoidCallback? onClose;

  /// Callback when view details is pressed
  final VoidCallback? onViewDetails;

  const RegionInfoPopup({
    super.key,
    required this.riskData,
    this.onClose,
    this.onViewDetails,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 400),
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 12),
            _buildRiskIndicator(),
            const SizedBox(height: 16),
            _buildMetricsGrid(),
            if (riskData.environmentalFactors != null) ...[
              const SizedBox(height: 16),
              _buildEnvironmentalFactors(),
            ],
            const SizedBox(height: 16),
            _buildActions(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: riskData.riskLevel.fillColor,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: riskData.riskLevel.borderColor, width: 2),
          ),
          child: Icon(
            riskData.riskLevel.icon,
            color: Colors.white,
            size: 24,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                riskData.regionName,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Text(
                riskData.administrativeLevel.toUpperCase(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
            ],
          ),
        ),
        IconButton(
          icon: const Icon(Icons.close, size: 20),
          onPressed: onClose,
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
        ),
      ],
    );
  }

  Widget _buildRiskIndicator() {
    final percentage = (riskData.riskScore * 100).toStringAsFixed(1);

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: riskData.riskLevel.fillColor.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: riskData.riskLevel.borderColor),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Risk Level',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 4),
                Text(
                  riskData.riskLevel.displayName,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: riskData.riskLevel.borderColor,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: riskData.riskLevel.color,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              '$percentage%',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricsGrid() {
    return Wrap(
      spacing: 16,
      runSpacing: 12,
      children: [
        _buildMetricChip(
          icon: Icons.verified,
          label: 'Confidence',
          value: '${(riskData.confidence * 100).toStringAsFixed(0)}%',
        ),
        if (riskData.predictedCases != null)
          _buildMetricChip(
            icon: Icons.sick,
            label: 'Predicted Cases',
            value: NumberFormat.compact().format(riskData.predictedCases),
          ),
        _buildMetricChip(
          icon: Icons.calendar_today,
          label: 'Prediction Date',
          value: DateFormat('MMM d').format(riskData.predictionDate),
        ),
        _buildMetricChip(
          icon: Icons.update,
          label: 'Last Updated',
          value: _formatTimeAgo(riskData.lastUpdated),
        ),
      ],
    );
  }

  Widget _buildMetricChip({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.grey.shade600),
          const SizedBox(width: 6),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
              ),
              Text(
                value,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEnvironmentalFactors() {
    final factors = riskData.environmentalFactors!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Environmental Factors',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildFactorBar(
                'Temperature',
                '${factors.temperature.toStringAsFixed(1)}°C',
                factors.temperature / 45, // Normalize to 0-45°C
                Colors.orange,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildFactorBar(
                'Humidity',
                '${factors.humidity.toStringAsFixed(0)}%',
                factors.humidity / 100,
                Colors.blue,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildFactorBar(
                'Rainfall',
                '${factors.rainfall.toStringAsFixed(0)}mm',
                factors.rainfall / 300, // Normalize to 0-300mm
                Colors.cyan,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildFactorBar(
                'Vegetation',
                factors.vegetationIndex.toStringAsFixed(2),
                factors.vegetationIndex,
                Colors.green,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildFactorBar(String label, String value, double progress, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 11)),
            Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress.clamp(0.0, 1.0),
            backgroundColor: color.withValues(alpha: 0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  Widget _buildActions(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: onViewDetails,
            icon: const Icon(Icons.open_in_new, size: 16),
            label: const Text('View Details'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () => _showAlertHistory(context),
            icon: const Icon(Icons.notifications, size: 16),
            label: const Text('Alerts'),
            style: ElevatedButton.styleFrom(
              backgroundColor: riskData.riskLevel.color,
              foregroundColor: Colors.white,
            ),
          ),
        ),
      ],
    );
  }

  void _showAlertHistory(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Alert history coming soon')),
    );
  }

  String _formatTimeAgo(DateTime dateTime) {
    final difference = DateTime.now().difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM d').format(dateTime);
    }
  }
}
