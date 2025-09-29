from flask import Blueprint, render_template, jsonify, request, make_response, redirect, url_for
from models import db, ScanResult, Scanner, Watchlist, ScanHistory
from datetime import datetime, timedelta
import csv
import io
import json

bp = Blueprint('results', __name__, url_prefix='/results')

@bp.route('/')
def list_results():
    # Get the latest scan or specific scan if ID provided
    scan_id = request.args.get('scan_id', type=int)

    if scan_id:
        # Get specific scan results
        history = ScanHistory.query.get(scan_id)
        if history:
            results = ScanResult.query.filter_by(
                scanner_id=history.scanner_id
            ).filter(
                ScanResult.timestamp >= history.started_at
            ).all()
        else:
            results = []
    else:
        # Get latest scan results
        latest_scan = ScanHistory.query.order_by(ScanHistory.id.desc()).first()
        if latest_scan:
            results = ScanResult.query.filter_by(
                scanner_id=latest_scan.scanner_id
            ).filter(
                ScanResult.timestamp >= latest_scan.started_at
            ).all()
            scan_id = latest_scan.id
        else:
            results = []
            scan_id = None

    # Process results for comprehensive display (Amibroker-style)
    processed_results = []
    buy_signals = 0
    sell_signals = 0
    no_signals = 0

    for r in results:
        metrics = r.get_metrics() if r.metrics else {}

        # Build processed result based on signal type
        processed = {
            'symbol': r.symbol,
            'signal': r.signal,
            'timestamp': r.timestamp,
            'metrics': metrics  # Keep original metrics
        }

        # Determine scanner type and add appropriate fields
        if r.signal in ['BUY', 'SELL']:
            # Trading signal scanner
            processed.update({
                'close_price': float(metrics.get('close_price', metrics.get('price', metrics.get('ltp', 0)))),
                'entry': float(metrics.get('entry', metrics.get('price', 0))),
                'target': float(metrics.get('target', 0)),
                'stop_loss': float(metrics.get('stop_loss', 0)),
                'risk_reward': float(metrics.get('risk_reward', 0)),
                'ema10': float(metrics.get('ema10', 0)),
                'ema20': float(metrics.get('ema20', 0)),
                'volume': float(metrics.get('volume', 0)),
                'strength': 3
            })
        elif r.signal in ['DATA', 'EXPLORE']:
            # Data exploration scanner
            processed.update({
                'ltp': float(metrics.get('ltp', metrics.get('close_price', 0))),
                'ema10': float(metrics.get('ema10', 0)),
                'ema20': float(metrics.get('ema20', 0)),
                'volume': float(metrics.get('volume', 0)),
                'close_price': float(metrics.get('ltp', metrics.get('close_price', 0)))
            })
            # Add any additional metrics dynamically
            for key, value in metrics.items():
                if key not in processed:
                    processed[key] = value
        else:
            # Generic scanner - include all metrics
            processed.update(metrics)
            processed['close_price'] = float(metrics.get('close_price', metrics.get('price', metrics.get('ltp', 0))))

        # Calculate potential gain and risk percentages ONLY for trading signals
        if r.signal in ['BUY', 'SELL']:
            if processed.get('entry', 0) > 0 and processed.get('target', 0) > 0:
                if r.signal == 'BUY':
                    processed['potential_gain'] = ((processed['target'] - processed['entry']) / processed['entry']) * 100
                    processed['risk'] = abs((processed.get('stop_loss', 0) - processed['entry']) / processed['entry']) * 100 if processed.get('stop_loss', 0) > 0 else 0
                else:  # SELL
                    processed['potential_gain'] = ((processed['entry'] - processed['target']) / processed['entry']) * 100
                    processed['risk'] = abs((processed.get('stop_loss', 0) - processed['entry']) / processed['entry']) * 100 if processed.get('stop_loss', 0) > 0 else 0
            else:
                processed['potential_gain'] = 0
                processed['risk'] = 0

            # Calculate signal strength based on risk-reward ratio
            rr_ratio = processed.get('risk_reward', 0)
            if rr_ratio >= 3:
                processed['strength'] = 5
            elif rr_ratio >= 2:
                processed['strength'] = 4
            elif rr_ratio >= 1.5:
                processed['strength'] = 3
            elif rr_ratio >= 1:
                processed['strength'] = 2
            else:
                processed['strength'] = 1
        else:
            # For DATA/EXPLORE scanners, no risk calculations needed
            processed['potential_gain'] = 0
            processed['risk'] = 0
            processed['strength'] = 0

        # Count signal types
        if r.signal == 'BUY':
            buy_signals += 1
        elif r.signal == 'SELL':
            sell_signals += 1
        elif r.signal in ['DATA', 'EXPLORE']:
            no_signals += 1  # Data rows, not signals
        else:
            no_signals += 1

        processed_results.append(processed)

    # Get scan info
    history = None
    scanner = None
    watchlist = None

    if scan_id:
        history = ScanHistory.query.get(scan_id)
        if history:
            scanner = Scanner.query.get(history.scanner_id)
            watchlist = Watchlist.query.get(history.watchlist_id)

    scan_info = {
        'scanner_name': scanner.name if scanner else 'Unknown Scanner',
        'watchlist_name': watchlist.name if watchlist else 'Unknown Watchlist',
        'timestamp': history.started_at.strftime('%d %b %Y %H:%M') if history and history.started_at else datetime.now().strftime('%d %b %Y %H:%M')
    }

    # Calculate summary statistics
    total_scanned = len(results)

    # Sort for top signals
    buy_results = sorted([r for r in processed_results if r['signal'] == 'BUY'],
                         key=lambda x: x.get('strength', 0), reverse=True)
    sell_results = sorted([r for r in processed_results if r['signal'] == 'SELL'],
                          key=lambda x: x.get('strength', 0), reverse=True)

    summary = {
        'total_scanned': total_scanned,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'no_signals': no_signals,
        'buy_percentage': (buy_signals / total_scanned * 100) if total_scanned > 0 else 0,
        'sell_percentage': (sell_signals / total_scanned * 100) if total_scanned > 0 else 0,
        'no_signal_percentage': (no_signals / total_scanned * 100) if total_scanned > 0 else 0,
        'watchlist_name': scan_info['watchlist_name'],
        'execution_time': history.execution_time if history and hasattr(history, 'execution_time') else 0,
        'avg_signal_strength': sum(r['strength'] for r in processed_results if r['signal'] in ['BUY', 'SELL']) / max(buy_signals + sell_signals, 1) * 20,
        'avg_risk_reward': sum(r['risk_reward'] for r in processed_results if r['signal'] in ['BUY', 'SELL'] and r['risk_reward'] > 0) / max(buy_signals + sell_signals, 1),
        'market_trend': 'Bullish' if buy_signals > sell_signals else 'Bearish' if sell_signals > buy_signals else 'Neutral',
        'top_buy_signals': buy_results[:5],
        'top_sell_signals': sell_results[:5]
    }

    # Check if we have exploration data
    if results and any(r.signal in ['EXPLORE', 'DATA'] for r in results):
        # Redirect to exploration view for EXPLORE/DATA type scanners
        return redirect(url_for('results.exploration_view', scan_id=scan_id))

    return render_template('results/comprehensive.html',
                         results=processed_results,
                         processed_results=processed_results,
                         scan_info=scan_info,
                         summary=summary,
                         scan_id=scan_id,
                         scan=history,
                         scan_status='completed')

