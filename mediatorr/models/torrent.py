from mediatorr.models.model import Model
from mediatorr.utils.string import sizeof_fmt
import PTN

TORRENT_STATE_NONE = ''
TORRENT_STATE_ERROR = 'error'
TORRENT_STATE_PAUSE = 'pause'
TORRENT_STATE_CHECKING = 'checking'
TORRENT_STATE_DOWNLOADING = 'downloading'
TORRENT_STATE_OK = 'ok'

TORRENT_STATES = [
    TORRENT_STATE_NONE,
    TORRENT_STATE_ERROR,
    TORRENT_STATE_PAUSE,
    TORRENT_STATE_CHECKING,
    TORRENT_STATE_DOWNLOADING,
    TORRENT_STATE_OK
]

TORRENT_STATE_EMOJI = {
    TORRENT_STATE_NONE: '',
    TORRENT_STATE_ERROR: '🚫',
    TORRENT_STATE_PAUSE: '⏸️',
    TORRENT_STATE_CHECKING: '🤔',
    TORRENT_STATE_DOWNLOADING: '🔄',
    TORRENT_STATE_OK: '✅',
}


class Torrent(Model):
    table = 'torrents'
    keys = ['name', 'link', 'size', 'category',
            'desc_link', 'hash', 'progress', 'eta',
            'speed', 'state', 'seeds', 'leech']

    def __fill(self, **kwargs):
        if 'state' in kwargs:
            self.ensure_state(kwargs.get('state'))

        for key in self.keys:
            if key in kwargs:
                self.update({key: kwargs[key]})

    def ensure_state(self, state):
        if state not in TORRENT_STATES:
            raise Exception("Invalid torrent state %s" % state)

    def from_qbittorrent_payload(self, payload):
        states_map = {
            'error': TORRENT_STATE_ERROR,
            'pausedUP': TORRENT_STATE_OK,
            'pausedDL': TORRENT_STATE_PAUSE,
            'queuedUP': TORRENT_STATE_DOWNLOADING,
            'queuedDL': TORRENT_STATE_DOWNLOADING,
            'uploading': TORRENT_STATE_OK,
            'stalledUP': TORRENT_STATE_OK,
            'checkingUP': TORRENT_STATE_CHECKING,
            'checkingDL': TORRENT_STATE_CHECKING,
            'downloading': TORRENT_STATE_DOWNLOADING,
            'stalledDL': TORRENT_STATE_DOWNLOADING,
            'metaDL': TORRENT_STATE_DOWNLOADING,
        }
        return self.__fill(
            name=payload.get('name'),
            hash=payload.get('hash'),
            progress=payload.get('progress'),
            eta=payload.get('eta'),
            speed=payload.get('dlspeed'),
            state=states_map[payload.get('state')],
        )

    def from_jackett_payload(self, payload):
        return self.__fill(
            name=payload.get('name'),
            link=payload.get('link'),
            size=payload.get('size'),
            category=payload.get('category'),
            desc_link=payload.get('desc_link'),
            seeds=int(payload.get('seeds')),
            leech=int(payload.get('leech'))
        )

    def make_search_result_string(self, link_id):
        info = PTN.parse(self.get('name'))
        badges = []
        if 'year' in info:
            badges.append('[%s]' % info['year'])
        if 'resolution' in info:
            badges.append('[%s]' % info['resolution'])
        if 'orig' in self.get('name').lower():
            badges.append('[original]')
        if ' sub' in self.get('name').lower():
            badges.append('[SUBS]')
        badges.append("[%s]" % sizeof_fmt(int(self.get('size').replace('B', '').strip())))
        badges.append("[Seeds: %s]" % (self.get('seeds') + self.get('leech')))

        badges_string = "" if not badges else " <b>%s</b> " % ("".join(badges))
        return '🍿{badges}\n{name}\n{link_id}\n'.format(link_id=link_id, badges=badges_string, **self)

