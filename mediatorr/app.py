import logging

import pickledb
import telebot
from qbittorrent import Client
import tmdbsimple as tmdb
import mediatorr.config as config
from mediatorr.handlers.torrent import *
from mediatorr.handlers.catalog import *
from mediatorr.handlers.cross_link import *
from mediatorr.services.jackett import Jackett


class App:
    def __init__(self):
        self.handlers = [
            TorrentListHandler,
            TorrentPauseAllHandler,
            TorrentResumeAllHandler,
            TorrentPauseHandler,
            TorrentResumeHandler,
            TorrentDeleteHandler,
            TorrentSearchHandler,
            TorrentUploadHandler,
            TorrentSearchDownloadHandler,
            TorrentCatalogSearchHandler,
            CatalogSearchHandler,
            CatalogInfoHandler,
        ]
        self.__configure()

    def __configure(self):
        self.__configure_services()
        self.__register_handlers()

    def __configure_services(self):
        def configurator(binder):
            cfg = config.app
            binder.bind('app', self)
            binder.bind('config', cfg)
            telebot.logger.setLevel(logging.DEBUG)
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
            binder.bind('db', pickledb.load(cfg.get('db').get('path'), False))
            tmdb.API_KEY = cfg.get('tmdb').get('token')
            binder.bind('catalog', tmdb)

        inject.clear_and_configure(configurator)

    def __register_handlers(self):
        bot = inject.instance('bot')
        for handler in self.handlers:
            instance = handler(bot)
            bot.add_message_handler({
                'function': instance.handle,
                'filters': {
                    'commands': instance.commands,
                    'content_types': instance.content_types,
                    'regexp': instance.regexp,
                    'func': instance.func
                },
                'instance': instance
            })

    def run(self):
        try:
            print("Bot is running!")
            inject.instance('bot').polling()
        finally:
            inject.instance('db').dump()
