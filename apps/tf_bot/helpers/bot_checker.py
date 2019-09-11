from datetime import datetime

from apps.tf_bot.models import Record
from apps.tf_bot.helpers.telegramcalendar import TelegramCalendarGenerator


class BotStartChecker:
    """
    This class is used to insure that there are no logical constraints to use bot, which are:
     - patient already has a record in the future (datetime.now().day < record day)
     - there aren't free intervals in this month
     - the last day, which could be chosen for a record < datetime.now().day
    """

    def __init__(self):
        current_time = datetime.now()
        self.year = current_time.year
        self.month = current_time.month
        self.day = current_time.day

        self.calendar_generator = TelegramCalendarGenerator(current_time)

    def get_bot_start_ability(self, user_id: int) -> bool:
        patient_can_register = self._check_patient_record_ability(user_id)
        db_has_free_intervals = self._check_db_record_ability()
        its_not_final_record_day = self._check_final_date()

        return patient_can_register & db_has_free_intervals & its_not_final_record_day

    def _check_patient_record_ability(self, user_id: int) -> bool:
        from_current_date = datetime(self.year, self.month, self.day)
        next_month_start = datetime(self.year, self.month + 1, 1)

        try:
            Record.objects.get(patient=user_id, record_start_time__range=(from_current_date, next_month_start))
        except Record.DoesNotExist:
            return True
        else:
            return False

    def _check_db_record_ability(self) -> bool:
        available_intervals = self.calendar_generator.generate_available_intervals(self.year,
                                                                                   self.month)
        reserved_intervals = self.calendar_generator.get_reserved_intervals(self.year,
                                                                            self.month)
        tmp_dict = dict()
        for day in available_intervals.keys():
            tmp_dict[day] = available_intervals[day].difference(reserved_intervals[day])

        return all(value != set() for value in tmp_dict.values())

    def _check_final_date(self) -> bool:
        last_day = self.calendar_generator.get_last_month_day()

        return self.day < last_day
