from .base import db, BaseModel
from datetime import datetime, timedelta

class ScanSchedule(BaseModel):
    __tablename__ = 'scan_schedules'

    scanner_id = db.Column(db.Integer, db.ForeignKey('scanners.id'), nullable=False)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    schedule_type = db.Column(db.String(20))  # 'once', 'interval', 'daily', 'weekly'
    interval_minutes = db.Column(db.Integer)
    run_time = db.Column(db.Time)
    days_of_week = db.Column(db.String(20))  # Comma-separated: '1,3,5' for Mon, Wed, Fri
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    market_hours_only = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ScanSchedule {self.scanner.name if self.scanner else "N/A"} - {self.schedule_type}>'

    def calculate_next_run(self):
        now = datetime.utcnow()

        if self.schedule_type == 'once':
            if not self.last_run:
                self.next_run = now
            else:
                self.next_run = None
                self.is_active = False

        elif self.schedule_type == 'interval':
            if self.interval_minutes:
                if self.last_run:
                    self.next_run = self.last_run + timedelta(minutes=self.interval_minutes)
                else:
                    self.next_run = now

        elif self.schedule_type == 'daily':
            if self.run_time:
                next_run = datetime.combine(now.date(), self.run_time)
                if next_run <= now:
                    next_run += timedelta(days=1)
                self.next_run = next_run

        elif self.schedule_type == 'weekly':
            if self.days_of_week and self.run_time:
                days = [int(d) for d in self.days_of_week.split(',')]
                current_weekday = now.weekday()

                # Find next scheduled day
                for i in range(7):
                    check_day = (current_weekday + i) % 7
                    if check_day in days:
                        next_run = datetime.combine(now.date() + timedelta(days=i), self.run_time)
                        if next_run > now:
                            self.next_run = next_run
                            break

    def should_run(self):
        if not self.is_active:
            return False

        now = datetime.utcnow()

        if self.market_hours_only:
            # Check if within market hours (9:15 AM to 3:30 PM IST)
            # Convert to IST (UTC+5:30)
            ist_now = now + timedelta(hours=5, minutes=30)
            market_open = ist_now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = ist_now.replace(hour=15, minute=30, second=0, microsecond=0)

            if not (market_open <= ist_now <= market_close):
                return False

        if self.next_run and now >= self.next_run:
            return True

        return False

    def mark_executed(self):
        self.last_run = datetime.utcnow()
        self.calculate_next_run()

    def to_dict(self):
        data = super().to_dict()
        data['scanner_name'] = self.scanner.name if self.scanner else None
        data['watchlist_name'] = self.watchlist.name if self.watchlist else None
        return data

    @classmethod
    def get_active_schedules(cls):
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_due_schedules(cls):
        schedules = cls.get_active_schedules()
        return [s for s in schedules if s.should_run()]