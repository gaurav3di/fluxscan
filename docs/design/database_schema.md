# FluxScan Database Schema Documentation

## Overview

FluxScan uses SQLAlchemy ORM with SQLite for development and can be easily migrated to PostgreSQL or MySQL for production. The database schema is designed for flexibility, performance, and data integrity.

## Entity Relationship Diagram

```mermaid
erDiagram
    SCANNER ||--o{ SCAN_RESULT : produces
    SCANNER ||--o{ SCAN_SCHEDULE : has
    SCANNER ||--o{ SCAN_HISTORY : tracks
    WATCHLIST ||--o{ SCAN_SCHEDULE : uses
    WATCHLIST ||--o{ SCAN_HISTORY : tracks
    SCANNER_TEMPLATE ||--o{ SCANNER : creates

    SCANNER {
        int id PK
        string name UK
        text description
        text code
        json parameters
        string category
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    WATCHLIST {
        int id PK
        string name UK
        text description
        json symbols
        string exchange
        datetime created_at
        datetime updated_at
    }

    SCAN_RESULT {
        int id PK
        int scanner_id FK
        string symbol
        string exchange
        string signal
        json metrics
        datetime timestamp
    }

    SCAN_SCHEDULE {
        int id PK
        int scanner_id FK
        int watchlist_id FK
        string schedule_type
        int interval_minutes
        time run_time
        string days_of_week
        boolean is_active
        datetime last_run
        datetime next_run
        boolean market_hours_only
        datetime created_at
        datetime updated_at
    }

    SCAN_HISTORY {
        int id PK
        int scanner_id FK
        int watchlist_id FK
        string status
        int symbols_scanned
        int signals_found
        int execution_time_ms
        text error_message
        datetime started_at
        datetime completed_at
        datetime created_at
        datetime updated_at
    }

    SETTINGS {
        string key PK
        json value
        datetime updated_at
    }

    SCANNER_TEMPLATE {
        int id PK
        string name
        string category
        text description
        text code
        json default_parameters
        datetime created_at
    }
```

## Table Definitions

### 1. scanners
Stores scanner definitions and configurations.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Scanner name |
| description | TEXT | | Scanner description |
| code | TEXT | NOT NULL | Python scanner code |
| parameters | JSON | | Default parameters |
| category | VARCHAR(50) | | Scanner category |
| is_active | BOOLEAN | DEFAULT 1 | Active status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_scanner_name` on (name)
- `idx_scanner_category` on (category)
- `idx_scanner_active` on (is_active)

### 2. watchlists
Stores collections of symbols for scanning.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Watchlist name |
| description | TEXT | | Watchlist description |
| symbols | JSON | NOT NULL | Array of symbols |
| exchange | VARCHAR(10) | DEFAULT 'NSE' | Exchange name |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_watchlist_name` on (name)
- `idx_watchlist_exchange` on (exchange)

### 3. scan_results
Stores individual scan results.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| scanner_id | INTEGER | NOT NULL, FOREIGN KEY | Scanner reference |
| symbol | VARCHAR(20) | NOT NULL | Stock symbol |
| exchange | VARCHAR(10) | | Exchange name |
| signal | VARCHAR(50) | | Signal type (BUY/SELL/WATCH) |
| metrics | JSON | | Additional metrics |
| timestamp | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Result timestamp |

**Indexes:**
- `idx_result_scanner` on (scanner_id)
- `idx_result_symbol` on (symbol)
- `idx_result_signal` on (signal)
- `idx_result_timestamp` on (timestamp)

**Foreign Keys:**
- `scanner_id` → scanners(id) ON DELETE CASCADE

### 4. scan_schedules
Manages automated scan schedules.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| scanner_id | INTEGER | NOT NULL, FOREIGN KEY | Scanner reference |
| watchlist_id | INTEGER | NOT NULL, FOREIGN KEY | Watchlist reference |
| schedule_type | VARCHAR(20) | | Type: once/interval/daily/weekly |
| interval_minutes | INTEGER | | Interval in minutes |
| run_time | TIME | | Scheduled run time |
| days_of_week | VARCHAR(20) | | Days (comma-separated) |
| is_active | BOOLEAN | DEFAULT 1 | Schedule active status |
| last_run | TIMESTAMP | | Last execution time |
| next_run | TIMESTAMP | | Next scheduled run |
| market_hours_only | BOOLEAN | DEFAULT 1 | Run only during market hours |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_schedule_scanner` on (scanner_id)
- `idx_schedule_watchlist` on (watchlist_id)
- `idx_schedule_active` on (is_active)
- `idx_schedule_next_run` on (next_run)

**Foreign Keys:**
- `scanner_id` → scanners(id) ON DELETE CASCADE
- `watchlist_id` → watchlists(id) ON DELETE CASCADE

### 5. scan_history
Tracks scan execution history and performance.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| scanner_id | INTEGER | NOT NULL, FOREIGN KEY | Scanner reference |
| watchlist_id | INTEGER | FOREIGN KEY | Watchlist reference |
| status | VARCHAR(20) | | Status: running/completed/failed/cancelled |
| symbols_scanned | INTEGER | | Number of symbols scanned |
| signals_found | INTEGER | | Number of signals found |
| execution_time_ms | INTEGER | | Execution time in milliseconds |
| error_message | TEXT | | Error details if failed |
| started_at | TIMESTAMP | | Scan start time |
| completed_at | TIMESTAMP | | Scan completion time |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_history_scanner` on (scanner_id)
- `idx_history_watchlist` on (watchlist_id)
- `idx_history_status` on (status)
- `idx_history_started` on (started_at)

