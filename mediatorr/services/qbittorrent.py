import requests
from qbittorrent import Client as QbitClient
from mediatorr.models.torrent import Torrent


class Client(QbitClient):
    def login(self, username='admin', password='admin'):
        self.username = username
        self.password = password
        return super().login(username, password)

    def _request(self, endpoint, method, data=None, **kwargs):
        try:
            return super()._request(endpoint, method, data, **kwargs)
        except requests.HTTPError as e:
            self.login(self.username, self.password)
            return super()._request(endpoint, method, data, **kwargs)

    def torrents(self, **filters):
        result = []
        for torrent in super().torrents(**filters):
            model = Torrent()
            model.from_qbittorrent_payload(torrent)
            result.append(model)
        return result
