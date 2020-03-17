import inject

from mediatorr.models.search import SearchResult

from mediatorr.utils.telegram import LiveMessage
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import detail_view


class DownloadTorrentController(Controller):
    patterns = [
        r"^/download(?P<search_id>\d+)$",
    ]

    torrent_service = inject.attr('torrent_service')
    bot = inject.attr('bot')
    search_service = inject.attr('search_service')
    live_message = None

    def __init__(self, params):
        self.search_result = SearchResult.get_by_id(params.get('search_id'))

    def handle(self, message):
        self.torrent_service.download(self.search_result)
        if self.live_message is not None:
            self.live_message.stop()
        self.live_message = LiveMessage(
            message.chat.id, lambda: self.update(self.search_result)
        )
        self.live_message.start()

    def update(self, search_result):
        model = self.torrent_service.get_model(search_result.id)
        if model:
            self.update_message(**detail_view(model))
        else:
            self.update_message(**{'text': "Torrent not found!"})
            self.live_message.stop()