@bp.route('/old')
def list_results_old():
    # Keep old view as backup
    # Get filter parameters
    scanner_id = request.args.get('scanner_id', type=int)
    symbol = request.args.get('symbol')
    signal = request.args.get('signal')

    # Build query
    query = ScanResult.query

    if scanner_id:
        query = query.filter_by(scanner_id=scanner_id)
    if symbol:
        query = query.filter_by(symbol=symbol)
    if signal:
        query = query.filter_by(signal=signal)

    # Get recent results
    results = query.order_by(ScanResult.timestamp.desc()).limit(100).all()

    # Get unique signals for filter
    signals = db.session.query(ScanResult.signal).distinct().all()
    signal_types = [s[0] for s in signals if s[0]]

    return render_template('results/list.html',
                         results=results,
                         signal_types=signal_types)

@bp.route('/exploration/<int:scan_id>')
def exploration_view(scan_id):
    """Display exploration-style results with all crossovers"""
    # Get scan history
    history = ScanHistory.query.get_or_404(scan_id)

    # Get scan results
    results = ScanResult.query.filter_by(
        scanner_id=history.scanner_id
    ).filter(
        ScanResult.timestamp >= history.started_at
    ).all()

    # Simply pass all results for exploration display
    # The template will handle the dynamic columns
    exploration_results = results
    stock_summaries = []
    total_buy_signals = 0
    total_sell_signals = 0

    # Count signal types
    for r in results:
        if r.signal == 'BUY':
            total_buy_signals += 1
        elif r.signal == 'SELL':
            total_sell_signals += 1

    # Calculate summary
    summary = {
        'total_scanned': len(results),
        'total_signals': len(results),  # All results are signals in exploration
        'buy_signals': total_buy_signals,
        'sell_signals': total_sell_signals,
        'avg_crossovers': 0  # Not applicable for simple exploration
    }

    # Get scan info
    scanner = Scanner.query.get(history.scanner_id) if history else None
    watchlist = Watchlist.query.get(history.watchlist_id) if history else None

    scan_info = {
        'scanner_name': scanner.name if scanner else 'Unknown',
        'watchlist_name': watchlist.name if watchlist else 'All Stocks',
        'timestamp': history.started_at.strftime('%Y-%m-%d %H:%M') if history else datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    return render_template('results/exploration.html',
                         scan=history,
                         results=results,  # For backward compatibility
                         exploration_results=exploration_results,
                         stock_summaries=stock_summaries,
                         summary=summary,
                         scan_info=scan_info)

# API Endpoints
@bp.route('/api/results/<int:id>', methods=['DELETE'])
def api_delete_result(id):
    result = ScanResult.query.get_or_404(id)
    db.session.delete(result)
    db.session.commit()

    return jsonify({'message': 'Result deleted successfully'})

@bp.route('/api/results/export', methods=['POST'])
def api_export_results():
    data = request.get_json()
    format_type = data.get('format', 'csv')
    scan_id = data.get('scan_id')

    # Get results for scan
    if scan_id:
        history = ScanHistory.query.get(scan_id)
        if history:
            results = ScanResult.query.filter_by(
                scanner_id=history.scanner_id
            ).filter(
                ScanResult.timestamp >= history.started_at
            ).all()
        else:
            results = []
    else:
        results = ScanResult.query.order_by(ScanResult.timestamp.desc()).limit(1000).all()

    if format_type == 'csv':
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Timestamp', 'Symbol', 'Signal', 'Price', 'Entry', 'Target',
                        'Stop Loss', 'Volume', 'EMA10', 'EMA20', 'RSI', 'Risk/Reward'])

        # Write data
        for result in results:
            metrics = result.get_metrics() if result.metrics else {}
            writer.writerow([
                result.timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.timestamp else '',
                result.symbol,
                result.signal,
                metrics.get('price', metrics.get('current_price', '')),
                metrics.get('entry', metrics.get('entry_price', '')),
                metrics.get('target', metrics.get('target_1', '')),
                metrics.get('stop_loss', metrics.get('stoploss', '')),
                metrics.get('volume', ''),
                metrics.get('ema_fast', metrics.get('ema10_current', '')),
                metrics.get('ema_slow', metrics.get('ema20_current', '')),
                metrics.get('rsi', ''),
                metrics.get('risk_reward', '')
            ])

        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=scan_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response

    return jsonify({'error': 'Invalid format'}), 400