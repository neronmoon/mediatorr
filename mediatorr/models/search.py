import time
from mediatorr.models.model import Model


class TorrentSearchResult(Model):
    _table = 'search_results'
    _key = 'desc_link'

    def __init__(self, **kwargs):
        super().__init__()
        self.update({
            'query': kwargs.get('query'),
            'name': kwargs.get('name'),
            'link': kwargs.get('link'),
            'size': kwargs.get('size'),
            'category': kwargs.get('category'),
            'desc_link': kwargs.get('desc_link'),
            'seeds': int(kwargs.get('seeds')),
            'leech': int(kwargs.get('leech')),
            'found_at': kwargs.get('time.time()'),
            'torrent_id': None
        })

    def link_torrent_model(self, model):
        self.update({'torrent_id': model.doc_id})
        return self

    @staticmethod
    def from_jackett_payload(payload, query):
        return TorrentSearchResult(
            query=query,
            name=payload.get('name').strip(),
            link=payload.get('link'),
            size=int(payload.get('size').replace(' B', '').strip()),
            category=payload.get('category'),
            desc_link=payload.get('desc_link'),
            seeds=int(payload.get('seeds')),
            leech=int(payload.get('leech'))
        )
