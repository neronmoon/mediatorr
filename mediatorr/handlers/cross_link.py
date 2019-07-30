import hashlib
import re

import inject
import simplejson

from mediatorr.handlers.handler import Handler


class CrossLinkHandler(Handler):
    db = inject.attr('db')

    def get_payload(self, message):
        cross_link_id = re.search(self.regexp, message.text).group(1)
        return self.db.get(cross_link_id)

    @staticmethod
    def store_link(prefix, payload):
        db = inject.instance('db')
        key = CrossLinkHandler.__get_cache_key(payload, prefix)
        if not db.exists(key):
            link_id = int(db.get('last_link_id') or "0") + 1
            db.set(str(link_id), payload)
            db.set('last_link_id', link_id)
            db.set(key, link_id)
        else:
            link_id = db.get(key)
        return "/%s%s" % (prefix, link_id, )

    @staticmethod
    def __get_cache_key(payload, prefix):
        hash = hashlib.md5(simplejson.dumps({'prefix': prefix, 'payload': payload}).encode())
        return hash.hexdigest()
