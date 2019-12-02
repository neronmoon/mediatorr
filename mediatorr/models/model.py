from tinydb import Query
import inject


class Model(dict):
    table = '_default'

    @classmethod
    def get_table(cls):
        return inject.instance('db').table(cls.table)

    @staticmethod
    def query():
        return Query()

