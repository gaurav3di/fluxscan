# FluxScan API Specification

## Overview

FluxScan provides a RESTful API for programmatic access to scanner functionality. All API endpoints return JSON responses and follow standard HTTP status codes.

## Base URL

```
Development: http://localhost:5001/api
Production: https://yourdomain.com/api
```

## Authentication

Currently, the API does not require authentication for local deployments. Future versions will support API key authentication.

```http
Authorization: Bearer <api_key>
```

## Common Headers

```http
Content-Type: application/json
Accept: application/json
```

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

## API Endpoints

### Scanner Management

#### List All Scanners

```http
GET /api/scanners
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "MACD Crossover",
        "description": "Detects MACD crossovers",
        "category": "momentum",
        "is_active": true,
        "parameters": {
            "fast_period": 12,
            "slow_period": 26
        },
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    }
]
```

#### Create Scanner

```http
POST /api/scanners
```

**Request Body:**
```json
{
    "name": "RSI Scanner",
    "description": "Finds oversold stocks",
    "code": "# Scanner code here",
    "category": "momentum",
    "parameters": {
        "rsi_period": 14,
        "oversold_level": 30
    }
}
```

**Response:**
```json
{
    "id": 2,
    "name": "RSI Scanner",
    "status": "created"
}
```

#### Get Scanner Details

```http
GET /api/scanners/{id}
```

**Response:**
```json
{
    "id": 1,
    "name": "MACD Crossover",
    "description": "Detects MACD crossovers",
    "code": "# Python code",
    "category": "momentum",
    "is_active": true,
    "parameters": {},
    "total_scans": 42,
    "active_schedules": 2
}
```

#### Update Scanner

```http
PUT /api/scanners/{id}
```

**Request Body:**
```json
{
    "name": "Updated Scanner Name",
    "description": "Updated description",
    "code": "# Updated code",
    "is_active": false
}
```

#### Delete Scanner

```http
DELETE /api/scanners/{id}
```

**Response:**
```json
{
    "message": "Scanner deleted successfully"
}
```

#### Test Scanner

```http
POST /api/scanners/{id}/test
```

**Request Body:**
```json
{
    "symbols": ["RELIANCE", "TCS", "INFY"],
    "parameters": {
        "custom_param": "value"
    }
}
```

**Response:**
```json
{
    "status": "completed",
    "results": [
        {
            "symbol": "RELIANCE",
            "signal": "BUY",
            "metrics": {
                "rsi": 28.5,
                "price": 2345.60
            }
        }
    ],
    "execution_time": 1.234
}
```

#### Validate Scanner Code

```http
POST /api/scanners/validate
```

**Request Body:**
```json
{
    "code": "# Scanner code to validate"
}
```

**Response:**
```json
{
    "is_valid": true,
    "errors": [],
    "warnings": ["Scanner should set 'signal' variable"]
}
```

### Watchlist Management

#### List Watchlists

```http
GET /api/watchlists
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "NIFTY 50",
        "description": "Top 50 stocks",
        "exchange": "NSE",
        "symbols": ["RELIANCE", "TCS", "INFY"],
        "symbol_count": 50
    }
]
```

#### Create Watchlist

```http
POST /api/watchlists
```

**Request Body:**
```json
{
    "name": "My Watchlist",
    "description": "Custom watchlist",
    "symbols": ["RELIANCE", "TCS"],
    "exchange": "NSE"
}
```

#### Update Watchlist

```http
PUT /api/watchlists/{id}
```

**Request Body:**
```json
{
    "name": "Updated Name",
    "symbols": ["RELIANCE", "TCS", "HDFC"]
}
```

#### Delete Watchlist

```http
DELETE /api/watchlists/{id}
```

#### Import Watchlist

```http
POST /api/watchlists/import
```

**Request Body (CSV):**
```json
{
    "name": "Imported List",
    "csv_content": "RELIANCE\nTCS\nINFY",
    "exchange": "NSE"
}
```

### Scan Execution

#### Run Scanner

```http
POST /scan/api/scan
```

**Request Body:**
```json
{
    "scanner_id": 1,
    "watchlist_id": 2,
    "parameters": {
        "lookback_days": 100,
        "min_volume": 100000
    }
}
```

**Response:**
```json
{
    "scan_id": "scan_123",
    "status": "running",
    "total_symbols": 50
}
```

#### Get Scan Status

```http
GET /scan/api/scan/status/{scan_id}
```

**Response:**
```json
{
    "scan_id": "scan_123",
    "status": "running",
    "progress": 45,
    "symbols_scanned": 23,
    "signals_found": 3
}
```

#### Cancel Scan

```http
POST /scan/api/scan/cancel/{scan_id}
```

**Response:**
```json
{
    "message": "Scan cancelled successfully"
}
```

### Results Management

#### Get Results

```http
GET /api/results?page=1&per_page=50&scanner_id=1&signal=BUY
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 50)
- `scanner_id`: Filter by scanner
- `symbol`: Filter by symbol
- `signal`: Filter by signal type

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "symbol": "RELIANCE",
            "signal": "BUY",
            "scanner_name": "MACD Crossover",
            "metrics": {
                "price": 2345.60,
                "rsi": 28.5
            },
            "timestamp": "2024-01-01T10:00:00Z"
        }
    ],
    "total": 100,
    "page": 1,
    "per_page": 50,
    "total_pages": 2
}
```

#### Export Results

```http
POST /api/results/export
```

