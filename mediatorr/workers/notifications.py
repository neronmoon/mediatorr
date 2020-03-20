from mediatorr.models.following import FollowSearch
from mediatorr.utils.string import convert_to_seconds
from mediatorr.views.search import search_view
from mediatorr.workers.worker import Worker
from mediatorr.models.torrent import *
from mediatorr.views.torrent import status_line
import inject
import logging


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
            if state in [TORRENT_STATE_OK]:
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
                torrent.search_model_id()
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


class FollowNotificationsWorker(Worker):
    bot = inject.attr('bot')
    config = inject.attr('config')
    search_service = inject.attr('search_service')

    def __init__(self):
        super().__init__()
        self.interval = convert_to_seconds(self.config.get('notifications').get('follow_check_interval'))

    def tick(self):
        for model in FollowSearch.select().group_by(FollowSearch.query).execute():
            logging.info("[FollowNotificationsWorker] Searching for `%s`" % model.query.query)
            updates = []

            old_results = SearchResult.select().where(SearchResult.query == model.query).execute()
            old_hashes = list(map(lambda x: x.unique_id, old_results))
            query_model, new_results = self.search_service.search(model.query.query)

            for item in new_results:
                if item.unique_id not in old_hashes:
                    updates.append(item)
                else:
                    old_item = next(x for x in old_results if x.unique_id == item.unique_id)
                    if item.size != old_item.size:
                        updates.append(item)
            if updates:
                logging.info("[FollowNotificationsWorker] Found updates! Sending message")
                msg_params = search_view(query_model, updates, model.chat_id)
                greeting_text = "<b>🔥🔥🔥 Here is updates for `%s` query! 🔥🔥🔥</b>" % query_model.query
                items_text = msg_params['text']
                del msg_params['text']
                message = self.bot.send_message(model.chat_id, greeting_text, parse_mode='html')
                self.bot.reply_to(message, items_text, **msg_params)
            else:
                logging.info("[FollowNotificationsWorker] Updates not found!")
