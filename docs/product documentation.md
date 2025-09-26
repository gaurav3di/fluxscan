# Product Requirements Document (PRD)
# FluxScan - Trading Scanner Engine

## 1. Executive Summary

FluxScan is a web-based trading scanner engine that enables traders and investors to create, manage, and execute custom stock screening strategies using Python. It provides a user-friendly interface for technical analysis-based scanning with real-time and scheduled execution capabilities, making algorithmic screening accessible to traders of all skill levels.

## 2. Product Overview

### 2.1 Vision
Democratize algorithmic stock screening by providing an open-source, Python-based platform that simplifies technical analysis and market scanning for retail traders and investors.

### 2.2 Goals
- Simplify custom scanner creation using Python
- Provide intuitive watchlist management
- Enable real-time and scheduled scanning
- Offer comprehensive technical analysis capabilities
- Create a modern, responsive web interface

### 2.3 Non-Goals
- Not a trading execution platform
- Not a backtesting engine
- Not a real-time charting application
- Not a portfolio management system

## 3. Technical Architecture

### 3.1 Technology Stack
```
Backend:
- Python 3.8+
- Flask 2.3+
- SQLAlchemy 2.0+
- TA-Lib 0.4.28+
- OpenAlgo SDK (latest)

Database:
- SQLite 3

Frontend:
- HTML5
- DaisyUI 4.0+ (CDN)
- Tailwind CSS 3.0+ (CDN)
- Vanilla JavaScript
- HTMX for dynamic updates

Development:
- Python virtual environment
- Git for version control
```

### 3.2 System Architecture
```
┌─────────────────────────────────────────────────┐
│                  Web Interface                   │
│            (DaisyUI + Tailwind CSS)             │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Flask Application                   │
│         (Routes, Controllers, API)              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│             Business Logic Layer                 │
├──────────────┬──────────────┬───────────────────┤
│   Scanner    │   Watchlist  │    Scheduler      │
│   Engine     │   Manager    │    Service        │
└──────────────┴──────────────┴───────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Data Access Layer                   │
├──────────────┬──────────────┬───────────────────┤
│  SQLAlchemy  │   OpenAlgo   │     TA-Lib       │
│   Models     │   SDK Client │    Indicators     │
└──────────────┴──────────────┴───────────────────┘
```

## 4. Database Schema

### 4.1 Tables

