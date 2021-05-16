"""
===============================
Showergel's APScheduler wrapper
===============================

All accesses to APScheduler are wrapped here: scheduler creation, but also
job storage and definition.
"""
from datetime import datetime
import logging
from typing import Type, List, Dict

from sqlalchemy.engine import Engine
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.events import EVENT_JOB_ERROR

from showergel.liquidsoap_connector import Connection

_log = logging.getLogger(__name__)


# Scheduled "jobs" should be independant functions because APS must be able to
# serialize all their parameters (that wouldn't work with self:Scheduler)
def _do_command(command):
    connection = Connection.get()
    result = connection.command(command)
    _log.info("Liquidsoap replied: %s", result)

class Scheduler:
    """
    Only one instance of this class should exist in the Showergel process:
    call :ref:`setup` once, then access the instance with :ref:`get`.
    """

    __instance = None

    @classmethod
    def setup(cls, db_engine:Type[Engine]):
        """
        This should be called once, when starting the program.
        """
        cls.__instance = cls(db_engine)

    @classmethod
    def get(cls):
        """
        This is the only accessor of the programs's ``Scheduler`` instance.
        Return:
            (Scheduler):
        """
        if not cls.__instance:
            raise ValueError("Scheduler.setup() has not been called yet")
        return cls.__instance

    def __init__(self, db_engine:Type[Engine]):
        jobstores = {
            'default': SQLAlchemyJobStore(engine=db_engine)
        }
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.start()

    def _on_job_error(self, event):
        """
        Handles APScheduler's ``EVENT_JOB_ERROR`` by logging the job ID and
        the caught exception, if any.
        """
        _log.critical("Error caught on job#%s scheduled at %s:",
            event.job_id, event.scheduled_run_time)
        if event.exception:
            _log.exception(event.exception)

    def command(self, command:str, when:Type[datetime]) -> str:
        """
        Squedule a Liquidsoap command. It will raise ``KeyError`` if a command
        was already scheduled at given date, or ``ValueError`` if given unusable
        parameters.
        Parameters:
            command (str): a complete Liquidsoap telnet command
            when (datetime):
        Return:
            (str): job identifier
        """
        if when < datetime.now():
            raise ValueError("Please schedule something in the future, given date is in the past")
        if not command:
            raise ValueError("Please provide a non-empty command")
        try:
            job = self.scheduler.add_job(_do_command,
                id=when.isoformat(),
                args=[command],
                trigger='date',
                run_date=when,
            )
        except ConflictingIdError:
            raise KeyError("A job is already scheduled at that time. Remove the existing one first")
        return job.id

    def upcoming(self) -> List[Dict]:
        """
        Return:
            (list): upcoming events descriptions
        """
        events = [
            {
                'event_id': job.id,
                'when': job.trigger.run_date.isoformat(),
                'command': job.args[0],
            } for job in self.scheduler.get_jobs()
        ]
        return events

    def delete(self, event_id):
        """
        May raise KeyError if ``event_id`` does not exists
        """
        try:
            self.scheduler.remove_job(event_id)
        except JobLookupError:
            raise KeyError("Event not found")
