from tinydb import Query
from mediatorr.models.search import TorrentSearchResult
from mediatorr.utils.string import convert_to_seconds
import time


class TorrentSearchService:
    expire = convert_to_seconds('1h')

    def __init__(self, db, api):
        self.db = db
        self.jackett = api

    def search(self, query, categories=['movies', 'tv']):
        queries_table = self.db.table('search_queries')

        query_model = queries_table.get(Query().text == query)
        if query_model is None or query_model.get('time') - time.time() > self.expire:
            results = sorted(
                self.jackett.search(query, cat=categories),
                key=lambda x: x.get('seeds') + x.get('leech'),
                reverse=True
            )
            models = []
            for result in results:
                models.append(TorrentSearchResult.from_jackett_payload(result, query).save())
            queries_table.upsert({
                'text': query,
                'time': int(time.time()),
                'models': list(map(lambda x: x.doc_id, models))
            }, Query().text == query)
            return models
        else:
            return list(map(lambda doc_id: TorrentSearchResult.fetch(doc_id=doc_id), query_model.get('models')))

