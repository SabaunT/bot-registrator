from datetime import datetime
from collections import namedtuple

from apps.tf_bot.models import Record
from dr_tf_bot.exceptions import UserTelegramError


PatientRecord = namedtuple('Record', ['start', 'end'])


def extend_lists(main_list: list, *lists):
    for each_list in lists:
        main_list.extend(each_list)
    return main_list


def restruct_patient_fields(user_response: str):
    listed_response = user_response.split(' ')

    if len(listed_response) != 3:
        raise UserTelegramError('Invalid input')

    return listed_response


def check_patient_record_ability(user_id: int) -> bool:
    now = datetime.now()

    year = now.year
    month = now.month
    day = now.day

    from_that_day = datetime(year, month, day)
    new_month_start = datetime(year, month + 1, 1)

    try:
        Record.objects.get(patient=user_id, record_start_time__range=(from_that_day, new_month_start))
    except Record.DoesNotExist:
        return True
    else:
        return False
