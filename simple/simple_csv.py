#!/usr/bin/env python

__author__ = 'mm'

"""
Simple CSV generator of data from the router
"""

import sys
sys.path.append('../py')

import B593
import csv
import datetime
import calendar
import getopt
import time

class RtrCSV():
    def __init__(self, filename, verbose):
        with open(filename, 'wb') as f:
            self.fieldnames = ['uplink', 'downlink', 'uplink rate', 'downlink rate', 'IP address', 'time', 'session id']
            csvwriter = csv.DictWriter(f, fieldnames=self.fieldnames)
            csvwriter.writeheader()
            self.verbose = verbose
            self.filename = filename

    def router_handler(self, data, id):
        data['time'] = calendar.timegm(datetime.datetime.now().timetuple()) * 1000
        data['session id'] = id

        with open(self.filename, 'awb') as f:
            csvwriter = csv.DictWriter(f, fieldnames=self.fieldnames)
            csvwriter.writerow(data)
            print time.asctime(), "Write %s" % self.filename if self.verbose else None

def router_handler(data, id):
    Rtr.router_handler(data, id)

if __name__ == '__main__':
    helpstr = 'simple_csv.py -o <outfile> -s <sampleperiod> -q'
    sampleperiod = 5
    verbose = True
    filename = 'B593.csv'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:s:q", ["outfile=", "sampleperiod=", "quiet"])
    except getopt.GetoptError:
        print helpstr
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print helpstr
            sys.exit()
        elif opt in ("-o", "--outfile"):
            filename = arg
        elif opt in ("-s", "--sampleperiod"):
            sampleperiod = int(arg)
        elif opt in ("-q", "--quiet"):
            verbose = False

    Rtr = RtrCSV(filename, verbose)
    B593.Router(sampleperiod, router_handler)