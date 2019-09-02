#!/usr/bin/env python3
#
# taken from grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.

NEED MAJOR REFACTOR !!!!!!!!!!!
VERY BAD CODE!!!!!!!!!!
"""
import os
import datetime
import calendar

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from helpers.record_data import RecordData
from helpers.registry_constants import Registry


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
    if not os.path.exists(RecordData.PICKLING_FILE):
        record_data_set = RecordData.new_data_set(year, month)
        record_data_set.dump_record_state()
    elif RecordData().check_data_set_actuality():
        record_data_set = RecordData()
    else:
        record_data_set = RecordData.new_data_set(year, month)
        record_data_set.dump_record_state()

    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = []
    # First row - Month and Year
    row = list()
    row.append(InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore))
    keyboard.append(row)
    # Second row - Week Days
    row = list()
    for day in ["Tu", "Fr", "Sa"]:
        row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = [
        [week[1], week[4], week[5]] for week in calendar.monthcalendar(year, month)
    ]

    for week in my_calendar:
        row = []
        for day in week:
            if day == 0 or day <= now.day:
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                keyboard_intervals: set = record_data_set.get_keyboard_intervals(day, record_type)
                if len(keyboard_intervals) != 0:
                    row.append(InlineKeyboardButton(day, callback_data=create_callback_data("DAY", year, month, day)))
        keyboard.append(row)

    for each in keyboard[2:]:
        for e in each:
            print(e.text)

    # list_to_filter = keyboard[2:].copy()

    return InlineKeyboardMarkup(keyboard)


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

if __name__ == '__main__':
    create_calendar(2019, 9)
