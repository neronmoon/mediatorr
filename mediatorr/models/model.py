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

    def save(self):
        if 'doc_id' in self:
            doc_id = self.get_table().upsert(self, self.query().doc_id == self.doc_id)
        else:
            doc_id = self.get_table().insert(self)
            self.update({'__table': self.table, 'doc_id': doc_id})
        return doc_id
