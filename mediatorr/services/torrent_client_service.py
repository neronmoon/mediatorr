from mediatorr.models.torrent import TorrentDto, TORRENT_NAME_SEPARATOR, TORRENT_SEARCH_RESULT_ID_KEY
import json, time
from mediatorr.utils.file import download_file
from mediatorr.utils.http import request


class TorrentClientService:
    def __init__(self, db, qbittorrent):
        self.db = db
        self.client = qbittorrent

    def list(self):
        data = self.client.torrents_info()
        models = []
        for item in data:
            models.append(TorrentDto.from_qbittorrent_payload(item))
        return models

    def resume(self, id):
        self.client.torrents_resume(hashes=[self.get_model(id).get('hash')])

    def resume_all(self):
        self.client.torrents_resume(hashes='all')

    def pause(self, id):
        self.client.torrents_pause(hashes=[self.get_model(id).get('hash')])

    def pause_all(self):
        self.client.torrents_pause(hashes='all')

    def delete(self, id, delete_files=True):
        self.client.torrents_delete(hashes=[self.get_model(id).get('hash')], deleteFiles=delete_files)

    def get_model(self, search_result_id):
        for model in self.list():
            if model.get(TORRENT_SEARCH_RESULT_ID_KEY) == search_result_id:
                return model
        return None

    def download(self, search_model):
        if self.get_model(search_model.id) is not None:
            self.delete(search_model.id, delete_files=False)
        path = self.__download_torrent_file(search_model.download_link)
        args = {
            'category': search_model.category,
            'rename': search_model.source_link,
        }
        if path.startswith('magnet?:'):
            self.client.torrents_add(urls=[path], **args)
            time.sleep(5)  # waiting for magnet resolution
        else:
            self.client.torrents_add(torrent_files=[path], **args)

        for torrent in self.client.torrents_info():
            model = TorrentDto.from_qbittorrent_payload(torrent)
            if torrent.name == search_model.source_link:
                title = search_model.title + TORRENT_NAME_SEPARATOR + json.dumps({'search_id': search_model.id})
                self.client.torrents_rename(
                    hash=torrent.hash,
                    new_torrent_name=title
                )
                model.update({
                    'title': title,
                    TORRENT_SEARCH_RESULT_ID_KEY: search_model.id
                })
                return model
            elif TORRENT_NAME_SEPARATOR in torrent.name:
                data = json.loads(torrent.name.split(TORRENT_NAME_SEPARATOR).pop())
                if data.get(TORRENT_SEARCH_RESULT_ID_KEY) == search_model.id:
                    return model

        raise Exception("Torrent was not added")

    @staticmethod
    def __download_torrent_file(download_url):
        # fix for some indexers with magnet link inside .torrent file
        if download_url.startswith('magnet:?'):
            return download_url
        response = request(download_url)
        if response is not None and response.startswith('magnet:?'):
            return download_url
        else:
            return download_file(download_url)
