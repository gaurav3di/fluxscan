from flask import Blueprint, render_template, jsonify, request
from models import db, ScanSchedule, Scanner, Watchlist

bp = Blueprint('schedules', __name__, url_prefix='/schedules')

@bp.route('/')
def list_schedules():
    schedules = ScanSchedule.query.all()
    scanners = Scanner.query.filter_by(is_active=True).all()
    watchlists = Watchlist.query.all()

    return render_template('schedules/list.html',
                         schedules=schedules,
                         scanners=scanners,
                         watchlists=watchlists)

# API Endpoints
@bp.route('/api/schedules', methods=['GET'])
def api_list_schedules():
    schedules = ScanSchedule.query.all()
    return jsonify([s.to_dict() for s in schedules])

@bp.route('/api/schedules', methods=['POST'])
def api_create_schedule():
    data = request.get_json()

    schedule = ScanSchedule(
        scanner_id=data['scanner_id'],
        watchlist_id=data['watchlist_id'],
        schedule_type=data['schedule_type'],
        is_active=data.get('is_active', True)
    )

    if data['schedule_type'] == 'interval':
        schedule.interval_minutes = data.get('interval_minutes', 60)
    elif data['schedule_type'] == 'daily':
        schedule.run_time = data.get('run_time')

    schedule.market_hours_only = data.get('market_hours_only', True)
    schedule.calculate_next_run()

    db.session.add(schedule)
    db.session.commit()

    return jsonify(schedule.to_dict()), 201

@bp.route('/api/schedules/<int:id>/toggle', methods=['POST'])
def api_toggle_schedule(id):
    schedule = ScanSchedule.query.get_or_404(id)
    schedule.is_active = not schedule.is_active
    db.session.commit()

    return jsonify({'status': 'success', 'is_active': schedule.is_active})

@bp.route('/api/schedules/<int:id>', methods=['DELETE'])
def api_delete_schedule(id):
    schedule = ScanSchedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()

    return jsonify({'message': 'Schedule deleted successfully'})