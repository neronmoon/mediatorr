from peewee import IntegerField, ForeignKeyField

from mediatorr.models.model import BaseModel
from mediatorr.models.search import SearchQuery


class FollowSearch(BaseModel):
    chat_id = IntegerField()
    query = ForeignKeyField(SearchQuery, backref='followers')

