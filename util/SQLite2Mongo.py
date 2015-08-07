__author__ = 'mm'

"""
This scripts reads records from an SQLite DB and stores into a Mongo DB
"""

import sqlite3 as lite
from pymongo import MongoClient

DBNAME = "Traffic.db"

if __name__ == '__main__':
    client = MongoClient()
    db = client.Router       # The name of the Mongo DB is 'Router'
    coll = db.B593           # The collection is named 'B593'
    #db.drop_collection(coll) # Remove any old collection

    con = lite.connect(DBNAME)

    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM Traffic")

        rows = cur.fetchall()

        for row in rows:
            result = coll.insert_one(
                {
                    "Time": row[1],
                    "UplinkVolume": row[2],
                    "DownlinkVolume": row[3],
                    "UplinkRate": row[4],
                    "DownlinkRate": row[5],
                    "IPAddress": row[6]
                }
            )
        print "Inserted {} records into Router DB, collection {!r}".format(coll.count(), db.collection_names(include_system_collections=False)[0].encode('ascii'))
