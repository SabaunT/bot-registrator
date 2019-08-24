from django.core.management.base import BaseCommand
from apps.tf_bot.bot import main

class Command(BaseCommand):
    help = "Up bot"

    def handle(self, *args, **options):
        main()