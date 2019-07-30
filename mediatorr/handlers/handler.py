import logging
import threading
import time


class Handler:
    help = 'Fill this help message'
    commands = None
    content_types = ['text']
    regexp = None
    func = None

    def __init__(self, bot):
        self.bot = bot

    def handle(self, message):
        process_message = self.bot.reply_to(
            message,
            "🤔 Processing.."
        )
        try:
            self.run(message)
            self.bot.edit_message_text(
                "✅ OK!",
                chat_id=process_message.chat.id,
                message_id=process_message.message_id
            )
            self.delay_remove_message(process_message.chat.id, process_message.message_id)
        except Exception as e:
            self.bot.delete_message(process_message.chat.id, process_message.message_id)
            self.bot.reply_to(message, "🚫" + repr(e))
            logging.error(e, exc_info=True)

    def get_clean_text(self, message):
        text = message.text
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
