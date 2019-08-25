from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


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
    REGULAR = 'Regular'
    EXTENDED = 'Extended'
    APPOINTMENTS = (
        (REGULAR, 'обычная запись'),
        (EXTENDED, 'расширенная запись')
    )

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    record_type = models.CharField(max_length=20, choices=APPOINTMENTS, default=REGULAR)
    day = models.DateField()
    record_start_time = models.IntegerField(default=9, validators=[MinValueValidator(9), MaxValueValidator(21)])

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    @classmethod
    def create(cls, **kwargs):
        record = cls(**kwargs)
        return record
