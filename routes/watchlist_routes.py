from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, make_response
from models import db, Watchlist
import json
import csv
import io

bp = Blueprint('watchlists', __name__, url_prefix='/watchlists')

@bp.route('/')
def list_watchlists():
    watchlists = Watchlist.query.all()
    return render_template('watchlists/list.html', watchlists=watchlists)

# API Endpoints
@bp.route('/api/watchlists', methods=['GET'])
def api_list_watchlists():
    watchlists = Watchlist.query.all()
    return jsonify([w.to_dict() for w in watchlists])

@bp.route('/api/watchlists', methods=['POST'])
def api_create_watchlist():
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    if Watchlist.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Watchlist with this name already exists'}), 400

    watchlist = Watchlist(
        name=data['name'],
        description=data.get('description', ''),
        exchange=data.get('exchange', 'NSE')
    )

    symbols = data.get('symbols', [])
    watchlist.set_symbols(symbols)

    db.session.add(watchlist)
    db.session.commit()

    return jsonify(watchlist.to_dict()), 201

@bp.route('/api/watchlists/<int:id>', methods=['GET'])
def api_get_watchlist(id):
    watchlist = Watchlist.query.get_or_404(id)
    return jsonify(watchlist.to_dict())

@bp.route('/api/watchlists/<int:id>', methods=['PUT'])
def api_update_watchlist(id):
    watchlist = Watchlist.query.get_or_404(id)
    data = request.get_json()

    if 'name' in data:
        existing = Watchlist.query.filter_by(name=data['name']).first()
        if existing and existing.id != id:
            return jsonify({'error': 'Watchlist with this name already exists'}), 400
        watchlist.name = data['name']

    if 'description' in data:
        watchlist.description = data['description']

    if 'symbols' in data:
        watchlist.set_symbols(data['symbols'])

    if 'exchange' in data:
        watchlist.exchange = data['exchange']

    db.session.commit()
    return jsonify(watchlist.to_dict())

@bp.route('/api/watchlists/<int:id>', methods=['DELETE'])
def api_delete_watchlist(id):
    watchlist = Watchlist.query.get_or_404(id)
    db.session.delete(watchlist)
    db.session.commit()
    return jsonify({'message': 'Watchlist deleted successfully'})

@bp.route('/api/watchlists/<int:id>/symbols', methods=['POST'])
def api_add_symbol(id):
    watchlist = Watchlist.query.get_or_404(id)
    data = request.get_json()
    symbol = data.get('symbol')

    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400

    symbols = watchlist.get_symbols()
    if symbol not in symbols:
        symbols.append(symbol)
        watchlist.set_symbols(symbols)
        db.session.commit()

    return jsonify(watchlist.to_dict())

@bp.route('/api/watchlists/<int:id>/symbols/<symbol>', methods=['DELETE'])
def api_remove_symbol(id, symbol):
    watchlist = Watchlist.query.get_or_404(id)
    symbols = watchlist.get_symbols()

    if symbol in symbols:
        symbols.remove(symbol)
        watchlist.set_symbols(symbols)
        db.session.commit()

    return jsonify(watchlist.to_dict())

@bp.route('/api/watchlists/import', methods=['POST'])
def api_import_watchlist():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file.filename.endswith('.csv'):
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)

        symbols = []
        for row in csv_input:
            if row:
                symbols.append(row[0])

        if not symbols:
            return jsonify({'error': 'No symbols found in file'}), 400

        # Create new watchlist with imported symbols
        name = request.form.get('name', 'Imported Watchlist')

        if Watchlist.query.filter_by(name=name).first():
            return jsonify({'error': 'Watchlist with this name already exists'}), 400

        watchlist = Watchlist(
            name=name,
            description=f'Imported from {file.filename}',
            exchange='NSE'
        )
        watchlist.set_symbols(symbols)

        db.session.add(watchlist)
        db.session.commit()

        return jsonify(watchlist.to_dict()), 201

    return jsonify({'error': 'Invalid file format'}), 400

@bp.route('/api/watchlists/<int:id>/export', methods=['GET'])
def api_export_watchlist(id):
    watchlist = Watchlist.query.get_or_404(id)
    symbols = watchlist.get_symbols()

    # Create CSV output
    output = io.StringIO()
    writer = csv.writer(output)

    for symbol in symbols:
        writer.writerow([symbol])

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={watchlist.name}.csv'

    return response