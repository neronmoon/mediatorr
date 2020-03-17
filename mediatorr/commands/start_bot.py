import inject
import logging

from mediatorr.workers.notifications import NotifyOnDownloadCompleteWorker, StartupNotificationWorker, \
    FollowNotificationsWorker


class StartBotCommand:
    command = 'start'
    help = 'Starts bot'
    bot = inject.attr('bot')

    def __init__(self):
        self.workers = [
            NotifyOnDownloadCompleteWorker,
            FollowNotificationsWorker,
            StartupNotificationWorker
        ]
        self.running_workers = []

    @staticmethod
    def configure(parser):
        pass

    def handle(self, args):
        logging.info("Starting workers!")
        self.__start_workers()
        logging.info("Bot is running!")
        self.bot.polling()

        for worker in self.running_workers:
            worker.stop()
            worker.join(worker.interval)

    def __start_workers(self):
        for worker in self.workers:
            w = worker()
            w.start()
            self.running_workers.append(w)
