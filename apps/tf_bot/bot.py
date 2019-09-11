import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,
                          ConversationHandler)
from django.conf import settings

from apps.tf_bot.models import Patient, Record
from apps.tf_bot.helpers.registry_constants import RegistryManager
from apps.tf_bot.helpers.telegramcalendar import CalendarManager
from apps.tf_bot.helpers.bot_checker import BotStartChecker
from apps.tf_bot.helpers.utils import restruct_patient_fields
from dr_tf_bot.exceptions import InternalTelegramError, UserTelegramError

# TODO поменяй логгер
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

REGISTER, RECORD, DATE, INTERVAL = range(4)


def start(update, context):
    user_id = update.message.chat.id
    bot_checker = BotStartChecker()

    if not bot_checker.get_bot_start_ability(user_id):
        update.message.reply_text(RegistryManager.not_able_response())
        return ConversationHandler.END

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
        patient.save_patient_fields(restructed_patient_fields)
    except Patient.DoesNotExist:
        raise InternalTelegramError('User does not exist')

    update.message.reply_text(
        RegistryManager.choose_record_type(),
        reply_markup=ReplyKeyboardMarkup(RegistryManager.get_reply_record_type(), one_time_keyboard=True)
    )

    return RECORD


def record(update, context):
    """
    record_type - Обычная или Расширенная
    """
    record_type = update.message.text

    context.user_data['record_type'] = Record.REGULAR if record_type == 'Обычная' else Record.EXTENDED

    reply_keyboard = CalendarManager.generate_calendar(Record.REGULAR)
    message_reply = RegistryManager.record_info(record_type, context.user_data['patient_type']) + 'Выберите дату.'

    update.message.reply_text(message_reply, reply_markup=reply_keyboard)

    return DATE


def date(update, context):
    is_selected, chosen_date, days_array = CalendarManager.process_calendar_selection(
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
    user_id = update.message.chat.id
    chosen_interval = update.message.text

    message_reply = f'Вы выбрали интервал {chosen_interval}. Осуществляю подготовку к записи...'
    update.message.reply_text(message_reply, reply_markup=ReplyKeyboardRemove())

    intervals_list = chosen_interval.split('-')

    try:
        current_patient = Patient.objects.get(telegram_id=user_id)
    except Patient.DoesNotExist:
        raise InternalTelegramError('User does not exist')

    new_record = Record.create(patient=current_patient)
    new_record.save_record_fields(context.user_data, intervals_list)

    update.message.reply_text(RegistryManager.end_registry())
    return ConversationHandler.END


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


class TFBot:
    def __init__(self):
        self.token = settings.BOT_TOKEN
        self.proxy_login = settings.TELEGRAM_PROXY_LOGIN
        self.proxy_pass = settings.TELEGRAM_PROXY_PASS

        self.updater = Updater(self.token, request_kwargs=self.request_kwargs, use_context=True)
        self.dispatcher = self.updater.dispatcher

    def setup(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],

            states={
                REGISTER: [MessageHandler(Filters.text, register)],
                RECORD: [MessageHandler(Filters.regex('^(Обычная|Расширенная)$'), record)],

                DATE: [CallbackQueryHandler(date)],

                INTERVAL: [MessageHandler(Filters.regex('^((\d{,2})-(\d{,2}))$'), time_interval)]
            },

            fallbacks=[CommandHandler('cancel', cancel)]
        )

        self.dispatcher.add_handler(conv_handler)
        self.dispatcher.add_error_handler(error)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()  # development

    @property
    def request_kwargs(self):
        return {'proxy_url': f'http://{self.proxy_login}:{self.proxy_pass}@proxy.mixbytes.io:3128'}
