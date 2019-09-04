import calendar
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from apps.tf_bot.models import Record
from apps.utils.record_data import RecordData
from apps.utils.util import PatientRecord


class Registry:
    GREETING_MAIN = f'Если вы хотите изменить параметры записи, то воспользуйтесь командой /change. \
                    \n\nВыберите тип записи'

    PRIMARY_GREETING = f'Вас приветствует бот - регистратор доктора Тараки Фердауса! '
    SECONDARY_GREETING = f'Рад видеть Вас снова. '

    APPOINTMENT = {
        'Обычная': {'primary': 'Стоимость первичной консультации 500р. ',
                    'secondary': 'Инфа про повторный обычный'
                    },
        'Расширенная': {
            'primary': 'Составляется подробный план лечения, высылающийся в виде вордовского файла по почте. Стоимость 2000р. При продолжении лечения по рекомендуемому плану, его стоимость идет в счет лечения. В случае, если Пациент отказывается от рекомендованного плана и составляется альтернативный план лечения, такой перерасчет не происходит. ',
            'secondary': 'Инфа про повторый расширенный'
            },
    }

    END_REGISTRY = 'Стоимость любой работы сообщается ТОЛЬКО после составления плана лечения, для которого нужен комплекс диагностических мероприятий. Ни по телефону, ни при помощи чатов диагнозы не ставятся, расчет стоимости лечения не проводится (ни примерный, ни точный).'


    @classmethod
    def greeting(cls, *, is_new: bool = True) -> str:
        greeting = cls.GREETING_MAIN
        if is_new:
            return cls.PRIMARY_GREETING + greeting
        return cls.SECONDARY_GREETING + greeting

    @classmethod
    def record_info(cls, record_type: str, patient_type: str) -> str:
        return cls.APPOINTMENT[record_type][patient_type]

    @classmethod
    def end_registry(cls):
        return cls.END_REGISTRY

    @classmethod
    def generate_calendar(cls, record_type: str):
        """
        Create an inline keyboard with the provided year and month
        :param str record_type: type of record: either regular or extended
        :return: Returns the InlineKeyboardMarkup object with the calendar.
        """
        now = datetime.now()
        year = now.year
        month = now.month

        # First two rows in telegram calendar object
        year_n_month_row, week_days_row = cls._create_support_rows(year, month)

        #days_row = cls._get_available_days_row()

    @classmethod
    def _create_support_rows(cls, year: int, month: int) -> (list, list):
        data_ignore = cls._create_callback_data("IGNORE", year, month, 0)

        year_month_row = list()
        year_and_month_keyboard = InlineKeyboardButton(
            calendar.month_name[month] + " " + str(year),
            callback_data=data_ignore
        )
        year_month_row.append(year_and_month_keyboard)

        week_days_row = list()
        for day in ["Tu", "Fr", "Sa"]:
            week_days_row.append(InlineKeyboardButton(day, callback_data=data_ignore))

        return year_month_row, week_days_row

    @staticmethod
    def _create_callback_data(action: str, year: int, month: int, day: int):
        """
         Create the callback data associated to each button
         """

        # todo FROM EXTERNAL LIB
        return ";".join([action, str(year), str(month), str(day)])

    @staticmethod
    def _separate_callback_data(data: str) -> [str]:
        """
        Separate the callback data
        """
        return data.split(";")

    @staticmethod
    def _generate_available_intervals(year: int, month: int) -> dict:
        available_intervals_template = RecordData.new_data_set(year, month)

        for day in available_intervals_template.keys():
            weekday_of_day = datetime(year, month, day).weekday()

            if weekday_of_day in {1, 4}:
                intervals_range = range(9, 15)
            elif weekday_of_day == 5:
                intervals_range = range(12, 20)
            else:
                raise Exception('tmp exception') # todo temp

            available_intervals_template[day] = {PatientRecord(h, h+1) for h in intervals_range}

        return available_intervals_template
