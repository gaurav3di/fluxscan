# FluxScan - Trading Scanner Engine

FluxScan is a powerful web-based trading scanner engine that enables traders and investors to create, manage, and execute custom stock screening strategies using Python. Built with Flask, OpenAlgo SDK, and TA-Lib, it provides real-time scanning capabilities with a modern, responsive interface.

## Features

- **Custom Scanner Creation**: Write Python-based scanners with full access to TA-Lib indicators
- **Watchlist Management**: Create and manage multiple watchlists with bulk import support
- **Real-time Scanning**: Execute scanners on multiple symbols with progress tracking
- **Scheduled Scans**: Set up automated scanning at specific intervals or times
- **Built-in Templates**: Pre-configured scanners for common strategies (MACD, RSI, Bollinger Bands, etc.)
- **Export Capabilities**: Export scan results to CSV or JSON formats
- **Modern UI**: Responsive interface built with DaisyUI and Tailwind CSS
- **WebSocket Support**: Real-time updates during scan execution

## Prerequisites

- Python 3.8 or higher
- OpenAlgo application running (for market data)
- TA-Lib library installed

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/fluxscan.git
cd fluxscan
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install TA-Lib

#### Windows:
Download the appropriate wheel file from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

```bash
pip install TA_Lib‑0.4.28‑cp39‑cp39‑win_amd64.whl
```

#### Linux:
```bash
sudo apt-get update
sudo apt-get install ta-lib
pip install TA-Lib
```

#### Mac:
```bash
brew install ta-lib
pip install TA-Lib
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` file:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# OpenAlgo Configuration
OPENALGO_API_KEY=your-openalgo-api-key
OPENALGO_HOST=http://127.0.0.1:5000

# Database
DATABASE_URL=sqlite:///fluxscan.db

# Application Settings
MAX_CONCURRENT_SCANS=10
DEFAULT_LOOKBACK_DAYS=100
```

### Step 6: Initialize Database

```bash
python init_db.py
```

This will:
- Create all database tables
- Load built-in scanner templates
- Create default watchlists
- Set up initial settings

### Step 7: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5001`

## Usage

### Creating a Scanner

1. Navigate to **Scanners** → **New Scanner**
2. Write your scanner code using Python and TA-Lib
3. Set parameters and test with sample data
4. Save the scanner

Example scanner code:
```python
# RSI Oversold Scanner
rsi = talib.RSI(close, timeperiod=14)
if rsi[-1] < 30:
    signal = True
    signal_type = 'BUY'
    metrics = {'rsi': float(rsi[-1]), 'price': float(close[-1])}
else:
    signal = False
```

### Managing Watchlists

1. Go to **Watchlists** section
2. Create a new watchlist or import from CSV
3. Add symbols manually or use predefined indices
4. Save the watchlist

### Running a Scan

1. Click **Quick Scan** on the dashboard
2. Select a scanner and watchlist
3. Click **Start Scan**
4. Monitor progress in real-time
5. View results and export if needed

### Scheduling Scans

1. Navigate to **Schedules**
2. Create a new schedule
3. Select scanner, watchlist, and timing
4. Enable the schedule

## Scanner Code Guidelines

### Available Variables

- `data`: DataFrame with OHLCV data
- `open`, `high`, `low`, `close`, `volume`: NumPy arrays
- `symbol`: Current symbol being scanned
- `params`: Dictionary of scanner parameters

### Available Libraries

- `pd` (pandas)
- `np` (numpy)
- `talib` (Technical Analysis Library)

### Required Output

Your scanner must set:
- `signal`: Boolean indicating if a signal was found
- `signal_type`: 'BUY', 'SELL', or 'WATCH'
- `metrics`: Dictionary with additional data

## API Documentation

### Scanner API

```
GET    /api/scanners              - List all scanners
POST   /api/scanners              - Create scanner
GET    /api/scanners/{id}         - Get scanner details
PUT    /api/scanners/{id}         - Update scanner
DELETE /api/scanners/{id}         - Delete scanner
POST   /api/scanners/{id}/test    - Test scanner
```

### Watchlist API

```
GET    /api/watchlists            - List all watchlists
POST   /api/watchlists            - Create watchlist
GET    /api/watchlists/{id}       - Get watchlist
PUT    /api/watchlists/{id}       - Update watchlist
DELETE /api/watchlists/{id}       - Delete watchlist
```

### Scan API

```
POST   /scan/api/scan             - Run scanner
GET    /scan/api/scan/status/{id} - Get scan status
POST   /scan/api/scan/cancel/{id} - Cancel scan
```

### Results API

```
GET    /api/results               - Get scan results
GET    /api/results/{id}          - Get specific result
DELETE /api/results/{id}          - Delete result
POST   /api/results/export        - Export results
```

## Project Structure

```
fluxscan/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
├── models/              # Database models
│   ├── scanner.py
│   ├── watchlist.py
│   └── scan_result.py
├── scanners/            # Scanner engine
│   ├── base.py
│   ├── scanner_engine.py
│   └── templates/       # Built-in scanners
├── services/            # Business logic
│   ├── data_service.py
│   └── cache_service.py
├── routes/              # API routes
│   ├── scanner_routes.py
│   └── watchlist_routes.py
├── templates/           # HTML templates
│   └── layout/
│       └── base.html
└── static/              # Static files
    ├── js/
    └── css/
```

## Troubleshooting

### TA-Lib Installation Issues

If you encounter issues installing TA-Lib:

1. Ensure you have the correct Python version
2. Install Visual C++ redistributables (Windows)
3. Use pre-built wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs/

### OpenAlgo Connection Issues

1. Verify OpenAlgo is running
2. Check API key in `.env` file
3. Ensure correct host URL
4. Test connection at `/api/settings/openalgo/test`

### Database Issues

Reset the database:
```bash
rm fluxscan.db
python init_db.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the AGPL-3.0 License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation at `/help`
- Review the API documentation

## Acknowledgments

- OpenAlgo SDK for market data integration
- TA-Lib for technical analysis
- DaisyUI for UI components
- Flask community for the framework