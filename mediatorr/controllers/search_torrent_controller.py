import inject

from mediatorr.models.search import SearchQuery
from mediatorr.controllers.controller import Controller
from mediatorr.views.search import search_view


class SearchTorrentController(Controller):
    patterns = [
        "^(?P<text>[^/].*)",
        "^/search\s+(?P<text>[^/].*)",
        "^/s\s+(?P<text>[^/].*)",
        r'^/search_results_paginate_(?P<query_id>.*)_(?P<page>\d+)$',
    ]

    search_service = inject.attr('search_service')

    def __init__(self, params):
        super().__init__(params)
        if 'text' in params:
            self.text = params.get('text').lower()
        else:
            self.text = SearchQuery.get_by_id(params.get('query_id')).query
        page = params.get('page', 1)
        self.page = int(page if page != '' else 1)

    def handle(self, message, **kwargs):
        query_model, results = self.search_service.search(self.text)
        self.update_message(**search_view(query_model, results, message.chat.id, page=self.page))
