import os
import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,
                          ConversationHandler)


from apps.tf_bot.models import Patient, Record
from apps.utils.registry_constants import RegistryManager
from apps.utils import telegramcalendar
from apps.utils.session import TemporarySession, TemporaryData


# TODO поменяй логгер
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Todo это вообще в другое место
BOT_TOKEN = os.environ.get('BOT_TOKEN')
assert BOT_TOKEN

REGISTER, DATE, INTERVAL = range(3)

session_storage = TemporarySession()


def start(update, context):
    # todo добавь проверку того, что человек уже имеет АКТУАЛЬНУЮ запись
    user_id = update.message.chat.id
    reply_keyboard = [['Обычная', 'Расширенная']]

    current_patient_session_data: TemporaryData = session_storage.add_user(user_id)

    print(user_id)

    # todo атомарно
    _, created = Patient.objects.get_or_create(telegram_id=user_id)
    current_patient_session_data.patient_type = 'primary' if created else 'secondary'

    message_text = RegistryManager.greeting(
        is_new=True if current_patient_session_data.patient_type == 'primary' else False
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
def register(update, context):
    """
    record_type - Обычная или Расширенная
    """
    user_id = update.message.chat.id
    record_type = update.message.text

    current_patient: TemporaryData = session_storage.get(user_id)
    current_patient_type = current_patient.patient_type
    current_patient.record_type = Record.REGULAR if record_type == 'Обычная' else Record.EXTENDED

    reply_keyboard = RegistryManager.generate_calendar(current_patient.record_type)
    message_reply = RegistryManager.record_info(record_type, current_patient_type)
    message_reply += 'Выберите дату.'

    update.message.reply_text(message_reply, reply_markup=reply_keyboard)

    return DATE


def date(update, context):
    user_id = update.effective_user.id
    current_patient: TemporaryData = session_storage.get(user_id)
    is_selected, chosen_date, days_array = telegramcalendar.process_calendar_selection(context.bot, update, current_patient.record_type)
    if is_selected:
        message_reply = 'Вы записаны на {}. '.format(chosen_date.strftime("%d/%m/%Y"))
        message_reply += 'Выберите интервал записи'

        reply_intervals = [days_array]
        context.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text=message_reply,
            reply_markup=ReplyKeyboardMarkup(reply_intervals, one_time_keyboard=True)
        )
        return INTERVAL


def time_interval(update, context):
    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Здоровья Вам! Если что, обязательно обращайтесь.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # todo скрой
    REQUEST_KWARGS = {
        'proxy_url': 'http://equohnge4fiequiem4Du:Ahphi7ahvoh6IejahPha@proxy.mixbytes.io:3128',
        # Optional, if you need authentication:
    }
    updater = Updater(BOT_TOKEN, request_kwargs=REQUEST_KWARGS, use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            REGISTER: [MessageHandler(Filters.regex('^(Обычная|Расширенная)$'), register)],

            DATE: [CallbackQueryHandler(date)],

            INTERVAL: []
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
