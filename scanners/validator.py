import ast
import sys
from typing import Tuple, List, Optional

class ScannerValidator:
    # Allowed modules and functions
    ALLOWED_IMPORTS = [
        'pandas', 'pd',
        'numpy', 'np',
        'talib',
        'datetime',
        'math'
    ]

    RESTRICTED_KEYWORDS = [
        '__import__',
        'eval',
        'exec',
        'compile',
        'open',
        'file',
        'input',
        'raw_input',
        '__builtins__',
        'globals',
        'locals',
        'vars',
        'dir',
        'getattr',
        'setattr',
        'delattr',
        'hasattr',
        '__dict__',
        '__class__',
        '__bases__',
        '__subclasses__',
        'type',
        'id',
        'help',
        'reload',
        '__loader__',
        '__spec__',
        'os',
        'sys',
        'subprocess',
        'socket',
        'requests',
        'urllib',
        'httpx'
    ]

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, code: str) -> Tuple[bool, List[str], List[str]]:
        self.errors = []
        self.warnings = []

        # Check for basic syntax errors
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return False, self.errors, self.warnings

        # Walk the AST and validate
        self._validate_ast(tree)

        # Check for required signal variable
        if not self._has_signal_assignment(tree):
            self.warnings.append("Scanner should set 'signal' variable to True/False")

        # Check for infinite loops
        if self._has_potential_infinite_loop(tree):
            self.warnings.append("Potential infinite loop detected")

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_ast(self, node):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in self.ALLOWED_IMPORTS:
                    self.errors.append(f"Import of '{alias.name}' is not allowed")

        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module not in self.ALLOWED_IMPORTS:
                self.errors.append(f"Import from '{node.module}' is not allowed")

        # Check for restricted function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.RESTRICTED_KEYWORDS:
                    self.errors.append(f"Use of '{node.func.id}' is not allowed")

        # Check for attribute access to restricted items
        elif isinstance(node, ast.Attribute):
            if node.attr in ['__dict__', '__class__', '__bases__', '__subclasses__']:
                self.errors.append(f"Access to '{node.attr}' is not allowed")

        # Check for file operations
        elif isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    if isinstance(item.context_expr.func, ast.Name):
                        if item.context_expr.func.id == 'open':
                            self.errors.append("File operations are not allowed")

        # Recursively validate child nodes
        for child in ast.iter_child_nodes(node):
            self._validate_ast(child)

    def _has_signal_assignment(self, tree) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'signal':
                        return True
        return False

    def _has_potential_infinite_loop(self, tree) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check if while True without break
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Break):
                            has_break = True
                            break
                    if not has_break:
                        return True
        return False

    @staticmethod
    def create_safe_namespace():
        return {
            '__builtins__': {
                'True': True,
                'False': False,
                'None': None,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'reversed': reversed,
                'round': round,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'print': print  # For debugging
            }
        }

    @staticmethod
    def get_template_code() -> str:
        return '''# Scanner Template
# Available variables:
#   data: DataFrame with columns - open, high, low, close, volume
#   symbol: Current symbol being scanned
#   params: Dictionary of scanner parameters

# Available libraries:
#   pd (pandas), np (numpy), talib

# Example: Simple Moving Average Crossover
fast_period = params.get('fast_period', 10)
slow_period = params.get('slow_period', 20)

# Calculate moving averages
fast_ma = talib.SMA(close, timeperiod=fast_period)
slow_ma = talib.SMA(close, timeperiod=slow_period)

# Check for crossover
if len(fast_ma) >= 2 and len(slow_ma) >= 2:
    # Bullish crossover
    if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'fast_ma': float(fast_ma[-1]),
            'slow_ma': float(slow_ma[-1]),
            'price': float(close[-1])
        }
else:
    signal = False
'''

    @staticmethod
    def get_examples() -> dict:
        return {
            'rsi_oversold': '''# RSI Oversold Scanner
rsi_period = params.get('rsi_period', 14)
oversold_level = params.get('oversold_level', 30)

# Calculate RSI
rsi = talib.RSI(close, timeperiod=rsi_period)

# Check if oversold
if len(rsi) > 0 and rsi[-1] < oversold_level:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'rsi': float(rsi[-1]),
        'price': float(close[-1])
    }
else:
    signal = False
''',
            'macd_crossover': '''# MACD Crossover Scanner
fast = params.get('fast_period', 12)
slow = params.get('slow_period', 26)
signal_period = params.get('signal_period', 9)

# Calculate MACD
macd, macdsignal, macdhist = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal_period)

# Check for bullish crossover
if len(macd) >= 2 and len(macdsignal) >= 2:
    if macd[-1] > macdsignal[-1] and macd[-2] <= macdsignal[-2]:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'macd': float(macd[-1]),
            'signal_line': float(macdsignal[-1]),
            'histogram': float(macdhist[-1]),
            'price': float(close[-1])
        }
    else:
        signal = False
else:
    signal = False
''',
            'bollinger_squeeze': '''# Bollinger Band Squeeze Scanner
bb_period = params.get('bb_period', 20)
bb_std = params.get('bb_std', 2)

# Calculate Bollinger Bands
upper, middle, lower = talib.BBANDS(close, timeperiod=bb_period, nbdevup=bb_std, nbdevdn=bb_std)

# Calculate band width
if len(upper) > 0 and len(lower) > 0:
    bandwidth = (upper[-1] - lower[-1]) / middle[-1] * 100

    # Check for squeeze (narrow bands)
    if bandwidth < params.get('squeeze_threshold', 2):
        signal = True
        signal_type = 'WATCH'
        metrics = {
            'bandwidth': float(bandwidth),
            'upper_band': float(upper[-1]),
            'lower_band': float(lower[-1]),
            'price': float(close[-1])
        }
    else:
        signal = False
else:
    signal = False
'''
        }