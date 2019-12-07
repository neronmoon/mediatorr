import time
import threading


class Worker(threading.Thread):
    alive = True
    interval = 5
    exceptions_count = 5

    def run(self):
        exceptions = []
        self.on_start()
        while self.alive:
            try:
                self.tick()
                time.sleep(self.interval)
            except Exception as e:
                exceptions.append(e)
                if len(exceptions) >= self.exceptions_count:
                    raise e

    def on_start(self):
        pass

    def tick(self):
        pass