```sql
-- Scanners table
CREATE TABLE scanners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    code TEXT NOT NULL,
    parameters JSON,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlists table
CREATE TABLE watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    symbols JSON NOT NULL,
    exchange VARCHAR(10) DEFAULT 'NSE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan results table
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10),
    signal VARCHAR(50),
    metrics JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scanner_id) REFERENCES scanners(id)
);

-- Scan schedules table
CREATE TABLE scan_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_id INTEGER NOT NULL,
    watchlist_id INTEGER NOT NULL,
    schedule_type VARCHAR(20), -- 'once', 'interval', 'daily'
    interval_minutes INTEGER,
    run_time TIME,
    is_active BOOLEAN DEFAULT 1,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scanner_id) REFERENCES scanners(id),
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
);

-- Scan history table
CREATE TABLE scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_id INTEGER NOT NULL,
    watchlist_id INTEGER,
    status VARCHAR(20), -- 'running', 'completed', 'failed'
    symbols_scanned INTEGER,
    signals_found INTEGER,
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (scanner_id) REFERENCES scanners(id),
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
);

-- User settings table
CREATE TABLE settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scanner templates table
CREATE TABLE scanner_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    code TEXT NOT NULL,
    default_parameters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 5. Core Features

### 5.1 Scanner Management

#### 5.1.1 Scanner Creation
```python
# Feature: Create New Scanner
# URL: POST /api/scanners
# Input:
{
    "name": "MACD Bullish Scanner",
    "description": "Finds MACD bullish crossovers",
    "code": "scanner_code_here",
    "category": "momentum",
    "parameters": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    }
}
```

#### 5.1.2 Scanner Editor Interface
- Syntax-highlighted Python code editor
- Template library for common patterns
- Parameter configuration panel
- Test run capability with sample data
- Code validation and error checking
- Save and version management

#### 5.1.3 Built-in Scanner Categories
**Momentum Indicators**
- MACD Crossover
- RSI Oversold/Overbought
- Stochastic Signals

**Volume Analysis**
- Volume Breakout
- Volume Dry-up
- Price-Volume Divergence

**Trend Following**
- Moving Average Crossover
- Trend Line Breaks
- ADX Trend Strength

**Volatility**
- Bollinger Band Squeeze
- ATR Expansion/Contraction
- Keltner Channel Breakout

**Price Patterns**
- Support/Resistance Levels
- Candlestick Patterns
- Chart Patterns

### 5.2 Watchlist Management

#### 5.2.1 Watchlist Operations
```python
# Feature: Watchlist CRUD
# URLs:
# GET    /api/watchlists          - List all
# POST   /api/watchlists          - Create new
# GET    /api/watchlists/{id}     - Get specific
# PUT    /api/watchlists/{id}     - Update
# DELETE /api/watchlists/{id}     - Delete
# POST   /api/watchlists/{id}/symbols - Add symbols
# DELETE /api/watchlists/{id}/symbols - Remove symbols
```

#### 5.2.2 Symbol Management
- Add/remove symbols individually or in bulk
- Import from CSV/TXT files
- Predefined index constituents (NIFTY50, NIFTY100, etc.)
- Symbol search with autocomplete
- Symbol validation against exchange

### 5.3 Scanning Engine

#### 5.3.1 Scan Execution
```python
# Feature: Run Scanner
# URL: POST /api/scan
# Input:
{
    "scanner_id": 1,
    "watchlist_id": 2,
    "parameters": {
        "lookback_days": 100,
        "min_volume": 100000
    }
}
# Response:
{
    "scan_id": "scan_123",
    "status": "running",
    "total_symbols": 50,
    "progress": 0
}
```

#### 5.3.2 Scan Results Display
- Tabular view with sorting/filtering
- Column customization
- Export to CSV/Excel
- Signal strength indicators
- Quick metrics summary
- Historical scan comparison

#### 5.3.3 Real-time Progress
- WebSocket connection for live updates
- Progress bar with current symbol
- Partial results streaming
- Cancel running scans

### 5.4 Scheduling System

#### 5.4.1 Schedule Types
- One-time execution
- Interval-based (every X minutes)
- Daily at specific time(s)
- Weekly on specific days
- Market hours only option

#### 5.4.2 Schedule Management
```python
# Feature: Schedule Scanner
# URL: POST /api/schedules
# Input:
{
    "scanner_id": 1,
    "watchlist_id": 2,
    "schedule_type": "interval",
    "interval_minutes": 15,
    "market_hours_only": true,
    "is_active": true
}
```

### 5.5 Data Integration

#### 5.5.1 OpenAlgo SDK Integration
- Historical data fetching
- Real-time quotes (if available)
- Symbol information
- Market status check

#### 5.5.2 Data Caching
- Cache historical data for performance
- Configurable cache duration
- Smart cache invalidation

## 6. User Interface Specification

### 6.1 Page Structure

#### 6.1.1 Dashboard (/)
```html
<!-- Main Dashboard Layout -->
<div class="container mx-auto p-4">
    <!-- Quick Actions -->
    <div class="flex gap-2 mb-4">
        <button class="btn btn-primary">Quick Scan</button>
        <button class="btn btn-secondary">New Scanner</button>
        <button class="btn btn-accent">Import Watchlist</button>
    </div>
    
    <!-- Stats Cards -->
    <div class="stats shadow w-full">
        <div class="stat">
            <div class="stat-figure text-primary">
                <svg><!-- Scanner icon --></svg>
            </div>
            <div class="stat-title">Active Scanners</div>
            <div class="stat-value text-primary">5</div>
            <div class="stat-desc">2 running now</div>
        </div>
        <div class="stat">
            <div class="stat-figure text-secondary">
                <svg><!-- List icon --></svg>
            </div>
            <div class="stat-title">Watchlists</div>
            <div class="stat-value text-secondary">3</div>
            <div class="stat-desc">156 total symbols</div>
        </div>
        <div class="stat">
            <div class="stat-figure text-accent">
                <svg><!-- Signal icon --></svg>
            </div>
            <div class="stat-title">Today's Signals</div>
            <div class="stat-value text-accent">42</div>
            <div class="stat-desc">↗︎ 12 more than yesterday</div>
        </div>
    </div>
    
    <!-- Recent Scan Results -->
    <div class="card bg-base-100 shadow-xl mt-4">
        <div class="card-body">
            <h2 class="card-title">Recent Signals</h2>
            <div class="overflow-x-auto">
                <table class="table table-zebra">
                    <!-- Results table -->
                </table>
            </div>
        </div>
    </div>
    
    <!-- Running Scans -->
    <div class="card bg-base-100 shadow-xl mt-4">
        <div class="card-body">
            <h2 class="card-title">Active Scans</h2>
            <!-- Progress indicators -->
        </div>
    </div>
