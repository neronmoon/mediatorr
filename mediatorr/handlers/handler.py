import logging
import re

import telebot
from tinydb import Query
from mediatorr.models.link import Link
from mediatorr.utils.telegram_keyboard import pagination_keyboard
import inject
import threading
import time
import json


class Handler:
    help = 'Fill this help message'
    commands = None
    content_types = ['text']
    regexp = None
    func = None
    callback_func = None

    def __init__(self, bot):
        self.bot = bot

    def handle_message(self, message):
        logging.debug("Processing message %s with handler %s" % (message.text, type(self)))
        process_message = self.bot.reply_to(message, "🤔 Processing..")
        try:
            self.run(message)
            self.bot.edit_message_text("✅ OK!", chat_id=process_message.chat.id, message_id=process_message.message_id)
            self.delay_remove_message(process_message.chat.id, process_message.message_id)
        except Exception as e:
            self.bot.delete_message(process_message.chat.id, process_message.message_id)
            self.bot.reply_to(message, "🚫" + repr(e))
            logging.error(e, exc_info=True)
            raise e

    def handle_callback(self, data):
        logging.debug("Processing callback with handler %s" % (type(self)))
        try:
            self.on_callback(data)
        except Exception as e:
            logging.error(e, exc_info=True)
            self.bot.reply_to(data.message, "🚫" + repr(e))
            raise e

    def get_clean_text(self, message):
        text = message.text
        if self.commands is not None:
            for command in self.commands:
                text = text.replace('/%s' % command, '')
        return text

    def delay_remove_message(self, chat_id, message_id, timeout=1):
        def worker():
            time.sleep(timeout)
            self.bot.delete_message(chat_id, message_id)

        thread = threading.Thread(target=worker)
        thread.start()

    def run(self, message):
        raise Exception('Not implemented')

    def on_callback(self, data):
        raise Exception('Not implemented')


class LiveHandler(Handler):
    live_thread = None
    live_update = True
    live_update_timeout = 2

    def run(self, message):
        if self.live_thread is not None:
            self.live_update = False
            self.live_thread.join()
            self.live_thread = None

        self.live_thread = threading.Thread(target=self.update, args=(message.chat.id,))
        self.live_update = True
        self.live_thread.start()

    def update(self, chat_id=None):
        msg = None
        last_text = ""
        while self.live_update:
            try:
                response = self.make_message()
                if msg is None:
                    msg = self.bot.send_message(chat_id=chat_id, text=response, parse_mode='html')
                if msg is not None and last_text != response:
                    last_text = response
                    msg = self.bot.edit_message_text(
                        response,
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        parse_mode='html'
                    )
            except telebot.apihelper.ApiException as e:
                pass
            time.sleep(self.live_update_timeout)

    def make_message(self):
        pass


class CrossLinkHandler(Handler):
    prefix = 'NOT_EXISTING_COMMAND'

    db = inject.attr('db')

    @property
    def regexp(self):
        return self.prefix + '(\d+)'

    def get_payload(self, message):
        cl_id = re.search(self.regexp, message.text).group(1)
        return Link.get_table().get(doc_id=int(cl_id)).get('payload')

    @classmethod
    def make_link(cls, payload):
        link = Link(cls.prefix, payload)
        link_id = Link.get_table().upsert(link, Link.query().id == link.get('id'))[0]
        return "/%s%s" % (cls.prefix, link_id,)


class PaginatingHandler(Handler):
    db = inject.attr('db')
    prefix = 'pgr'
    page_size = 10
    callback_func = lambda _, cb: PaginatingHandler.prefix in cb.data

    def run(self, message):
        cache_key = self.__get_cache_key(message)
        items = self.get_items(message)
        self.db.table(self.__get_table_name()).upsert({
            'id': cache_key,
            'items': items
        }, Query().id == cache_key)
        pages_number = (len(items) + self.page_size - 1) // self.page_size
        self.bot.send_message(
            message.chat.id,
            text=self.__join_items(items, 1),
            reply_markup=pagination_keyboard(cache_key, 1, pages_number),
            parse_mode='html'
        )

    def on_callback(self, cb):
        cb_data = json.loads(cb.data)
        cache_key = cb_data.get('cache_key')
        pages_count = cb_data.get('pages_count')
        page = cb_data.get('page')
        items = self.db.table(self.__get_table_name()).get(Query().id == cache_key).get('items')
        self.bot.edit_message_text(
            text=self.__join_items(items, page),
            reply_markup=pagination_keyboard(cache_key, page, pages_count),
            message_id=cb.message.message_id,
            chat_id=cb.from_user.id,
            parse_mode='html'
        )

    def __get_cache_key(self, message):
        return self.prefix + str(message.message_id)

    def __get_table_name(self):
        return 'pagination_items_' + self.prefix

    def __join_items(self, items, page):
        offset = self.page_size * (page - 1)
        limit = self.page_size * page
        return '\n'.join(items[offset:limit])

    def get_items(self, message):
        return []
