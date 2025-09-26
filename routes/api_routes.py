from flask import Blueprint, jsonify, request, current_app
from models import db, ScanResult, Settings
from datetime import datetime, timedelta
import csv
import io

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/results', methods=['GET'])
def get_results():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    scanner_id = request.args.get('scanner_id', type=int)
    symbol = request.args.get('symbol')
    signal = request.args.get('signal')

    query = ScanResult.query

    if scanner_id:
        query = query.filter_by(scanner_id=scanner_id)
    if symbol:
        query = query.filter_by(symbol=symbol)
    if signal:
        query = query.filter_by(signal=signal)

    query = query.order_by(ScanResult.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    results = [r.to_dict() for r in pagination.items]

    return jsonify({
        'results': results,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages
    })

@bp.route('/results/<int:id>', methods=['GET'])
def get_result(id):
    result = ScanResult.query.get_or_404(id)
    return jsonify(result.to_dict())

@bp.route('/results/<int:id>', methods=['DELETE'])
def delete_result(id):
    result = ScanResult.query.get_or_404(id)
    db.session.delete(result)
    db.session.commit()
    return jsonify({'message': 'Result deleted successfully'})

@bp.route('/results/export', methods=['POST'])
def export_results():
    data = request.get_json()
    format = data.get('format', 'csv')
    scanner_id = data.get('scanner_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    query = ScanResult.query

    if scanner_id:
        query = query.filter_by(scanner_id=scanner_id)

    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(ScanResult.timestamp >= start)

    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(ScanResult.timestamp <= end)

    results = query.order_by(ScanResult.timestamp.desc()).limit(
        current_app.config['MAX_EXPORT_ROWS']
    ).all()

    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Timestamp', 'Symbol', 'Exchange', 'Signal', 'Scanner', 'Metrics'])

        # Write data
        for result in results:
            writer.writerow([
                result.timestamp.isoformat(),
                result.symbol,
                result.exchange,
                result.signal,
                result.scanner.name if result.scanner else '',
                str(result.get_metrics())
            ])

        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=scan_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }

    else:
        # JSON format
        data = [r.to_dict() for r in results]
        return jsonify(data)

@bp.route('/symbols/search', methods=['GET'])
def search_symbols():
    query = request.args.get('q', '')
    exchange = request.args.get('exchange', 'NSE')

    if not query:
        return jsonify([])

    data_service = current_app.data_service
    symbols = data_service.search_symbols(query, exchange)

    return jsonify(symbols)

@bp.route('/symbols/validate', methods=['POST'])
def validate_symbol():
    data = request.get_json()
    symbol = data.get('symbol')
    exchange = data.get('exchange', 'NSE')

    if not symbol:
        return jsonify({'valid': False, 'error': 'Symbol is required'}), 400

    data_service = current_app.data_service
    is_valid = data_service.validate_symbol(symbol, exchange)

    return jsonify({'valid': is_valid})

@bp.route('/data/history', methods=['GET'])
def get_history():
    symbol = request.args.get('symbol')
    exchange = request.args.get('exchange', 'NSE')
    interval = request.args.get('interval', 'D')
    lookback = request.args.get('lookback', 100, type=int)

    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400

    data_service = current_app.data_service
    data = data_service.get_historical_data(symbol, exchange, interval, lookback)

    if data is not None:
        return jsonify({
            'symbol': symbol,
            'exchange': exchange,
            'interval': interval,
            'data': data.to_dict(orient='records')
        })

    return jsonify({'error': 'Failed to fetch data'}), 500

@bp.route('/data/intervals', methods=['GET'])
def get_intervals():
    data_service = current_app.data_service
    intervals = data_service.get_available_intervals()
    return jsonify(intervals)

@bp.route('/data/exchanges', methods=['GET'])
def get_exchanges():
    return jsonify({
        'exchanges': ['NSE', 'BSE', 'NFO', 'CDS', 'MCX']
    })

@bp.route('/settings', methods=['GET'])
def get_settings():
    settings = Settings.get_all()
    return jsonify(settings)

@bp.route('/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()

    for key, value in data.items():
        Settings.set(key, value)

    return jsonify({'message': 'Settings updated successfully'})

@bp.route('/settings/openalgo/test', methods=['GET'])
def test_openalgo():
    data_service = current_app.data_service
    is_connected = data_service.test_connection()

    return jsonify({
        'connected': is_connected,
        'message': 'Connection successful' if is_connected else 'Connection failed'
    })

@bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    data_service = current_app.data_service
    data_service.cache.clear()

    return jsonify({'message': 'Cache cleared successfully'})