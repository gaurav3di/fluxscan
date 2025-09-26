# FluxScan Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Security Architecture](#security-architecture)
7. [Performance Considerations](#performance-considerations)
8. [Deployment Architecture](#deployment-architecture)

## System Overview

FluxScan is a modular, web-based trading scanner engine built on a three-tier architecture:

```
┌─────────────────────────────────────────┐
│          Presentation Layer              │
│     (Web UI - DaisyUI/Tailwind)         │
└─────────────────┬───────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────┐
│         Application Layer                │
│      (Flask + Business Logic)           │
└─────────────────┬───────────────────────┘
                  │ SQL/API
┌─────────────────▼───────────────────────┐
│           Data Layer                     │
│    (SQLite + OpenAlgo + Cache)          │
└─────────────────────────────────────────┘
```

## Architecture Principles

### 1. Separation of Concerns
- **Models**: Database schema and ORM mappings
- **Services**: Business logic and data processing
- **Routes**: HTTP endpoints and request handling
- **Templates**: UI rendering and presentation
- **Static**: Client-side assets and scripts

### 2. Modularity
- Scanner engine is independent of web framework
- Data service abstracted from specific providers
- Pluggable scanner templates
- Extensible validation system

### 3. Scalability
- Stateless application design
- Cache layer for performance
- Async processing for long-running tasks
- WebSocket for real-time updates

### 4. Security
- Input validation at all layers
- Sandboxed scanner execution
- SQL injection prevention
- XSS protection

## System Components

### Core Components

#### 1. Scanner Engine (`scanners/scanner_engine.py`)
```python
class ScannerEngine:
    - execute_scanner()      # Main execution method
    - execute_parallel()     # Multi-threaded execution
    - _execute_for_symbol()  # Single symbol processing
    - _create_namespace()    # Safe execution environment
```

**Responsibilities:**
- Execute Python scanner code safely
- Manage parallel execution
- Progress tracking
- Result aggregation

#### 2. Data Service (`services/data_service.py`)
```python
class DataService:
    - get_historical_data()  # Fetch OHLCV data
    - get_quote()           # Real-time quotes
    - get_depth()           # Market depth
    - validate_symbol()     # Symbol validation
```

**Responsibilities:**
- OpenAlgo API integration
- Data caching
- Fallback mechanisms
- Data transformation

#### 3. Scanner Validator (`scanners/validator.py`)
```python
class ScannerValidator:
    - validate()           # Code validation
    - _validate_ast()      # AST analysis
    - create_safe_namespace()  # Sandbox environment
```

**Responsibilities:**
- Scanner code validation
- Security checks
- Syntax verification
- Import restrictions

### Database Models

#### Entity Relationship Diagram
```
Scanner (1) ──────< (N) ScanResult
   │                        │
   │ (1)                    │
   │                        │
   ▼ (N)                    │
ScanSchedule                │
   │                        │
   │ (N)                    │
   ▼                        ▼
Watchlist (1) ──────< (N) ScanHistory
```

#### Key Models
1. **Scanner**: Scanner definitions and code
2. **Watchlist**: Symbol collections
3. **ScanResult**: Individual scan results
4. **ScanSchedule**: Automated scan schedules
5. **ScanHistory**: Execution history and metrics

### Service Layer

```
┌────────────────────────────────────────┐
│            Service Layer               │
├────────────────────────────────────────┤
│  ScannerService  │  WatchlistService   │
│  ScheduleService │  ExportService      │
│  DataService     │  CacheService       │
└────────────────────────────────────────┘
```

Each service encapsulates business logic for its domain:
- **ScannerService**: Scanner CRUD and execution
- **WatchlistService**: Watchlist management
- **ScheduleService**: Scheduled scan management
- **ExportService**: Data export functionality
- **CacheService**: Caching layer

## Data Flow

### Scan Execution Flow
```
1. User Request
   │
   ▼
2. Route Handler (/scan/api/scan)
   │
   ▼
3. Scanner Service
   │
   ▼
4. Scanner Engine
   │
   ├──► Data Service (fetch market data)
   │    │
   │    └──► Cache Service (check/store)
   │
   ├──► Scanner Validator (validate code)
   │
   ├──► Execute Scanner Code
   │
   └──► Store Results
        │
        └──► WebSocket Update
```

### Real-time Updates Flow
```
Client Browser
   │
   ├──► HTTP Request ──► Flask Routes
   │
   └──► WebSocket ──► Socket.IO
                      │
                      └──► Scan Progress Events
                           └──► Scan Complete Events
```

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Flask 3.x | Web application framework |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Database | SQLite | Data persistence |
| WebSocket | Flask-SocketIO | Real-time communication |
| Scheduler | APScheduler | Task scheduling |
| HTTP Client | httpx | API requests |
| Technical Analysis | TA-Lib | Indicator calculations |
| Data Processing | Pandas/NumPy | Data manipulation |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| CSS Framework | DaisyUI/Tailwind | UI components and styling |
| JavaScript | Vanilla JS | Client-side logic |
| Real-time | Socket.IO Client | WebSocket communication |
| Dynamic Updates | HTMX | Partial page updates |

## Security Architecture

### Code Execution Security
1. **AST Validation**: Scanner code parsed and validated
2. **Import Restrictions**: Limited to safe libraries
3. **Namespace Isolation**: Restricted execution environment
4. **Resource Limits**: Timeout and memory constraints

### Web Security
1. **Input Validation**: All user inputs validated
2. **SQL Injection Prevention**: Parameterized queries
3. **XSS Protection**: Template escaping
4. **CSRF Protection**: Token validation
5. **Rate Limiting**: API endpoint throttling

### Data Security
1. **API Key Management**: Environment variables
2. **Sensitive Data**: Never logged or exposed
3. **Session Security**: Secure cookie settings

## Performance Considerations

### Optimization Strategies

#### 1. Caching
```python
# Three-tier caching strategy
L1: In-memory cache (5 min TTL)
L2: Database cache (1 hour TTL)
L3: OpenAlgo API (real-time)
```

#### 2. Parallel Processing
```python
# Multi-threaded scanner execution
MAX_WORKERS = 5
Thread Pool for concurrent symbol processing
```

#### 3. Database Optimization
- Indexed columns for frequent queries
- Batch inserts for results
- Connection pooling
- Query optimization

#### 4. Frontend Optimization
- CDN for static assets
- Lazy loading for components
- WebSocket for selective updates
- Client-side result caching

### Performance Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Page Load | < 1s | ~800ms |
| API Response | < 200ms | ~150ms |
| Scanner Execution | < 2s/symbol | ~1.5s |
| WebSocket Latency | < 100ms | ~50ms |

## Deployment Architecture

### Development Environment
```
Local Machine
├── Flask Dev Server (port 5001)
├── SQLite Database
├── OpenAlgo Mock Server
└── File System Cache
```

### Production Environment
```
Production Server
├── Gunicorn WSGI Server
│   └── Multiple Worker Processes
├── PostgreSQL/MySQL Database
├── Redis Cache
├── Nginx Reverse Proxy
└── SSL/TLS Termination
```

### Docker Deployment
```dockerfile
# Multi-stage build
FROM python:3.9-slim AS builder
# Install dependencies

FROM python:3.9-slim
# Copy application
# Run with gunicorn
```

### Environment Variables
```bash
# Application
FLASK_ENV=production
SECRET_KEY=<secure-random-key>

# Database
DATABASE_URL=postgresql://...

# OpenAlgo
OPENALGO_API_KEY=<api-key>
OPENALGO_HOST=<api-host>

# Cache
REDIS_URL=redis://...
```

## Monitoring and Logging

### Application Monitoring
- Request/Response times
- Scanner execution metrics
- Error rates and types
- Resource utilization

### Logging Strategy
```python
# Log Levels
ERROR: System errors, failed scans
WARNING: Validation failures, API issues
INFO: Scan completions, user actions
DEBUG: Detailed execution flow
```

### Health Checks
```
GET /api/health
- Database connectivity
- OpenAlgo API status
- Cache availability
- Scheduler status
```

## Future Architecture Considerations

### Microservices Migration
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Web API    │  │Scanner Engine│  │Data Service  │
│   Service    │  │   Service    │  │   Service    │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                    Message Queue
```

### Horizontal Scaling
- Load balancer for multiple app instances
- Distributed cache (Redis Cluster)
- Database read replicas
- Queue-based scanner distribution

### Cloud Native Architecture
- Kubernetes orchestration
- Service mesh for communication
- Cloud-native databases
- Serverless scanner execution

## Conclusion

FluxScan's architecture prioritizes modularity, security, and performance while maintaining simplicity for ease of deployment and maintenance. The system is designed to scale from single-user deployments to enterprise-level installations with minimal architectural changes.