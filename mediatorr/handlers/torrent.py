import inject
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from mediatorr.handlers.handler import Handler, CrossLinkHandler, PaginatingHandler
from mediatorr.utils.file import download_telegram_file


class TorrentUploadHandler(Handler):
    content_types = ['document']
    torrent = inject.attr('torrent')

    def run(self, message):
        file_info = self.bot.get_file(message.document.file_id)
        local_file_path = download_telegram_file(file_info)
        self.torrent.download_from_file(open(local_file_path, 'rb'), category=message.caption)


class TorrentSearchHandler(PaginatingHandler):
    help = 'Search torrents'
    func = lambda _, msg: not msg.text.startswith('/')
    jackett = inject.attr('jackett')

    def get_items(self, message):
        clean_text = self.get_clean_text(message)
        return self.search(clean_text)

    def search(self, query, categories=['movies', 'tv']):
        results = []
        for cat in categories:
            results += self.jackett.search(query, cat=cat)
        lst = []
        results.sort(key=lambda x: x.get('seeds') + x.get('leech'), reverse=True)
        for result in results:
            result.save()
            link = TorrentSearchDownloadHandler.make_link(result)
            lst.append(result.make_search_result_string(link))
        return lst


class TorrentSearchDownloadHandler(CrossLinkHandler):
    commands = None
    prefix = 'download'

    jackett = inject.attr('jackett')
    torrent = inject.attr('torrent')

    def run(self, message):
        payload = self.get_payload(message)

        local_file_path = self.jackett.download_torrent(payload.get('link'))
        if local_file_path.startswith('magnet'):
            self.torrent.download_from_link(local_file_path, category=payload.get('category'))
        else:
            self.torrent.download_from_file(open(local_file_path, 'rb'), category=payload.get('category'))
