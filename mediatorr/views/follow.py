import json

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def follow_list(models):
    follows = InlineKeyboardMarkup()
    for model in models:
        follows.row(InlineKeyboardButton(
            text="Unfollow `%s`" % model.query.query,
            callback_data=json.dumps({'path': '/unfollow%s_follow_list' % model.query.id})
        ))
    return {
        'text': "Following list:" if len(models) > 0 else "You don't follow anything",
        'reply_markup': follows,
        'parse_mode': 'html'
    }


