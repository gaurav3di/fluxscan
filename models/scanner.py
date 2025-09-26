from .base import db, BaseModel
import json

class Scanner(BaseModel):
    __tablename__ = 'scanners'

    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    code = db.Column(db.Text, nullable=False)
    parameters = db.Column(db.Text)  # JSON string
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    scan_results = db.relationship('ScanResult', backref='scanner', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('ScanSchedule', backref='scanner', lazy='dynamic', cascade='all, delete-orphan')
    histories = db.relationship('ScanHistory', backref='scanner', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Scanner {self.name}>'

    def get_parameters(self):
        if self.parameters:
            return json.loads(self.parameters)
        return {}

    def set_parameters(self, params):
        self.parameters = json.dumps(params)

    def to_dict(self):
        data = super().to_dict()
        data['parameters'] = self.get_parameters()
        data['total_scans'] = self.histories.count()
        data['active_schedules'] = self.schedules.filter_by(is_active=True).count()
        return data

    @classmethod
    def get_by_category(cls, category):
        return cls.query.filter_by(category=category, is_active=True).all()

    @classmethod
    def get_active_scanners(cls):
        return cls.query.filter_by(is_active=True).all()

    def validate_code(self):
        try:
            compile(self.code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, str(e)