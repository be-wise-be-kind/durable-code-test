# Web Application Framework

**Purpose**: Full-stack web application demonstrating AI-ready development practices with modern React and FastAPI architecture

**Scope**: Complete web application implementation including frontend, backend, development workflows, and deployment strategies

**Overview**: Comprehensive full-stack web application that demonstrates AI-ready development practices
    through modern React/TypeScript frontend and FastAPI backend architecture. Showcases development
    workflows, quality assurance processes, testing strategies, and maintenance approaches through
    an interactive tabbed interface. Serves as a practical reference for full-stack development
    patterns, component architecture, and production-ready application structure.

**Dependencies**: React, TypeScript, FastAPI, Docker, development tooling, testing frameworks

**Exports**: Web application architecture, component patterns, development workflows, deployment strategies

**Related**: Development tooling documentation, testing framework guides, deployment documentation

**Implementation**: React/TypeScript frontend with FastAPI backend, containerized deployment, comprehensive testing

---

## Architecture Overview

Modern full-stack web application demonstrating AI-ready development practices with comprehensive development workflows and interactive user interface.

## Frontend Architecture

### Technology Stack

**Location**: `durable-code-app/frontend/`

- **React 18** with functional components and modern hooks
- **TypeScript** for comprehensive type safety
- **Vite** for fast development and optimized builds
- **CSS Modules** for component-scoped styling
- **Vitest** for testing framework
- **React.lazy()** and **Suspense** for code splitting and lazy loading

### Core Components

#### Main Application

**Location**: `durable-code-app/frontend/src/App.tsx`

- **HomePage Component**: Root application component with tabbed navigation
- **URL-based Navigation**: Hash-based routing with browser back/forward support
- **State Management**: React hooks for tab state and navigation
- **Responsive Design**: Mobile-first responsive layout

#### Tab System

**Locations**:
- Simple tabs: `durable-code-app/frontend/src/components/tabs/`
- Feature-based tabs: `durable-code-app/frontend/src/features/[feature-name]/`

Six main tabs representing different aspects of AI-ready development:

1. **Repository**: Development environment and tooling setup (feature-based: `src/features/repository/`)
2. **PlanningTab.tsx**: Project planning and architectural decisions
3. **BuildingTab.tsx**: Implementation strategies and coding practices
4. **QualityAssuranceTab.tsx**: Testing, validation, and quality processes
5. **MaintenanceTab.tsx**: Ongoing maintenance and optimization strategies
6. **DemoTab.tsx**: Interactive oscilloscope demonstration with real-time WebSocket streaming

#### Architecture Patterns

**Feature-Based Architecture**: Complex tabs like Repository are organized as features with:
- `components/` - React components with proper separation of concerns
- `hooks/` - Custom React hooks for state management and data fetching
- `types/` - TypeScript interfaces and type definitions
- `index.ts` - Feature exports and public API

**Simple Tab Architecture**: Basic tabs remain in `components/tabs/` for simpler content.

**CSS Modules + CSS Variables**: All components use scoped styling with systematic theming:
- `ComponentName.module.css` - Component-scoped styles
- `src/styles/theme/` - CSS Variables design token system
- Badge system with semantic variants (essential, active, warning, success, etc.)
- Common title classes for accessibility and consistency (.hero-title, .light-title-on-dark)

#### Visual Components

**Location**: `durable-code-app/frontend/src/components/`

- **ParticleBackground.tsx**: Animated particle system for visual appeal
- **Interactive Elements**: Dynamic content and user interaction components

#### Reusable Common Components

**Location**: `durable-code-app/frontend/src/components/common/`

- **DetailsCard**: Reusable card component for displaying detailed information with icons, titles, and descriptions
- **FeatureCard**: Standardized card for feature highlights with consistent styling and layout
- **Button, Card, Tab, Icon, Link, Badge**: Complete component library with TypeScript types and CSS Modules
- **LoadingSpinner, ErrorMessage, Section**: Utility components for common UI patterns

#### Utility Services

**Location**: `durable-code-app/frontend/src/utils/`

