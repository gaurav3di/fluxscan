# FluxScan Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenAlgo API:**
   - Copy `.env.example` to `.env`
   - Update the following settings:
   ```
   OPENALGO_API_KEY=your_api_key_here
   OPENALGO_HOST=http://127.0.0.1:5000
   ```

3. **Initialize database:**
   ```bash
   python utils/seed_data.py
   ```

4. **Run FluxScan:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open browser at `http://localhost:5001`

## Getting OpenAlgo API Key

### Option 1: From OpenAlgo Server
1. Start your OpenAlgo server
2. Go to OpenAlgo dashboard
3. Navigate to API Settings
4. Copy your API key

### Option 2: Default Testing Key
If you're using OpenAlgo in test mode, try:
```
OPENALGO_API_KEY=your_api_key_here
```

## Troubleshooting

### "Invalid openalgo apikey" Error
This means your API key is not valid. Solutions:
1. Check if OpenAlgo server is running
2. Verify API key is correct in `.env` file
3. Ensure no extra spaces in the API key
4. Make sure the host URL is correct

### Using Dummy Data
If you see "Using dummy data" messages:
- The system is working but using simulated data
- This happens when OpenAlgo API is not accessible
- Scanners will still work for testing purposes

### Parameters Not Showing Correctly
Run the seed script again:
```bash
python utils/seed_data.py
```

## Testing the Setup

### 1. Test Data Connection:
```bash
python test_data_download.py
```

### 2. Test Scanner:
```bash
python run_ema_test.py
```

### 3. Test Full Integration:
```bash
python test_scan_integration.py
```

## Default Scanners Available

After running seed_data.py, you'll have:
1. **10/20 EMA Crossover** - Detects EMA crossovers (15m timeframe)
2. **RSI Oversold Scanner** - Finds oversold stocks (1h timeframe)
3. **MACD Bullish** - Detects MACD crossovers (Daily)
4. **Volume Breakout** - Identifies volume spikes (5m timeframe)

## Scanner Parameters

Each scanner has configurable parameters that are properly displayed in the UI:
- `fast_period`: Fast EMA period (default: 10)
- `slow_period`: Slow EMA period (default: 20)
- `min_volume`: Minimum volume filter (default: 100000)
- `rsi_period`: RSI calculation period (default: 14)
- `threshold`: RSI threshold level (default: 30)

## Need Help?

1. Check if all services are running
2. Review the logs in the terminal
3. Run the test scripts to diagnose issues
4. Ensure your broker is connected in OpenAlgo (for real data)