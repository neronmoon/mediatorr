import inject
from mediatorr.utils.telegram import LiveMessage
from mediatorr.controllers.controller import Controller
from mediatorr.views.torrent import list_view, detail_view


class ControlTorrentController(Controller):
    patterns = [
        r"^/(?P<action>(details|pause|resume|delete))(?P<torrent_id>(\d+)|all)$",
        r"^/(?P<action>(list))$",
    ]

    torrent = inject.attr('torrent_service')
    bot = inject.attr('bot')
    list_message = None
    details_message = None

    def __init__(self, params):
        self.action = params.get('action', 1)
        self.torrent_id = params.get('torrent_id', None)
        if self.torrent_id == 'all':
            self.torrent_id = None
        if self.torrent_id is not None:
            self.torrent_id = int(self.torrent_id)

    def handle(self, message):
        if self.action == 'details':
            if self.details_message is not None:
                self.details_message.stop()
            self.details_message = LiveMessage(
                message.chat.id, lambda: self.update_details(self.torrent_id)
            )
            self.details_message.start()
        if self.action == 'list':
            if self.list_message is not None:
                self.list_message.stop()
            self.list_message = LiveMessage(message.chat.id, self.update_list)
            self.list_message.start()
        elif self.action == 'pause':
            self.torrent.pause_all() if self.torrent_id is None else self.torrent.pause(self.torrent_id)
        elif self.action == 'resume':
            self.torrent.resume_all() if self.torrent_id is None else self.torrent.resume(self.torrent_id)
        elif self.action == 'delete':
            self.torrent.delete(self.torrent_id)
            self.update_message(text="Torrent deleted")

    def update_details(self, id):
        model = self.torrent.get_model(id)
        self.update_message(**detail_view(model))

    def update_list(self):
        self.update_message(**list_view(self.torrent.list()))
