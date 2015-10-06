__author__ = 'mm'

from threading import Event, Thread
import time


class RepeatTimer(Thread):
    def __init__(self, interval, function, iterations=0, args=[], kwargs={}):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.iterations = iterations
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()

    def run(self):
        count = 0
        offset = 0
        while not self.finished.is_set() and (self.iterations <= 0 or count < self.iterations):
            self.finished.wait(self.interval - offset)  # Adjust for execution time of self.function
            if not self.finished.is_set():
                t = time.time()
                self.function(*self.args, **self.kwargs)
                offset = time.time() - t
                count += 1

    def cancel(self):
        self.finished.set()