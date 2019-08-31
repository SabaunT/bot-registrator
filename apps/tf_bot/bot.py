import os
import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, CallbackQueryHandler,
                          ConversationHandler)


from apps.tf_bot.models import Patient, Record
from helpers.constants import Registry
from helpers import telegramcalendar
from helpers.session import TemporarySession, TemporaryData


# TODO поменяй логгер
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Todo это вообще в другое место
BOT_TOKEN = os.environ.get('BOT_TOKEN')
assert BOT_TOKEN

REGISTER, DATE = range(2)

DB_mock = {}
temporary_storage = {}
session_storage = TemporarySession()

"""
user_id: {
        тип записи
        когда была осуществлена запись
        на какое число и время
        актуальность записи
        }
"""


def start(bot, update):
    user_id = update.message.chat.id
    reply_keyboard = [['Обычная', 'Расширенная']]

    current_user_session: TemporaryData = session_storage.add_user(user_id)

    print(user_id)

    try:
        # todo рефактор с добавлением типа? копипаст будто
        current_patient = Patient.objects.get(telegram_id=user_id)
        current_user_session.patient_type = 'secondary'
        print('[DEBUG] exists')
    except Patient.DoesNotExist:
        current_patient = Patient.objects.create(telegram_id=user_id)
        current_user_session.patient_type = 'primary'
        print('[DEBUG] A new one')

    message_text = Registry.greeting(
        is_new=True if current_user_session.patient_type == 'primary' else False
    )

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
1/ Подключить БД с помощью джанго (ГОТОВО)
2/ адаптировать показ правильных сообщений вместе с датами
3/ Адаптировать показ дат вместе с данными, сохраняемыми в БД
4/ Отсылать админу сообщения о новой записи
5/ Добавить поддержку /change
6/ Добавить поддержку /show для регистраторов
7/ Разобраться с работой логгера и определиться как лучше логгировать
8/ Выкатить в прод
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
    is_selected, chosen_date = telegramcalendar.process_calendar_selection(bot, update)
    if is_selected:
        message_reply = 'Вы записаны на {}. '.format(chosen_date.strftime("%d/%m/%Y"))
        message_reply += Registry.end_registry()
        bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text=message_reply,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Здоровья Вам! Если что, обязательно обращайтесь.',
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
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
