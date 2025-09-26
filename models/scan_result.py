from .base import db, BaseModel
import json
from datetime import datetime

class ScanResult(BaseModel):
    __tablename__ = 'scan_results'

    scanner_id = db.Column(db.Integer, db.ForeignKey('scanners.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    exchange = db.Column(db.String(10))
    signal = db.Column(db.String(50))
    metrics = db.Column(db.Text)  # JSON object with detailed metrics
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScanResult {self.symbol} - {self.signal}>'

    def get_metrics(self):
        if self.metrics:
            return json.loads(self.metrics)
        return {}

    def set_metrics(self, metrics_dict):
        self.metrics = json.dumps(metrics_dict)

    def to_dict(self):
        data = super().to_dict()
        data['metrics'] = self.get_metrics()
        data['scanner_name'] = self.scanner.name if self.scanner else None
        return data

    @classmethod
    def get_recent_results(cls, limit=100):
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def get_by_symbol(cls, symbol):
        return cls.query.filter_by(symbol=symbol).order_by(cls.timestamp.desc()).all()

    @classmethod
    def get_by_scanner(cls, scanner_id, limit=None):
        query = cls.query.filter_by(scanner_id=scanner_id).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        return cls.query.filter(
            cls.timestamp >= start_date,
            cls.timestamp <= end_date
        ).order_by(cls.timestamp.desc()).all()

    @classmethod
    def cleanup_old_results(cls, days=30):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_results = cls.query.filter(cls.timestamp < cutoff_date).all()
        for result in old_results:
            db.session.delete(result)
        db.session.commit()
        return len(old_results)