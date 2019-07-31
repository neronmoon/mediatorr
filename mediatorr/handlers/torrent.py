import PTN
import inject

from mediatorr.handlers.handler import Handler, CrossLinkHandler
from mediatorr.utils.file import download_telegram_file
from mediatorr.utils.string import sizeof_fmt, time_fmt


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
        for result in self.__sort_and_filter_results(results):
            link_id = CrossLinkHandler.store_link(TorrentSearchDownloadHandler.prefix, result)
            lst.append(self.__build_result_string(link_id, result))
        return "\n".join(lst)

    @staticmethod
    def __build_result_string(link_id, result):
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

        return '🍿{badges}\n{name}\n{link_id}\n'.format(
            link_id=link_id,
            badges="" if not badges else " *%s* " % ("".join(badges)),
            **result
        )

    @staticmethod
    def __sort_and_filter_results(raw_results, limit=15):
        raw_results.sort(key=lambda x: x.get('seeds') + x.get('leech'), reverse=True)
        return raw_results[:limit]


class TorrentCatalogSearchHandler(TorrentSearchHandler, CrossLinkHandler):
    commands = None
    prefix = 'torrents'

    def run(self, message):
        payload = self.get_payload(message)
        text = self.search(
            self.__build_search_query(payload.get('info')),
            categories=payload.get('categories')
        )
        if text:
            self.bot.send_message(message.chat.id, text, parse_mode='markdown')

    @staticmethod
    def __build_search_query(info):
        return '{original_title}'.format(**info)


class TorrentSearchDownloadHandler(CrossLinkHandler):
    prefix = 'download'

    jackett = inject.attr('jackett')
    torrent = inject.attr('torrent')

    def run(self, message):
        payload = self.get_payload(message)
        local_file_path = self.jackett.download_torrent(payload.get('link'))
        if local_file_path.startswith('magnet:?'):
            self.torrent.download_from_link(local_file_path, category=payload.get('category'))
        else:
            self.torrent.download_from_file(open(local_file_path, 'rb'), category=payload.get('category'))
