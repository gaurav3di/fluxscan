import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback
import threading
import queue
import time

class ScannerEngine:
    def __init__(self, data_service, max_workers=5):
        self.data_service = data_service
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        self.progress = 0
        self.is_running = False
        self.cancel_requested = False
        self._lock = threading.Lock()

    def execute_scanner(self, scanner_code: str, symbols: List, parameters: Dict[str, Any] = None,
                       progress_callback=None) -> Dict[str, Any]:
        self.results = []
        self.errors = []
        self.progress = 0
        self.is_running = True
        self.cancel_requested = False

        start_time = time.time()
        total_symbols = len(symbols)

        # Compile scanner code first
        try:
            compiled_code = compile(scanner_code, '<scanner>', 'exec')
        except SyntaxError as e:
            return {
                'status': 'error',
                'error': f'Scanner code compilation failed: {str(e)}',
                'results': [],
                'execution_time': 0
            }

        # Process symbols
        for idx, symbol_info in enumerate(symbols):
            if self.cancel_requested:
                break

            # Handle both string and dict formats
            if isinstance(symbol_info, str):
                symbol = symbol_info
                exchange = parameters.get('exchange', 'NSE')
            else:
                symbol = symbol_info.get('symbol', symbol_info) if isinstance(symbol_info, dict) else symbol_info
                exchange = symbol_info.get('exchange', 'NSE') if isinstance(symbol_info, dict) else 'NSE'

            try:
                # Fetch data for symbol
                data = self.data_service.get_historical_data(
                    symbol=symbol,
                    exchange=exchange,
                    interval=parameters.get('interval', 'D'),
                    lookback_days=parameters.get('lookback_days', 100)
                )

                if data is not None and not data.empty:
                    # Execute scanner for this symbol (namespace is now created inside _execute_for_symbol)
                    result = self._execute_for_symbol(
                        compiled_code,
                        None,  # Don't pass a shared namespace
                        data,
                        symbol,
                        parameters
                    )

                    if result:
                        self.results.append(result)

            except Exception as e:
                self.errors.append({
                    'symbol': symbol,
                    'error': str(e)
                })

            # Update progress
            self.progress = int(((idx + 1) / total_symbols) * 100)
            if progress_callback:
                progress_callback(self.progress, symbol)

        execution_time = time.time() - start_time
        self.is_running = False

        return {
            'status': 'cancelled' if self.cancel_requested else 'completed',
            'results': self.results,
            'errors': self.errors,
            'total_scanned': total_symbols,
            'signals_found': len(self.results),
            'execution_time': execution_time
        }

    def _execute_for_symbol(self, compiled_code, namespace, data, symbol, parameters):
        try:
            # Create a fresh namespace for each symbol to avoid data contamination
            local_namespace = self._create_namespace(parameters)
            local_namespace['data'] = data.copy()  # Make a copy of the data
            local_namespace['df'] = data.copy()
            local_namespace['symbol'] = symbol
            local_namespace['params'] = parameters

            # Add common data columns as Series for better compatibility
            # Make copies to ensure isolation
            local_namespace['open'] = data['open'].copy() if 'open' in data.columns else pd.Series()
            local_namespace['high'] = data['high'].copy() if 'high' in data.columns else pd.Series()
            local_namespace['low'] = data['low'].copy() if 'low' in data.columns else pd.Series()
            local_namespace['close'] = data['close'].copy() if 'close' in data.columns else pd.Series()
            local_namespace['volume'] = data['volume'].copy() if 'volume' in data.columns else pd.Series()

            # Execute scanner code
            exec(compiled_code, local_namespace)

            # Check for Amibroker-style Filter first
            if local_namespace.get('Filter', False):
                # Use columns if AddColumn was used
                if local_namespace.get('columns'):
                    return {
                        'symbol': symbol,
                        'signal': 'EXPLORE',
                        'metrics': dict(local_namespace['columns']),  # Make a copy of columns
                        'timestamp': datetime.now().isoformat()
                    }

            # Legacy check for backward compatibility
            elif 'signal' in local_namespace and local_namespace['signal']:
                metrics = local_namespace.get('metrics', {})

                # Extract additional data if available
                if 'signal_strength' in local_namespace:
                    metrics['signal_strength'] = local_namespace['signal_strength']
                if 'entry_price' in local_namespace:
                    metrics['entry_price'] = local_namespace['entry_price']
                if 'target' in local_namespace:
                    metrics['target'] = local_namespace['target']
                if 'stop_loss' in local_namespace:
                    metrics['stop_loss'] = local_namespace['stop_loss']

                return {
                    'symbol': symbol,
                    'signal': local_namespace.get('signal_type', 'BUY'),
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            raise Exception(f"Scanner execution failed for {symbol}: {str(e)}")

        return None

    def _create_namespace(self, parameters):
        # Columns storage for Amibroker-style exploration
        columns = {}

        # AddColumn function (Amibroker style) - create a new closure for each namespace
        def make_add_column(cols):
            def AddColumn(name, value, format_spec='1.2'):
                cols[name] = value
            return AddColumn

        namespace = {
            'pd': pd,
            'np': np,
            'numpy': np,  # Add numpy alias
            'talib': talib,
            'datetime': datetime,
            'parameters': parameters or {},
            'signal': False,
            'signal_type': None,
            'metrics': {},
            # Amibroker-style exploration
            'Filter': False,
            'AddColumn': make_add_column(columns),
            'columns': columns
        }

        # Add TA-Lib functions
        namespace.update({
            'SMA': talib.SMA,
            'EMA': talib.EMA,
            'RSI': talib.RSI,
            'MACD': talib.MACD,
            'BBANDS': talib.BBANDS,
            'ATR': talib.ATR,
            'ADX': talib.ADX,
            'STOCH': talib.STOCH,
            'CCI': talib.CCI,
            'MFI': talib.MFI,
            'OBV': talib.OBV,
            'SAR': talib.SAR,
            'WILLR': talib.WILLR,
            'ROC': talib.ROC,
            'MOM': talib.MOM
        })

        return namespace

    def cancel(self):
        self.cancel_requested = True

    def get_progress(self):
        return self.progress

    def is_scanning(self):
        return self.is_running

    def execute_parallel(self, scanner_code: str, symbols: List[str],
                        parameters: Dict[str, Any] = None, progress_callback=None) -> Dict[str, Any]:
        self.results = []
        self.errors = []
        self.progress = 0
        self.is_running = True
        self.cancel_requested = False

        start_time = time.time()
        total_symbols = len(symbols)

        # Create work queue
        work_queue = queue.Queue()
        for symbol in symbols:
            work_queue.put(symbol)

        # Create result queue
        result_queue = queue.Queue()

        # Compile scanner code
        try:
            compiled_code = compile(scanner_code, '<scanner>', 'exec')
        except SyntaxError as e:
            return {
                'status': 'error',
                'error': f'Scanner code compilation failed: {str(e)}',
                'results': [],
                'execution_time': 0
            }

        # Worker function
        def worker():
            while not work_queue.empty() and not self.cancel_requested:
                try:
                    symbol = work_queue.get_nowait()

                    # Fetch data
                    data = self.data_service.get_historical_data(
                        symbol=symbol,
                        exchange=parameters.get('exchange', 'NSE'),
                        interval=parameters.get('interval', 'D'),
                        lookback_days=parameters.get('lookback_days', 100)
                    )

                    if data is not None and not data.empty:
                        result = self._execute_for_symbol(
                            compiled_code,
                            None,  # Don't pass a shared namespace
                            data,
                            symbol,
                            parameters
                        )
                        if result:
                            result_queue.put(('result', result))

                    # Update progress
                    with self._lock:
                        self.progress = int(((total_symbols - work_queue.qsize()) / total_symbols) * 100)

                    if progress_callback:
                        progress_callback(self.progress, symbol)

                except queue.Empty:
                    break
                except Exception as e:
                    result_queue.put(('error', {'symbol': symbol, 'error': str(e)}))

        # Start worker threads
        threads = []
        for _ in range(min(self.max_workers, len(symbols))):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Collect results
        while not result_queue.empty():
            result_type, result_data = result_queue.get()
            if result_type == 'result':
                self.results.append(result_data)
            elif result_type == 'error':
                self.errors.append(result_data)

        execution_time = time.time() - start_time
        self.is_running = False

        return {
            'status': 'cancelled' if self.cancel_requested else 'completed',
            'results': self.results,
            'errors': self.errors,
            'total_scanned': total_symbols,
            'signals_found': len(self.results),
            'execution_time': execution_time
        }