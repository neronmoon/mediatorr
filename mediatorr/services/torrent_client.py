from mediatorr.models.torrent import Torrent
from tinydb import Query
import json
from tinydb.database import Document
from mediatorr.utils.file import download_file
from mediatorr.utils.http import request


class TorrentClient:
    def __init__(self, db, qbittorrent):
        self.db = db
        self.client = qbittorrent

    def list(self):
        data = self.client.torrents_info()
        models = []
        for item in data:
            models.append(Torrent.from_qbittorrent_payload(item).save())
        return models

    def resume(self, id):
        self.client.torrents_resume(hashes=[self.get_model(id).get('hash')])

    def resume_all(self):
        self.client.torrents_resume(hashes='all')

    def pause(self, id):
        self.client.torrents_pause(hashes=[self.get_model(id).get('hash')])

    def pause_all(self):
        self.client.torrents_pause(hashes='all')

    def delete(self, id):
        model = Torrent.fetch(doc_id=id)
        model.delete()
        self.client.torrents_delete(hashes=[model.get('hash')], deleteFiles=True)

    def get_model(self, id):
        model = Torrent.fetch(doc_id=id)
        info = self.client.torrents_info(hashes=[model.get('hash')]).pop()
        return Torrent.from_qbittorrent_payload(info)

    def download(self, search_model):
        path = self.__download_torrent_file(search_model.get('link'))
        args = {
            'category': search_model.get('category'),
            'rename': search_model.get('desc_link'),
        }
        if path.startswith('magnet?:'):
            self.client.torrents_add(urls=[path], **args)
        else:
            self.client.torrents_add(torrent_files=[path], **args)

        separator = "|mediatorr|"
        for torrent in self.client.torrents_info():
            if torrent.name == search_model.get('desc_link'):
                model = Torrent.from_qbittorrent_payload(torrent).save()
                name = search_model.get('name') + separator + json.dumps({
                    'search_id': search_model.doc_id,
                    'torrent_id': model.doc_id
                })
                self.client.torrents_rename(
                    hash=torrent.hash,
                    new_torrent_name=name
                )
                model.update({'name': name})
                model.link_search_model(search_model).save()
                search_model.link_torrent_model(model).save()
                return model
            elif separator in torrent.name:
                data = json.loads(torrent.name.split(separator).pop())
                if data.get('search_id') == search_model.doc_id:
                    model = Torrent.fetch(doc_id=data.get('torrent_id'))
                    model.link_search_model(search_model)
                    return model

        raise Exception("Torrent was not added")

    def __download_torrent_file(self, download_url):
        # fix for some indexers with magnet link inside .torrent file
        if download_url.startswith('magnet:?'):
            return download_url
        response = request(download_url)
        if response is not None and response.startswith('magnet:?'):
            return download_url
        else:
            return download_file(download_url)
