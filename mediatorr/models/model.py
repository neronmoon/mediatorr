from tinydb import Query
import inject


class Model(dict):
    doc_id = None
    _table = '_default'
    _key = '_id'

    @classmethod
    def __get_table(cls):
        return inject.instance('db').table(cls._table)

    @classmethod
    def fetch(cls, cond=None, doc_id=None):
        document = cls.__get_table().get(cond=cond, doc_id=doc_id)
        instance = cls(**document)
        instance.doc_id = document.doc_id
        return instance

    @classmethod
    def search(cls, cond):
        return cls.__get_table().search(cond)

    def save(self):
        ids = self.__get_table().upsert(self, Query().hash == self.get(self._key))
        if len(ids) > 1:
            raise Exception("Non unique key %s in table %s" % (self._key, self._table,))
        self.doc_id = ids.pop()
        return self

    def delete(self):
        self.__get_table().remove(doc_ids=[self.doc_id])
