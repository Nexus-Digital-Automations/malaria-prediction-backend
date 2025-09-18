# Malaria Prediction Flutter Frontend

AI-powered malaria outbreak prediction and monitoring mobile application built with Flutter.

## 🏗️ Architecture Overview

This Flutter application follows Clean Architecture principles with a feature-based modular structure:

```
lib/
├── main.dart                    # App entry point
├── app/                         # App-level configuration
│   ├── app.dart                 # Main app widget
│   ├── routes/                  # Navigation routing (Go Router)
│   └── theme/                   # Comprehensive theme system
├── core/                        # Shared utilities and constants
│   ├── constants/               # App constants and configuration
│   ├── errors/                  # Error handling classes
│   ├── network/                 # Network configuration
│   ├── utils/                   # Utility functions
│   └── widgets/                 # Reusable UI components
├── features/                    # Feature modules (Clean Architecture)
│   ├── authentication/          # User authentication
│   ├── dashboard/              # Main dashboard with health metrics
│   ├── risk_maps/              # Interactive risk maps
│   ├── alerts/                 # Real-time alert system
│   ├── analytics/              # Data visualization
│   ├── settings/               # User preferences & theme
│   └── offline/                # Offline functionality
└── injection_container.dart    # Dependency injection setup
```

## 🎨 Design System

### Material Design 3 Implementation
- **Healthcare-appropriate color palette** with risk assessment colors
- **Comprehensive theming** supporting light/dark modes with system preference detection
- **Accessibility compliance** meeting WCAG 2.1 AA standards
- **Responsive layouts** optimized for mobile, tablet, and desktop

### Color Palette
- **Primary**: Healthcare blue (#1976D2)
- **Secondary**: Healthcare green (#388E3C)
- **Risk Colors**: 
  - Low: Green (#4CAF50)
  - Medium: Orange (#FF9800)
  - High: Red (#F44336)
  - Critical: Purple (#9C27B0)

## 🧭 Navigation System

### Bottom Navigation (Primary)
- **Dashboard**: Health metrics overview
- **Maps**: Interactive risk visualization
- **Alerts**: Notification center
- **Analytics**: Data insights
- **Profile**: User account management

### Navigation Drawer (Secondary)
- Data Sources management
- Offline mode access
- Export functionality
- Settings and preferences
- Help and support

## 📊 Dashboard Features

### Overview Widgets
- **Risk Overview Card**: Current regional risk levels with visual indicators
- **Environmental Metrics**: Weather and satellite data display
- **Alert Summary**: Recent notifications and warnings
- **Prediction Charts**: Risk forecasts with interactive visualizations
- **Quick Actions**: Rapid access to common tasks
- **Recent Activity**: System activity timeline

### Responsive Design
- **Mobile**: Single-column layout optimized for touch
- **Tablet**: Multi-column grid layout
- **Desktop**: Three-column dashboard with expanded widgets

## 🔧 Technical Stack

### Core Framework
- **Flutter**: 3.16+ for cross-platform development
- **Dart**: 3.2+ with null safety

### State Management
- **flutter_bloc**: 8.1+ for predictable state management
- **hydrated_bloc**: Persistent state across sessions
- **equatable**: Value equality for state objects

### Navigation
- **go_router**: 12.1+ for declarative routing
- **Deep linking** support for all features
- **Authenticated route** protection

### UI & Visualization
- **fl_chart**: Interactive data visualization
- **flutter_map**: Geospatial visualization
- **lottie**: Smooth animations
- **shimmer**: Loading state animations

### Data & Storage
- **dio**: HTTP client with interceptors
- **hive**: Lightweight local database
- **flutter_secure_storage**: Encrypted credential storage
- **shared_preferences**: Simple key-value storage

## 🚀 Getting Started

### Prerequisites
- Flutter SDK 3.16.0 or higher
- Dart SDK 3.2.0 or higher
- Android Studio / VS Code with Flutter extension
- iOS development tools (for iOS builds)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd flutter_frontend
   ```

2. **Install dependencies**
   ```bash
   flutter pub get
   ```

3. **Generate code** (for serialization and routing)
   ```bash
   flutter packages pub run build_runner build
   ```

4. **Run the application**
   ```bash
   flutter run
   ```

### Development Commands

```bash
# Run with hot reload
flutter run

# Run tests
flutter test

# Run tests with coverage
flutter test --coverage

# Analyze code
flutter analyze

# Format code
dart format .

# Generate code
flutter packages pub run build_runner build --delete-conflicting-outputs

# Build for release
flutter build apk --release    # Android
flutter build ios --release    # iOS
flutter build web --release    # Web
```

## 🔧 Configuration

### Environment Setup
Configure different environments in:
- `lib/core/constants/app_constants.dart`
- Update API URLs for development/production

### Theme Customization
Modify themes in:
- `lib/app/theme/app_theme.dart`
- `lib/app/theme/app_colors.dart`

## 🧪 Testing Strategy

### Unit Tests
- BLoC logic testing
- Utility function validation
- Model serialization/deserialization

### Widget Tests
- UI component behavior
- User interaction flows
- State management integration

### Integration Tests
- End-to-end user journeys
- API integration validation
- Offline functionality

## 📱 Platform Support

### Mobile (Primary)
- **Android**: API 21+ (Android 5.0)
- **iOS**: iOS 12.0+

### Web (Secondary)
- Progressive Web App capabilities
- Responsive design for desktop browsers

### Desktop (Future)
- Windows, macOS, Linux support planned

## 🔐 Security Features

### Authentication
- JWT token-based authentication
- Biometric authentication support
- Secure token storage

### Data Protection
- Encrypted local storage
- SSL/TLS communication
- Input validation and sanitization

## 🌐 Offline Capabilities

### Data Synchronization
- Essential data caching for 7-day offline use
- Background sync when connection restored
- Conflict resolution for offline changes

### Offline Features
- Cached risk maps and predictions
- Local alert storage
- Offline-first architecture

## 📈 Performance Optimizations

### Image Handling
- WebP format support for 30% smaller files
- Cached network images with memory management
- Lazy loading for large datasets

### State Management
- Efficient BLoC state transitions
- Hydrated state for instant app launches
- Memory leak prevention

## 🎯 Accessibility Features

### WCAG 2.1 AA Compliance
- High contrast color schemes
- Text scaling support (0.8x - 1.4x)
- Screen reader compatibility
- Keyboard navigation support

### Inclusive Design
- Minimum 48px touch targets
- Clear visual feedback
- Error message clarity
- Multi-language support ready

## 🔄 CI/CD Pipeline

### Automated Testing
- Unit and widget test execution
- Code coverage reporting
- Static analysis with custom rules

### Build Pipeline
- Multi-platform builds (Android, iOS, Web)
- Automated code signing
- Release artifact generation

## 📚 Development Guidelines

### Code Style
- Follow Flutter style guide
- Use meaningful variable names
- Comprehensive inline documentation
- Error handling best practices

### Feature Development
- Clean Architecture principles
- Test-driven development
- Responsive design considerations
- Accessibility testing

## 🤝 Contributing

1. Follow the established architecture patterns
2. Maintain test coverage above 80%
3. Ensure accessibility compliance
4. Update documentation for new features

## 📄 License

This project is part of the malaria prediction system. See the main project README for license details.

## 🆘 Support

For issues and questions:
- Check the main project documentation
- Review existing GitHub issues
- Create detailed bug reports with reproduction steps

---

**Built with ❤️ for global health surveillance**