- **LinkValidationService.ts**: URL validation and health checking
- **LinkExtractionService.ts**: Automatic link discovery from content
- **LinkCategorizationService.ts**: Link classification and organization
- **LinkReportService.ts**: Comprehensive link analysis reporting
- **HttpRequestService.ts**: HTTP client wrapper with error handling
- **ParticleSystem.ts**: Particle animation physics and rendering

#### Page Components

**Location**: `durable-code-app/frontend/src/pages/`

- **Standards.tsx**: Development standards and guidelines documentation
- **CustomLinters.tsx**: Custom linting rule configuration interface

### Frontend Features

#### Navigation System

- Hash-based routing for direct tab access
- URL parameter support for return navigation
- Browser history integration
- Accessibility-compliant navigation

#### Interactive Elements

- Dynamic content loading and state management
- Real-time link validation and reporting
- Particle animation system with physics
- Responsive design across device sizes

#### Development Workflow

- Hot module replacement with Vite
- TypeScript compilation and type checking
- ESLint configuration for code quality
- Automated testing with Vitest

## Backend Architecture

### Technology Stack

**Location**: `durable-code-app/backend/`

- **FastAPI** for high-performance API development
- **Python 3.11+** with modern async/await patterns
- **Poetry** for dependency management
- **Pydantic** for data validation and serialization

### Core Application

**Location**: `durable-code-app/backend/app/main.py`

- **FastAPI Application**: Production-ready API server
- **CORS Configuration**: Cross-origin resource sharing setup
- **Health Endpoints**: System monitoring and status checking
- **Middleware Integration**: Request/response processing pipeline

### API Features

#### Core Endpoints

- **Root Endpoint** (`/`): Welcome message and API information
- **Health Check** (`/health`): System status and monitoring
- **CORS Support**: Frontend integration configuration

#### Development Features

- **Automatic Documentation**: OpenAPI/Swagger integration
- **Request Validation**: Pydantic model validation
- **Error Handling**: Comprehensive error response system
- **Async Support**: High-performance async request handling

### Oscilloscope Demo Feature

**Location**: `durable-code-app/backend/app/oscilloscope.py`

#### Overview

Interactive oscilloscope demonstration showcasing real-time data streaming capabilities using WebSocket connections. This feature demonstrates advanced async programming patterns and real-time data visualization.

#### WebSocket Endpoints

- **Stream Endpoint** (`/api/oscilloscope/stream`): Real-time waveform data streaming
- **Health Endpoint** (`/api/oscilloscope/health`): Module health and capability information

#### Waveform Generation

**Supported Waveforms**:
- **Sine Wave**: Smooth sinusoidal waveform generation
- **Square Wave**: Digital pulse waveform with configurable duty cycle
- **White Noise**: Random signal generation for testing

**Configurable Parameters**:
- **Frequency**: 0.1 Hz to 100 Hz range
- **Amplitude**: 0.1 to 10.0 units
- **DC Offset**: -10.0 to +10.0 units
- **Phase Continuity**: Maintained across streaming sessions

#### WebSocket Protocol

**Commands**:
- `start`: Begin waveform streaming with specified parameters
- `stop`: Halt streaming session
- `configure`: Modify waveform parameters during active streaming

**Data Format**:
```json
{
    "timestamp": 1234567890.123,
    "samples": [0.1, 0.2, ...],
    "sample_rate": 1000,
    "wave_type": "sine",
    "parameters": {
        "frequency": 10.0,
        "amplitude": 1.0,
        "offset": 0.0
    }
}
```

#### Frontend Integration

**Location**: `durable-code-app/frontend/src/components/tabs/DemoTab.tsx`

- **Real-time Visualization**: Canvas-based oscilloscope display
- **Interactive Controls**: Waveform selection and parameter adjustment
- **WebSocket Management**: Connection handling with auto-reconnect
- **Performance Optimization**: Efficient rendering with animation frames

#### Testing Coverage

**Location**: `durable-code-app/backend/test/test_oscilloscope.py`

- **Unit Tests**: Waveform generator validation
- **Integration Tests**: WebSocket connection and streaming
- **Performance Tests**: Data rate and latency validation
- **Error Handling**: Edge case and invalid input testing

## Integration Features

### Development Environment

#### Docker Configuration

**Location**: `.docker/compose/prod.yml`, `.docker/compose/dev.yml`

