__author__ = 'mm'

import B593
import datetime
import calendar
from pymongo import MongoClient
import logging

def router_handler(data, id):
    data['time'] = calendar.timegm(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = id

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
    logging.info('Inserted %s', str(data))


if __name__ == '__main__':
#    logging.basicConfig(filename='/var/log/Traffic.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    B593.Router(2, router_handler)
