from .base import db, BaseModel
from datetime import datetime

class ScanHistory(BaseModel):
    __tablename__ = 'scan_history'

    scanner_id = db.Column(db.Integer, db.ForeignKey('scanners.id'), nullable=False)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'))
    status = db.Column(db.String(20))  # 'running', 'completed', 'failed', 'cancelled'
    symbols_scanned = db.Column(db.Integer)
    signals_found = db.Column(db.Integer)
    execution_time_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<ScanHistory {self.id} - {self.status}>'

    def start(self):
        self.status = 'running'
        self.started_at = datetime.now()

    def complete(self, symbols_scanned, signals_found):
        self.status = 'completed'
        self.completed_at = datetime.now()
        self.symbols_scanned = symbols_scanned
        self.signals_found = signals_found

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)

    def fail(self, error_message):
        self.status = 'failed'
        self.completed_at = datetime.now()
        self.error_message = error_message

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)

    def cancel(self):
        self.status = 'cancelled'
        self.completed_at = datetime.now()

    def to_dict(self):
        data = super().to_dict()
        data['scanner_name'] = self.scanner.name if self.scanner else None
        data['watchlist_name'] = self.watchlist.name if self.watchlist else None
        data['execution_time_seconds'] = self.execution_time_ms / 1000 if self.execution_time_ms else None
        return data

    @classmethod
    def get_recent_history(cls, limit=50):
        return cls.query.order_by(cls.started_at.desc()).limit(limit).all()

    @classmethod
    def get_by_scanner(cls, scanner_id):
        return cls.query.filter_by(scanner_id=scanner_id).order_by(cls.started_at.desc()).all()

    @classmethod
    def get_running_scans(cls):
        return cls.query.filter_by(status='running').all()

    @classmethod
    def get_statistics(cls, scanner_id=None):
        query = cls.query.filter_by(status='completed')
        if scanner_id:
            query = query.filter_by(scanner_id=scanner_id)

        histories = query.all()

        if not histories:
            return {
                'total_scans': 0,
                'average_execution_time': 0,
                'total_signals': 0,
                'average_signals_per_scan': 0,
                'success_rate': 0
            }

        total = len(histories)
        total_time = sum(h.execution_time_ms for h in histories if h.execution_time_ms)
        total_signals = sum(h.signals_found for h in histories if h.signals_found)

        # Calculate success rate
        all_query = cls.query
        if scanner_id:
            all_query = all_query.filter_by(scanner_id=scanner_id)
        all_count = all_query.count()

        return {
            'total_scans': total,
            'average_execution_time': total_time / total if total > 0 else 0,
            'total_signals': total_signals,
            'average_signals_per_scan': total_signals / total if total > 0 else 0,
            'success_rate': (total / all_count * 100) if all_count > 0 else 0
        }