import datetime

from mediatorr.models.search import SearchResult, SearchQuery

import logging
import cachetools.func


class TorrentSearchService:
    def __init__(self, db, api):
        self.db = db
        self.jackett = api
        self.logger = logging.getLogger('TorrentSearchService')

    @cachetools.func.ttl_cache(ttl=60 * 60)  # remember for one hour
    def search(self, query, categories=['movies', 'tv']):
        self.logger.info(f"Searching for `{query}`")
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
