import telebot
import tmdbsimple as tmdb
import logging
import sentry_sdk
import mediatorr.config as config
from mediatorr.controllers.follow_manage_controller import FollowManageController
from mediatorr.services.command_processor import CommandProcessor
from mediatorr.controllers.search_torrent_controller import *
from mediatorr.controllers.control_torrent_controller import *
from mediatorr.controllers.download_torrent_controller import *
from mediatorr.services.torrent_search_service import TorrentSearchService
from mediatorr.services.torrent_client_service import TorrentClientService
from mediatorr.services.api.jackett import Jackett
from qbittorrentapi import Client
from peewee import *


class Configurator:
    def configure(self):
        self.__configure_services()

    def __configure_services(self):
        def configurator(binder):
            cfg = config.app
            logging_level = logging.getLevelName(cfg.get('logging', {}).get('level', 'INFO'))
            logger = logging.getLogger()
            logger.setLevel(logging_level)

            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%d-%m-%Y %H:%M:%S")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            telebot.logger.setLevel(logging_level)
            binder.bind('config', cfg)
            db = self.__make_db(cfg)
            binder.bind('db', db)
            binder.bind('bot', self.__make_bot(cfg, self.__make_processor()))
            jackett = Jackett(cfg.get('jackett').get('url'), cfg.get('jackett').get('token'))
            binder.bind('search_service', TorrentSearchService(db, jackett))
            torrent_config = cfg.get('qbittorrent')
            qbittorrent = Client(
                host=torrent_config.get('url'),
                username=torrent_config.get('username'),
                password=torrent_config.get('password'),
                RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS=True
            )
            binder.bind('torrent_service', TorrentClientService(db, qbittorrent))
            tmdb.API_KEY = cfg.get('tmdb').get('token')
            binder.bind('catalog', tmdb)
            sentry_cfg = cfg.get('sentry', None)
            if sentry_cfg:
                sentry_sdk.init(sentry_cfg.get('dsn'))

        inject.clear_and_configure(configurator)

    def __make_db(self, cfg):
        db_cfg = cfg.get('db')
        db = MySQLDatabase(db_cfg.pop('name'), **db_cfg)
        from mediatorr.models.model import database_proxy
        database_proxy.initialize(db)
        return db

    def __make_processor(self):
        processor = CommandProcessor()
        processor.connect(SearchTorrentController)
        processor.connect(ControlTorrentController)
        processor.connect(DownloadTorrentController)
        processor.connect(FollowManageController)
        return processor

    def __make_bot(self, config, processor):
        bot = telebot.TeleBot(
            config.get('telegram').get('token'),
            threaded=True
        )
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
        return bot
