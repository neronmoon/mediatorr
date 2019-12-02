from mediatorr.models.model import Model
from mediatorr.utils.string import sizeof_fmt, time_fmt
import PTN

import json
import uuid

ID_NAMESPACE = uuid.UUID('{503cf7de-2957-4504-a4ae-60283b60c599}')

TORRENT_STATE_NONE = 'UNKNOWN'
TORRENT_STATE_ERROR = 'ERROR'
TORRENT_STATE_PAUSE = 'PAUSED'
TORRENT_STATE_CHECKING = 'CHECKING'
TORRENT_STATE_DOWNLOADING = 'DOWNLOADING'
TORRENT_STATE_OK = 'OK'

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
    keys = ['id', 'name', 'link', 'size', 'category',
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
            'stalledDL': TORRENT_STATE_OK,
            'metaDL': TORRENT_STATE_DOWNLOADING,
        }
        return self.__fill(
            id=self.get_id(),
            name=payload.get('name'),
            hash=payload.get('hash'),
            progress=payload.get('progress'),
            eta=payload.get('eta'),
            speed=payload.get('dlspeed'),
            state=states_map[payload.get('state')],
        )

    def from_jackett_payload(self, payload):
        return self.__fill(
            id=self.get_id(),
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

    def make_status_string(self):
        chunks = [
            TORRENT_STATE_EMOJI[self.get('state')]
        ]
        if self.get('progress') != 1:
            chunks.append("<b>{:.0%}</b>".format(self.get('progress')))
        chunks.append('{0}'.format(self.get('name')))
        if self.get('state') == TORRENT_STATE_DOWNLOADING:
            chunks.append("<b>| %s |</b>" % sizeof_fmt(self.get('speed'), 'B/s'))
            chunks.append(time_fmt(self.get('eta')))

        return " ".join(chunks)

    def get_id(self):
        return str(uuid.uuid3(ID_NAMESPACE, json.dumps([
            self.get('name'),
        ])))
