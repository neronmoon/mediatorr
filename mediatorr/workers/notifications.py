from mediatorr.workers.worker import Worker
from mediatorr.models.torrent import *
from mediatorr.views.torrent import status_line
import inject


class NotifyOnDownloadCompleteWorker(Worker):
    torrent = inject.attr('torrent_service')
    bot = inject.attr('bot')
    config = inject.attr('config')

    state = {}

    def on_start(self):
        self.reset_state(self.torrent.list())

    def tick(self):
        torrents = self.torrent.list()
        for torrent in torrents:
            hash = torrent.get('hash')
            state = torrent.get('state')
            states_filter = [TORRENT_STATE_OK, TORRENT_STATE_DOWNLOADING]
            if state in states_filter:
                if hash in self.state and state != self.state[hash]:
                    self._notify(state, torrent)
                elif hash not in self.state:
                    self._notify(state, torrent)
        self.reset_state(torrents)

    def _notify(self, state, torrent):
        self.bot.send_message(
            chat_id=self.config.get('notifications').get('chat_id'),
            text="%s is now <b>%s</b>!\n /details%s" % (
                status_line(torrent, links=False, progress=False),
                state,
                torrent.doc_id
            ),
            parse_mode='html'
        )

    def reset_state(self, state):
        for torrent in state:
            self.state[torrent.get('hash')] = torrent.get('state')


class StartupNotificationWorker(Worker):
    bot = inject.attr('bot')
    config = inject.attr('config')

    def on_start(self):
        self.bot.send_message(
            chat_id=self.config.get('notifications').get('chat_id'),
            text="🍿Mediatorr🍿 is up!"
        )
        self.stop()
