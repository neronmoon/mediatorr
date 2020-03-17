import datetime
import json

import inject

from telebot.types import InlineKeyboardButton
from mediatorr.models.search import SearchQuery
from mediatorr.utils.telegram import paginate
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import search_line


class SearchTorrentController(Controller):
    patterns = [r"^(?P<text>[^/].*)", r'^/s_(?P<query_id>.*)_p_(?P<page>\d+)$']

    search_service = inject.attr('search_service')
    db = inject.attr('db')

    def __init__(self, params):
        if 'text' in params:
            self.text = params.get('text').lower()
        else:
            self.text = SearchQuery.get_by_id(params.get('query_id')).text
        self.page = int(params.get('page', 1))

    def handle(self, message):
        query_model, results = self.search_service.search(self.text)
        paginated = paginate(
            '/s_%s_p_{page}' % query_model.id,
            list(map(search_line, results)),
            self.page
        )
        paginated.get('reply_markup').row(
            InlineKeyboardButton(text="Follow", callback_data=json.dumps({'path': '/follow%s' % query_model.id}))
        )
        self.update_message(**paginated)