**Request Body:**
```json
{
    "format": "csv",
    "scanner_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

**Response:**
- For CSV: Returns CSV file
- For JSON: Returns JSON array

### Schedule Management

#### List Schedules

```http
GET /api/schedules
```

**Response:**
```json
[
    {
        "id": 1,
        "scanner_name": "MACD Scanner",
        "watchlist_name": "NIFTY 50",
        "schedule_type": "interval",
        "interval_minutes": 60,
        "is_active": true,
        "next_run": "2024-01-01T11:00:00Z"
    }
]
```

#### Create Schedule

```http
POST /api/schedules
```

**Request Body (Interval):**
```json
{
    "scanner_id": 1,
    "watchlist_id": 2,
    "schedule_type": "interval",
    "interval_minutes": 30,
    "market_hours_only": true
}
```

**Request Body (Daily):**
```json
{
    "scanner_id": 1,
    "watchlist_id": 2,
    "schedule_type": "daily",
    "run_time": "09:30:00"
}
```

#### Toggle Schedule

```http
POST /api/schedules/{id}/toggle
```

**Request Body:**
```json
{
    "is_active": false
}
```

### Data APIs

#### Search Symbols

```http
GET /api/symbols/search?q=RELI&exchange=NSE
```

**Response:**
```json
[
    {
        "symbol": "RELIANCE",
        "name": "Reliance Industries Ltd",
        "exchange": "NSE"
    }
]
```

#### Validate Symbol

```http
POST /api/symbols/validate
```

**Request Body:**
```json
{
    "symbol": "RELIANCE",
    "exchange": "NSE"
}
```

**Response:**
```json
{
    "valid": true
}
```

#### Get Historical Data

```http
GET /api/data/history?symbol=RELIANCE&exchange=NSE&interval=D&lookback=100
```

**Response:**
```json
{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "interval": "D",
    "data": [
        {
            "timestamp": "2024-01-01",
            "open": 2340.00,
            "high": 2360.00,
            "low": 2330.00,
            "close": 2345.60,
            "volume": 1000000
        }
    ]
}
```

### Settings APIs

#### Get Settings

```http
GET /api/settings
```

**Response:**
```json
{
    "market_open_time": "09:15",
    "market_close_time": "15:30",
    "timezone": "Asia/Kolkata",
    "default_exchange": "NSE"
}
```

#### Update Settings

```http
PUT /api/settings
```

**Request Body:**
```json
{
    "market_open_time": "09:30",
    "enable_notifications": true
}
```

### System APIs

#### Health Check

```http
GET /api/health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Statistics

```http
GET /api/stats
```

**Response:**
```json
{
    "scanners": {
        "total": 10,
        "active": 8
    },
    "watchlists": {
        "total": 5,
        "symbols": 250
    },
    "scans": {
        "total": 1000,
        "running": 2,
        "completed": 950,
        "failed": 48
    },
    "results": {
        "total": 5000,
        "today": 42
    }
}
```

#### Test OpenAlgo Connection

```http
GET /api/settings/openalgo/test
```

**Response:**
```json
{
    "connected": true,
    "message": "Connection successful"
}
```

#### Clear Cache

```http
POST /api/cache/clear
```

**Response:**
```json
{
    "message": "Cache cleared successfully"
}
```

## WebSocket Events

### Connection

```javascript
const socket = io('ws://localhost:5001');

socket.on('connect', function() {
    console.log('Connected');
});
```

### Subscribe to Scan

```javascript
socket.emit('subscribe_scan', {
    scan_id: 'scan_123'
});
```

### Scan Progress Event

```javascript
socket.on('scan_progress', function(data) {
    console.log(data);
    // {
    //     scan_id: 'scan_123',
    //     progress: 45,
    //     symbol: 'RELIANCE'
    // }
});
```

### Scan Complete Event

```javascript
socket.on('scan_complete', function(data) {
    console.log(data);
    // {
    //     scan_id: 'scan_123',
    //     status: 'completed',
    //     total_scanned: 50,
    //     signals_found: 8
    // }
});
```

## Error Responses

### Validation Error

```json
{
    "error": "Validation failed",
    "errors": {
        "name": "Name is required",
        "code": "Invalid scanner code"
    }
}
```

### Not Found

```json
{
    "error": "Resource not found",
    "resource": "scanner",
    "id": 123
}
```

### Server Error

```json
{
    "error": "Internal server error",
    "message": "An unexpected error occurred"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Default limit**: 100 requests per minute
- **Scan execution**: 10 concurrent scans
- **Export**: 10 requests per hour

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110400
```

## Pagination

List endpoints support pagination:

```http
GET /api/results?page=2&per_page=25
```

Response includes pagination metadata:
```json
{
    "data": [...],
    "page": 2,
    "per_page": 25,
    "total": 100,
    "total_pages": 4,
    "has_next": true,
    "has_prev": true
}
```

## Versioning

API versioning through URL path:

```
/api/v1/scanners  (current)
/api/v2/scanners  (future)
```

## CORS

CORS is enabled for all origins in development:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

Production should restrict to specific domains.

## SDK Examples

### Python

```python
import requests

class FluxScanAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def list_scanners(self):
        return requests.get(f"{self.base_url}/api/scanners").json()

    def run_scan(self, scanner_id, watchlist_id):
        return requests.post(
            f"{self.base_url}/scan/api/scan",
            json={
                "scanner_id": scanner_id,
                "watchlist_id": watchlist_id
            }
        ).json()

# Usage
api = FluxScanAPI("http://localhost:5001")
scanners = api.list_scanners()
```

### JavaScript

```javascript
class FluxScanAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async listScanners() {
        const response = await fetch(`${this.baseUrl}/api/scanners`);
        return response.json();
    }

    async runScan(scannerId, watchlistId) {
        const response = await fetch(`${this.baseUrl}/scan/api/scan`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                scanner_id: scannerId,
                watchlist_id: watchlistId
            })
        });
        return response.json();
    }
}

// Usage
const api = new FluxScanAPI('http://localhost:5001');
const scanners = await api.listScanners();
```