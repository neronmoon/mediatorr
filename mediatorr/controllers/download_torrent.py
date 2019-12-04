import inject

from mediatorr.models.search import TorrentSearchResult

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
        self.search_id = int(params.get('search_id'))

    def handle(self, message):
        model = TorrentSearchResult.fetch(doc_id=self.search_id)
        torrent_model = self.torrent_service.download(model)
        if self.live_message is not None:
            self.live_message.stop()
        self.live_message = LiveMessage(
            message.chat.id, lambda: self.update(torrent_model.doc_id)
        )
        self.live_message.start()

    def update(self, id):
        model = self.torrent_service.get_model(id)
        self.update_message(**detail_view(model))