</div>
```

#### 6.1.2 Scanner Management (/scanners)
```html
<!-- Scanner Grid View -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <!-- Scanner Card -->
    <div class="card w-full bg-base-100 shadow-xl">
        <div class="card-body">
            <div class="flex justify-between items-start">
                <h2 class="card-title">MACD Scanner</h2>
                <div class="badge badge-success">Active</div>
            </div>
            <p class="text-sm opacity-70">Momentum</p>
            <p>Finds MACD bullish crossovers with volume confirmation</p>
            <div class="stats stats-horizontal mt-2">
                <div class="stat px-2">
                    <div class="stat-title text-xs">Last Run</div>
                    <div class="stat-value text-sm">2h ago</div>
                </div>
                <div class="stat px-2">
                    <div class="stat-title text-xs">Signals</div>
                    <div class="stat-value text-sm">8</div>
                </div>
            </div>
            <div class="card-actions justify-end mt-4">
                <button class="btn btn-ghost btn-sm">Edit</button>
                <button class="btn btn-primary btn-sm">Run Now</button>
            </div>
        </div>
    </div>
</div>
```

#### 6.1.3 Scanner Editor Modal
```html
<!-- Code Editor Modal -->
<dialog id="scanner_editor" class="modal">
    <div class="modal-box w-11/12 max-w-5xl">
        <h3 class="font-bold text-lg">Scanner Editor</h3>
        
        <!-- Tabs -->
        <div class="tabs tabs-boxed mt-4">
            <a class="tab tab-active">Code</a>
            <a class="tab">Parameters</a>
            <a class="tab">Test Run</a>
        </div>
        
        <!-- Code Editor -->
        <div class="mt-4">
            <textarea class="textarea textarea-bordered w-full h-96 font-mono text-sm"
                      placeholder="# Scanner code here"></textarea>
        </div>
        
        <!-- Actions -->
        <div class="modal-action">
            <button class="btn btn-ghost">Cancel</button>
            <button class="btn btn-secondary">Validate</button>
            <button class="btn btn-primary">Save</button>
        </div>
    </div>
</dialog>
```

### 6.2 UI Components Theme

```html
<!-- Color Scheme (DaisyUI) -->
<!-- Primary: Scanner actions -->
<!-- Secondary: Watchlist operations -->
<!-- Accent: Signals/Results -->
<!-- Success: Buy signals -->
<!-- Warning: Hold/Watch signals -->
<!-- Error: Sell signals -->

<!-- Toast Notifications -->
<div class="toast toast-end">
    <div class="alert alert-success">
        <span>Scan completed successfully!</span>
    </div>
