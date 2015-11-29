#!/usr/bin/env python

__author__ = 'mm'

import B593
import datetime
import time
from pymongo import MongoClient
import logging
from logging.handlers import RotatingFileHandler
import sys
import getopt
import os
from ConfigParser import SafeConfigParser
import twitter
import urllib3


class TrafficTweet():
    def __init__(self):
        # Kludge to silent warnings in python-twitter, not needed for Python versions > 2.7.9
        # See https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.InsecurePlatformWarning
        urllib3.disable_warnings()

        self.up = 0
        self.down = 0

        self.parser = SafeConfigParser()
        self.parser.read('traffic_collector.conf')

        self.consumer_key = self.parser.get('twitter', 'consumer_key')
        self.consumer_secret = self.parser.get('twitter', 'consumer_secret')
        self.access_key = self.parser.get('twitter', 'access_key')
        self.access_secret = self.parser.get('twitter', 'access_secret')
        self.api = twitter.Api(consumer_key=self.consumer_key,
                               consumer_secret=self.consumer_secret,
                               access_token_key=self.access_key,
                               access_token_secret=self.access_secret)

    @staticmethod
    def _scale(val):
        if val >= 1024**2:
            return val/1024**2, "(%.1f GB)"
        elif val >= 1024:
            return val/1024, "(%.1f MB)"
        else:
            val = 0 if val < 0 else val  # Avoid negative values
            return val, "(%.0f kB)"

    def update(self, up, down):
        self.parser.read('traffic_collector.conf')
        tweet_limit = self.parser.getint('twitter', 'limit')  # Limit in MB

        # up and down in kB
        up = float(up)
        down = float(down)

        do_tweet = True if ((up + down) - (self.up + self.down)) > (tweet_limit * 1024) else False

        diff_up = up - self.up
        diff_down = down - self.down
        diff_sum = diff_up + diff_down

        diff_up, diff_up_str = self._scale(diff_up)
        diff_down, diff_down_str = self._scale(diff_down)
        diff_sum, diff_sum_str = self._scale(diff_sum)

        # Avoid tweet if first time (self.up/down == 0)
        # Avoid tweet to be duplicate of previous => error by including date string
        if (self.up != 0 and self.down != 0) and do_tweet:
            status = self.api.PostUpdate(("%s @ecsmame #B593 Traffic: uplink " + diff_up_str +
                                          " downlink " + diff_down_str + " total " + diff_sum_str) %
                                         (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          diff_up, diff_down, diff_sum))
        else:
            status = None

        self.up = up
        self.down = down
        return status

    def daily_update(self, t, up, down):
        # Provide a daily summary of volume
        # Avoid tweet to be duplicate of previous => error by including date string

        status = None
        dt = datetime.datetime.fromtimestamp(int(t/1000)).timetuple()  # To time_struct
        if dt.tm_hour == 1:  # any time during the first hour of the day
            up = float(up)
            down = float(down)
            start_time = t - (24*60*60*1000)  # 24 hours before t
            client = MongoClient()
            db = client.Router
            coll = db.B593
            post = coll.find_one({"Time": {"$gte": start_time}})

            diff_up = up - post['UplinkVolume']
            diff_down = down - post['DownlinkVolume']
            diff_sum = diff_up + diff_down

            diff_up, diff_up_str = self._scale(diff_up)
            diff_down, diff_down_str = self._scale(diff_down)
            diff_sum, diff_sum_str = self._scale(diff_sum)

            # Calculate start_time as first time of month
            start_time = (datetime.datetime(dt.tm_year, dt.tm_mon, day=1) -
                          datetime.datetime(1970, 1, 1)).total_seconds()*1000
            post = coll.find_one({"Time": {"$gte": start_time}})

            if post is None:  # First day of month, current value not synced to DB
                if not quiet:
                    app_log.warning('Null post at monthly tweet')
                diff_month_up = 0
                diff_month_down = 0
            else:
                diff_month_up = up - post['UplinkVolume']
                diff_month_down = down - post['DownlinkVolume']

            diff_month_sum = diff_month_up + diff_month_down
            diff_month_left = (40*1024**2) - diff_month_sum

            diff_month_up, diff_month_up_str = self._scale(diff_month_up)
            diff_month_down, diff_month_down_str = self._scale(diff_month_down)
            diff_month_sum, diff_month_sum_str = self._scale(diff_month_sum)
            diff_month_left, diff_month_left_str = self._scale(diff_month_left)

            status = self.api.PostUpdate(("Daily %s @ecsmame #B593 up " + diff_up_str +
                                          " down " + diff_down_str + " total " + diff_sum_str) %
                                         (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          diff_up, diff_down, diff_sum))

            status = self.api.PostUpdate(("Monthly %s @ecsmame #B593 up " +
                                          diff_month_up_str + " down " + diff_month_down_str + " total " +
                                          diff_month_sum_str + " left " + diff_month_left_str) %
                                         (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          diff_month_up, diff_month_down, diff_month_sum, diff_month_left))


        else:
            status = None

        return status


def router_handler(data, sid):
    # Milliseconds since 1970-01-01 in local time (not UTC)
    data['time'] = time.mktime(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = sid

    try:
        client = MongoClient()
        db = client.Router       # The name of the Mongo DB is 'Router'
        coll = db.B593           # The collection is named 'B593'
        result = coll.insert_one(
            {
                "Time":           data['time'],
                "UplinkVolume":   data['uplink'],
                "DownlinkVolume": data['downlink'],
                "UplinkRate":     data['uplink rate'],
                "DownlinkRate":   data['downlink rate'],
                "IPAddress":      data['IP address']
            }
        )
        if not quiet:
            app_log.info('Inserted %s', str(data))

    except:
        if not quiet:
            app_log.warning('Mongo exception: %s', sys.exc_info()[0])
        pass

    if tweet:
        status = tw.update(data['uplink'], data['downlink'])
        if not quiet and status is not None:
            app_log.info(status.text)

        status = tw.daily_update(data['time'], data['uplink'], data['downlink'])
        if not quiet and status is not None:
            app_log.info(status.text)


if __name__ == '__main__':
    interval = 60*60  # 1 hour
    logFile = '/var/log/traffic.log'
    quiet = False
    helpstr = 'collector.py -l <logfile> -r <seconds> -t -q'
    tweet = True

    # Change working directory to where the script is, needed for B593 to read rt.pem when running as a daemon
    # See http://stackoverflow.com/questions/595305/python-path-of-script
    pathname = os.path.dirname(sys.argv[0])
    os.chdir(os.path.abspath(pathname))

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:r:tq", ["logfile=", "repeat=", "notweet", "quiet"])
    except getopt.GetoptError:
        print helpstr
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print helpstr
            sys.exit()
        elif opt in ("-l", "--logfile"):
            logFile = arg
        elif opt in ("-r", "--repeat"):
            interval = int(arg)
        elif opt in ("-t", "--notweet"):
            tweet = False
        elif opt in ("-q", "--quiet"):
            quiet = True

    if not quiet:
        # Setup logging with max 5kB and 2 backups
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5 * 1024 * 1024, backupCount=2)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(logging.INFO)

        app_log = logging.getLogger('Collector')
        app_log.setLevel(logging.DEBUG)

        app_log.addHandler(my_handler)
        app_log.info("Start")

    if tweet:
        tw = TrafficTweet()

    B593.Router(interval, router_handler)
