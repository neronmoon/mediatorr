import inject, logging, time, threading


class Controller:
    bot = inject.attr('bot')

    message = None
    __was_updated = False

    def __init__(self, params):
        self.params = params

    def update_message(self, count_update=True, **kwargs):
        text_has_changed = 'text' in kwargs and self.message.text != kwargs.get('text')
        if not text_has_changed and 'reply_markup' not in kwargs:
            return
        if count_update:
            self.__was_updated = True
        args = {
            'message_id': self.message.message_id,
            'chat_id': self.message.chat.id,
            'parse_mode': 'html',
            **kwargs
        }
        try:
            self.message = self.bot.edit_message_text(**args)
        except Exception as e:
            if "specified new message content and reply markup are exactly the same" not in e.args[0]:
                del args['message_id']
                self.message = self.bot.send_message(**args)

    def run(self, is_callback, message):
        if is_callback:
            self.message = message
        else:
            self.message = self.reply_to(message, text="🤔 Processing..")
        try:
            self.handle(self.message, is_callback=is_callback)
            if not self.__was_updated and not is_callback:
                self.update_message(text="✅ OK!")
        except Exception as e:
            self.delete_message(self.message)
            self.reply_to(message, text="🚫" + repr(e))
            logging.error(e, exc_info=True)
            raise e

    def __delay_remove_message(self, message, timeout=1):
        def worker():
            time.sleep(timeout)
            self.delete_message(message)

        thread = threading.Thread(target=worker)
        thread.start()

    def delete_message(self, msg):
        try:
            self.bot.delete_message(msg.chat.id, msg.message_id)
        except Exception as e:
            logging.warning("Tried to delete already deleted message with id %s in chat %s" % (
                msg.message_id, msg.chat.id,
            ))

    def reply_to(self, message, **kwargs):
        args = kwargs
        try:
            text = kwargs['text']
            del kwargs['text']
            return self.bot.reply_to(message, text, **kwargs)
        except Exception as e:
            logging.warning("Tried to reply to deleted message id %s in chat %s" % (
                message.message_id, message.chat.id,
            ))
            return self.bot.send_message(**args)

    def flash_message(self, message=None, timeout=5, **kwargs):
        msg = self.reply_to(message, **kwargs) if message else self.bot.send_message(**kwargs)
        self.__delay_remove_message(msg, timeout)

    def handle(self, message, **kwargs):
        pass
