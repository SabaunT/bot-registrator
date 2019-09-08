from telegram.error import TelegramError


class InternalTelegramError(TelegramError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserTelegramError(TelegramError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
