import os
import calendar
from datetime import datetime
from itertools import chain
from collections import namedtuple
from pickle import load, dump

from numpy import trim_zeros


from apps.tf_bot.models import Record
from apps.utils.util import PatientRecord
# from helpers.registry_constants import RegistryManager


class RecordData(object):
    """
    This is a helper class used to maintain records state. `Record` model in `apps.tf_bot`
    is actually used to store registered patients records. That model is for an external
    use by admins too. But this class is an internal helper, that simplifies viewing
    days and time intervals available for patients.
    """

    BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PICKLING_FILE = os.path.join(BOT_DIR, 'internal_record_state/../../internal_record_state/record_state')

    @classmethod
    def new_data_set(cls, year, month):
        days_for_data_set = cls._create_calendar(month, year)
        records_in_day = {day: set() for day in days_for_data_set}

        return records_in_day

    def __init__(self, record_data: dict = None):
        internal_record_state_dir = os.path.join(self.BOT_DIR, 'internal_record_state')
        if not os.path.exists(internal_record_state_dir):
            os.makedirs(internal_record_state_dir)

        self.record_data = record_data if record_data is not None else self.load_record_state()

    def dump_record_state(self):
        with open(self.PICKLING_FILE, 'wb') as f:
            dump(self.record_data, f)

    def load_record_state(self):
        with open(self.PICKLING_FILE, 'rb') as f:
            record_state = load(f)

        return record_state

    def check_data_set_actuality(self) -> bool:
        """
        Checks if records data set could be used
        :return: bool, true if data set is actual, false - instead
        """
        now = datetime.now()
        return self.record_data["month"] == now.month

    # def get_keyboard_intervals(self, day, record_type) -> set:
    #     reserved_intervals_in_day: set = self.record_data["records_in_day"][day]
    #
    #     free_intervals_in_day = self.get_free_intervals_in_day(day, reserved_intervals_in_day)
    #
    #     if record_type == Record.REGULAR:
    #         return free_intervals_in_day
    #
    #     return self.generate_double_intervals(free_intervals_in_day)

    # @staticmethod
    # def get_free_intervals_in_day(day: int, reserved_intervals_in_day: set) -> set:
    #     now = datetime.now()
    #     weekday_of_day = datetime(now.year, now.month, day).weekday()
    #
    #     return RegistryManager.AVAILABLE_INTERVALS[weekday_of_day].difference(reserved_intervals_in_day)

    @staticmethod
    def get_record_typed_intervals(record_type, keyboard_intervals: set):
        if record_type == Record.REGULAR:
            return keyboard_intervals

        return RecordData.generate_double_intervals(keyboard_intervals)

    @staticmethod
    def generate_double_intervals(free_intervals: set) -> set:
        """
        Generates double intervals from ordinary intervals.
        The idea is just to take two ordinary intervals.

        :param free_intervals: set of tuples
        :return: set of double intervals
        """
        if len(free_intervals) == 0:
            return free_intervals

        double_intervals = set()
        for interval in free_intervals:
            next_interval = PatientRecord(interval.end, interval.end + 1)
            if next_interval in free_intervals:
                double_intervals.add(PatientRecord(interval.start, interval.end + 1))

        return double_intervals

    @staticmethod
    def _create_calendar(month, year):
        """
        Creates a list of Tuesdays, Fridays, Saturdays of month in the form of dates.
        :return: list of all available for records days
        """
        my_month_calendar = [
            [week[1], week[4], week[5]] for week in calendar.monthcalendar(year, month)
        ]

        merged_my_month_calendar = list(chain.from_iterable(my_month_calendar))
        return trim_zeros(merged_my_month_calendar)
