class RegistryManager:
    GREETING_MAIN = f'\n\nЕсли в процессе взаимодействия со мной вы ошибетесь, то используйте команду /cancel для отмены действий.'

    PRIMARY_GREETING = f'Вас приветствует бот - регистратор доктора Тараки Фердауса! Напишите ваше имя, фамилию и номер телефона последовательно через 1 пробел. Не используйте пробелы при написании ваших данных. Если ваше имя или фамилия состоят из нескольких слов, то используйте тире. '
    SECONDARY_GREETING = f'Рад видеть Вас снова. '
    CHOOSE_RECORD_TYPE = f'Выберите тип записи.'
    REPLY_RECORD_TYPE = [['Обычная', 'Расширенная']]

    APPOINTMENT = {
        'Обычная': {'primary': 'Стоимость первичной консультации 500р. ',
                    'secondary': 'Инфа про повторный обычный'
                    },
        'Расширенная': {
            'primary': 'Составляется подробный план лечения, высылающийся в виде вордовского файла по почте. Стоимость 2000р. При продолжении лечения по рекомендуемому плану, его стоимость идет в счет лечения. В случае, если Пациент отказывается от рекомендованного плана и составляется альтернативный план лечения, такой перерасчет не происходит. ',
            'secondary': 'Инфа про повторый расширенный'
            },
    }

    END_REGISTRY = 'Вы успешно записаны. Стоимость любой работы сообщается ТОЛЬКО после составления плана лечения, для которого нужен комплекс диагностических мероприятий. Ни по телефону, ни при помощи чатов диагнозы не ставятся, расчет стоимости лечения не проводится (ни примерный, ни точный).'

    NOT_ABLE_TO_REGISTER = 'Простите, но запись пока недоступна.'
    INTERNAL_ERROR = 'Появилась ошибка. Сообщите об этом в поддержку: @drTFSupport'
    EXTERNAL_ERROR = 'Кажется, вы сделали что-то не по инструкции...'

    @classmethod
    def greeting(cls, is_new: bool = True) -> str:
        greeting = cls.GREETING_MAIN
        if is_new:
            return cls.PRIMARY_GREETING + greeting
        return cls.SECONDARY_GREETING + cls.CHOOSE_RECORD_TYPE + greeting

    @classmethod
    def choose_record_type(cls):
        return cls.CHOOSE_RECORD_TYPE

    @classmethod
    def get_reply_record_type(cls):
        return cls.REPLY_RECORD_TYPE

    @classmethod
    def record_info(cls, record_type: str, patient_type: str) -> str:
        return cls.APPOINTMENT[record_type][patient_type]

    @classmethod
    def end_registry(cls):
        return cls.END_REGISTRY

    @classmethod
    def not_able_response(cls):
        return cls.NOT_ABLE_TO_REGISTER

    @classmethod
    def internal_error_occured(cls):
        return cls.INTERNAL_ERROR

    @classmethod
    def external_error_occured(cls):
        return cls.EXTERNAL_ERROR
