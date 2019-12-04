import inject
import PTN
from mediatorr.utils.telegram import paginate
from mediatorr.utils.string import sizeof_fmt
from mediatorr.controllers.controller import Controller


class SearchTorrentController(Controller):
    patterns = [r"^(?P<text>[^/].*)", r'^/search_(?P<text>.*)_page_(?P<page>\d+)$']

    search_service = inject.attr('search_service')
    db = inject.attr('db')
    bot = inject.attr('bot')

    def __init__(self, params):
        self.page = int(params.get('page', 1))
        self.text = params.get('text')

    def handle(self, message):
        results = self.search_service.search(self.text)
        paginated = paginate(
            '/search_%s_page_{page}' % self.text,
            list(map(self.render, results)),
            self.page
        )
        self.update_message(**paginated)

    def render(self, item):
        info = PTN.parse(item.get('name'))
        badges = []
        if 'year' in info:
            badges.append('[%s]' % info['year'])
        if 'resolution' in info:
            badges.append('[%s]' % info['resolution'])
        if 'orig' in item.get('name').lower():
            badges.append('[original]')
        if ' sub' in item.get('name').lower():
            badges.append('[SUBS]')
        badges.append("[%s]" % sizeof_fmt(item.get('size')))
        badges.append("[Seeds: %s]" % (item.get('seeds') + item.get('leech')))

        badges_string = "" if not badges else " <b>%s</b> " % ("".join(badges))
        return '🍿{badges}\n{name}\n/download{link_id}\n'.format(link_id=item.doc_id, badges=badges_string, **item)
