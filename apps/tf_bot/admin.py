from django.contrib import admin
from apps.tf_bot.models import Record, Patient

# Register your models here.
@admin.register(Record)
class RecordsAdmin(admin.ModelAdmin):
    list_display = ('registered_patient', 'record_start_time', 'record_end_time')
    list_filter = ('record_start_time', 'record_end_time')
    search_fields = ['record_start_time', 'record_end_time']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'last_name', 'first_name', 'phone_number')
    search_fields = ['patient_id', 'telegram_id, phone_number', 'last_name']
