import datetime

from mediatorr.models.search import SearchResult, SearchQuery
import functools


class TorrentSearchService:

    def __init__(self, db, api):
        self.db = db
        self.jackett = api

    @functools.lru_cache()
    def search(self, query, categories=['movies', 'tv']):
        query_text = query.lower()
        query_model, created = SearchQuery.get_or_create(
            query=query_text,
            defaults={'query': query_text}
        )
        if created:
            query_model.last_search_at = datetime.datetime.now()
            query_model.save()

        results = sorted(
            self.jackett.search(query_text, cat=categories),
            key=lambda x: x.get('seeds') + x.get('leech'),
            reverse=True
        )
        models = []
        for result in results:
            model = SearchResult.from_jackett_payload(result)
            model.query = query_model
            model.save()
            models.append(model)
        return query_model, models
