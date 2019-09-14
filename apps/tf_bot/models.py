from datetime import timedelta

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from dr_tf_bot.exceptions import InternalTelegramError

from apps.tf_bot.helpers.validators import date_field_validator


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

    def __str__(self):
        return f'{self.telegram_id} - {self.last_name} {self.first_name}'

    def save_patient_fields(self, patient_fields):
        model_fields = ['last_name', 'first_name', 'phone_number']
        try:
            for field, patient_info in zip(model_fields, patient_fields):
                self.__dict__[field] = patient_info

            self.full_clean()
            self.save()
        except ValidationError as e:
            raise InternalTelegramError('Failed to save patient fields') from e


class Record(models.Model):
    REGULAR = 'Regular'
    EXTENDED = 'Extended'

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    record_start_time = models.DateTimeField(validators=[date_field_validator])
    record_end_time = models.DateTimeField(validators=[date_field_validator])

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    @classmethod
    def create(cls, **kwargs):
        record = cls(**kwargs)
        return record

    def registered_patient(self):
        return f'{self.patient.first_name}-{self.patient.last_name}'
    registered_patient.short_description = 'Пациент'

    def save_record_fields(self, user_data: dict, intervals: list):
        fields = ['record_start_time', 'record_end_time']

        for field, interval in zip(fields, intervals):
            self.__dict__[field] = user_data['day'] + timedelta(hours=int(interval))

        self.save()

    def save(self, *args, **kwargs):
        try:
            self._validate_record_time_logic()
            self._validate_interval_length()
            self.full_clean()
        except ValidationError as e:
            raise InternalTelegramError('Failed to save record') from e
        
        super().save(*args, **kwargs)

    def _validate_record_time_logic(self):
        if self.record_start_time >= self.record_end_time:
            raise ValidationError

    def _validate_interval_length(self):
        interval_length = self.record_end_time.hour - self.record_start_time.hour
        if interval_length not in {1, 2}:
            raise ValidationError
