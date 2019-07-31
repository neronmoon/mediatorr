import threading
import time

import inject

from mediatorr.handlers.handler import Handler, CrossLinkHandler
from mediatorr.utils.string import sizeof_fmt, time_fmt


class TorrentListHandler(Handler):
    help = 'List of added torrents'
    commands = ['torrents', 'list', 'tl']
    torrent = inject.attr('torrent')
    db = inject.attr('db')

    live_thread = None
    live_update = True
    live_update_timeout = 2

    def run(self, message):
        response = self.build_response()
        msg = self.bot.send_message(chat_id=message.chat.id, text=response, parse_mode='markdown')

        if self.live_thread is not None:
            self.live_update = False
            self.live_thread.join()
            self.live_thread = None

        self.live_thread = threading.Thread(target=self.update, args=(msg,))
        self.live_update = True
        self.live_thread.start()

    def update(self, msg):
        while self.live_update:
            time.sleep(self.live_update_timeout)
            try:
                msg = self.bot.edit_message_text(
                    self.build_response(),
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    parse_mode='markdown'
                )
            except:
                pass

    def build_response(self):
        response = []
        torrents = self.torrent.torrents()
        torrents.sort(key=lambda x: x['state'])
        for trt in torrents:
            response.append(self.__make_torrent_status_string(trt))
        response.append("/resumeall    /pauseall")
        return '\n'.join(response)

    @staticmethod
    def __make_torrent_status_string(torrent):
        statuses = {
            'error': '🚫',
            'pausedUP': '✅',
            'pausedDL': '⏸️',
            'queuedUP': '[Q]',
            'queuedDL': '[Q]',
            'uploading': '✅',
            'stalledUP': '✅',
            'checkingUP': '🤔',
            'checkingDL': '🤔',
            'downloading': '🔄',
            'stalledDL': '🔄',
            'metaDL': '🔄',
        }

        chunks = [
            statuses[torrent['state']]
        ]
        if torrent['progress'] != 1:
            chunks.append("*{:.0%}*".format(torrent['progress']))
        chunks.append('{0}'.format(torrent['name']))
        is_downloading = torrent['state'] in ['downloading', 'stalledDL', 'metaDL']
        if is_downloading:
            chunks.append("*| %s |*" % sizeof_fmt(torrent['dlspeed'], 'B/s'))
            chunks.append(time_fmt(torrent['eta']))

        if is_downloading:
            chunks.append("\n%s" % CrossLinkHandler.store_link(TorrentPauseHandler.prefix, torrent['hash']))
        elif torrent['state'] == 'pausedDL':
            chunks.append("\n%s" % CrossLinkHandler.store_link(TorrentResumeHandler.prefix, torrent['hash']))
        else:
            chunks.append("\n")
        chunks.append("%s\n" % CrossLinkHandler.store_link(TorrentDeleteHandler.prefix, torrent['hash']))

        return " ".join(chunks)


class TorrentPauseAllHandler(Handler):
    help = 'Pause all torrents'
    commands = ['pauseall']
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.pause_all()


class TorrentPauseHandler(CrossLinkHandler):
    prefix = "pauseone"
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.pause(self.get_payload(message))


class TorrentResumeAllHandler(Handler):
    help = 'Resume all torrents'
    commands = ['resumeall']
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.resume_all()


class TorrentResumeHandler(CrossLinkHandler):
    prefix = "resumeone"
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.resume(self.get_payload(message))


class TorrentDeleteHandler(CrossLinkHandler):
    prefix = "delete"
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.delete_permanently(self.get_payload(message))