</div>

<!-- Loading States -->
<div class="flex items-center gap-2">
    <span class="loading loading-spinner loading-sm"></span>
    <span>Scanning RELIANCE...</span>
</div>
```

## 7. API Specification

### 7.1 RESTful API Endpoints

```python
# Scanner APIs
GET    /api/scanners              # List all scanners
POST   /api/scanners              # Create scanner
GET    /api/scanners/{id}         # Get scanner details
PUT    /api/scanners/{id}         # Update scanner
DELETE /api/scanners/{id}         # Delete scanner
POST   /api/scanners/{id}/test    # Test scanner with sample data
POST   /api/scanners/{id}/clone   # Clone scanner

# Watchlist APIs
GET    /api/watchlists            # List all watchlists
POST   /api/watchlists            # Create watchlist
GET    /api/watchlists/{id}       # Get watchlist
PUT    /api/watchlists/{id}       # Update watchlist
DELETE /api/watchlists/{id}       # Delete watchlist
POST   /api/watchlists/import     # Import symbols from file
GET    /api/watchlists/predefined # Get predefined lists

# Scanning APIs
POST   /api/scan                  # Run scanner
GET    /api/scan/status/{job_id}  # Get scan status
POST   /api/scan/cancel/{job_id}  # Cancel running scan
GET    /api/results                # Get scan results (paginated)
GET    /api/results/{id}          # Get specific result
DELETE /api/results/{id}          # Delete result
POST   /api/results/export        # Export results

# Schedule APIs
GET    /api/schedules             # List schedules
POST   /api/schedules             # Create schedule
PUT    /api/schedules/{id}        # Update schedule
DELETE /api/schedules/{id}        # Delete schedule
POST   /api/schedules/{id}/toggle # Enable/disable schedule
GET    /api/schedules/{id}/history # Get execution history

# Data APIs
GET    /api/symbols/search        # Search symbols
GET    /api/symbols/validate      # Validate symbol
GET    /api/data/history          # Get historical data
GET    /api/data/intervals        # Get available intervals
GET    /api/data/exchanges        # Get supported exchanges

# Template APIs
GET    /api/templates             # List scanner templates
GET    /api/templates/{id}        # Get template details
POST   /api/templates/{id}/use    # Create scanner from template

# Settings APIs
GET    /api/settings              # Get all settings
PUT    /api/settings              # Update settings
GET    /api/settings/openalgo/test # Test OpenAlgo connection

# System APIs
GET    /api/health                # Health check
GET    /api/stats                 # System statistics
POST   /api/cache/clear           # Clear cache
```

### 7.2 WebSocket Events

```javascript
// WebSocket connection for real-time updates
ws://localhost:5000/ws

// Events:
{
    "event": "scan_progress",
    "data": {
        "scan_id": "scan_123",
        "current_symbol": "RELIANCE",
        "progress": 45,
        "signals_found": 3
    }
}

