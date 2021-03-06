import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,
                          ConversationHandler)
from django.conf import settings

from apps.tf_bot.models import Patient, Record
from apps.tf_bot.helpers.registry_constants import RegistryManager
from apps.tf_bot.helpers.telegram_calendar import CalendarManager
from apps.tf_bot.helpers.bot_checker import BotStartChecker
from apps.tf_bot.helpers.utils import split_patient_info
from dr_tf_bot.exceptions import InternalTelegramError, UserTelegramError


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

REGISTER, RECORD, DATE, INTERVAL = range(4)


def start(update, context):
    user_id = update.message.chat.id
    bot_checker = BotStartChecker()

    if not bot_checker.get_bot_start_ability_status(user_id):
        update.message.reply_text(RegistryManager.not_able_response())
        logger.info(f'{user_id} tried to use bot, but was stopped.')
        return ConversationHandler.END

    patient, _ = Patient.objects.get_or_create(telegram_id=user_id)
    is_known_patient = bool(patient.phone_number)
    context.user_data['patient_type'] = 'primary' if not is_known_patient else 'secondary'

    update.message.reply_text(
        text=RegistryManager.greeting(is_known_patient),
        reply_markup=None if not is_known_patient else ReplyKeyboardMarkup(RegistryManager.get_reply_record_type(),
                                                                           one_time_keyboard=True)
    )
    return REGISTER if not is_known_patient else RECORD


def register(update, context):
    user_id = update.message.chat.id
    user_response = update.message.text

    listed_patient_info = split_patient_info(user_response)
    try:
        patient = Patient.objects.get(telegram_id=user_id)
        patient.save_patient_fields(listed_patient_info)
    except Patient.DoesNotExist:
        raise InternalTelegramError(f'User {user_id} user does not exist/ register')

    update.message.reply_text(
        text=RegistryManager.choose_record_type(),
        reply_markup=ReplyKeyboardMarkup(RegistryManager.get_reply_record_type(), one_time_keyboard=True)
    )
    return RECORD


def record(update, context):
    record_type = update.message.text

    context.user_data['record_type'] = Record.REGULAR if record_type == 'Обычная' else Record.EXTENDED

    reply_keyboard = CalendarManager.generate_calendar(context.user_data['record_type'])
    message_reply = RegistryManager.record_info(record_type, context.user_data['patient_type']) + 'Выберите дату.'

    update.message.reply_text(text=message_reply, reply_markup=reply_keyboard)
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
    update.message.reply_text(text=message_reply, reply_markup=ReplyKeyboardRemove())

    try:
        current_patient = Patient.objects.get(telegram_id=user_id)
    except Patient.DoesNotExist:
        raise InternalTelegramError(f'User {user_id} does not exist/ time_interval ')

    intervals_list = chosen_interval.split('-')
    new_record = Record.create(patient=current_patient)
    new_record.save_record_fields(context.user_data, intervals_list)

    update.message.reply_text(text=RegistryManager.end_registry())
    return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(text='Здоровья Вам! Если что, обязательно обращайтесь.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    try:
        raise context.error
    except InternalTelegramError:
        update.message.reply_text(text=RegistryManager.internal_error_occured(),
                                  reply_markup=ReplyKeyboardRemove())
        logger.exception('Update "%s" caused error "%s"', update, context.error)
    except UserTelegramError:
        update.message.reply_text(text=RegistryManager.external_error_occured(),
                                  reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


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
