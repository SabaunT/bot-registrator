from collections import namedtuple

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
