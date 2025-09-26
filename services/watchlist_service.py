from typing import List, Optional
from models import Watchlist
import csv
import io

class WatchlistService:
    def __init__(self, data_service):
        self.data_service = data_service

    def create_watchlist(self, name: str, symbols: List[str],
                        exchange: str = 'NSE', description: str = None) -> Watchlist:
        # Validate symbols
        valid_symbols = []
        for symbol in symbols:
            if self.data_service.validate_symbol(symbol, exchange):
                valid_symbols.append(symbol)

        if not valid_symbols:
            raise ValueError("No valid symbols found")

        # Create watchlist
        watchlist = Watchlist(
            name=name,
            exchange=exchange,
            description=description
        )
        watchlist.set_symbols(valid_symbols)
        watchlist.save()

        return watchlist

    def add_symbols(self, watchlist_id: int, symbols: List[str]) -> Watchlist:
        watchlist = Watchlist.get_by_id(watchlist_id)
        if not watchlist:
            raise ValueError(f"Watchlist {watchlist_id} not found")

        # Validate and add symbols
        added = 0
        for symbol in symbols:
            if self.data_service.validate_symbol(symbol, watchlist.exchange):
                if watchlist.add_symbol(symbol):
                    added += 1

        watchlist.save()
        return watchlist

    def remove_symbols(self, watchlist_id: int, symbols: List[str]) -> Watchlist:
        watchlist = Watchlist.get_by_id(watchlist_id)
        if not watchlist:
            raise ValueError(f"Watchlist {watchlist_id} not found")

        for symbol in symbols:
            watchlist.remove_symbol(symbol)

        watchlist.save()
        return watchlist

    def import_from_csv(self, name: str, csv_content: str,
                       exchange: str = 'NSE') -> Watchlist:
        # Parse CSV content
        symbols = []
        reader = csv.reader(io.StringIO(csv_content))
        for row in reader:
            if row:
                # Assume first column is symbol
                symbol = row[0].strip().upper()
                if symbol and not symbol.startswith('#'):  # Skip comments
                    symbols.append(symbol)

        if not symbols:
            raise ValueError("No symbols found in CSV")

        return self.create_watchlist(name, symbols, exchange)

    def import_predefined(self, index_name: str) -> Watchlist:
        # Get predefined symbols
        symbols = self.data_service.get_index_constituents(index_name)

        if not symbols:
            raise ValueError(f"Index {index_name} not found")

        return self.create_watchlist(
            name=index_name,
            symbols=symbols,
            exchange='NSE',
            description=f"Constituents of {index_name} index"
        )

    def merge_watchlists(self, watchlist_ids: List[int], new_name: str) -> Watchlist:
        all_symbols = set()
        exchange = None

        for wl_id in watchlist_ids:
            watchlist = Watchlist.get_by_id(wl_id)
            if watchlist:
                all_symbols.update(watchlist.get_symbols())
                if not exchange:
                    exchange = watchlist.exchange

        if not all_symbols:
            raise ValueError("No symbols found to merge")

        return self.create_watchlist(
            name=new_name,
            symbols=list(all_symbols),
            exchange=exchange or 'NSE',
            description=f"Merged from {len(watchlist_ids)} watchlists"
        )

    def get_watchlist_quotes(self, watchlist_id: int) -> List[dict]:
        watchlist = Watchlist.get_by_id(watchlist_id)
        if not watchlist:
            return []

        quotes = []
        for symbol in watchlist.get_symbols():
            quote = self.data_service.get_quote(symbol, watchlist.exchange)
            if quote:
                quote['symbol'] = symbol
                quotes.append(quote)

        return quotes