from django.core.management.base import BaseCommand
from apps.tf_bot.bot import TFBot

class Command(BaseCommand):
    help = "Up bot"

    def handle(self, *args, **options):
        tf_bot = TFBot()
        tf_bot.setup()
        tf_bot.run()
