from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, current_app
from models import db, Scanner, ScannerTemplate
from scanners.validator import ScannerValidator
import json

bp = Blueprint('scanners', __name__, url_prefix='/scanners')

@bp.route('/')
def list_scanners():
    scanners = Scanner.query.all()
    categories = db.session.query(Scanner.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template('scanners/list.html',
                         scanners=scanners,
                         categories=categories)

@bp.route('/new')
def new_scanner():
    templates = ScannerTemplate.query.all()
    return render_template('scanners/edit.html',
                         scanner=None,
                         templates=templates)

@bp.route('/edit/<int:id>')
def edit_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    templates = ScannerTemplate.query.all()
    return render_template('scanners/edit.html',
                         scanner=scanner,
                         templates=templates)

@bp.route('/test/<int:id>')
def test_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    return render_template('scanners/test.html', scanner=scanner)

@bp.route('/execute')
def execute_scan():
    from models import Watchlist
    scanners = Scanner.query.filter_by(is_active=True).all()
    watchlists = Watchlist.query.all()
    return render_template('scan/execute.html',
                         scanners=scanners,
                         watchlists=watchlists)

# API Endpoints
@bp.route('/api/scan', methods=['POST'])
def api_execute_scan():
    """Execute a scan with selected parameters including timeframe"""
    from models import Watchlist, ScanResult, ScanHistory
    from scanners import ScannerEngine
    from datetime import datetime
    import threading

    data = request.get_json()

    scanner_id = data.get('scanner_id')
    watchlist_id = data.get('watchlist_id')
    parameters = data.get('parameters', {})

    if not scanner_id or not watchlist_id:
        return jsonify({'error': 'Scanner ID and Watchlist ID are required'}), 400

    scanner = Scanner.query.get(scanner_id)
    watchlist = Watchlist.query.get(watchlist_id)

    if not scanner or not watchlist:
        return jsonify({'error': 'Scanner or Watchlist not found'}), 404

    # Create scan history
    history = ScanHistory(
        scanner_id=scanner_id,
        watchlist_id=watchlist_id
    )
    history.start()
    db.session.add(history)
    db.session.commit()

    scan_id = f"scan_{history.id}"
    history_id = history.id  # Store the ID before passing to thread

    # Run scan asynchronously with app context
    def run_scan(app, history_id):
        with app.app_context():
            try:
                # Re-fetch objects in this context
                scanner = Scanner.query.get(scanner_id)
                watchlist = Watchlist.query.get(watchlist_id)
                history = ScanHistory.query.get(history_id)

                data_service = app.data_service
                engine = ScannerEngine(data_service)

                # Get symbols from watchlist
                symbols = watchlist.get_symbol_list() if hasattr(watchlist, 'get_symbol_list') else watchlist.get_symbols()

                # Execute scanner with parameters including interval
                result = engine.execute_scanner(
                    scanner.code,
                    symbols,
                    parameters
                )

                # Save results
                if result['status'] == 'completed':
                    for res in result['results']:
                        scan_result = ScanResult(
                            scanner_id=scanner_id,
                            symbol=res['symbol'],
                            exchange=parameters.get('exchange', 'NSE'),
                            signal=res['signal'],
                            timestamp=datetime.now()
                        )
                        scan_result.set_metrics(res.get('metrics', {}))
                        db.session.add(scan_result)

                    history.complete(
                        symbols_scanned=result['total_scanned'],
                        signals_found=result['signals_found']
                    )
                else:
                    history.fail('Scan failed or was cancelled')

                db.session.commit()

            except Exception as e:
                print(f"Scan error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Try to update history if it exists
                if 'history' in locals() and history:
                    history.fail(str(e))
                    db.session.commit()
                else:
                    # Create a new connection to update the history
                    try:
                        history = ScanHistory.query.get(history_id)
                        if history:
                            history.fail(str(e))
                            db.session.commit()
                    except:
                        pass

    # Pass the app instance and history_id to the thread
    thread = threading.Thread(target=run_scan, args=(current_app._get_current_object(), history_id))
    thread.start()

    return jsonify({
        'status': 'success',
        'scan_id': scan_id,
        'message': 'Scan started successfully'
    })

@bp.route('/api/scan/<scan_id>/status', methods=['GET'])
def api_scan_status(scan_id):
    """Get scan status and results"""
    from models import ScanHistory, ScanResult

    # Extract history ID from scan_id
    history_id = int(scan_id.replace('scan_', ''))
    history = ScanHistory.query.get(history_id)

    if not history:
        return jsonify({'error': 'Scan not found'}), 404

    # Get results if completed
    results = []
    if history.status == 'completed':
        scan_results = ScanResult.query.filter_by(scanner_id=history.scanner_id)\
            .filter(ScanResult.timestamp >= history.started_at).all()
        results = [r.to_dict() for r in scan_results]

    return jsonify({
        'scan_id': scan_id,
        'status': history.status,
        'progress': 100 if history.status == 'completed' else 50,
        'results': results,
        'symbols_scanned': history.symbols_scanned,
        'signals_found': history.signals_found
    })

@bp.route('/api/scanners', methods=['GET'])
def api_list_scanners():
    scanners = Scanner.query.all()
    return jsonify([s.to_dict() for s in scanners])

@bp.route('/api/scanners', methods=['POST'])
def api_create_scanner():
    data = request.get_json()

    # Validate required fields
    if not data.get('name') or not data.get('code'):
        return jsonify({'error': 'Name and code are required'}), 400

    # Check for duplicate name
    if Scanner.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Scanner with this name already exists'}), 400

    # Validate scanner code
    validator = ScannerValidator()
    is_valid, errors, warnings = validator.validate(data['code'])

    if not is_valid:
        return jsonify({
            'error': 'Scanner code validation failed',
            'errors': errors,
            'warnings': warnings
        }), 400

    # Create scanner
    scanner = Scanner(
        name=data['name'],
        description=data.get('description', ''),
        code=data['code'],
        category=data.get('category', 'custom'),
        is_active=data.get('is_active', True)
    )

    if data.get('parameters'):
        scanner.set_parameters(data['parameters'])

    db.session.add(scanner)
    db.session.commit()

    return jsonify(scanner.to_dict()), 201

@bp.route('/api/scanners/<int:id>', methods=['GET'])
def api_get_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    return jsonify(scanner.to_dict())

@bp.route('/api/scanners/<int:id>', methods=['PUT'])
def api_update_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    data = request.get_json()

    # Validate code if provided
    if 'code' in data:
        validator = ScannerValidator()
        is_valid, errors, warnings = validator.validate(data['code'])

        if not is_valid:
            return jsonify({
                'error': 'Scanner code validation failed',
                'errors': errors,
                'warnings': warnings
            }), 400

        scanner.code = data['code']

    # Update other fields
    if 'name' in data:
        # Check for duplicate name
        existing = Scanner.query.filter_by(name=data['name']).first()
        if existing and existing.id != id:
            return jsonify({'error': 'Scanner with this name already exists'}), 400
        scanner.name = data['name']

    if 'description' in data:
        scanner.description = data['description']

    if 'category' in data:
        scanner.category = data['category']

    if 'is_active' in data:
        scanner.is_active = data['is_active']

    if 'parameters' in data:
        scanner.set_parameters(data['parameters'])

    db.session.commit()
    return jsonify(scanner.to_dict())

@bp.route('/api/scanners/<int:id>', methods=['DELETE'])
def api_delete_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    db.session.delete(scanner)
    db.session.commit()
    return jsonify({'message': 'Scanner deleted successfully'})

@bp.route('/api/scanners/<int:id>/test', methods=['POST'])
def api_test_scanner(id):
    scanner = Scanner.query.get_or_404(id)
    data = request.get_json()

    # Get test symbols
    test_symbols = data.get('symbols', ['RELIANCE', 'TCS', 'INFY'])
    test_params = data.get('parameters', scanner.get_parameters())

    # Get data service
    data_service = current_app.data_service

    # Create scanner engine
    from scanners import ScannerEngine
    engine = ScannerEngine(data_service)

    # Execute scanner
    result = engine.execute_scanner(
        scanner.code,
        test_symbols,
        test_params
    )

    return jsonify(result)

@bp.route('/api/scanners/<int:id>/clone', methods=['POST'])
def api_clone_scanner(id):
    original = Scanner.query.get_or_404(id)
    data = request.get_json()

    new_name = data.get('name', f"{original.name} (Copy)")

    # Check for duplicate name
    if Scanner.query.filter_by(name=new_name).first():
        return jsonify({'error': 'Scanner with this name already exists'}), 400

    # Create clone
    scanner = Scanner(
        name=new_name,
        description=original.description,
        code=original.code,
        category=original.category,
        is_active=True
    )

    if original.parameters:
        scanner.parameters = original.parameters

    db.session.add(scanner)
    db.session.commit()

    return jsonify(scanner.to_dict()), 201

@bp.route('/api/scanners/validate', methods=['POST'])
def api_validate_scanner():
    data = request.get_json()
    code = data.get('code', '')

    validator = ScannerValidator()
    is_valid, errors, warnings = validator.validate(code)

    return jsonify({
        'is_valid': is_valid,
        'errors': errors,
        'warnings': warnings
    })