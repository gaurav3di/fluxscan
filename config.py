import os
from datetime import timedelta
from dotenv import load_dotenv, dotenv_values

# Load .env file with override=True to prioritize .env over system env
load_dotenv(override=True)

# Also directly load .env values to ensure we get file values
env_file_values = dotenv_values('.env')

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///fluxscan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OpenAlgo - PRIORITIZE .env file over system environment
    OPENALGO_API_KEY = env_file_values.get('OPENALGO_API_KEY') or os.environ.get('OPENALGO_API_KEY')
    OPENALGO_HOST = env_file_values.get('OPENALGO_HOST') or os.environ.get('OPENALGO_HOST', 'http://127.0.0.1:5000')

    # Scanning
    MAX_CONCURRENT_SCANS = int(os.environ.get('MAX_CONCURRENT_SCANS', 10))
    DEFAULT_LOOKBACK_DAYS = int(os.environ.get('DEFAULT_LOOKBACK_DAYS', 100))
    SCAN_TIMEOUT = int(os.environ.get('SCAN_TIMEOUT', 30))
    MIN_VOLUME_FILTER = int(os.environ.get('MIN_VOLUME_FILTER', 100000))

    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Kolkata'
    SCHEDULER_JOBSTORES = {
        'default': {
            'type': 'sqlalchemy',
            'url': os.environ.get('DATABASE_URL') or 'sqlite:///fluxscan.db'
        }
    }
    SCHEDULER_EXECUTORS = {
        'default': {
            'type': 'threadpool',
            'max_workers': 20
        }
    }
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }

    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # Results
    RESULTS_PER_PAGE = int(os.environ.get('RESULTS_PER_PAGE', 50))
    MAX_EXPORT_ROWS = int(os.environ.get('MAX_EXPORT_ROWS', 10000))

    # WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'

    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)