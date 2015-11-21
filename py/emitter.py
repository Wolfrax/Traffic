#!/usr/bin/env python

__author__ = 'mm'
import sys
sys.path.append('../py')

import B593
import datetime
import time
from pymongo import MongoClient
from flask import Flask, request
import json
from Queue import Queue

app = Flask(__name__)
Q = Queue()   # Need to use Queue mechanism, to synch between the router reading and HTTP response


def router_handler(data, sessionid):
    data['time'] = time.mktime(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = sessionid
    Q.put(data)


@app.route("/traffic/B593")
def b593rt():
    B593.Router(0, router_handler)
    return json.dumps(Q.get())


@app.route("/traffic/B593DB")
def b593db():
    start_time = int(request.args.get('StartTime'))
    stop_time = int(request.args.get('StopTime'))

    try:
        client = MongoClient()
        db = client.Router       # The name of the Mongo DB is 'Router'
        coll = db.B593           # The collection is named 'B593'
        posts = coll.find({"Time": {"$gte": start_time, "$lte": stop_time}},
                           projection={"_id": False, "IPAddress": False}).sort("Time")

        return json.dumps([post for post in posts])
    except:
        pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
