from flask import Blueprint, render_template, jsonify
from models import Scanner, Watchlist, ScanResult, ScanHistory
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get dashboard statistics
    active_scanners = Scanner.query.filter_by(is_active=True).count()
    total_watchlists = Watchlist.query.count()

    # Get recent scan results (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_results = ScanResult.query.filter(
        ScanResult.timestamp >= yesterday
    ).order_by(ScanResult.timestamp.desc()).limit(10).all()

    # Get today's signal count
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_signals = ScanResult.query.filter(
        ScanResult.timestamp >= today_start
    ).count()

    # Get yesterday's signal count
    yesterday_start = today_start - timedelta(days=1)
    yesterday_signals = ScanResult.query.filter(
        ScanResult.timestamp >= yesterday_start,
        ScanResult.timestamp < today_start
    ).count()

    # Get running scans
    running_scans = ScanHistory.query.filter_by(status='running').all()

    # Calculate total symbols across all watchlists
    total_symbols = 0
    for watchlist in Watchlist.query.all():
        total_symbols += watchlist.symbol_count()

    return render_template('pages/index.html',
                         active_scanners=active_scanners,
                         total_watchlists=total_watchlists,
                         total_symbols=total_symbols,
                         today_signals=today_signals,
                         yesterday_signals=yesterday_signals,
                         recent_results=recent_results,
                         running_scans=running_scans)

@bp.route('/about')
def about():
    return render_template('pages/about.html')

@bp.route('/help')
def help():
    return render_template('pages/help.html')

@bp.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@bp.route('/api/stats')
def get_stats():
    stats = {
        'scanners': {
            'total': Scanner.query.count(),
            'active': Scanner.query.filter_by(is_active=True).count()
        },
        'watchlists': {
            'total': Watchlist.query.count(),
            'symbols': sum(w.symbol_count() for w in Watchlist.query.all())
        },
        'scans': {
            'total': ScanHistory.query.count(),
            'running': ScanHistory.query.filter_by(status='running').count(),
            'completed': ScanHistory.query.filter_by(status='completed').count(),
            'failed': ScanHistory.query.filter_by(status='failed').count()
        },
        'results': {
            'total': ScanResult.query.count(),
            'today': ScanResult.query.filter(
                ScanResult.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            ).count()
        }
    }

    return jsonify(stats)