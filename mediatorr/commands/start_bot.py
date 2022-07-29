import inject
import logging

from mediatorr.workers.notifications import NotifyOnDownloadCompleteWorker, StartupNotificationWorker, \
    FollowNotificationsWorker
from mediatorr.workers.system import NotifyLowMemoryWorker


class StartBotCommand:
    command = 'start'
    help = 'Starts bot'
    bot = inject.attr('bot')

    def __init__(self):
        self.workers = [
            NotifyOnDownloadCompleteWorker,
            FollowNotificationsWorker,
            StartupNotificationWorker,
            NotifyLowMemoryWorker
        ]
        self.running_workers = []

    @staticmethod
    def configure(parser):
        pass

    def handle(self, args):
        logging.info("Starting workers!")
        self.__start_workers()
        logging.info("Bot is running!")
        self.bot.infinity_polling()

        for worker in self.running_workers:
            worker.stop()
            worker.join(worker.interval)

    def __start_workers(self):
        for worker in self.workers:
            w = worker()
            w.start()
            self.running_workers.append(w)
