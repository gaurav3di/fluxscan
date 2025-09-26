from .base import db, BaseModel
import json

class Watchlist(BaseModel):
    __tablename__ = 'watchlists'

    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    symbols = db.Column(db.Text, nullable=False)  # JSON array with exchange info
    exchange = db.Column(db.String(10), default='NSE')  # Default exchange

    # Relationships
    schedules = db.relationship('ScanSchedule', backref='watchlist', lazy='dynamic')
    histories = db.relationship('ScanHistory', backref='watchlist', lazy='dynamic')

    # Supported exchanges
    SUPPORTED_EXCHANGES = ['NSE', 'BSE', 'NFO', 'BFO', 'CDS', 'BCD', 'MCX']

    def __repr__(self):
        return f'<Watchlist {self.name}>'

    def get_symbols(self):
        """Get symbols with exchange information"""
        if self.symbols:
            data = json.loads(self.symbols)
            # Handle both old format (list) and new format (list of dicts)
            if data and isinstance(data[0], str):
                # Old format - convert to new format with default exchange
                return [{'symbol': s, 'exchange': self.exchange} for s in data]
            return data
        return []

    def get_symbol_list(self):
        """Get just the symbol names (backward compatibility)"""
        return [s['symbol'] if isinstance(s, dict) else s for s in self.get_symbols()]

    def set_symbols(self, symbol_data):
        """Set symbols with exchange information
        symbol_data can be:
        - List of strings (uses default exchange)
        - List of dicts with 'symbol' and 'exchange' keys
        - List of tuples (symbol, exchange)
        """
        if not symbol_data:
            self.symbols = json.dumps([])
            return

        normalized = []
        for item in symbol_data:
            if isinstance(item, str):
                normalized.append({'symbol': item.upper(), 'exchange': self.exchange})
            elif isinstance(item, dict):
                normalized.append({
                    'symbol': item['symbol'].upper(),
                    'exchange': item.get('exchange', self.exchange).upper()
                })
            elif isinstance(item, (list, tuple)) and len(item) >= 1:
                exchange = item[1] if len(item) > 1 else self.exchange
                normalized.append({'symbol': item[0].upper(), 'exchange': exchange.upper()})

        self.symbols = json.dumps(normalized)

    def add_symbol(self, symbol, exchange=None):
        """Add a symbol with optional exchange"""
        symbols = self.get_symbols()
        new_symbol = {
            'symbol': symbol.upper(),
            'exchange': (exchange or self.exchange).upper()
        }

        # Check if already exists
        for s in symbols:
            if s['symbol'] == new_symbol['symbol'] and s['exchange'] == new_symbol['exchange']:
                return False

        symbols.append(new_symbol)
        self.symbols = json.dumps(symbols)
        return True

    def remove_symbol(self, symbol, exchange=None):
        """Remove a symbol with optional exchange"""
        symbols = self.get_symbols()
        symbol = symbol.upper()

        if exchange:
            exchange = exchange.upper()
            symbols = [s for s in symbols if not (s['symbol'] == symbol and s['exchange'] == exchange)]
        else:
            symbols = [s for s in symbols if s['symbol'] != symbol]

        self.symbols = json.dumps(symbols)
        return True

    def symbol_count(self):
        return len(self.get_symbols())

    def to_dict(self):
        data = super().to_dict()
        data['symbols'] = self.get_symbols()
        data['symbol_count'] = self.symbol_count()
        data['supported_exchanges'] = self.SUPPORTED_EXCHANGES
        return data

    @classmethod
    def get_by_exchange(cls, exchange):
        """Get watchlists that contain symbols from specified exchange"""
        all_watchlists = cls.query.all()
        result = []
        for wl in all_watchlists:
            symbols = wl.get_symbols()
            if any(s.get('exchange', wl.exchange) == exchange for s in symbols):
                result.append(wl)
        return result

    @classmethod
    def create_from_csv(cls, name, csv_content, default_exchange='NSE'):
        """Create watchlist from CSV content
        CSV format: SYMBOL,EXCHANGE or just SYMBOL (uses default exchange)
        """
        import csv
        import io

        symbols = []
        reader = csv.reader(io.StringIO(csv_content))

        for row in reader:
            if not row or not row[0].strip():
                continue

            symbol = row[0].strip().upper()
            exchange = row[1].strip().upper() if len(row) > 1 and row[1].strip() else default_exchange

            # Validate exchange
            if exchange not in cls.SUPPORTED_EXCHANGES:
                exchange = default_exchange

            symbols.append({'symbol': symbol, 'exchange': exchange})

        watchlist = cls(name=name, exchange=default_exchange)
        watchlist.symbols = json.dumps(symbols)
        return watchlist