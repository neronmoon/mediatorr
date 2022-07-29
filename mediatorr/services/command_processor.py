import json
import re
import logging

IS_CALLBACK = 'is_callback'


class CommandProcessor:
    def __init__(self):
        self.map = {}

    def connect(self, handler):
        self.map[handler] = handler.patterns

    def process_message(self, message):
        match_data = self.__resolve(message.text)
        if match_data:
            self.next(match_data.get('target'), match_data.get('info'), message)

    def process_callback(self, callback):
        data = json.loads(callback.data)
        match_data = self.__resolve(data.get('path'))
        if match_data:
            self.next(match_data.get('target'), match_data.get('info'), callback.message, is_callback=True)

    def process_file(self, message):
        caption = message.document.caption
        match_data = self.__resolve("file" + ("" if caption == "" else "_" + caption))
        self.next(match_data.get('target'), match_data.get('info'), message)

    def next(self, target, match_info, message, is_callback=False):
        target(match_info).run(is_callback, message)

    def __resolve(self, path):
        for handler, patterns in self.map.items():
            for pattern in patterns:
                matcher = re.compile(pattern)
                match = matcher.match(path)
                if match:
                    return {
                        'target': handler,
                        'path': path,
                        'info': match.groupdict()
                    }
        logging.warning("No match for `%s`" % path, exc_info=True)
