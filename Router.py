#!/usr/bin/env python

__author__ = 'Wolfrax'

from threading import Event, Thread
import B593
import cgi
import json

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
        while not self.finished.is_set() and (self.iterations <= 0 or count < self.iterations):
            self.finished.wait(self.interval)
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
                count += 1

    def cancel(self):
        self.finished.set()

class Router():
    def __init__(self, interval=0):
        self.rtr = B593.RtrB593()
        if interval > 0:
            self.Timer = RepeatTimer(interval, self.RtrTimer)
            self.Timer.start()

    def read(self):
        print self.rtr.read()

    def RtrTimer(self):
        print self.rtr.read()

if __name__ == '__main__':
    Router()
