import time
import threading
import logging


class Worker(threading.Thread):
    alive = True
    interval = 20
    last_run = 0

    def run(self):
        self.on_start()
        while self.alive:
            current_time = time.time()
            if current_time - self.last_run > self.interval:
                self.tick()
                self.last_run = current_time
            time.sleep(1)
        logging.info("Worker %s stopped" % self.__get_name())

    def on_start(self):
        pass

    def tick(self):
        pass

    def stop(self):
        logging.info("Worker %s stop requested" % self.__get_name())
        self.alive = False

    def __get_name(self):
        return self.__class__.__name__
