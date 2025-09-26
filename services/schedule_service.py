from typing import List, Optional, Dict, Any
from models import ScanSchedule, Scanner, Watchlist, ScanHistory
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ScheduleService:
    def __init__(self, scanner_service):
        self.scanner_service = scanner_service
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def create_schedule(self, scanner_id: int, watchlist_id: int,
                       schedule_type: str, **kwargs) -> ScanSchedule:
        # Validate scanner and watchlist
        scanner = Scanner.get_by_id(scanner_id)
        watchlist = Watchlist.get_by_id(watchlist_id)

        if not scanner or not watchlist:
            raise ValueError("Invalid scanner or watchlist")

        # Create schedule
        schedule = ScanSchedule(
            scanner_id=scanner_id,
            watchlist_id=watchlist_id,
            schedule_type=schedule_type,
            is_active=True
        )

        # Set schedule-specific parameters
        if schedule_type == 'interval':
            schedule.interval_minutes = kwargs.get('interval_minutes', 60)
        elif schedule_type == 'daily':
            schedule.run_time = kwargs.get('run_time')
        elif schedule_type == 'weekly':
            schedule.days_of_week = kwargs.get('days_of_week')
            schedule.run_time = kwargs.get('run_time')

        schedule.market_hours_only = kwargs.get('market_hours_only', True)
        schedule.calculate_next_run()
        schedule.save()

        # Add to scheduler
        self._add_to_scheduler(schedule)

        return schedule

    def update_schedule(self, schedule_id: int, **kwargs) -> ScanSchedule:
        schedule = ScanSchedule.get_by_id(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        # Remove from scheduler
        self._remove_from_scheduler(schedule_id)

        # Update fields
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        schedule.calculate_next_run()
        schedule.save()

        # Re-add to scheduler if active
        if schedule.is_active:
            self._add_to_scheduler(schedule)

        return schedule

    def toggle_schedule(self, schedule_id: int, is_active: bool) -> ScanSchedule:
        schedule = ScanSchedule.get_by_id(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        schedule.is_active = is_active
        schedule.save()

        if is_active:
            self._add_to_scheduler(schedule)
        else:
            self._remove_from_scheduler(schedule_id)

        return schedule

    def execute_scheduled_scan(self, schedule_id: int):
        schedule = ScanSchedule.get_by_id(schedule_id)
        if not schedule or not schedule.is_active:
            return

        try:
            # Check if should run (market hours, etc.)
            if not schedule.should_run():
                logger.info(f"Schedule {schedule_id} skipped - outside market hours")
                return

            # Create history record
            history = ScanHistory(
                scanner_id=schedule.scanner_id,
                watchlist_id=schedule.watchlist_id
            )
            history.start()
            history.save()

            # Get watchlist symbols
            watchlist = Watchlist.get_by_id(schedule.watchlist_id)
            symbols = watchlist.get_symbols()

            # Execute scan
            result = self.scanner_service.execute_scanner(
                schedule.scanner_id,
                symbols
            )

            # Update history
            if result['status'] == 'completed':
                history.complete(
                    symbols_scanned=result['total_scanned'],
                    signals_found=result['signals_found']
                )
            else:
                history.fail('Scheduled scan failed')

            history.save()

            # Update schedule
            schedule.mark_executed()
            schedule.save()

            logger.info(f"Scheduled scan {schedule_id} completed successfully")

        except Exception as e:
            logger.error(f"Error executing scheduled scan {schedule_id}: {e}")

    def _add_to_scheduler(self, schedule: ScanSchedule):
        job_id = f"schedule_{schedule.id}"

        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Add new job based on schedule type
        if schedule.schedule_type == 'interval':
            trigger = IntervalTrigger(minutes=schedule.interval_minutes)
        elif schedule.schedule_type == 'daily':
            if schedule.run_time:
                trigger = CronTrigger(
                    hour=schedule.run_time.hour,
                    minute=schedule.run_time.minute
                )
            else:
                return
        elif schedule.schedule_type == 'weekly':
            if schedule.run_time and schedule.days_of_week:
                trigger = CronTrigger(
                    day_of_week=schedule.days_of_week,
                    hour=schedule.run_time.hour,
                    minute=schedule.run_time.minute
                )
            else:
                return
        else:
            return

        self.scheduler.add_job(
            func=self.execute_scheduled_scan,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True
        )

    def _remove_from_scheduler(self, schedule_id: int):
        job_id = f"schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def get_due_schedules(self) -> List[ScanSchedule]:
        return ScanSchedule.get_due_schedules()

    def get_schedule_history(self, schedule_id: int) -> List[ScanHistory]:
        schedule = ScanSchedule.get_by_id(schedule_id)
        if not schedule:
            return []

        return ScanHistory.query.filter_by(
            scanner_id=schedule.scanner_id,
            watchlist_id=schedule.watchlist_id
        ).order_by(ScanHistory.started_at.desc()).limit(50).all()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()