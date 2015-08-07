#!/usr/bin/env python

"""
Mats Melander (Wolfrax) 2015-07-21, Copyright.
Licensed under BSD

Read up/downlink traffic volume, up/downlink rate and WAN IP address from Huawei B593 router recurrently
Works with router FW version V100R001C07SP102, using RSA PKCS1 encryption of password
Previous version of the router used only base64 encoding of password

"""

import urllib, urllib2, base64, cookielib
from threading import Event, Thread
import sqlite3 as lite
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

global DBName
DBName = "Traffic.db"


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


class RtrB593():
    url1 = "http://192.168.1.1/index/login.cgi"
    url2 = "http://192.168.1.1/html/status/waninfo.asp"
    loginstr = '<title>replace</title>'

    Name = 'admin'
    PW = 'admin'  # Note, change as needed, don't expose to others. TODO: Change to command line argument

    # Huawei router version V100R001C07SP102 uses RSA PKCS1 type 2 encryption and transfer the result in base64 encoding
    # Previous version of the router did not use RSA, only base64 encoding of the password
    # This is made through javascript rsa.js by Tom Wu, see http://www-cs-students.stanford.edu/~tjw/jsbn/
    #
    # Using Firebug in Firefox it is easy to debug rsa.js, thus finding the modulus and exponent of the PKCS1 public key
    # Modulus: "BEB90F8AF5D8A7C7DA8CA74AC43E1EE8A48E6860C0D46A5D690BEA082E3A74E1571F2C58E94EE339862A49A811A31BB4A48F41B3BCDFD054C3443BB610B5418B3CBAFAE7936E1BE2AFD2E0DF865A6E59C2B8DF1E8D5702567D0A9650CB07A43DE39020969DF0997FCA587D9A8AE4627CF18477EC06765DF3AA8FB459DD4C9AF3"
    #  Exponent: "10001" (hex, 65537 dec)
    #
    # Generating a pem-file ("rt.pem", below) is done by using http://www.techper.net/2012/06/01/converting-rsa-public-key-modulus-and-exponent-into-pem-file/
    # The source code is available in the pem folder.
    # Modification to modexp2pubkey.c, see https://groups.google.com/forum/#!topic/mailing.openssl.users/h-JyUqCXOu4
    #  instead of bn = BN_bin2bn(data, len, NULL); use len = BN_dec2bn(&bn, data);
    # See https://www.openssl.org/docs/crypto/BN_dec2bn.html
    #
    # Command to generate pem file:
    #   arg1 is base64 encoded modulus  ($ base64 n.txt -o n.b64), available in n.b64, n.txt is modulus as long decimal int
    #   arg2 is base64 encoded exponent ($ base64 e.txt -o e.b64), available in e.b64, e.txt is exponent as decimal int
    # ./modexp2pubkey MTMzOTMwMTcwMzcyMDEzNzcyOTQzNTM4NDA2MzM5ODk1MjA4ODEyMDE1MTk3OTIxOTY5MjQ0OTU1MjA5NDcwOTg1MTc5ODMwMjU3OTY0NDkxMjIwMTc3ODQxMTMxNDg3NDUyNTg5MzMxOTU5OTQ5OTkxMzk2NjAzNTE0ODUyNDk5MjQ2MTEwOTA2ODExMzE1MDkwODE5MjAxMDIyMzQyMjAyNDI1NjYzNzE1NTI4NzczMzA5ODA5MzMxNzQyMjQ3NTQzMTUxMTEyMzY4MTg0OTU5MDQzODk2NTAzNTY5OTIzNjYzMTQ1MTA0ODk2ODM5MTM1NTQxNTM1ODI4MDMyMTk0OTkyODE1MTQ5NjE1MjEzNTY3OTc0ODg1Mzk0MDIwOTAzMzQ5NTY0MTA1NjA5MjIyODk5 NjU1MzcK rt.pem
    #
    # Check pem file by $ openssl rsa -in rt.pem -text -pubin -modulus -noout
    # See http://users.dcc.uchile.cl/~pcamacho/tutorial/crypto/openssl/openssl_intro.html for openssl
    # In general: http://di-mgt.com.au/rsa_alg.html and http://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
    #
    # Note that the encrypted b64 encoded password needs to be urlencoded before submitted (urllib.urlencode)

    key_text = open("rt.pem", "r").read()
    public_key = RSA.importKey(key_text)
    cipher = PKCS1_v1_5.new(public_key)
    enc = cipher.encrypt(PW)  #RSA encrypted string
    PWRSAB64 = base64.b64encode(enc)

    def __init__(self):
        self.cookieJar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar), urllib2.HTTPHandler())
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:19.0) Gecko/20100101 Firefox/19.0'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US, en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Cookie', 'Language=sv; SessionID_R3=0; FirstMenu=Admin_0; SecondMenu=Admin_0_0; ThirdMenu=Admin_0_0_0'),
            ('Connection', 'keep-alive')]
        urllib2.install_opener(self.opener)
        self.data = None
        self.Timer = RepeatTimer(90, self.RtrTimer)
        self.Timer.start()
        self.loggedin = False

        con = lite.connect(DBName)
        with con:
            cur = con.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS Traffic(
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Time TEXT,
                    UplinkVolume REAL,
                    DownlinkVolume REAL,
                    UplinkRate REAL,
                    DownlinkRate REAL,
                    IPAddress TEXT
                    );
                """)

    def close(self):
        self.data = None

    def login(self):
        self.cookieJar.clear()
        params = urllib.urlencode(dict(Username=self.Name, Password=self.PWRSAB64))
        try:
            f = self.opener.open(self.url1, params)
            self.data = f.read()
        except:
            pass

        f._close()
        self.loggedin = True

    def getData(self):
        if not self.loggedin:
            self.login()

        # Read data through url2
        try:
            f = self.opener.open(self.url2)
            self.data = f.read()
        except:
            pass

        if '<title>replace</title>' in self.data: # Title of page when logged out, 60 seconds
            self.loggedin = False
            self.getData()

        f._close()

    def getStr(self, str):
        if self.data == None:
            self.getData()

        i = self.data.find(str)
        if i > 0:
            j = self.data[i + len(str):].find("'")
            return self.data[i + len(str):i + len(str) + j] if j > 0 else None
        else:
            return None

    def getUplinkVolume(self):
        s = self.getStr("'upvolume' : '")
        return float(s) if s != None else 0.0

    def getDownlinkVolume(self):
        s = self.getStr("'downvolume' : '")
        return float(s) if s != None else 0.0

    def getUplinkRate(self):
        s = self.getStr("'uprate' : '")
        return float(s) if s != None else 0.0

    def getDownlinkRate(self):
        s = self.getStr("'downrate' : '")
        return float(s) if s != None else 0.0

    def getIPAddr(self):
        s = self.getStr("'dataip' : '")
        return s if s != None else ""

    def RtrTimer(self):
        con = lite.connect(DBName)
        with con:
            try:
                con.cursor().execute(
                    "INSERT INTO Traffic(Time, UplinkVolume, DownlinkVolume, UplinkRate, DownlinkRate, IPAddress) VALUES (?, ?, ?, ?, ?, ?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     self.getUplinkVolume(),
                     self.getDownlinkVolume(),
                     self.getUplinkRate(),
                     self.getDownlinkRate(),
                     self.getIPAddr()))
            except:
                pass

        print " Uplink: %.2f Downlink: %.2f Uplink rate: %.2f Downlink rate: %.2f IP address: %s" % (
            self.getUplinkVolume(),
            self.getDownlinkVolume(),
            self.getUplinkRate(),
            self.getDownlinkRate(),
            self.getIPAddr())

        self.close()


if __name__ == '__main__':
    Rtr = RtrB593()

    

