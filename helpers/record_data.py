import os
import calendar
from datetime import datetime
from itertools import chain
from pickle import load, dump

from numpy import trim_zeros

from apps.tf_bot.models import Record
from helpers.registry_constants import Registry


class RecordData(object):
    """
    This is a helper class used to maintain records state. `Record` model in `apps.tf_bot`
    is actually used to store registered patients records. That model is for an external
    use by admins too. But this class is an internal helper, that simplifies viewing
    days and time intervals available for patients.
    """

    BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PICKLING_FILE = os.path.join(BOT_DIR, 'internal_record_state/record_state')

    @classmethod
    def new_data_set(cls, year, month):
        days_for_data_set = cls._create_calendar(month, year)
        records_in_day = dict.fromkeys(days_for_data_set, set())

        record_data = {
            "month": month,
            "records_in_day": records_in_day
        }

        return cls(record_data)

    def __init__(self, record_data: dict = None):
        internal_record_state_dir = os.path.join(self.BOT_DIR, 'internal_record_state')
        if not os.path.exists(internal_record_state_dir):
            os.makedirs(internal_record_state_dir)

        self.record_data = record_data if record_data is not None else self.load_record_state()

    def check_data_set_actuality(self) -> bool:
        """
        Checks if records data set could be used
        :return: bool, true if data set is actual, false - instead
        """
        now = datetime.now()
        return self.record_data["month"] == now.month

    def get_intervals(self, day, record_type):
        reserved_intervals_in_day: set = self.record_data["records_in_day"][day]

        now = datetime.now()
        weekday_of_day = datetime(now.year, now.month, day).weekday()
        free_intervals_in_day = Registry.AVAILABLE_RECORDS[weekday_of_day].difference(reserved_intervals_in_day)

        if record_type == Record.REGULAR:
            print('continue logic')

    def dump_record_state(self):
        with open(self.PICKLING_FILE, 'wb') as f:
            dump(self.record_data, f)

    def load_record_state(self):
        with open(self.PICKLING_FILE, 'rb') as f:
            record_state = load(f)

        return record_state

    @classmethod
    def _create_calendar(cls, month, year):
        """
        Creates a list of Tuesdays, Fridays, Saturdays of month in the form of dates.
        :return: list of all available for records days
        """
        my_month_calendar = [
            [week[1], week[4], week[5]] for week in calendar.monthcalendar(year, month)
        ]

        merged_my_month_calendar = list(chain.from_iterable(my_month_calendar))
        return trim_zeros(merged_my_month_calendar)


if __name__ == '__main__':
    a = RecordData.new_data_set(2019, 9)
    print(a.record_data)
    a.dump_record_state()

    b = RecordData()
    print(b.record_data)
