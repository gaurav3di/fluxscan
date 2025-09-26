from .base import db, BaseModel
import json

class ScannerTemplate(BaseModel):
    __tablename__ = 'scanner_templates'

    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    code = db.Column(db.Text, nullable=False)
    default_parameters = db.Column(db.Text)  # JSON string

    def __repr__(self):
        return f'<ScannerTemplate {self.name}>'

    def get_parameters(self):
        if self.default_parameters:
            return json.loads(self.default_parameters)
        return {}

    def set_parameters(self, params):
        self.default_parameters = json.dumps(params)

    def to_dict(self):
        data = super().to_dict()
        data['default_parameters'] = self.get_parameters()
        return data

    @classmethod
    def get_by_category(cls, category):
        return cls.query.filter_by(category=category).all()

    def create_scanner(self, scanner_name, custom_params=None):
        from .scanner import Scanner

        scanner = Scanner(
            name=scanner_name,
            description=f"Created from template: {self.name}",
            code=self.code,
            category=self.category,
            is_active=True
        )

        # Merge default and custom parameters
        params = self.get_parameters()
        if custom_params:
            params.update(custom_params)
        scanner.set_parameters(params)

        return scanner