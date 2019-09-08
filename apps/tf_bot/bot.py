import os
import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,
                          ConversationHandler)
from django.db import transaction


from apps.tf_bot.models import Patient, Record
from apps.utils.registry_constants import RegistryManager
from apps.utils import telegramcalendar
from apps.utils.util import restruct_patient_fields
from dr_tf_bot.exceptions import InternalTelegramError, UserTelegramError


# TODO поменяй логгер
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Todo это вообще в другое место
BOT_TOKEN = os.environ.get('BOT_TOKEN')
assert BOT_TOKEN

REGISTER, RECORD, DATE, INTERVAL = range(4)


def start(update, context):
    # todo добавь проверку того, что человек уже имеет АКТУАЛЬНУЮ запись
    user_id = update.message.chat.id

    patient, created = Patient.objects.get_or_create(telegram_id=user_id)
    context.user_data['patient_type'] = 'primary' if created else 'secondary'

    update.message.reply_text(
        RegistryManager.greeting(is_new=created),
        reply_markup=None if created else ReplyKeyboardMarkup(
            RegistryManager.get_reply_record_type(),
            one_time_keyboard=True)
    )

    return REGISTER if patient.phone_number == '' else RECORD


def register(update, context):
    user_id = update.message.chat.id
    user_response = update.message.text

    restructed_patient_fields = restruct_patient_fields(user_response)
    try:
        patient = Patient.objects.get(telegram_id=user_id)
        with transaction.atomic():
            patient.save_patient_fields(restructed_patient_fields)
    except Patient.DoesNotExist:
        raise InternalTelegramError('User does not exist')

    update.message.reply_text(
        RegistryManager.choose_record_type(),
        reply_markup=ReplyKeyboardMarkup(RegistryManager.get_reply_record_type(), one_time_keyboard=True)
    )

    return RECORD

'''
TODO:
5/ Добавить поддержку /change
7/ Разобраться с работой логгера и определиться как лучше логгировать
8/ Выкатить в прод
'''


def record(update, context):
    """
    record_type - Обычная или Расширенная
    """
    record_type = update.message.text

    context.user_data['record_type'] = Record.REGULAR if record_type == 'Обычная' else Record.EXTENDED

    reply_keyboard = RegistryManager.generate_calendar(Record.REGULAR)
    message_reply = RegistryManager.record_info(record_type, context.user_data['patient_type']) + 'Выберите дату.'

    update.message.reply_text(message_reply, reply_markup=reply_keyboard)

    return DATE


def date(update, context):
    is_selected, chosen_date, days_array = telegramcalendar.process_calendar_selection(
        context.bot,
        update,
        context.user_data['record_type']
    )

    context.user_data['day'] = chosen_date

    if is_selected:
        message_reply = 'Вы выбрали {}. Выберите интервал записи'.format(chosen_date.strftime("%d/%m/%Y"))

        reply_intervals = [days_array]
        context.bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text=message_reply,
            reply_markup=ReplyKeyboardMarkup(reply_intervals, one_time_keyboard=True)
        )

        return INTERVAL


def time_interval(update, context):
    chosen_interval = update.message.text
    context.user_data['interval'] = chosen_interval

    message_reply = f'Вы выбрали интервал {chosen_interval}. Осуществляю подготовку к записи...'
    update.message.reply_text(message_reply)

    """
    распакуй context.user_data, чтобы сохранить оттуда day и interval
    """
    print(context.user_data)

    cancel(update, context)


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Здоровья Вам! Если что, обязательно обращайтесь.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    try:
        raise context.error
    except InternalTelegramError:
        logger.warning('Update "%s" caused error "%s"', update, context.error)
    except UserTelegramError:
        update.message.reply_text('Появилась ошибка! Из-за тебя, между прочим!', reply_markup=ReplyKeyboardRemove())


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
            REGISTER: [MessageHandler(Filters.text, register)],
            RECORD: [MessageHandler(Filters.regex('^(Обычная|Расширенная)$'), record)],

            DATE: [CallbackQueryHandler(date)],

            INTERVAL: [MessageHandler(Filters.text, time_interval)] # todo regexp
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