{
    "event": "scan_complete",
    "data": {
        "scan_id": "scan_123",
        "total_scanned": 50,
        "total_signals": 8,
        "execution_time": 12500
    }
}
```

## 8. File Structure

```
fluxscan/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── init_db.py                 # Database initialization
├── run_scheduler.py           # Background scheduler process
├── wsgi.py                    # WSGI entry point
├── README.md                  # Project documentation
├── PRD.md                     # This document
├── LICENSE                    # AGPL-3.0 License
├── .gitignore                 # Git ignore rules
├── .env.example               # Environment variables template
│
├── models/
│   ├── __init__.py
│   ├── base.py              # Base model class
│   ├── scanner.py           # Scanner model
│   ├── watchlist.py         # Watchlist model
│   ├── scan_result.py       # Scan result model
│   ├── schedule.py          # Schedule model
│   ├── scan_history.py      # Scan history model
│   └── settings.py          # Settings model
│
├── scanners/
│   ├── __init__.py
│   ├── base.py              # Base scanner class
│   ├── scanner_engine.py    # Scanner execution engine
│   ├── validator.py         # Code validation
│   └── templates/           # Built-in scanner templates
│       ├── __init__.py
│       ├── momentum/
│       │   ├── macd.py
│       │   ├── rsi.py
│       │   └── stochastic.py
│       ├── volume/
│       │   ├── volume_breakout.py
│       │   └── obv.py
│       ├── trend/
│       │   ├── ma_crossover.py
│       │   └── adx.py
│       └── volatility/
│           ├── bollinger.py
│           └── atr.py
│
├── routes/
│   ├── __init__.py
│   ├── main.py              # Main page routes
│   ├── scanner_routes.py    # Scanner management routes
│   ├── watchlist_routes.py  # Watchlist routes
│   ├── scan_routes.py       # Scanning execution routes
│   ├── schedule_routes.py   # Schedule management routes
│   ├── template_routes.py   # Template routes
│   └── api_routes.py        # API endpoints
│
├── services/
│   ├── __init__.py
│   ├── data_service.py      # OpenAlgo data integration
│   ├── scanner_service.py   # Scanner business logic
│   ├── watchlist_service.py # Watchlist operations
│   ├── schedule_service.py  # Scheduling logic
│   ├── cache_service.py     # Caching logic
│   └── export_service.py    # Export functionality
│
├── templates/
│   ├── layout/
│   │   ├── base.html       # Base template
│   │   ├── navbar.html     # Navigation bar
│   │   └── footer.html     # Footer
│   ├── pages/
│   │   ├── index.html      # Dashboard
│   │   ├── about.html      # About page
│   │   └── help.html       # Help documentation
│   ├── scanners/
│   │   ├── list.html       # Scanner list
│   │   ├── edit.html       # Scanner editor
│   │   └── test.html       # Scanner test
│   ├── watchlists/
│   │   ├── list.html       # Watchlist list
│   │   └── edit.html       # Watchlist editor
│   ├── results/
│   │   ├── list.html       # Results display
│   │   └── detail.html     # Result details
│   ├── schedules/
│   │   ├── list.html       # Schedule management
│   │   └── edit.html       # Schedule editor
│   └── components/
│       ├── scanner_card.html
│       ├── result_table.html
│       └── progress_bar.html
│
├── static/
│   ├── css/
│   │   └── custom.css      # Custom styles
│   ├── js/
│   │   ├── app.js          # Main application JS
│   │   ├── scanner-editor.js # Code editor logic
│   │   ├── watchlist.js     # Watchlist management
│   │   ├── websocket.js     # WebSocket handling
│   │   └── charts.js        # Chart rendering
│   └── img/
│       ├── logo.png
│       └── icons/
│
├── utils/
│   ├── __init__.py
│   ├── validators.py        # Input validation
│   ├── helpers.py          # Helper functions
│   ├── decorators.py       # Custom decorators
│   └── constants.py        # Application constants
│
└── tests/
    ├── __init__.py
    ├── test_scanners.py
    ├── test_watchlists.py
    ├── test_api.py
    └── fixtures/
        └── sample_data.py
