import xml.etree.ElementTree
from urllib.parse import urlencode, unquote
from mediatorr.utils.http import request


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

    def search(self, what, cat='all'):
        if isinstance(cat, list):
            result = []
            for c in cat:
                result += self.search(what, c)
            return result

        category = self.supported_categories[cat.lower()]
        what = unquote(what)

        # prepare jackett url
        params = [
            ('apikey', self.api_key),
            ('q', what)
        ]
        if category is not None:
            params.append(('cat', ','.join(category)))
        params = urlencode(params)
        jacket_url = self.url + "/api/v2.0/indexers/all/results/torznab/api?%s" % params
        response = request(jacket_url)
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
        return search_result

    def generate_xpath(self, tag):
        return './{http://torznab.com/schemas/2015/feed}attr[@name="%s"]' % tag
