import inject

from mediatorr.models.following import FollowSearch
from mediatorr.models.search import SearchQuery
from mediatorr.controllers.controller import Controller
from mediatorr.views.search import search_view


class SearchTorrentController(Controller):
    patterns = [
        "^(?P<text>[^/].*)",
        r'^/search_results_paginate_(?P<query_id>.*)_(?P<page>\d+)$',
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
        self.update_message(**search_view(query_model, results, message.chat.id, page=self.page))

    def __handle_following_callback(self, query_model, message):
        params = {'query_id': query_model.id, 'chat_id': message.chat.id}
        task = FollowSearch.get_or_none(**params)
        if self.should_follow and task is None:
            FollowSearch(**params).save()
        elif not self.should_follow and task is not None:
            task.delete_instance()
