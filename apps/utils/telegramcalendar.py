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
from apps.utils.registry_constants import RegistryManager


def separate_callback_data(data: str) -> [str]:
    """
    Separate the callback data
    """
    return data.split(";")


def process_calendar_selection(bot, update, record_type: str):
    """
    Process the callback_query. This method generates a new calendar if forward or
    backward is pressed. This method should be called inside a CallbackQueryHandler.
    :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                and returning the date if so.
    """
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    available_intervals = RegistryManager.generate_available_intervals(year, month)
    reserved_intervals = RegistryManager.get_reserved_intervals(year, month)

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
        free_intervals_in_day = RegistryManager.get_keyboard_typed_intervals_in_day(
            available_intervals,
            reserved_intervals,
            record_type,
            int(day)
        )
        ret_array = list()
        for interval in free_intervals_in_day:
            ret_array.append(f'{interval.start}-{interval.end}')
        ret_data = True, datetime.datetime(int(year), int(month), int(day)), sorted(ret_array)
    else:
        bot.answer_callback_query(callback_query_id=query.id, text="Something went wrong!")
        # UNKNOWN
    return ret_data

