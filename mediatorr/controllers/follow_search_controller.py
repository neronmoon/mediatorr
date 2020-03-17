import datetime
import json

import inject

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from mediatorr.models.following import FollowSearch
from mediatorr.models.search import SearchQuery
from mediatorr.utils.telegram import paginate
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import search_line


class FollowSearchController(Controller):
    patterns = [r'^/(?P<is_not_following>(un)?)follow(?P<query_id>.*)$']

    def __init__(self, params):
        self.should_follow = params.get('is_not_following') != 'un'
        self.query = SearchQuery.get_by_id(params.get('query_id'))

    def handle(self, message):
        chat_id = message.chat.id
        params = {'query_id': self.query.id, 'chat_id': chat_id}
        task = FollowSearch.get_or_none(**params)
        if self.should_follow and task is None:
            FollowSearch(**params).save()
        elif not self.should_follow and task is not None:
            task.delete_instance()
        next_action_pattern = 'unfollow' if self.should_follow else 'follow'
        self.update_message(**{
            'text': 'You are%s following %s query now!' % ('' if self.should_follow else ' NOT', self.query.query,),
            'reply_markup': InlineKeyboardMarkup().row(
                InlineKeyboardButton(
                    next_action_pattern.capitalize(),
                    callback_data=json.dumps({'path': '/%s%s' % (next_action_pattern, self.query.id,)})
                ))})
