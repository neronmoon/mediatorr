import inject, logging, time, threading


class Controller:
    bot = inject.attr('bot')

    message = None
    __was_updated = False

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
        self.message = self.bot.edit_message_text(**args)

    def run(self, is_callback, message):
        if is_callback:
            self.message = message
        else:
            self.message = self.bot.reply_to(message, "🤔 Processing..")
        try:
            self.handle(self.message, is_callback=is_callback)
            if not self.__was_updated and not is_callback:
                self.update_message(text="✅ OK!")
        except Exception as e:
            self.bot.delete_message(self.message.chat.id, self.message.message_id)
            self.bot.reply_to(message, "🚫" + repr(e))
            logging.error(e, exc_info=True)
            raise e

    def __delay_remove_message(self, message, timeout=1):
        def worker():
            time.sleep(timeout)
            self.bot.delete_message(message.chat.id, self.message.message_id)

        thread = threading.Thread(target=worker)
        thread.start()

    def handle(self, message, **kwargs):
        pass
