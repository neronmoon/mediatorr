from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import json, threading, inject, telebot, time


class LiveMessage:
    live_thread = None
    live_update = True
    live_update_timeout = 2

    bot = inject.attr('bot')

    def __init__(self, chat_id, update_message_handler):
        self.chat_id = chat_id
        self.update_message_handler = update_message_handler

    def start(self):
        if self.live_thread is not None:
            self.live_update = False
            self.live_thread.join()
            self.live_thread = None

        self.live_thread = threading.Thread(target=self.update)
        self.live_update = True
        self.live_thread.start()

    def stop(self):
        self.live_update = False
        if threading.current_thread().ident != self.live_thread.ident:
            self.live_thread.join(self.live_update_timeout)

    def update(self):
        while self.live_update:
            try:
                self.update_message_handler()
            except telebot.apihelper.ApiException as e:
                pass
            time.sleep(self.live_update_timeout)


def paginate(pattern, items, page, page_size=10):
    offset = page_size * (page - 1)
    limit = page_size * page
    pages_count = (len(items) + page_size - 1) // page_size
    return {
        'text': "[No items]" if len(items) == 0 else '\n'.join(items[offset:limit]),
        'reply_markup': keyboard(pattern, page, pages_count)
    }


def keyboard(pattern, page, pages_count, buttons_count=5):
    if pages_count < 2:
        pages_count = 1
    if page < 1:
        page = 1
    if page > pages_count:
        page = pages_count

    marks = ['« ', '< ', '·', ' >', ' »']
    buttons = {}

    if pages_count > buttons_count:
        left = page - (buttons_count // 2)
        right = page + (buttons_count // 2)

        if left < 1:
            left = 1
            right = buttons_count
        if right > pages_count:
            right = pages_count
            left = pages_count - buttons_count + 1

        for i in range(left, right + 1):
            if i < page:
                buttons[i] = marks[1] + str(i)
            elif i == page:
                buttons[i] = marks[2] + str(i) + marks[2]
            elif i > page:
                buttons[i] = str(i) + marks[3]

        if buttons[left].startswith(marks[1]):
            del buttons[left]
            buttons[1] = marks[0] + '1'
        if buttons[right].endswith(marks[3]):
            del buttons[right]
            buttons[pages_count] = str(pages_count) + marks[4]

    else:
        for i in range(1, pages_count + 1):
            if i == page:
                buttons[i] = marks[2] + str(i) + marks[2]
            else:
                buttons[i] = str(i)

    button_row = [
        InlineKeyboardButton(
            text=buttons[key],
            callback_data=json.dumps({'path': pattern.format(page=key)})
        ) for key in sorted(buttons.keys())
    ]
    markup = InlineKeyboardMarkup()
    if len(button_row) > 1:
        markup.row(*button_row)
    return markup
