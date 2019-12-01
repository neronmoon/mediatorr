from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import json


def pagination_keyboard(cache_key, page_no, pages_count, buttons_count=5, marks=None):
    """
    Buttons for pagers.
    Helper function for telebot library (https://github.com/eternnoir/pyTelegramBotAPI).
    Creates a list of InlineKeyboardButtons like one in @music bot (https://t.me/music).

    Usage
    -----
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(*pager_buttons('list', 1, 10))
    Parameters
    ----------
    cache_key : str
        Prefix for callback_data. Use different for different list types.
    page_no : int
        Current page number
    pages_count : int
        Amount of pages
    buttons_count : int
        Optional: amount of buttons. Odd numbers recommended. Defaults to 5.
    marks : list of strings
        Optional: list of markings for buttons. Defaults to ['« ', '< ', '·', ' >', ' »']
    Returns
    -------
    list of telebot.types.InlineKeyboardButtons
    """
    if pages_count < 2:
        pages_count = 1
    if page_no < 1:
        page_no = 1
    if page_no > pages_count:
        page_no = pages_count

    if not marks:
        marks = ['« ', '< ', '·', ' >', ' »']
    buttons = {}

    if pages_count > buttons_count:
        left = page_no - (buttons_count // 2)
        right = page_no + (buttons_count // 2)

        if left < 1:
            left = 1
            right = buttons_count
        if right > pages_count:
            right = pages_count
            left = pages_count - buttons_count + 1

        for i in range(left, right + 1):
            if i < page_no:
                buttons[i] = marks[1] + str(i)
            elif i == page_no:
                buttons[i] = marks[2] + str(i) + marks[2]
            elif i > page_no:
                buttons[i] = str(i) + marks[3]

        if buttons[left].startswith(marks[1]):
            del buttons[left]
            buttons[1] = marks[0] + '1'
        if buttons[right].endswith(marks[3]):
            del buttons[right]
            buttons[pages_count] = str(pages_count) + marks[4]

    else:
        for i in range(1, pages_count + 1):
            if i == page_no:
                buttons[i] = marks[2] + str(i) + marks[2]
            else:
                buttons[i] = str(i)

    button_row = [
        InlineKeyboardButton(
            text=buttons[key],
            callback_data=json.dumps({'cache_key': cache_key, 'pages_count': pages_count, 'page': key})
        ) for key in sorted(buttons.keys())
    ]
    markup = InlineKeyboardMarkup()
    markup.row(*button_row)
    return markup
