from django.db import models

from django.core.validators import RegexValidator
from helpers.validators import day_of_week_validator, record_interval_validator


class Patient(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    telegram_id = models.IntegerField(primary_key=True)

    # Это отработает в админке
    phone_regexp = RegexValidator(regex=r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$')
    phone_number = models.CharField(validators=[phone_regexp], max_length=20)

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"

    @classmethod
    def create(cls, **kwargs):
        patient = cls(**kwargs)
        return patient

class Record(models.Model):
    # todo удали enum этот
    # todo вставь констрэинт через sql
    REGULAR = 'Regular'
    EXTENDED = 'Extended'
    APPOINTMENTS = (
        (REGULAR, 'обычная запись'),
        (EXTENDED, 'расширенная запись')
    )

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    record_start_time = models.DateTimeField(validators=[day_of_week_validator, record_interval_validator])
    record_end_time = models.DateTimeField(validators=[day_of_week_validator, record_interval_validator])

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    @classmethod
    def create(cls, **kwargs):
        record = cls(**kwargs)
        return record
