import inject
from mediatorr.utils.telegram import paginate
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import search_line


class SearchTorrentController(Controller):
    patterns = [r"^(?P<text>[^/].*)", r'^/s_(?P<query_id>.*)_p_(?P<page>\d+)$']

    search_service = inject.attr('search_service')
    db = inject.attr('db')
    bot = inject.attr('bot')

    def __init__(self, params):
        self.page = int(params.get('page', 1))
        if 'query_id' in params:
            self.text = self.db.table('search_queries').get(doc_id=int(params.get('query_id'))).get('text')
        else:
            self.text = params.get('text')

    def handle(self, message):
        results, query_id = self.search_service.search(self.text)
        paginated = paginate(
            '/s_%s_p_{page}' % query_id,
            list(map(search_line, results)),
            self.page
        )
        self.update_message(**paginated)

