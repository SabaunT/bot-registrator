import calendar
from datetime import datetime
from itertools import chain

from numpy import trim_zeros
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from django.db.models import QuerySet

from apps.tf_bot.models import Record
from apps.tf_bot.helpers.utils import PatientRecord, extend_lists


class TelegramCalendarGenerator:
    def __init__(self, now: datetime.now()):
        self.year = now.year
        self.month = now.month
        self.current_day = now.day

    def create_available_days_row(self, record_type: str):

        # for buttons with no actions
        data_ignore = self.create_callback_data("IGNORE", self.year, self.month, 0)

        available_intervals = self.generate_available_intervals(self.year, self.month)
        reserved_intervals = self.get_reserved_intervals(self.year, self.month)

        # todo unreadable?
        keyboard_days = list()
        my_base_calendar: list = self._create_base_calendar(self.year, self.month)
        for week in my_base_calendar:
            days_row = list()
            for day in week:
                if day == 0 or day <= self.current_day:
                    days_row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
                else:
                    free_typed_intervals_in_day = self.get_keyboard_typed_intervals_in_day(
                        available_intervals,
                        reserved_intervals,
                        record_type,
                        day
                    )
                    if len(free_typed_intervals_in_day) != 0:
                        data_process = self.create_callback_data("DAY", self.year, self.month, day)
                        days_row.append(InlineKeyboardButton(day, callback_data=data_process))

            keyboard_days.append(days_row)

        return keyboard_days

    def create_support_rows(self) -> [[InlineKeyboardButton], [InlineKeyboardButton]]:
        """
        Creates info support rows with current month, year, and weekdays
        :return: list of lists. Each of the list contains InlineKeyboardButton object
        """

        # for buttons with no actions
        data_ignore = self.create_callback_data("IGNORE", self.year, self.month, 0)

        year_month_row = list()
        year_and_month_keyboard = InlineKeyboardButton(
            calendar.month_name[self.month] + " " + str(self.year),
            callback_data=data_ignore
        )
        year_month_row.append(year_and_month_keyboard)

        week_days_row = list()
        for day in ["Tu", "Fr", "Sa"]:
            week_days_row.append(InlineKeyboardButton(day, callback_data=data_ignore))

        return [year_month_row, week_days_row]

    def get_last_month_day(self):
        my_calendar = self._trimmed_flat_calendar(self.year, self.month)
        return my_calendar[-1]

    def generate_available_intervals(self, year: int, month: int) -> {int: {PatientRecord}}:
        """
        Generates all the intervals which possibly could be chosen
        :param year: datetime current year
        :param month: datetime current month
        :return: dict where keys are dates for Tuesdays, Fridays and Saturdays of the month
                 and values are sets of tuples - intervals
        """
        available_intervals_template = self._new_data_set(year, month)

        for day in available_intervals_template.keys():
            weekday_of_day = datetime(year, month, day).weekday()

            if weekday_of_day in {1, 4}:
                intervals_range = range(9, 15)
            elif weekday_of_day == 5:
                intervals_range = range(12, 20)

            available_intervals_template[day] = {PatientRecord(h, h + 1) for h in intervals_range}

        return available_intervals_template

    def get_reserved_intervals(self, year: int, month: int):
        min_for_query = datetime(year, month, 1, 0, 0, 0)
        max_for_query = datetime(year, month + 1, 1, 0, 0, 0)

        reserved_intervals = Record.objects.filter(record_end_time__range=(min_for_query, max_for_query))

        return self._restructure_reserved_intervals(year, month, reserved_intervals)

    def get_keyboard_typed_intervals_in_day(
            self, available_intervals: {int: {PatientRecord}}, reserved_interval, record_type: str, day: int
    ):
        """
        Gets allowed for record intervals which will be presented on board. The argument `record_type` means that
        that shown intervals could be doubled (regular record: 9-10, extended record: 9-11)
        """
        keyboard_intervals_in_day = self._get_keyboard_intervals_in_day(available_intervals, reserved_interval, day)

        if record_type == Record.REGULAR:
            return keyboard_intervals_in_day

        return self._generate_double_intervals_in_day(keyboard_intervals_in_day)

    @staticmethod
    def _get_keyboard_intervals_in_day(
            available_intervals: {int: {PatientRecord}}, reserved_interval: {int: {PatientRecord}}, day: int
    ) -> {PatientRecord}:
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

    @classmethod
    def _restructure_reserved_intervals(cls, year: int, month: int, reserved_intervals: QuerySet) -> {
            int: {PatientRecord}
    }:
        """
        Restructures records from query set in the following way: if a patient has double interval, it
        adds two intervals to the record day key.
        """
        reserved_intervals_template_set = cls._new_data_set(year, month)

        for reserved_interval in reserved_intervals:
            interval_start_hour = reserved_interval.record_start_time.hour
            interval_end_hour = reserved_interval.record_end_time.hour

            if interval_end_hour - interval_start_hour == 2:
                adding_intervals = [PatientRecord(interval_start_hour + i, interval_end_hour + i-1) for i in range(2)]
            else:
                adding_intervals = [PatientRecord(interval_start_hour, interval_end_hour)]
            reserved_intervals_template_set[reserved_interval.record_start_time.day].update(adding_intervals)

        return reserved_intervals_template_set

    @classmethod
    def _new_data_set(cls, year: int, month: int) -> {int: set}:
        """
        Returns a new data set
        """
        days_for_data_set = cls._trimmed_flat_calendar(year, month)
        records_in_day = {day: set() for day in days_for_data_set}

        return records_in_day

    @classmethod
    def _trimmed_flat_calendar(cls, year: int, month: int):
        """
        Returns base calendar without zeroes
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

    @staticmethod
    def create_callback_data(action: str, year: int, month: int, day: int) -> str:
        """
         Create the callback data associated to each button
         """
        return ";".join([action, str(year), str(month), str(day)])

    @staticmethod
    def separate_callback_data(data: str) -> [str]:
        """
        Separate the callback data
        """
        return data.split(";")


class CalendarManager:

    @classmethod
    def generate_calendar(cls, record_type: str):
        """
        Create an inline keyboard with the provided year and month
        :param str record_type: type of record: either regular or extended
        :return: Returns the InlineKeyboardMarkup object with the calendar.
        """
        now = datetime.now()
        calendar_generator = TelegramCalendarGenerator(now)
        formed_calendar = list()

        # First two rows in telegram calendar object
        year_and_weekdays_rows = calendar_generator.create_support_rows()

        days_rows = calendar_generator.create_available_days_row(record_type)

        return InlineKeyboardMarkup(extend_lists(formed_calendar, year_and_weekdays_rows, days_rows))

    @classmethod
    def process_calendar_selection(cls, bot, update, record_type: str):

        now = datetime.now()

        calendar_generator = TelegramCalendarGenerator(now)
        available_intervals = calendar_generator.generate_available_intervals(calendar_generator.year,
                                                                              calendar_generator.month)

        reserved_intervals = calendar_generator.get_reserved_intervals(calendar_generator.year,
                                                                       calendar_generator.month)

        ret_data = (False, None)
        query = update.callback_query
        (action, year, month, day) = calendar_generator.separate_callback_data(query.data)
        # todo UNREADABLE
        if action == "IGNORE":
            bot.answer_callback_query(callback_query_id=query.id)
        elif action == "DAY":
            bot.edit_message_text(text=query.message.text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id
                                  )
            free_intervals_in_day = calendar_generator.get_keyboard_typed_intervals_in_day(
                available_intervals,
                reserved_intervals,
                record_type,
                int(day)
            )
            ret_array = list()
            for interval in free_intervals_in_day:
                ret_array.append(f'{interval.start}-{interval.end}')    # actually, I am sorting strings. Uh...
            ret_data = True, datetime(int(year), int(month), int(day)), sorted(ret_array)

        return ret_data
