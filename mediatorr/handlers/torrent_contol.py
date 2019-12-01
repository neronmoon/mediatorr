import inject

from mediatorr.handlers.handler import LiveHandler


class TorrentListHandler(LiveHandler):
    help = 'List of added torrents'
    commands = ['torrents', 'list', 'tl', 'l']
    torrent = inject.attr('torrent')
    db = inject.attr('db')

    def make_message(self):
        response = []
        torrents = self.torrent.torrents()
        torrents.sort(key=lambda x: x['state'])
        for trt in torrents:
            trt.save()
            response.append(trt.make_status_string())
        return '\n'.join(response)

