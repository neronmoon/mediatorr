from threading import Lock

from tinydb import JSONStorage


class ThreadSafeJSONStorage(JSONStorage):
    lock = Lock()

    def read(self):
        self.lock.acquire()
        data = super().read()
        self.lock.release()
        return data

    def write(self, data):
        self.lock.acquire()
        super().write(data)
        self.lock.release()
