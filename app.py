from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('fluxscan.log')  # File output
    ]
)

# Set specific logger levels
logging.getLogger('services.data_service').setLevel(logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask request logs

# Load environment variables
load_dotenv()

# Import models and services
from models import db
from config import Config

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Import routes after app creation
from routes import (
    main_routes,
    scanner_routes,
    watchlist_routes,
    scan_routes,
    api_routes,
    results_routes,
    schedule_routes
)

# Register blueprints
app.register_blueprint(main_routes.bp)
app.register_blueprint(scanner_routes.bp)
app.register_blueprint(watchlist_routes.bp)
app.register_blueprint(scan_routes.bp)
app.register_blueprint(api_routes.bp)
app.register_blueprint(results_routes.bp)
app.register_blueprint(schedule_routes.bp)

# Initialize services
from services import DataService

# Global data service instance
data_service = None

# Initialize services
data_service = None

def initialize_services():
    global data_service
    if data_service is None:
        data_service = DataService(
            api_key=app.config['OPENALGO_API_KEY'] or 'demo-key',
            host=app.config['OPENALGO_HOST'] or 'http://127.0.0.1:5000'
        )
        app.data_service = data_service

# Initialize on first request using before_request
@app.before_request
def before_request():
    initialize_services()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error='Internal server error'), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to FluxScan WebSocket'})

@socketio.on('disconnect')
def handle_disconnect():
    pass

@socketio.on('subscribe_scan')
def handle_subscribe_scan(data):
    scan_id = data.get('scan_id')
    emit('scan_subscribed', {'scan_id': scan_id})

@socketio.on('unsubscribe_scan')
def handle_unsubscribe_scan(data):
    scan_id = data.get('scan_id')
    emit('scan_unsubscribed', {'scan_id': scan_id})

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.context_processor
def inject_config():
    return {
        'app_name': 'FluxScan',
        'version': '1.0.0'
    }

# CLI commands
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

@app.cli.command()
def seed_db():
    """Seed the database with sample data."""
    from utils.seed_data import seed_database
    seed_database()
    print('Database seeded!')

@app.cli.command()
def clear_cache():
    """Clear all cached data."""
    if data_service:
        data_service.cache.clear()
    print('Cache cleared!')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=app.config['DEBUG']
    )