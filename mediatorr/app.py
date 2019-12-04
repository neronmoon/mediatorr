import telebot
import tmdbsimple as tmdb
import tinydb
import logging
import mediatorr.config as config
from mediatorr.services.command_processor import CommandProcessor
from mediatorr.controllers.search_torrent import *
from mediatorr.controllers.control_torrent import *
from mediatorr.controllers.download_torrent import *
from mediatorr.services.torrent_search import TorrentSearchService
from mediatorr.services.torrent_client import TorrentClient
from mediatorr.services.api.jackett import Jackett
from qbittorrentapi import Client
from mediatorr.services.tinydb_storage import ThreadSafeJSONStorage
from mediatorr.workers.notifications import NotifyOnDownloadCompleteWorker


class App:
    def __init__(self):
        self.workers = [
            NotifyOnDownloadCompleteWorker
        ]
        self.running_workers = []
        self.__configure()

    def __configure(self):
        self.__configure_services()

    def __configure_services(self):
        def configurator(binder):
            cfg = config.app
            logging_level = logging.getLevelName(cfg.get('logging', {}).get('level', 'INFO'))
            logging.getLogger().setLevel(logging_level)
            telebot.logger.setLevel(logging_level)
            binder.bind('app', self)
            binder.bind('config', cfg)
            processor = self.__make_processor()
            binder.bind('processor', processor)
            bot = telebot.TeleBot(cfg.get('telegram').get('token'))
            bot.add_message_handler({
                'function': processor.process_message,
                'filters': {'content_types': ['text']},
                'instance': processor
            })
            bot.add_message_handler({
                'function': processor.process_file,
                'filters': {'content_types': ['document']},
                'instance': processor
            })
            bot.add_callback_query_handler({
                'function': processor.process_callback,
                'filters': {'func': lambda _1: True},
                'instance': processor
            })
            binder.bind('bot', bot)
            db = tinydb.TinyDB(cfg.get('db').get('path'), storage=ThreadSafeJSONStorage)
            binder.bind('db', db)
            jackett = Jackett(cfg.get('jackett').get('url'), cfg.get('jackett').get('token'))
            binder.bind('search_service', TorrentSearchService(db, jackett))
            torrent_config = cfg.get('qbittorrent')
            qbittorrent = Client(
                host=torrent_config.get('url'),
                username=torrent_config.get('username'),
                password=torrent_config.get('password'),
                RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS=True
            )
            binder.bind('torrent_service', TorrentClient(db, qbittorrent))
            tmdb.API_KEY = cfg.get('tmdb').get('token')
            binder.bind('catalog', tmdb)

        inject.clear_and_configure(configurator)

    def __make_processor(self):
        processor = CommandProcessor()
        processor.connect(SearchTorrentController)
        processor.connect(ControlTorrentController)
        processor.connect(DownloadTorrentController)
        return processor

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
