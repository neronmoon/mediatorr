import gzip
import io
import os
import tempfile

import inject
import requests
import yaml


def parse_yaml_file(file_path):
    with open(file_path, 'r') as stream:
        return read_yaml(stream)


def read_yaml(string):
    return yaml.safe_load(string)


def download_telegram_file(file_info):
    token = inject.instance('config').get('telegram').get('token')
    return download_file('https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path))


def download_file(url):
    """ Download file at url and write it to a file, return the path to the file"""
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:38.0) Gecko/20100101 Firefox/38.0'}

    file, path = tempfile.mkstemp()
    file = os.fdopen(file, "wb")

    response = requests.get(url, headers=headers)
    dat = response.content
    # Check if it is gzipped
    if dat[:2] == b'\x1f\x8b':
        # Data is gzip encoded, decode it
        compressedstream = io.BytesIO(dat)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        extracted_data = gzipper.read()
        dat = extracted_data
    file.write(dat)
    file.close()
    return path
