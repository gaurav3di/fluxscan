from flask import Blueprint, jsonify, request, current_app
from flask_socketio import emit
from models import db, Scanner, Watchlist, ScanResult, ScanHistory
from scanners import ScannerEngine
from datetime import datetime
import threading

bp = Blueprint('scan', __name__, url_prefix='/scan')

# Store running scans
running_scans = {}

@bp.route('/api/scan', methods=['POST'])
def api_run_scan():
    data = request.get_json()

    scanner_id = data.get('scanner_id')
    watchlist_id = data.get('watchlist_id')
    parameters = data.get('parameters', {})

    if not scanner_id or not watchlist_id:
        return jsonify({'error': 'Scanner ID and Watchlist ID are required'}), 400

    scanner = Scanner.query.get(scanner_id)
    watchlist = Watchlist.query.get(watchlist_id)

    if not scanner:
        return jsonify({'error': 'Scanner not found'}), 404

    if not watchlist:
        return jsonify({'error': 'Watchlist not found'}), 404

    # Create scan history record
    history = ScanHistory(
        scanner_id=scanner_id,
        watchlist_id=watchlist_id
    )
    history.start()
    db.session.add(history)
    db.session.commit()

    scan_id = f"scan_{history.id}"

    # Get data service
    data_service = current_app.data_service

    # Create scanner engine
    engine = ScannerEngine(data_service)

    # Store in running scans
    running_scans[scan_id] = {
        'engine': engine,
        'status': 'running',
        'history_id': history.id
    }

    # Progress callback
    def progress_callback(progress, symbol):
        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('scan_progress', {
                'scan_id': scan_id,
                'progress': progress,
                'symbol': symbol
            })

    # Run scan in background thread
    def run_scan():
        try:
            # Merge scanner default parameters with provided parameters
            # Extract default values from parameter definitions if they exist
            raw_params = scanner.get_parameters()
            scan_params = {}

            # Handle both simple values and parameter definitions
            for key, value in raw_params.items():
                if isinstance(value, dict) and 'default' in value:
                    scan_params[key] = value['default']
                else:
                    scan_params[key] = value

            # Update with provided parameters
            scan_params.update(parameters)
            scan_params['exchange'] = watchlist.exchange

            # Execute scan
            result = engine.execute_scanner(
                scanner.code,
                watchlist.get_symbols(),
                scan_params,
                progress_callback
            )

            # Update history
            history_record = ScanHistory.query.get(history.id)
            if result['status'] == 'completed':
                # Save results
                for res in result['results']:
                    scan_result = ScanResult(
                        scanner_id=scanner_id,
                        symbol=res['symbol'],
                        exchange=watchlist.exchange,
                        signal=res['signal'],
                        timestamp=datetime.utcnow()
                    )
                    scan_result.set_metrics(res.get('metrics', {}))
                    db.session.add(scan_result)

                history_record.complete(
                    symbols_scanned=result['total_scanned'],
                    signals_found=result['signals_found']
                )
            else:
                history_record.fail('Scan was cancelled or failed')

            db.session.commit()

            # Emit completion event
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('scan_complete', {
                    'scan_id': scan_id,
                    'status': result['status'],
                    'total_scanned': result['total_scanned'],
                    'signals_found': result['signals_found']
                })

            # Update running scans
            running_scans[scan_id]['status'] = result['status']

        except Exception as e:
            history_record = ScanHistory.query.get(history.id)
            history_record.fail(str(e))
            db.session.commit()

            running_scans[scan_id]['status'] = 'failed'
            running_scans[scan_id]['error'] = str(e)

    # Start background thread
    thread = threading.Thread(target=run_scan)
    thread.start()

    return jsonify({
        'scan_id': scan_id,
        'status': 'running',
        'total_symbols': watchlist.symbol_count()
    })

@bp.route('/api/scan/status/<scan_id>', methods=['GET'])
def api_get_scan_status(scan_id):
    if scan_id not in running_scans:
        return jsonify({'error': 'Scan not found'}), 404

    scan_info = running_scans[scan_id]
    engine = scan_info['engine']

    return jsonify({
        'scan_id': scan_id,
        'status': scan_info['status'],
        'progress': engine.get_progress() if engine else 0,
        'is_running': engine.is_scanning() if engine else False
    })

@bp.route('/api/scan/cancel/<scan_id>', methods=['POST'])
def api_cancel_scan(scan_id):
    if scan_id not in running_scans:
        return jsonify({'error': 'Scan not found'}), 404

    scan_info = running_scans[scan_id]
    engine = scan_info['engine']

    if engine and engine.is_scanning():
        engine.cancel()

        # Update history
        history = ScanHistory.query.get(scan_info['history_id'])
        if history:
            history.cancel()
            db.session.commit()

        return jsonify({'message': 'Scan cancelled successfully'})

    return jsonify({'error': 'Scan is not running'}), 400