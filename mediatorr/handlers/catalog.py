import inject

from mediatorr.handlers.handler import Handler, CrossLinkHandler
from mediatorr.handlers.torrent import TorrentCatalogSearchHandler
from mediatorr.utils.file import download_file


class CatalogSearchHandler(Handler):
    movies_commands = ['movie', 'm']
    tv_commands = ['tv', 'series', 's']
    commands = movies_commands + tv_commands

    catalog = inject.attr('catalog')

    def run(self, message):
        search = self.catalog.Search()
        search_api, media_type = self.get_search_api(search, message)
        search_api(query=self.get_clean_text(message), language='ru')
        lst = []
        for result in search.results:
            result = normalize_data(result)
            result['media_type'] = media_type
            link_id = CrossLinkHandler.store_link(CatalogInfoHandler.prefix, result)
            lst.append(self.__build_result_string(link_id, result))
        text = "\n".join(lst)
        if text:
            self.bot.send_message(message.chat.id, text, parse_mode='markdown')

    @staticmethod
    def __build_result_string(link_id, result):
        return '🍿 *{title}* ({year})\n{description}{link_id}\n'.format(
            link_id=link_id,
            **result
        )

    def get_search_api(self, search, message):
        for cmd in self.movies_commands:
            if "/%s" % cmd in message.text:
                return search.movie, 'movie'
        for cmd in self.tv_commands:
            if "/%s" % cmd in message.text:
                return search.tv, 'tv'


class CatalogInfoHandler(CrossLinkHandler):
    prefix = 'info'

    catalog = inject.attr('catalog')
    config = inject.attr('config')

    def run(self, message):
        payload = self.get_payload(message)
        if payload.get('media_type') == 'movie':
            media = self.catalog.Movies(payload.get('id'))
        else:
            media = self.catalog.TV(payload.get('id'))
        info = normalize_data(media.info(language='ru'))

        text = self.__build_result_string(info, category='movies') if payload.get('media_type') == 'movie' \
            else self.__build_result_string(info, category='tv')
        file = download_file(self.config.get('tmdb').get('image_prefix') + info.get('poster_path'))
        self.bot.send_photo(message.chat.id, open(file, 'rb'), caption=text, parse_mode='markdown')

    @staticmethod
    def __build_result_string(info, category):
        torrents_link = CrossLinkHandler.store_link(
            TorrentCatalogSearchHandler.prefix, {'info': info, 'categories': [category]}
        )
        return """*{title}* [{original_title}] ({year})
{overview}
{torrents_link}
""".format(torrents_link=torrents_link, **info)


def normalize_data(data):
    return {
        'id': data['id'],
        'title': data.get('title') or data.get('name'),
        'original_title': data.get('original_title') or data.get('original_name'),
        'year': (data.get('release_date') or data.get('first_air_date'))[:4],
        'poster_path': data['backdrop_path'],
        'description': data['overview'][:100] + "..\n",
        'overview': data['overview'],
    }