**Foreign Keys:**
- `scanner_id` → scanners(id) ON DELETE CASCADE
- `watchlist_id` → watchlists(id) ON DELETE SET NULL

### 6. settings
Stores application-wide settings.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| key | VARCHAR(50) | PRIMARY KEY | Setting key |
| value | JSON | | Setting value |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

### 7. scanner_templates
Pre-built scanner templates.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Template name |
| category | VARCHAR(50) | | Template category |
| description | TEXT | | Template description |
| code | TEXT | NOT NULL | Scanner code |
| default_parameters | JSON | | Default parameters |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |

**Indexes:**
- `idx_template_category` on (category)

## JSON Field Structures

### Scanner Parameters
```json
{
    "rsi_period": 14,
    "oversold_level": 30,
    "overbought_level": 70,
    "min_volume": 100000
}
```

### Watchlist Symbols
```json
[
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFC",
    "ICICIBANK"
]
```

### Scan Result Metrics
```json
{
    "price": 1234.56,
    "volume": 1000000,
    "rsi": 28.5,
    "macd": 12.34,
    "signal_strength": 85,
    "entry_price": 1234.56,
    "stop_loss": 1200.00,
    "target": 1300.00
}
```

## Database Operations

### Common Queries

#### Get Active Scanners
```sql
SELECT * FROM scanners
WHERE is_active = 1
ORDER BY created_at DESC;
```

#### Get Recent Results
```sql
SELECT sr.*, s.name as scanner_name
FROM scan_results sr
JOIN scanners s ON sr.scanner_id = s.id
WHERE sr.timestamp >= datetime('now', '-24 hours')
ORDER BY sr.timestamp DESC
LIMIT 100;
```

#### Get Schedule Due for Execution
```sql
SELECT * FROM scan_schedules
WHERE is_active = 1
  AND next_run <= datetime('now')
ORDER BY next_run ASC;
```

#### Scanner Performance Statistics
```sql
SELECT
    s.name,
    COUNT(sh.id) as total_scans,
    AVG(sh.execution_time_ms) as avg_time,
    SUM(sh.signals_found) as total_signals,
    COUNT(CASE WHEN sh.status = 'completed' THEN 1 END) as successful_scans
FROM scanners s
LEFT JOIN scan_history sh ON s.id = sh.scanner_id
GROUP BY s.id, s.name;
```

## Migration Strategy

### Development to Production

#### SQLite to PostgreSQL
```python
# Connection string changes
# From: sqlite:///fluxscan.db
# To: postgresql://user:pass@host/dbname

# JSON field changes
# SQLite: TEXT with JSON serialization
# PostgreSQL: JSONB native type
```

#### Schema Migration Script
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create tables
    op.create_table('scanners', ...)

    # Add indexes
    op.create_index('idx_scanner_name', 'scanners', ['name'])

def downgrade():
    # Drop tables
    op.drop_table('scanners')
```

## Performance Optimization

### Index Strategy
1. **Primary Keys**: Automatic B-tree index
2. **Foreign Keys**: Index for join operations
3. **Search Fields**: Index frequently queried columns
4. **Timestamp Fields**: Index for time-based queries

### Query Optimization
1. Use prepared statements
2. Batch insert operations
3. Limit result sets with pagination
4. Use connection pooling
5. Implement query caching

### Data Archival
```sql
-- Archive old results (> 30 days)
INSERT INTO scan_results_archive
SELECT * FROM scan_results
WHERE timestamp < datetime('now', '-30 days');

DELETE FROM scan_results
WHERE timestamp < datetime('now', '-30 days');
```

## Backup Strategy

### Backup Script
```bash
#!/bin/bash
# Daily backup
sqlite3 fluxscan.db ".backup backup/fluxscan_$(date +%Y%m%d).db"

# Weekly backup with compression
sqlite3 fluxscan.db ".dump" | gzip > backup/fluxscan_$(date +%Y%m%d).sql.gz
```

### Restore Process
```bash
# From backup file
cp backup/fluxscan_20240101.db fluxscan.db

# From SQL dump
gunzip < backup/fluxscan_20240101.sql.gz | sqlite3 fluxscan.db
```

## Data Integrity

### Constraints
1. **Unique Constraints**: Scanner and watchlist names
2. **Foreign Key Constraints**: Referential integrity
3. **Check Constraints**: Valid enum values
4. **Not Null Constraints**: Required fields

### Triggers
```sql
-- Update timestamp trigger
CREATE TRIGGER update_scanner_timestamp
AFTER UPDATE ON scanners
BEGIN
    UPDATE scanners SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

## Security Considerations

1. **SQL Injection Prevention**: Use parameterized queries
2. **Data Encryption**: Encrypt sensitive fields
3. **Access Control**: Database user permissions
4. **Audit Trail**: Log all modifications
5. **Data Sanitization**: Validate JSON inputs