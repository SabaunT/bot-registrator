from datetime import datetime
from django.core.exceptions import ValidationError


class TemporaryData(dict):
    """
    Data for TemporarySession object:

    {
      record_type: record_type,
      patient_type: patient_type (primary, secondary)
      day: day,
      start_time: start_time
    }
    """

    _ATTRIBUTES = {'patient_type', 'record_type', 'day', 'start_time'}

    def __init__(self):
        super().__init__()

    def __getattr__(self, item):
        if item in self._ATTRIBUTES:
            return self.__getitem__(item)

        raise AttributeError(f'Key {item} is forbidden')

    def __setattr__(self, key, value):
        if key in self._ATTRIBUTES:
            self.__setitem__(key, value)
        else:
            raise AttributeError(f'Key {key} is forbidden')


class TemporarySession(dict):
    """
    Object emulating session.

    Structure:
    {
      telegram_id: {
                      TemporaryData()
                    }
    }
    """

    def __init__(self, *args):
        super().__init__(*args)

    def add_user(self, telegram_id: str) -> TemporaryData:
        self[telegram_id] = TemporaryData()
        return self[telegram_id]

    def clear_session(self, telegram_id: str):
        del self[telegram_id]

    # Todo метод подготовки к сохранению
