#!/usr/bin/env python3
#
# taken from grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.

NEED MAJOR REFACTOR !!!!!!!!!!!
VERY BAD CODE!!!!!!!!!!
"""
import datetime
import calendar
from pprint import pprint

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from apps.utils.record_data import RecordData
from apps.utils.registry_constants import Registry
from apps.utils.util import PatientRecord
from apps.tf_bot.models import Record


def create_callback_data(action, year, month, day):
    """ Create the callback data associated to each button"""
    return ";".join([action, str(year), str(month), str(day)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_calendar(record_type: str, year=None, month=None):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """
    now = datetime.datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    # todo need refactor

    keyboard_calendar = list()

    # getting reserved intervals in current month
    min_for_query = datetime.datetime(year, month, 1, 0, 0, 0)
    max_for_query = datetime.datetime(year,  month + 1, 1, 0, 0, 0)
    reserved_intervals = Record.objects.filter(record_end_time__range=(min_for_query, max_for_query))

    if len(reserved_intervals) == 0:
        return keyboard_calendar

    reserved_intervals_subtrahend_sets: dict[int: set] = RecordData.new_data_set(year, month)
    for reserved_interval in reserved_intervals:
        interval_start_hour = reserved_interval.record_start_time.hour
        interval_end_hour = reserved_interval.record_end_time.hour

        interval_tuple = PatientRecord(interval_start_hour, interval_end_hour)
        reserved_intervals_subtrahend_sets[reserved_interval.record_start_time.day].add(interval_tuple) # todo а тут точно нужна проверка?

    data_ignore = create_callback_data("IGNORE", year, month, 0)
    # First row - Month and Year
    row = list()
    row.append(InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore))
    keyboard_calendar.append(row)
    # Second row - Week Days
    row = list()
    for day in ["Tu", "Fr", "Sa"]:
        row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard_calendar.append(row)

    my_calendar = [
        [week[1], week[4], week[5]] for week in calendar.monthcalendar(year, month)
    ]

    for week in my_calendar:
        row = []
        for day in week:
            if day == 0 or day <= now.day:
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                available_intervals = Registry.generate_available_intervals(year, month)
                keyboard_intervals = available_intervals[day].difference(reserved_intervals_subtrahend_sets[day])
                if len(keyboard_intervals) != 0:
                    row.append(InlineKeyboardButton(day, callback_data=create_callback_data("DAY", year, month, day)))
        keyboard_calendar.append(row)

    for each in keyboard_calendar[2:]:
        for e in each:
            print(e.text)

    # list_to_filter = keyboard[2:].copy()

    return InlineKeyboardMarkup(keyboard_calendar)


def process_calendar_selection(bot, update):
    """
    Process the callback_query. This method generates a new calendar if forward or
    backward is pressed. This method should be called inside a CallbackQueryHandler.
    :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                and returning the date if so.
    """
    ret_data = (False, None)
    query = update.callback_query
    (action, year, month, day) = separate_callback_data(query.data)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=query.id)
    elif action == "DAY":
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id
                              )
        ret_data = True, datetime.datetime(int(year), int(month), int(day))
    else:
        bot.answer_callback_query(callback_query_id=query.id, text="Something went wrong!")
        # UNKNOWN
    return ret_data

