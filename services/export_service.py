import csv
import json
import io
from typing import List, Dict, Any
from models import ScanResult
from datetime import datetime
import pandas as pd

class ExportService:
    @staticmethod
    def export_to_csv(results: List[ScanResult]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            'Timestamp', 'Symbol', 'Exchange', 'Signal',
            'Scanner', 'Price', 'Volume', 'RSI', 'MACD',
            'Signal_Strength', 'Other_Metrics'
        ]
        writer.writerow(headers)

        # Write data
        for result in results:
            metrics = result.get_metrics()

            row = [
                result.timestamp.isoformat() if result.timestamp else '',
                result.symbol,
                result.exchange or 'NSE',
                result.signal,
                result.scanner.name if result.scanner else '',
                metrics.get('price', ''),
                metrics.get('volume', ''),
                metrics.get('rsi', ''),
                metrics.get('macd', ''),
                metrics.get('signal_strength', ''),
                json.dumps({k: v for k, v in metrics.items()
                           if k not in ['price', 'volume', 'rsi', 'macd', 'signal_strength']})
            ]
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def export_to_json(results: List[ScanResult]) -> str:
        data = []
        for result in results:
            data.append({
                'timestamp': result.timestamp.isoformat() if result.timestamp else None,
                'symbol': result.symbol,
                'exchange': result.exchange,
                'signal': result.signal,
                'scanner': result.scanner.name if result.scanner else None,
                'metrics': result.get_metrics()
            })

        return json.dumps(data, indent=2)

    @staticmethod
    def export_to_excel(results: List[ScanResult]) -> bytes:
        # Create DataFrame
        data = []
        for result in results:
            metrics = result.get_metrics()
            row = {
                'Timestamp': result.timestamp,
                'Symbol': result.symbol,
                'Exchange': result.exchange or 'NSE',
                'Signal': result.signal,
                'Scanner': result.scanner.name if result.scanner else '',
                'Price': metrics.get('price', ''),
                'Volume': metrics.get('volume', ''),
                'RSI': metrics.get('rsi', ''),
                'MACD': metrics.get('macd', ''),
                'Signal_Strength': metrics.get('signal_strength', '')
            }

            # Add other metrics as columns
            for key, value in metrics.items():
                if key not in ['price', 'volume', 'rsi', 'macd', 'signal_strength']:
                    row[key] = value

            data.append(row)

        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Scan Results', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Scan Results']
            for column in df.columns:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)

        return output.getvalue()

    @staticmethod
    def export_summary_report(results: List[ScanResult]) -> Dict[str, Any]:
        if not results:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'watch_signals': 0,
                'unique_symbols': 0,
                'scanners_used': [],
                'top_symbols': [],
                'signal_distribution': {}
            }

        # Calculate statistics
        buy_signals = len([r for r in results if r.signal == 'BUY'])
        sell_signals = len([r for r in results if r.signal == 'SELL'])
        watch_signals = len([r for r in results if r.signal == 'WATCH'])

        # Get unique symbols and their counts
        symbol_counts = {}
        for result in results:
            symbol_counts[result.symbol] = symbol_counts.get(result.symbol, 0) + 1

        # Get scanner usage
        scanner_counts = {}
        for result in results:
            if result.scanner:
                scanner_name = result.scanner.name
                scanner_counts[scanner_name] = scanner_counts.get(scanner_name, 0) + 1

        # Sort and get top symbols
        top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_signals': len(results),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'watch_signals': watch_signals,
            'unique_symbols': len(symbol_counts),
            'scanners_used': list(scanner_counts.keys()),
            'top_symbols': [{'symbol': s[0], 'count': s[1]} for s in top_symbols],
            'signal_distribution': {
                'BUY': buy_signals,
                'SELL': sell_signals,
                'WATCH': watch_signals
            },
            'scanner_performance': scanner_counts,
            'time_range': {
                'start': min(r.timestamp for r in results if r.timestamp).isoformat() if results else None,
                'end': max(r.timestamp for r in results if r.timestamp).isoformat() if results else None
            }
        }

    @staticmethod
    def export_to_tradingview(results: List[ScanResult]) -> str:
        """Export symbols in TradingView watchlist format"""
        symbols = []
        for result in results:
            exchange = result.exchange or 'NSE'
            # Format: EXCHANGE:SYMBOL
            symbols.append(f"{exchange}:{result.symbol}")

        return ','.join(set(symbols))  # Remove duplicates

    @staticmethod
    def export_to_html(results: List[ScanResult]) -> str:
        """Generate HTML report of scan results"""
        html = """
        <html>
        <head>
            <title>FluxScan Results Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .buy { color: green; font-weight: bold; }
                .sell { color: red; font-weight: bold; }
                .watch { color: orange; font-weight: bold; }
                h1 { color: #333; }
                .summary { background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>FluxScan Results Report</h1>
            <div class="summary">
                <h3>Summary</h3>
                <p>Generated: {timestamp}</p>
                <p>Total Signals: {total_signals}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Signal</th>
                        <th>Scanner</th>
                        <th>Price</th>
                        <th>Strength</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """

        rows = []
        for result in results:
            metrics = result.get_metrics()
            signal_class = result.signal.lower()
            row = f"""
                <tr>
                    <td>{result.timestamp.strftime('%Y-%m-%d %H:%M') if result.timestamp else ''}</td>
                    <td>{result.symbol}</td>
                    <td class="{signal_class}">{result.signal}</td>
                    <td>{result.scanner.name if result.scanner else ''}</td>
                    <td>{metrics.get('price', '')}</td>
                    <td>{metrics.get('signal_strength', '')}</td>
                </tr>
            """
            rows.append(row)

        return html.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_signals=len(results),
            rows=''.join(rows)
        )