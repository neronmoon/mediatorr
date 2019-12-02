from mediatorr.models.model import Model

import json
import uuid

ID_NAMESPACE = uuid.UUID('{503cf7de-2957-4504-a4ae-60283b60c599}')


class Link(Model):
    table = 'links'

    def __init__(self, prefix, payload):
        super().__init__()
        self.update({
            'prefix': prefix,
            'payload': payload
        })
        self.update({'id': self.get_id()})

    def get_id(self):
        return str(uuid.uuid3(ID_NAMESPACE, json.dumps([
            self.get('prefix'),
            self.get('payload'),
        ])))
