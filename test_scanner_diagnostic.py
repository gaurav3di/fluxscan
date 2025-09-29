import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from scanners import ScannerEngine
from services import DataService
from app import app, initialize_services
import pandas as pd
import numpy as np

def test_scanner_with_different_symbols():
    """Test scanner with multiple symbols to ensure each gets unique data"""

    # Simple test scanner that shows data uniqueness
    test_code = """
# Test to verify each symbol gets unique data
Filter = True

# Get unique values for this symbol
current_close = float(close.iloc[-1]) if len(close) > 0 else 0
max_close = float(close.max()) if len(close) > 0 else 0
min_close = float(close.min()) if len(close) > 0 else 0
avg_close = float(close.mean()) if len(close) > 0 else 0
std_close = float(close.std()) if len(close) > 0 else 0

# Add columns to verify data is unique per symbol
AddColumn('Symbol', symbol)
AddColumn('Close', round(current_close, 2))
AddColumn('Max', round(max_close, 2))
AddColumn('Min', round(min_close, 2))
AddColumn('Avg', round(avg_close, 2))
AddColumn('Std Dev', round(std_close, 2))
AddColumn('Data Points', len(close))
"""

    # Test with different symbols
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'WIPRO']

    with app.app_context():
        # Initialize services
        initialize_services()

        # Use the app's data service
        data_service = app.data_service

        # Create scanner engine
        engine = ScannerEngine(data_service)

        # Execute scanner
        print("\n" + "="*60)
        print("Testing Scanner Engine - Symbol Data Isolation")
        print("="*60)

        result = engine.execute_scanner(
            test_code,
            test_symbols,
            {'interval': 'D', 'lookback_days': 30}
        )

        if result['status'] == 'completed':
            print(f"\nScanned {result['total_scanned']} symbols")
            print(f"Found {result['signals_found']} results")
            print(f"Execution time: {result['execution_time']:.2f} seconds")

            if result['results']:
                print("\n" + "-"*60)
                print("Results (showing unique data per symbol):")
                print("-"*60)

                # Create a DataFrame for better display
                data_rows = []
                for r in result['results']:
                    row = {'Symbol': r['symbol']}
                    row.update(r['metrics'])
                    data_rows.append(row)

                df = pd.DataFrame(data_rows)

                # Display the results
                print("\n", df.to_string(index=False))

                # Check if data is unique
                print("\n" + "-"*60)
                print("Data Uniqueness Verification:")
                print("-"*60)

                # Check if Symbol column matches the actual symbol
                symbol_check_passed = True
                for r in result['results']:
                    actual_symbol = r['symbol']
                    reported_symbol = r['metrics'].get('Symbol', '')
                    if actual_symbol != reported_symbol:
                        print(f"X MISMATCH: {actual_symbol} reported as {reported_symbol}")
                        symbol_check_passed = False
                    else:
                        print(f"OK {actual_symbol}: Symbol matches")

                # Check if values are different across symbols
                if len(df) > 1:
                    print("\n" + "-"*60)
                    print("Value Diversity Check:")
                    print("-"*60)

                    for col in ['Close', 'Max', 'Min', 'Avg']:
                        if col in df.columns:
                            unique_values = df[col].nunique()
                            total_values = len(df[col])
                            if unique_values == 1:
                                print(f"X {col}: All values are identical ({df[col].iloc[0]})")
                            else:
                                print(f"OK {col}: {unique_values}/{total_values} unique values")

                if symbol_check_passed and all(df[col].nunique() > 1 for col in ['Close', 'Max', 'Min'] if col in df.columns):
                    print("\n" + "="*60)
                    print("SUCCESS: Scanner engine properly isolates data per symbol!")
                    print("="*60)
                else:
                    print("\n" + "="*60)
                    print("ISSUE DETECTED: Data contamination across symbols")
                    print("="*60)
            else:
                print("\nNo results found")

            # Show any errors
            if result['errors']:
                print("\n" + "-"*60)
                print("Errors:")
                print("-"*60)
                for error in result['errors']:
                    print(f"Symbol: {error['symbol']}, Error: {error['error']}")
        else:
            print(f"\nScan failed with status: {result['status']}")
            if 'error' in result:
                print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_scanner_with_different_symbols()