import threading
import time

import PTN
import inject

from mediatorr.handlers.cross_link import CrossLinkHandler
from mediatorr.handlers.handler import Handler
from mediatorr.utils.file import download_telegram_file
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
            response.append(self.make_torrent_status_string(trt))
        response.append("/resumeall    /pauseall")
        return '\n'.join(response)

    def make_torrent_status_string(self, torrent):
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
            chunks.append("\nPause: %s" % CrossLinkHandler.store_link('pauseone', torrent['hash']))
        elif torrent['state'] == 'pausedDL':
            chunks.append("\nResume: %s" % CrossLinkHandler.store_link('resumeone', torrent['hash']))
        else:
            chunks.append("\n")
        chunks.append("Delete: %s\n" % CrossLinkHandler.store_link('delete', torrent['hash']))

        return " ".join(chunks)


class TorrentPauseAllHandler(Handler):
    help = 'Pause all torrents'
    commands = ['pauseall']
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.pause_all()


class TorrentPauseHandler(CrossLinkHandler):
    regexp = "pauseone(.*)"
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
    regexp = "resumeone(.*)"
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.resume(self.get_payload(message))


class TorrentDeleteHandler(CrossLinkHandler):
    regexp = "delete(.*)"
    torrent = inject.attr('torrent')

    def run(self, message):
        self.torrent.delete_permanently(self.get_payload(message))


class TorrentUploadHandler(Handler):
    content_types = ['document']
    torrent = inject.attr('torrent')

    def run(self, message):
        file_info = self.bot.get_file(message.document.file_id)
        local_file_path = download_telegram_file(file_info)
        self.torrent.download_from_file(open(local_file_path, 'rb'), category=message.caption)


class TorrentSearchHandler(Handler):
    help = 'Search torrents'
    commands = ['searchtorrent', 'st', 't']
    jackett = inject.attr('jackett')

    def run(self, message):
        clean_text = self.get_clean_text(message)
        text = self.search(clean_text)
        if text:
            self.bot.send_message(message.chat.id, text, parse_mode='markdown')

    def search(self, query, categories=['movies', 'tv']):
        results = []
        for cat in categories:
            results += self.jackett.search(query, cat=cat)
        lst = []
        for result in self.sort_and_filter_results(results):
            link_id = CrossLinkHandler.store_link('dl', result)
            lst.append(self.build_result_string(link_id, result))
        return "\n".join(lst)

    def build_result_string(self, link_id, result):
        info = PTN.parse(result['name'])
        badges = []
        if 'year' in info:
            badges.append('[%s]' % info['year'])
        if 'resolution' in info:
            badges.append('[%s]' % info['resolution'])
        if 'orig' in result['name'].lower():
            badges.append('[original]')
        if ' sub' in result['name'].lower():
            badges.append('[SUBS]')
        badges.append("[%s]" % sizeof_fmt(int(result['size'].replace('B', '').strip())))
        badges.append("[Seeds: %s]" % (result['seeds'] + result['leech']))

        return '🍿{badges}\n{name}\nDownload: {link_id}\n'.format(
            link_id=link_id,
            badges="" if not badges else " *%s* " % ("".join(badges)),
            **result
        )

    def sort_and_filter_results(self, raw_results, limit=15):
        raw_results.sort(key=lambda x: x.get('seeds') + x.get('leech'), reverse=True)
        return raw_results[:limit]


class TorrentCatalogSearchHandler(TorrentSearchHandler, CrossLinkHandler):
    commands = None
    regexp = 'torrents(.*)'

    def run(self, message):
        payload = self.get_payload(message)
        text = self.search(
            self.build_search_query(payload.get('info')),
            categories=payload.get('categories')
        )
        if text:
            self.bot.send_message(message.chat.id, text, parse_mode='markdown')

    def build_search_query(self, info):
        return '{original_title}'.format(**info)


class TorrentSearchDownloadHandler(CrossLinkHandler):
    regexp = 'dl(.*)'

    jackett = inject.attr('jackett')
    torrent = inject.attr('torrent')

    def run(self, message):
        payload = self.get_payload(message)
        local_file_path = self.jackett.download_torrent(payload.get('link'))
        if local_file_path.startswith('magnet:?'):
            self.torrent.download_from_link(local_file_path)
        else:
            self.torrent.download_from_file(open(local_file_path, 'rb'))
