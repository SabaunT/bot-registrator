from datetime import datetime

from django.core.exceptions import ValidationError


def day_of_week_validator(day: datetime):
    valid_days_of_week = {1, 4, 5}
    if day.weekday() not in valid_days_of_week:
        raise ValidationError('Chosen day is not valid.')


def record_interval_validator(record: datetime):
    valid_intervals = {
        1: set(range(9, 16)),
        4: set(range(9, 16)),
        5: set(range(12, 21))
    }

    # todo перенеси подобную проверку
    # if record_start.weekday() != record_end.weekday():
    #     raise ValidationError('End of the interval can not be less than start')

    record_week_day = record.weekday()
    if record.hour not in valid_intervals[record_week_day]:
        raise ValidationError('Wrong time interval')
