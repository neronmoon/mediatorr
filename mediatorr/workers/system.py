from mediatorr.utils.string import convert_to_seconds
from mediatorr.workers.worker import Worker
import inject
import psutil


class ReconnectDatabaseWorker(Worker):
    db = inject.attr('db')

    interval = convert_to_seconds('1m')

    def tick(self):
        self.db.connect(True)


class NotifyLowMemoryWorker(Worker):
    interval = convert_to_seconds('1m')
    config = inject.attr('config')
    bot = inject.attr('bot')

    def __init__(self):
        super().__init__()
        self.__is_ok = True

    def tick(self):
        hdd = psutil.disk_usage('/')

        is_now_ok = hdd.free / hdd.total <= 0.1
        if self.__is_ok != is_now_ok:
            self.__is_ok = is_now_ok
            self.bot.send_message(
                chat_id=self.config.get('notifications').get('chat_id'),
                text="%s Free memory is %s!" % (
                    "✅" if self.__is_ok else "🔥",
                    "OK" if self.__is_ok else "LOW"
                ),
                parse_mode='html'
            )
