from datetime import datetime
from django.core.exceptions import ValidationError


class TemporaryData(dict):
    """
    Temporary storage emulating session.

    Structure:
    {
      telegram_id: {
                    record_type: record_type,
                    day: day,
                    start_time: start_time
                    }
    }
    """

    def __init__(self, *args):
        super().__init__(*args)

    def add_user(self, telegram_id: str):
        self[telegram_id] = dict()

    def add_record_type(self, telegram_id: str, record_type: str):
        self[telegram_id]['record_type'] = record_type

    def add_record_day(self, telegram_id: str, day: datetime):
        self[telegram_id]['day'] = day

    def add_record_start_time(self, telegram_id: str, start_time: int):
        # TODO too explicit
        if not start_time in range(9, 22):
            ValidationError('Wrong start time for record')

        self[telegram_id]['start_time'] = start_time

    # Todo метод подготовки к сохранению
