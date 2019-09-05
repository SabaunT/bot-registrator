from collections import namedtuple


PatientRecord = namedtuple('Record', ['start', 'end'])


def extend_lists(main_list: list, *lists):
    for each_list in lists:
        main_list.extend(each_list)
    return main_list
