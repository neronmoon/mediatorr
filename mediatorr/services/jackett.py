import xml.etree.ElementTree
from http.cookiejar import CookieJar
from urllib import request as urllib_request
from urllib.parse import urlencode, unquote
from mediatorr.models.torrent import Torrent
from mediatorr.utils.file import download_file


class Jackett(object):
    supported_categories = {
        'all': None,
        'anime': ['5070'],
        'books': ['8000'],
        'games': ['1000', '4000'],
        'movies': ['2000'],
        'music': ['3000'],
        'software': ['4000'],
        'tv': ['5000'],
    }

    def __init__(self, url, api_key):
        self.url = url if url[-1] != '/' else url[:-1]
        self.api_key = api_key

    def download_torrent(self, download_url):
        # fix for some indexers with magnet link inside .torrent file
        if download_url.startswith('magnet:?'):
            return download_url
        response = self.get_response(download_url)
        if response is not None and response.startswith('magnet:?'):
            return download_url
        else:
            return download_file(download_url)

    def search(self, what, cat='all'):
        what = unquote(what)
        category = self.supported_categories[cat.lower()]

        # prepare jackett url
        params = [
            ('apikey', self.api_key),
            ('q', what)
        ]
        if category is not None:
            params.append(('cat', ','.join(category)))
        params = urlencode(params)
        jacket_url = self.url + "/api/v2.0/indexers/all/results/torznab/api?%s" % params
        response = self.get_response(jacket_url)
        if response is None:
            raise Exception("Jackett connection error")

        # process search results
        response_xml = xml.etree.ElementTree.fromstring(response)
        search_result = []
        for result in response_xml.find('channel').findall('item'):
            res = {}
            title = result.find('title')
            if title is not None:
                title = title.text
            else:
                continue
            tracker = result.find('jackettindexer')
            tracker = '' if tracker is None else tracker.text
            res['name'] = '%s [%s]' % (title, tracker)

            res['link'] = result.find(self.generate_xpath('magneturl'))
            if res['link'] is not None:
                res['link'] = res['link'].attrib['value']
            else:
                res['link'] = result.find('link')
                if res['link'] is not None:
                    res['link'] = res['link'].text
                else:
                    continue

            res['size'] = result.find('size')
            res['size'] = -1 if res['size'] is None else (res['size'].text + ' B')

            res['seeds'] = result.find(self.generate_xpath('seeders'))
            res['seeds'] = -1 if res['seeds'] is None else int(res['seeds'].attrib['value'])

            res['leech'] = result.find(self.generate_xpath('peers'))
            res['leech'] = -1 if res['leech'] is None else int(res['leech'].attrib['value'])

            if res['seeds'] != -1 and res['leech'] != -1:
                res['leech'] -= res['seeds']

            res['desc_link'] = result.find('comments')
            if res['desc_link'] is not None:
                res['desc_link'] = res['desc_link'].text
            else:
                res['desc_link'] = result.find('guid')
                res['desc_link'] = '' if res['desc_link'] is None else res['desc_link'].text

            # note: engine_url can't be changed, torrent download stops working
            res['engine_url'] = self.url
            res['category'] = cat
            search_result.append(res)
        models = []
        for result in search_result:
            model = Torrent()
            model.from_jackett_payload(result)
            models.append(model)
        return models

    def generate_xpath(self, tag):
        return './{http://torznab.com/schemas/2015/feed}attr[@name="%s"]' % tag

    def get_response(self, query):
        response = None
        try:
            opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(CookieJar()))
            response = opener.open(query).read().decode('utf-8')
        except urllib_request.HTTPError as e:
            # if the page returns a magnet redirect, used in download_torrent
            if e.code == 302:
                response = e.url
        except Exception:
            pass
        return response
