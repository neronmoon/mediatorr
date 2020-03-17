from peewee import DatabaseProxy, Model

database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy
