from telebot.types import InlineKeyboardButton

from mediatorr.models.following import FollowSearch
from mediatorr.utils.string import sizeof_fmt
import json
import PTN

from mediatorr.utils.telegram import paginate


def search_view(query_model, results, chat_id, page=1):
    paginated = paginate(
        '/search_results_paginate_%s_{page}' % query_model.id,
        list(map(search_line, results)),
        page
    )
    paginated['parse_mode'] = 'html'
    paginated.get('reply_markup').row(follow_button(chat_id, query_model, page=page))
    return paginated


def follow_button(chat_id, query_model, page=1):
    params = {'query_id': query_model.id, 'chat_id': chat_id}
    task = FollowSearch.get_or_none(**params)
    next_action_pattern = 'unfollow' if task is not None else 'follow'
    return InlineKeyboardButton(
        text=next_action_pattern.capitalize(),
        callback_data=json.dumps({'path': '/%s%s %s' % (next_action_pattern, query_model.id, page)}))


def search_line(result_model):
    info = PTN.parse(result_model.title)
    badges = []
    if 'year' in info:
        badges.append('[%s]' % info['year'])
    if 'resolution' in info:
        badges.append('[%s]' % info['resolution'])
    if 'orig' in result_model.title:
        badges.append('[original]')
    if ' sub' in result_model.title:
        badges.append('[SUBS]')
    badges.append("[%s]" % sizeof_fmt(result_model.size))
    badges.append("[Seeds: %s]" % (result_model.seeds + result_model.leech))

    badges_string = "" if not badges else " <b>%s</b> " % ("".join(badges))
    return '🍿{badges}\n{title}\n/download{link_id}\n'.format(
        link_id=result_model.id, badges=badges_string, title=result_model.title)
