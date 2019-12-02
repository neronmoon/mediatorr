from mediatorr.workers.worker import Worker
import inject


class NotifyOnDownloadCompleteWorker(Worker):
    torrent = inject.attr('torrent')
    bot = inject.attr('bot')
    config = inject.attr('config')

    state = {}

    def on_start(self):
        self.reset_state(self.torrent.torrents())

    def tick(self):
        torrents = self.torrent.torrents()
        for torrent in torrents:
            hash = torrent.get('hash')
            if hash in self.state and torrent.get('state') != self.state[hash]:
                self.bot.send_message(
                    chat_id=self.config.get('notifications').get('chat_id'),
                    text="%s is now <b>%s</b>:\n\n%s" % (
                        torrent.get('name'), torrent.get('state'),
                        torrent.make_status_string()
                    ),
                    parse_mode='html'
                )
        self.reset_state(torrents)

    def reset_state(self, state):
        for torrent in state:
            self.state[torrent.get('hash')] = torrent.get('state')
