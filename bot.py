import os
import logging
from constants import Registry
from calendar_telegram import telegramcalendar
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, CallbackQueryHandler,
                          ConversationHandler)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
assert BOT_TOKEN

REGISTER, DATE, FINAL, LOCATION, BIO = range(5)

DB_mock = {}
temporary_storage = {}
"""
user_id: {
        тип записи
        когда была осуществлена запись
        на какое число и время
        актуальность записи
        }
"""


def start(bot, update):
    user = update.message.chat.id
    reply_keyboard = [['Обычная', 'Расширенная']]

    temporary_storage[user] = {}
    print(user)

    if user in DB_mock: #ORM
        _change_records_actuality(user)

        temporary_storage[user]['patient_type'] = 'secondary'
        message_text = Registry.greeting(is_new=False)
    else:
        temporary_storage[user]['patient_type'] = 'primary'
        message_text = Registry.greeting(is_new=True)

    update.message.reply_text(message_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return REGISTER


def _change_records_actuality(user_id: int):
    '''
    SQL: update RECORD where на какое число и время < now + 4 часа: актуальность записи = 0
    '''
    pass


def _check_hot_record(user_id: int):
    '''
    if DB_mock[user_id][на какое число записан] - now <= 24 часа:
        У тебя есть хот рекордперейди к процедуре отмены записи по команде: /buy
        return 0
    '''


'''
TODO:
1/ Определиться с правильностью сообщений
2/ Разобраться с возможностью показывать дату
3/ Подключить БД - orm
4/ Разобраться с работой логгера и определиться как лучше логгировать
5/ Выкатить в прод
'''
def register(bot, update):
    user = update.message.chat.id
    reply_keyboard = telegramcalendar.create_calendar()
    record_type = update.message.text

    patient_type = temporary_storage[user]['patient_type']
    temporary_storage[user]['record_type'] = record_type

    message_reply = Registry.record_info(update.message.text, patient_type)
    message_reply += 'Выберите дату.'
    update.message.reply_text(message_reply, reply_markup=reply_keyboard)

    return DATE


def date(bot, update):
    """
    ИЗМЕНИ ПРОЦЕССИНГ!
    """
    selected, date_ = telegramcalendar.process_calendar_selection(bot, update)
    if selected:
        bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="You selected %s" % (date_.strftime("%d/%m/%Y")),
            reply_markup=ReplyKeyboardRemove()
        )

    return FINAL


def final(bot, update):
    print('final')
    message_reply = Registry.end_registry()
    update.message.reply_text(message_reply)
    return ConversationHandler.END


def location(bot, update):
    user = update.message.from_user
    user_location = update.message.location
    logger.info("Location of %s: %f / %f", user.first_name, user_location.latitude,
                user_location.longitude)
    update.message.reply_text('Maybe I can visit you sometime! '
                              'At last, tell me something about yourself.')

    return BIO


def skip_location(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    update.message.reply_text('You seem a bit paranoid! '
                              'At last, tell me something about yourself.')

    return BIO


def cancel(bot, update):
    user = update.message.from_user
    print(update)
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(BOT_TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            REGISTER: [RegexHandler('^(Обычная|Расширенная)$', register)],

            DATE: [CallbackQueryHandler(date)],

            FINAL: [MessageHandler(Filters.text, final)],

            LOCATION: [MessageHandler(Filters.location, location),
                       CommandHandler('skip', skip_location)],
        },

        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
