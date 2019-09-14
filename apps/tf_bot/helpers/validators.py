from datetime import datetime

from django.core.exceptions import ValidationError


def date_field_validator(day: datetime):
    valid_intervals = {
        1: set(range(9, 16)),
        4: set(range(9, 16)),
        5: set(range(12, 21))
    }

    if day.weekday() not in valid_intervals.keys():
        raise ValidationError('Chosen day is not valid.')

    if day.hour not in valid_intervals[day.weekday()]:
        raise ValidationError('Wrong time interval')