```

## 9. Implementation Roadmap

### Phase 1: Core Foundation (Week 1-2)
- [ ] Project setup and structure
- [ ] Database models and migrations
- [ ] Basic Flask application setup
- [ ] Configuration management
- [ ] OpenAlgo SDK integration
- [ ] Base scanner class implementation

### Phase 2: Scanner Engine (Week 3-4)
- [ ] Scanner CRUD operations
- [ ] Scanner validation system
- [ ] Scanner execution engine
- [ ] Code editor interface
- [ ] Built-in scanner templates
- [ ] TA-Lib integration

### Phase 3: Data Management (Week 5-6)
- [ ] Watchlist CRUD operations
- [ ] Symbol search and validation
- [ ] Historical data fetching
- [ ] Data caching layer
- [ ] Results storage and retrieval
- [ ] Export functionality

### Phase 4: User Interface (Week 7-8)
- [ ] Dashboard implementation
- [ ] Scanner management UI
- [ ] Watchlist management UI
- [ ] Results display interface
- [ ] DaisyUI/Tailwind integration
- [ ] Responsive design

### Phase 5: Advanced Features (Week 9-10)
- [ ] Scheduling system implementation
- [ ] Background job processing
- [ ] WebSocket for real-time updates
- [ ] Progress tracking
- [ ] Batch operations
- [ ] Performance optimization

### Phase 6: Polish & Testing (Week 11-12)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance testing
- [ ] Security review
- [ ] Documentation completion
- [ ] Deployment preparation

## 10. Performance Requirements

### 10.1 Response Times
- Page load: < 1 second
- API response: < 200ms (excluding scan execution)
- Scanner execution: < 2 seconds per symbol
- Database queries: < 100ms

### 10.2 Scalability
- Support 100+ concurrent users
- Handle 50+ concurrent scans
- Store 1M+ scan results
- Manage 100+ scanners
- Support watchlists with 1000+ symbols

### 10.3 Reliability
- 99.9% uptime for core features
- Graceful error handling
- Automatic recovery from failures
- Data consistency guarantees

## 11. Security Requirements

### 11.1 Code Execution
- Sandboxed scanner execution environment
- Input sanitization for user code
- Resource limits (CPU, memory, time)
- Restricted module imports

### 11.2 Web Security
- SQL injection prevention via parameterized queries
- XSS protection through template escaping
- CSRF token implementation
- Rate limiting on all endpoints
- Input validation on all forms

### 11.3 Data Security
- Environment-based configuration
- Secure API key storage
- Audit logging for sensitive operations

## 12. Success Metrics

### 12.1 Technical Metrics
- Scanner creation time: < 5 minutes
- Scan execution reliability: > 99%
- API availability: > 99.9%
- Average response time: < 500ms

### 12.2 User Experience Metrics
- Intuitive navigation (< 3 clicks to any feature)
- Mobile-responsive design
- Clear error messages
- Comprehensive help documentation

### 12.3 Feature Completeness
- 20+ built-in technical indicators
- 10+ scanner templates
- Support for all major Indian exchanges
- CSV/Excel export functionality

## 13. Future Enhancements

### Version 2.0 Considerations
- Multi-user support with authentication
- Cloud deployment capabilities
- Advanced charting integration
- Alert notifications (email/SMS/webhook)
- Scanner marketplace for sharing strategies
- AI-powered scanner suggestions
- Backtesting capabilities
- Performance analytics dashboard

## 14. Configuration Examples

### config.py
```python
import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///fluxscan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAlgo
    OPENALGO_API_KEY = os.environ.get('OPENALGO_API_KEY')
    OPENALGO_HOST = os.environ.get('OPENALGO_HOST', 'http://127.0.0.1:5000')
    
    # Scanning
    MAX_CONCURRENT_SCANS = 10
    DEFAULT_LOOKBACK_DAYS = 100
    SCAN_TIMEOUT = 30
    MIN_VOLUME_FILTER = 100000
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Kolkata'
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Results
    RESULTS_PER_PAGE = 50
    MAX_EXPORT_ROWS = 10000
```

### .env.example
```bash
# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-in-production

# OpenAlgo
OPENALGO_API_KEY=your-api-key
OPENALGO_HOST=http://127.0.0.1:5000

# Database
DATABASE_URL=sqlite:///fluxscan.db

# Application
MAX_CONCURRENT_SCANS=10
DEFAULT_LOOKBACK_DAYS=100
```

---

This PRD provides a comprehensive specification for building FluxScan, a modern trading scanner engine that empowers traders to create and manage custom screening strategies efficiently. The modular architecture and clear implementation phases ensure systematic development while maintaining flexibility for future enhancements.