- **Production Configuration**: Optimized for deployment
- **Development Configuration**: Hot reloading and debugging
- **Service Orchestration**: Frontend, backend, and database coordination
- **Environment Isolation**: Consistent development across platforms

#### Make Targets

**Location**: `Makefile`

- `just dev`: Start development environment
- `just build`: Build production images
- `just test`: Run comprehensive test suites
- `just launch`: Build and start with browser opening

### Configuration Management

#### Environment Files

- **`.env.example`**: Template for environment configuration
- **Package Configuration**:
  - `durable-code-app/frontend/package.json`: Frontend dependencies
  - `durable-code-app/backend/pyproject.toml`: Backend dependencies

#### Build Configuration

- **Vite Configuration**: `durable-code-app/frontend/vite.config.ts`
- **TypeScript Configuration**: Multiple tsconfig files for different targets
- **ESLint Configuration**: Code quality and style enforcement

## Quality Assurance

### Testing Strategy

#### Frontend Testing

**Location**: `durable-code-app/frontend/src/`

- **Component Testing**: React component unit tests
- **Integration Testing**: End-to-end user workflow validation
- **Utility Testing**: Service and utility function validation
- **Type Safety**: Comprehensive TypeScript coverage

#### Backend Testing

- **API Testing**: Endpoint functionality validation
- **Integration Testing**: Database and service integration
- **Performance Testing**: Load and stress testing capabilities

### Code Quality

#### Linting and Formatting

- **ESLint**: JavaScript/TypeScript code quality
- **Prettier**: Code formatting consistency
- **TypeScript**: Compile-time type checking
- **Design Linters**: Custom rule enforcement

#### Standards Compliance

- **File Header Standards**: Consistent documentation headers
- **CSS Layout Stability**: Visual consistency guidelines
- **Branch Protection**: Git workflow enforcement
- **Security Practices**: Secure coding guidelines

## Deployment and Operations

### Production Readiness

#### Performance Optimization

- **Vite Build Optimization**: Optimized bundle generation
- **Code Splitting**: Dynamic import and lazy loading
- **Asset Optimization**: Image and resource compression
- **Caching Strategies**: Browser and CDN optimization

#### Monitoring and Observability

- **Health Endpoints**: System status monitoring
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Application performance monitoring
- **User Analytics**: Usage pattern analysis

### Scalability Features

- **Microservice Architecture**: Modular service design
- **Container Orchestration**: Docker-based deployment
- **API Versioning**: Backward compatibility support
- **Database Integration**: Scalable data persistence

## Development Workflow

### Local Development

```bash
# Frontend development
cd durable-code-app/frontend
npm install
npm run dev

# Backend development
cd durable-code-app/backend
poetry install
poetry run uvicorn app.main:app --reload

# Full stack with Docker
just dev
```

### Production Deployment

```bash
# Build and deploy
just build
just start

# Health check
curl http://localhost:8000/health
```

## Extension Points

### Adding New Tabs

**For Simple Tabs**:
1. Create new tab component in `src/components/tabs/`
2. Add to tab configuration in `App.tsx`
3. Update navigation and routing logic
4. Implement tab-specific functionality

**For Complex Feature Tabs**:
1. Create feature directory in `src/features/[feature-name]/`
2. Implement feature structure: `components/`, `hooks/`, `types/`, `index.ts`
3. Add lazy loading in `App.tsx` with `React.lazy()` and `Suspense`
4. Create comprehensive TypeScript interfaces
5. Implement custom hooks for data management
6. Add proper test coverage with async handling

**Example Feature Structure**:
```
src/features/repository/
├── components/
│   └── RepositoryTab/
│       ├── RepositoryTab.tsx
│       ├── RepositoryTab.module.css
│       └── index.ts
├── hooks/
│   └── useRepository.ts
├── types/
│   └── repository.types.ts
└── index.ts
```

### API Extension

1. Create new FastAPI routers
2. Add to main application routing
3. Implement Pydantic models for validation
4. Add comprehensive error handling

### Service Integration

1. Add new utility services in `src/utils/`
2. Implement service interfaces
3. Add error handling and retry logic
4. Include comprehensive testing
