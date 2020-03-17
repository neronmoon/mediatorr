import datetime
import json

import inject

from telebot.types import InlineKeyboardButton

from mediatorr.models.following import FollowSearch
from mediatorr.models.search import SearchQuery
from mediatorr.utils.telegram import paginate
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import search_line


class SearchTorrentController(Controller):
    patterns = [
        "^(?P<text>[^/].*)",
        r'^/s_(?P<query_id>.*)_p_(?P<page>\d+)$',
        r'^/(?P<follow_state>(un)?follow)(?P<query_id>\d+)\s?(?P<page>.*)$'
    ]

    search_service = inject.attr('search_service')

    def __init__(self, params):
        if 'text' in params:
            self.text = params.get('text').lower()
        else:
            self.text = SearchQuery.get_by_id(params.get('query_id')).query
        self.handle_follow = 'follow_state' in params
        self.should_follow = params.get('follow_state') == 'follow'
        self.page = int(params.get('page', 1))

    def handle(self, message, **kwargs):
        query_model, results = self.search_service.search(self.text)
        if self.handle_follow:
            self.__handle_following_callback(query_model, message)
        paginated = paginate(
            '/s_%s_p_{page}' % query_model.id,
            list(map(search_line, results)),
            self.page
        )
        paginated.get('reply_markup').row(self.__make_follow_button(message, query_model))
        self.update_message(**paginated)

    def __handle_following_callback(self, query_model, message):
        params = {'query_id': query_model.id, 'chat_id': message.chat.id}
        task = FollowSearch.get_or_none(**params)
        if self.should_follow and task is None:
            FollowSearch(**params).save()
        elif not self.should_follow and task is not None:
            task.delete_instance()

    def __make_follow_button(self, message, query_model):
        params = {'query_id': query_model.id, 'chat_id': message.chat.id}
        task = FollowSearch.get_or_none(**params)
        next_action_pattern = 'unfollow' if task is not None else 'follow'
        return InlineKeyboardButton(
            text=next_action_pattern.capitalize(),
            callback_data=json.dumps({'path': '/%s%s %s' % (next_action_pattern, query_model.id, self.page)}))
