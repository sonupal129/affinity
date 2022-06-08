from django.core.management.base import BaseCommand, CommandError
from trading.trading import Trader

class Command(BaseCommand):
    help = 'Start trade worker'


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting trade'))
        Trader(stoploss=0.0005, target=0.0008).start_trading()