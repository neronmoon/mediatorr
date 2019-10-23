import hashlib
import logging
import re
import threading
import time

import inject
import simplejson


class Handler:
    help = 'Fill this help message'
    commands = None
    content_types = ['text']
    regexp = None
    func = None

    def __init__(self, bot):
        self.bot = bot

    def handle(self, message):
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


class CrossLinkHandler(Handler):
    prefix = 'NOT_EXISTING_COMMAND'

    db = inject.attr('db')

    @property
    def regexp(self):
        return self.prefix + '(.*)'

    def get_payload(self, message):
        cross_link_id = re.search(self.regexp, message.text).group(1)
        return self.db.get(cross_link_id)

    @staticmethod
    def store_link(prefix, payload):
        db = inject.instance('db')
        key = CrossLinkHandler.__get_cache_key(payload, prefix)
        if not db.exists(key):
            link_id = int(db.get('last_link_id') or "0") + 1
            db.set(str(link_id), payload)
            db.set('last_link_id', link_id)
            db.set(key, link_id)
        else:
            link_id = db.get(key)
        return "/%s%s" % (prefix, link_id,)

    @staticmethod
    def __get_cache_key(payload, prefix):
        return hashlib.md5(simplejson.dumps({'prefix': prefix, 'payload': payload}).encode()).hexdigest()
