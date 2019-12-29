from mediatorr.models.model import Model
from mediatorr.models.search import TorrentSearchResult
import json

TORRENT_STATE_UNKNOWN = 'UNKNOWN'
TORRENT_STATE_ERROR = 'ERROR'
TORRENT_STATE_PAUSE = 'PAUSED'
TORRENT_STATE_CHECKING = 'CHECKING'
TORRENT_STATE_DOWNLOADING = 'DOWNLOADING'
TORRENT_STATE_OK = 'OK'

TORRENT_STATES = [
    TORRENT_STATE_UNKNOWN,
    TORRENT_STATE_ERROR,
    TORRENT_STATE_PAUSE,
    TORRENT_STATE_CHECKING,
    TORRENT_STATE_DOWNLOADING,
    TORRENT_STATE_OK
]


class Torrent(Model):
    _table = 'torrents'
    _key = 'hash'

    def __init__(self, **kwargs):
        super().__init__()
        state = kwargs.get('state')
        if state not in TORRENT_STATES:
            raise Exception("Invalid torrent state %s" % state)
        self.update({
            'name': kwargs.get('name'),
            'hash': kwargs.get('hash'),
            'progress': kwargs.get('progress'),
            'eta': kwargs.get('eta'),
            'speed': kwargs.get('speed'),
            'state': state,
            'search_id': None
        })

    def link_search_model(self, model):
        self.update({'search_id': model.doc_id})
        return self

    def search_model(self):
        id = self.get('search_id')
        if id is not None:
            return TorrentSearchResult.fetch(doc_id=id)

    @staticmethod
    def from_qbittorrent_payload(payload):
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
            'stalledDL': TORRENT_STATE_CHECKING,
            'metaDL': TORRENT_STATE_CHECKING,
            'checkingResumeData': TORRENT_STATE_CHECKING,
            'missingFiles': TORRENT_STATE_ERROR,
            'forcedUP': TORRENT_STATE_OK,
            'allocating': TORRENT_STATE_CHECKING,
            'forceDL': TORRENT_STATE_DOWNLOADING,
            'moving': TORRENT_STATE_CHECKING,
            'unknown': TORRENT_STATE_UNKNOWN,
        }
        name = payload.get('name')
        model = Torrent(
            name=name,
            hash=payload.get('hash'),
            progress=payload.get('progress'),
            eta=payload.get('eta'),
            speed=payload.get('dlspeed'),
            state=states_map[payload.get('state')],
        )

        separator = "|mediatorr|"
        if separator in name:
            data = json.loads(name.split(separator).pop())
            model.update({'search_id': data.get('search_id')})
            model.doc_id = data.get('torrent_id')
        return model
