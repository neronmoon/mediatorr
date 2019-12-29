import time
import threading


class Worker(threading.Thread):
    alive = True
    interval = 5

    def run(self):
        self.on_start()
        while self.alive:
            self.tick()
            time.sleep(self.interval)

    def on_start(self):
        pass

    def tick(self):
        pass

    def stop(self):
        self.alive = False
