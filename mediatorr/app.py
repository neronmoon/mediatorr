import telebot
import tmdbsimple as tmdb
import tinydb
import logging
import mediatorr.config as config
from mediatorr.handlers.torrent import *
from mediatorr.handlers.torrent_contol import *
from mediatorr.services.jackett import Jackett
from mediatorr.services.qbittorrent import Client
from mediatorr.services.tinydb_storage import ThreadSafeJSONStorage
from mediatorr.workers.notifications import NotifyOnDownloadCompleteWorker


class App:
    def __init__(self):
        self.handlers = [
            TorrentListHandler,
            TorrentSearchHandler,
            TorrentUploadHandler,
            TorrentSearchDownloadHandler,
        ]
        self.workers = [
            NotifyOnDownloadCompleteWorker
        ]
        self.running_workers = []
        self.__configure()

    def __configure(self):
        self.__configure_services()
        self.__register_handlers()

    def __configure_services(self):
        def configurator(binder):
            cfg = config.app
            logging_level = logging.getLevelName(cfg.get('logging', {}).get('level', 'INFO'))
            binder.bind('app', self)
            binder.bind('config', cfg)
            logging.getLogger().setLevel(logging_level)
            telebot.logger.setLevel(logging_level)
            binder.bind('bot', telebot.TeleBot(cfg.get('telegram').get('token')))
            binder.bind('jackett', Jackett(
                cfg.get('jackett').get('url'),
                cfg.get('jackett').get('token')
            ))
            torrent_client = Client(cfg.get('qbittorrent').get('url'))
            login_exception = torrent_client.login(
                cfg.get('qbittorrent').get('username'),
                cfg.get('qbittorrent').get('password')
            )
            if login_exception:
                raise Exception(login_exception)
            binder.bind('torrent', torrent_client)
            binder.bind('db', tinydb.TinyDB(
                cfg.get('db').get('path'),
                storage=ThreadSafeJSONStorage
            ))
            tmdb.API_KEY = cfg.get('tmdb').get('token')
            binder.bind('catalog', tmdb)

        inject.clear_and_configure(configurator)

    def __register_handlers(self):
        bot = inject.instance('bot')
        for handler in self.handlers:
            instance = handler(bot)
            bot.add_message_handler({
                'function': instance.handle_message,
                'filters': {
                    'commands': instance.commands,
                    'content_types': instance.content_types,
                    'regexp': instance.regexp,
                    'func': instance.func
                },
                'instance': instance
            })
            if instance.callback_func is not None:
                bot.add_callback_query_handler({
                    'function': instance.handle_callback,
                    'filters': {
                        'func': instance.callback_func
                    },
                    'instance': instance
                })

    def __start_workers(self):
        for worker in self.workers:
            w = worker()
            w.start()
            self.running_workers.append(w)

    def run(self):
        print("Starting workers!")
        self.__start_workers()
        print("Bot is running!")
        inject.instance('bot').polling()
