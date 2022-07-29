from peewee import DateTimeField, CharField, SQL, IntegerField, TextField, BigIntegerField, ForeignKeyField

from mediatorr.models.model import BaseModel
import hashlib


class SearchQuery(BaseModel):
    query = CharField(unique=True)
    last_search_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class SearchResult(BaseModel):
    unique_id = CharField(unique=True)
    title = CharField(max_length=400)
    download_link = TextField()
    size = BigIntegerField()
    source_link = TextField()
    seeds = IntegerField()
    leech = IntegerField()
    category = CharField()
    query = ForeignKeyField(SearchQuery, backref='results')

    @staticmethod
    def from_jackett_payload(payload):
        source_link = payload.get('desc_link')
        unique_id = hashlib.md5(source_link.encode('utf-8')).hexdigest()
        model = SearchResult.get_or_none(unique_id=unique_id)
        if not model:
            model = SearchResult()
            model.unique_id = unique_id

        model.title = payload.get('name').strip()
        model.download_link = payload.get('link')
        model.size = int(payload.get('size').replace(' B', '').strip())
        model.source_link = source_link
        model.seeds = int(payload.get('seeds'))
        model.leech = int(payload.get('leech'))
        model.category = payload.get('category')
        return model
