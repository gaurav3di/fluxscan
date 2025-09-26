from flask import Blueprint, render_template, jsonify, request, make_response
from models import db, ScanResult
from datetime import datetime, timedelta
import csv
import io

bp = Blueprint('results', __name__, url_prefix='/results')

@bp.route('/')
def list_results():
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

    # Get filter parameters if provided
    scanner_id = data.get('scanner_id')
    symbol = data.get('symbol')
    signal = data.get('signal')

    # Build query
    query = ScanResult.query

    if scanner_id:
        query = query.filter_by(scanner_id=scanner_id)
    if symbol:
        query = query.filter_by(symbol=symbol)
    if signal:
        query = query.filter_by(signal=signal)

    results = query.order_by(ScanResult.timestamp.desc()).all()

    if format_type == 'csv':
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Timestamp', 'Symbol', 'Signal', 'Scanner', 'Price', 'Volume', 'Signal Strength'])

        # Write data
        for result in results:
            metrics = result.get_metrics()
            writer.writerow([
                result.timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.timestamp else '',
                result.symbol,
                result.signal,
                result.scanner.name if result.scanner else '',
                metrics.get('price', ''),
                metrics.get('volume', ''),
                metrics.get('signal_strength', '')
            ])

        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=scan_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response

    return jsonify({'error': 'Invalid format'}), 400