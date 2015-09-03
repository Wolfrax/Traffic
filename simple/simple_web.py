#!/usr/bin/env python

__author__ = 'mm'

"""
Simple HTTP server returning JSON formatted list of data from the router
"""

import sys
sys.path.append('../py')

import B593
import datetime
import calendar
import getopt, os
import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from Queue import Queue
import time
from os import curdir, sep

# The callback function, puts returned data into the global Q(ueue), for synchronisation purposes
def router_handler(data, id):
    data['time'] = calendar.timegm(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = id
    Q.put(data)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type','text-html')
            self.end_headers()
            if self.path.endswith(".html") or self.path.endswith(".js"):
                f = open(curdir + sep + self.path)
                self.wfile.write(f.read())
                f.close()
                return
            else:
                B593.Router(0, router_handler)
                self.wfile.write(json.dumps(Q.get())) # Note, Q.get waits until router_handler have updated the Q.
                return
        except IOError:
            self.send_error(404, 'File not found: %s' % self.path)

if __name__ == '__main__':
    port = 8000

    pathname = os.path.dirname(sys.argv[0])
    os.chdir(os.path.abspath(pathname)) # Change working directory to where the script is, needed for B593 to read rt.pem when running as a daemon
                                        # See http://stackoverflow.com/questions/595305/python-path-of-script
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:", ["port="])
    except getopt.GetoptError:
        print 'simple_web.py -p <port>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'simple_web.py -p <port>'
            sys.exit()
        elif opt in ("-p", "--port"):
            port = int(arg)

    Q = Queue() # Need to use Queue mechanism, to synch between the router reading and HTTP response

    httpd = HTTPServer(('', port), Handler)
    print time.asctime(), "Server Starts - %s" % port
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s" % port
