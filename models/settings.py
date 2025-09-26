from .base import db
import json
from datetime import datetime

class Settings(db.Model):
    __tablename__ = 'settings'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Settings {self.key}>'

    def get_value(self):
        if self.value:
            try:
                return json.loads(self.value)
            except:
                return self.value
        return None

    def set_value(self, val):
        if isinstance(val, (dict, list)):
            self.value = json.dumps(val)
        else:
            self.value = str(val)

    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.get(key)
        if setting:
            return setting.get_value()
        return default

    @classmethod
    def set(cls, key, value):
        setting = cls.query.get(key)
        if not setting:
            setting = cls(key=key)

        setting.set_value(value)
        setting.updated_at = datetime.utcnow()
        db.session.add(setting)
        db.session.commit()
        return setting

    @classmethod
    def get_all(cls):
        settings = cls.query.all()
        return {s.key: s.get_value() for s in settings}

    @classmethod
    def bulk_update(cls, settings_dict):
        for key, value in settings_dict.items():
            cls.set(key, value)