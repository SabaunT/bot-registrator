from datetime import datetime, time

from helpers.record_data import RecordData


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

    AVAILABLE_INTERVALS = {
        1: {(9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15)},
        4: {(9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15)},
        5: {(12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20)}
    }

    @classmethod
    def greeting(cls, *, is_new: bool = True) -> str:
        greeting = cls.GREETING_MAIN
        if is_new:
            return cls.PRIMARY_GREETING + greeting
        return cls.SECONDARY_GREETING + greeting

    @staticmethod
    def generate_available_intervals(year: int, month: int):
        available_intervals_template = RecordData.new_data_set(year, month)

        for day in available_intervals_template.keys():
            weekday_of_day = datetime(year, month, day).weekday()

            if weekday_of_day in {1, 4}:
                intervals_range = range(9, 15)
            elif weekday_of_day == 5:
                intervals_range = range(12, 20)
            else:
                raise Exception('tmp exception') # todo temp

            # todo use named tuple
            available_intervals_template[day] = {(time(h), time(h+1)) for h in intervals_range}

    @classmethod
    def record_info(cls, record_type: str, patient_type: str) -> str:
        return cls.APPOINTMENT[record_type][patient_type]

    @classmethod
    def end_registry(cls):
        return cls.END_REGISTRY
