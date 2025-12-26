/// Map Controls Widget for Interactive Map Navigation
///
/// Provides zoom, pan, and location controls for the flutter_map.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';

/// Map controls widget for zoom and navigation
class MapControlsWidget extends StatelessWidget {
  /// Map controller for programmatic control
  final MapController mapController;

  /// Callback for zoom in
  final VoidCallback? onZoomIn;

  /// Callback for zoom out
  final VoidCallback? onZoomOut;

  /// Callback for reset view
  final VoidCallback? onResetView;

  /// Callback for locate user
  final VoidCallback? onLocate;

  /// Show compass
  final bool showCompass;

  /// Show scale
  final bool showScale;

  const MapControlsWidget({
    super.key,
    required this.mapController,
    this.onZoomIn,
    this.onZoomOut,
    this.onResetView,
    this.onLocate,
    this.showCompass = true,
    this.showScale = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Compass
        if (showCompass) ...[
          _buildControlButton(
            icon: Icons.explore,
            tooltip: 'Reset Rotation',
            onPressed: _resetRotation,
          ),
          const SizedBox(height: 8),
        ],

        // Zoom controls
        Card(
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildZoomButton(
                icon: Icons.add,
                tooltip: 'Zoom In',
                onPressed: onZoomIn ?? _zoomIn,
              ),
              Container(
                height: 1,
                width: 36,
                color: Colors.grey.shade300,
              ),
              _buildZoomButton(
                icon: Icons.remove,
                tooltip: 'Zoom Out',
                onPressed: onZoomOut ?? _zoomOut,
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),

        // Location button
        _buildControlButton(
          icon: Icons.my_location,
          tooltip: 'My Location',
          onPressed: onLocate,
        ),
        const SizedBox(height: 8),

        // Reset view button
        _buildControlButton(
          icon: Icons.home,
          tooltip: 'Reset View',
          onPressed: onResetView,
        ),
      ],
    );
  }

  Widget _buildControlButton({
    required IconData icon,
    required String tooltip,
    VoidCallback? onPressed,
  }) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(8),
        child: Tooltip(
          message: tooltip,
          child: Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            child: Icon(icon, size: 22),
          ),
        ),
      ),
    );
  }

  Widget _buildZoomButton({
    required IconData icon,
    required String tooltip,
    VoidCallback? onPressed,
  }) {
    return InkWell(
      onTap: onPressed,
      child: Tooltip(
        message: tooltip,
        child: Container(
          width: 44,
          height: 40,
          alignment: Alignment.center,
          child: Icon(icon, size: 22),
        ),
      ),
    );
  }

  void _zoomIn() {
    final currentZoom = mapController.camera.zoom;
    mapController.move(
      mapController.camera.center,
      (currentZoom + 1).clamp(3.0, 18.0),
    );
  }

  void _zoomOut() {
    final currentZoom = mapController.camera.zoom;
    mapController.move(
      mapController.camera.center,
      (currentZoom - 1).clamp(3.0, 18.0),
    );
  }

  void _resetRotation() {
    mapController.rotate(0);
  }
}
