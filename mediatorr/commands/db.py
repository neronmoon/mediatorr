import inject

from mediatorr.models.following import FollowSearch
from mediatorr.models.search import SearchQuery, SearchResult


class DatabaseCommand:
    command = 'db'
    help = 'Database'
    db = inject.attr('db')

    def __init__(self):
        self.models = [
            SearchResult,
            FollowSearch,
            SearchQuery,
        ]

    @staticmethod
    def configure(parser):
        parser.add_argument('command', choices=['fresh', ])

    def handle(self, params):
        if 'fresh' == params.get('command'):
            self.__drop_tables()
            self.__create_tables()

    def __create_tables(self):
        self.models.reverse()
        for model in self.models:
            model.create_table()

    def __drop_tables(self):
        for model in self.models:
            model.drop_table()
