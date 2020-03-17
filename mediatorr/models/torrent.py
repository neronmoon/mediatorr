import json

from mediatorr.models.search import SearchResult

TORRENT_NAME_SEPARATOR = '|mediatorr|'
TORRENT_SEARCH_RESULT_ID_KEY = 'search_id'

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


class TorrentDto(dict):
    def __init__(self, **kwargs):
        super().__init__()
        state = kwargs.get('state')
        if state not in TORRENT_STATES:
            raise Exception("Invalid torrent state %s" % state)
        self.update({
            'title': kwargs.get('title'),
            'hash': kwargs.get('hash'),
            'progress': kwargs.get('progress'),
            'eta': kwargs.get('eta'),
            'speed': kwargs.get('speed'),
            'state': state,
            TORRENT_SEARCH_RESULT_ID_KEY: None
        })

    def search_model_id(self):
        return self.get(TORRENT_SEARCH_RESULT_ID_KEY)

    def search_model(self):
        model_id = self.search_model_id()
        if model_id:
            return SearchResult.get_or_none(id=model_id)

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
        title = payload.get('name')
        model = TorrentDto(
            title=title,
            hash=payload.get('hash'),
            progress=payload.get('progress'),
            eta=payload.get('eta'),
            speed=payload.get('dlspeed'),
            state=states_map[payload.get('state')],
        )

        if TORRENT_NAME_SEPARATOR in title:
            data = json.loads(title.split(TORRENT_NAME_SEPARATOR).pop())
            model.update({TORRENT_SEARCH_RESULT_ID_KEY: data.get(TORRENT_SEARCH_RESULT_ID_KEY)})
        return model
