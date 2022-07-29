from http.cookiejar import CookieJar
from urllib import request as urllib_request


def request(query):
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
