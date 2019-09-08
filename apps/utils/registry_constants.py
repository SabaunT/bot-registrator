import calendar
from datetime import datetime
from itertools import chain
from typing import NamedTuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from numpy import trim_zeros

from apps.tf_bot.models import Record
from apps.utils.util import PatientRecord, extend_lists


class RegistryManager:
    GREETING_MAIN = f'\n\nЕсли в процессе взаимодействия со мной вы ошибетесь, то используйте команду /cancel для отмены действий.'

    PRIMARY_GREETING = f'Вас приветствует бот - регистратор доктора Тараки Фердауса! Напишите ваше имя, фамилию и номер телефона последовательно через 1 пробел. Не используйте пробелы при написании ваших данных. Если ваше имя или фамилия состоят из нескольких слов, то используйте тире. '
    SECONDARY_GREETING = f'Рад видеть Вас снова. '
    CHOOSE_RECORD_TYPE = f'Выберите тип записи.'
    REPLY_RECORD_TYPE = [['Обычная', 'Расширенная']]

    APPOINTMENT = {
        'Обычная': {'primary': 'Стоимость первичной консультации 500р. ',
                    'secondary': 'Инфа про повторный обычный'
                    },
        'Расширенная': {
            'primary': 'Составляется подробный план лечения, высылающийся в виде вордовского файла по почте. Стоимость 2000р. При продолжении лечения по рекомендуемому плану, его стоимость идет в счет лечения. В случае, если Пациент отказывается от рекомендованного плана и составляется альтернативный план лечения, такой перерасчет не происходит. ',
            'secondary': 'Инфа про повторый расширенный'
            },
    }

    END_REGISTRY = 'Стоимость любой работы сообщается ТОЛЬКО после составления плана лечения, для которого нужен комплекс диагностических мероприятий. Ни по телефону, ни при помощи чатов диагнозы не ставятся, расчет стоимости лечения не проводится (ни примерный, ни точный).'


    @classmethod
    def greeting(cls, *, is_new: bool = True) -> str:
        greeting = cls.GREETING_MAIN
        if is_new:
            return cls.PRIMARY_GREETING + greeting
        return cls.SECONDARY_GREETING + cls.CHOOSE_RECORD_TYPE + greeting

    @classmethod
    def choose_record_type(cls):
        return cls.CHOOSE_RECORD_TYPE

    @classmethod
    def get_reply_record_type(cls):
        return cls.REPLY_RECORD_TYPE

    @classmethod
    def record_info(cls, record_type: str, patient_type: str) -> str:
        return cls.APPOINTMENT[record_type][patient_type]

    @classmethod
    def end_registry(cls):
        return cls.END_REGISTRY

    @classmethod
    def generate_calendar(cls, record_type: str):
        """
        Create an inline keyboard with the provided year and month
        :param str record_type: type of record: either regular or extended
        :return: Returns the InlineKeyboardMarkup object with the calendar.
        """
        now = datetime.now()
        formed_calendar = list()

        # First two rows in telegram calendar object
        year_and_weekdays_rows = cls._create_support_rows(now)

        days_rows = cls._create_available_days_row(record_type, now)

        return InlineKeyboardMarkup(extend_lists(formed_calendar, year_and_weekdays_rows, days_rows))

    @classmethod
    def generate_available_intervals(cls, year: int, month: int) -> dict:
        available_intervals_template = cls._new_data_set(year, month)

        for day in available_intervals_template.keys():
            weekday_of_day = datetime(year, month, day).weekday()

            if weekday_of_day in {1, 4}:
                intervals_range = range(9, 15)
            elif weekday_of_day == 5:
                intervals_range = range(12, 20)
            else:
                raise Exception('tmp exception') # todo temp

            available_intervals_template[day] = {PatientRecord(h, h+1) for h in intervals_range}

        return available_intervals_template

    @classmethod
    def get_reserved_intervals(cls, year, month):
        min_for_query = datetime(year, month, 1, 0, 0, 0)
        max_for_query = datetime(year, month + 1, 1, 0, 0, 0)

        reserved_intervals = Record.objects.filter(record_end_time__range=(min_for_query, max_for_query))

        return cls._restructure_reserved_intervals(year, month, reserved_intervals)

    @classmethod
    def _create_available_days_row(cls, record_type: str, now: datetime.now()):
        """
        Может вернуть пустой массив, что означает, что сообщение должно быть соответствующим
        :param record_type:
        :return:
        """
        year = now.year
        month = now.month
        current_day = now.day

        # for buttons with no actions
        data_ignore = cls._create_callback_data("IGNORE", year, month, 0)

        available_intervals = cls.generate_available_intervals(year, month)
        reserved_intervals = cls.get_reserved_intervals(year, month)

        keyboard_days = list()
        my_base_calendar: list = cls._create_base_calendar(year, month)
        for week in my_base_calendar:
            days_row = list()
            for day in week:
                if day == 0 or day <= current_day:
                    days_row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
                else:
                    free_typed_intervals_in_day = cls.get_keyboard_typed_intervals_in_day(
                        available_intervals,
                        reserved_intervals,
                        record_type,
                        day
                    )
                    if len(free_typed_intervals_in_day) != 0:
                        data_process = cls._create_callback_data("DAY", year, month, day)
                        days_row.append(InlineKeyboardButton(day, callback_data=data_process))

            keyboard_days.append(days_row)

        return keyboard_days

    @classmethod
    def _restructure_reserved_intervals(cls, year, month, reserved_intervals):
        reserved_intervals_template_set = cls._new_data_set(year, month)

        for reserved_interval in reserved_intervals:
            interval_start_hour = reserved_interval.record_start_time.hour
            interval_end_hour = reserved_interval.record_end_time.hour

            if interval_end_hour - interval_start_hour == 2:
                adding_intervals = [PatientRecord(interval_start_hour + i, interval_end_hour + i) for i in range(2)]
            else:
                adding_intervals = [PatientRecord(interval_start_hour, interval_end_hour)]
            reserved_intervals_template_set[reserved_interval.record_start_time.day].update(adding_intervals)

        return reserved_intervals_template_set

    @classmethod
    def _create_support_rows(cls, now: datetime.now()) -> [list, list]:
        year = now.year
        month = now.month

        # for buttons with no actions
        data_ignore = cls._create_callback_data("IGNORE", year, month, 0)

        year_month_row = list()
        year_and_month_keyboard = InlineKeyboardButton(
            calendar.month_name[month] + " " + str(year),
            callback_data=data_ignore
        )
        year_month_row.append(year_and_month_keyboard)

        week_days_row = list()
        for day in ["Tu", "Fr", "Sa"]:
            week_days_row.append(InlineKeyboardButton(day, callback_data=data_ignore))

        return [year_month_row, week_days_row]

    @classmethod
    def get_keyboard_typed_intervals_in_day(
            cls, available_intervals: {int: NamedTuple}, reserved_interval, record_type: str, day: int
    ):
        keyboard_intervals_in_day = cls._get_keyboard_intervals_in_day(available_intervals, reserved_interval, day)

        if record_type == Record.REGULAR:
            return keyboard_intervals_in_day

        return cls._generate_double_intervals_in_day(keyboard_intervals_in_day)

    @classmethod
    def _new_data_set(cls, year, month):
        days_for_data_set = cls._trimmed_flat_calendar(year, month)
        records_in_day = {day: set() for day in days_for_data_set}

        return records_in_day

    @staticmethod
    def _get_keyboard_intervals_in_day(available_intervals, reserved_interval, day: int):
        return available_intervals[day].difference(reserved_interval[day])

    @staticmethod
    def _generate_double_intervals_in_day(keyboard_intervals_in_day):
        """
        Generates double intervals from ordinary intervals.
        The idea is just to take two ordinary intervals.

        :param keyboard_intervals_in_day: set of tuples
        :return: set of double intervals
        """
        if len(keyboard_intervals_in_day) == 0:
            return keyboard_intervals_in_day

        double_intervals = set()
        for interval in keyboard_intervals_in_day:
            next_interval = PatientRecord(interval.end, interval.end + 1)
            if next_interval in keyboard_intervals_in_day:
                double_intervals.add(PatientRecord(interval.start, interval.end + 1))

        return double_intervals

    @staticmethod
    def _create_callback_data(action: str, year: int, month: int, day: int):
        """
         Create the callback data associated to each button
         """

        # todo FROM EXTERNAL LIB
        return ";".join([action, str(year), str(month), str(day)])

    @staticmethod
    def _separate_callback_data(data: str) -> [str]:
        """
        Separate the callback data
        """
        return data.split(";")

    @classmethod
    def _trimmed_flat_calendar(cls, year: int, month: int):
        """
        Calendar without zeroes
        """
        base_calendar = cls._create_base_calendar(year, month)
        merged_base_calendar = list(chain.from_iterable(base_calendar))
        return trim_zeros(merged_base_calendar)

    @staticmethod
    def _create_base_calendar(year: int, month: int):
        """
        Creates a list of Tuesdays, Fridays, Saturdays of month in the form of dates.
        Returning list contains zeroes
        :return: [[int]] - list of lists containing ints, which are dates
        """
        my_month_calendar = [
            [week[1], week[4], week[5]] for week in calendar.monthcalendar(year, month)
        ]

        return my_month_calendar
