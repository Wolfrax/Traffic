#!/usr/bin/env python

import cgi, cgitb
import sys
import sqlite3 as lite
import json
import time

class Traffic():
    def get(self, startTime, stopTime):
        con = lite.connect("/var/EMC/Traffic.db")
        with con:
            cur = con.cursor()      
            cur.execute("SELECT strftime('%s', Time) as T, UpLinkVolume, DownlinkVolume, UplinkRate, DownlinkRate FROM Traffic WHERE Time BETWEEN ? AND ?", (startTime, stopTime))
            rows = cur.fetchall()

            uplinkVolume = []
            downlinkVolume = []
            uplinkRate = []
            downlinkRate = []
            t = time.localtime() # Check if the current time is daylight within saving period
            if (t.tm_isdst):
                timeOffset = 1
            else:
                timeOffset = 1
            
            for row in rows:
                # Send time as millseconds adjusted for UTC + 1:00 and volume as GB
                uplinkVolume.append(  [1000 * int(row[0]) - 1000 * 60 * 60 * timeOffset, row[1] / (1024 **2)])
                downlinkVolume.append([1000 * int(row[0]) - 1000 * 60 * 60 * timeOffset, row[2] / (1024 **2)])
                uplinkRate.append(    [1000 * int(row[0]) - 1000 * 60 * 60 * timeOffset, row[3]])
                downlinkRate.append(  [1000 * int(row[0]) - 1000 * 60 * 60 * timeOffset, row[4]])
                
            # return vector with volumes
            return uplinkVolume, downlinkVolume, uplinkRate, downlinkRate
    
if __name__ == '__main__':
    cgiParameters = cgi.FieldStorage()

    print "Content-type: text/html"
    print
    print json.dumps(Traffic().get(cgiParameters.getvalue('StartTime'), cgiParameters.getvalue('StopTime')))
