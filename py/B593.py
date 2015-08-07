#!/usr/bin/env python

__author__ = 'Wolfrax'

"""
Mats Melander (Wolfrax) 2015-07-21, Copyright.
Licensed under BSD

Read up/downlink traffic volume, up/downlink rate and WAN IP address from Huawei B593 router recurrently
Works with router FW version V100R001C07SP102, using RSA PKCS1 encryption of password
Previous version of the router used only base64 encoding of password
"""

import urllib, urllib2, base64, cookielib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from threading import Event, Thread
from inspect import isfunction
import cgi
import json
import datetime
import calendar

class RtrB593():

    def __init__(self, url='http://192.168.1.1', Name='admin', PW='admin'):
        if url[-1] == '/':
            url = url[:-1] # Remove any trailing /

        self.url1 = url + "/index/login.cgi"
        self.url2 = url + "/html/status/waninfo.asp"

        self.Name = Name
        self.PW = PW

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
        enc = cipher.encrypt(PW)
        self.PWRSAB64 = base64.b64encode(enc)

        self.cookieJar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar), urllib2.HTTPHandler())
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:19.0) Gecko/20100101 Firefox/19.0'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US, en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Cookie', 'Language=en; SessionID_R3=0; FirstMenu=Admin_0; SecondMenu=Admin_0_0; ThirdMenu=Admin_0_0_0'),
            ('Connection', 'keep-alive')]
        urllib2.install_opener(self.opener)
        self.data = None
        self.loggedin = False

    def _close(self):
        self.data = None

    def _login(self):
        self.cookieJar.clear()
        params = urllib.urlencode(dict(Username=self.Name, Password=self.PWRSAB64))
        try:
            f = self.opener.open(self.url1, params)
            self.data = f.read()
        except:
            pass

        f.close()
        self.loggedin = True

    def _getData(self):
        if not self.loggedin:
            self._login()

        # Read data through url2
        try:
            f = self.opener.open(self.url2)
            self.data = f.read()
        except:
            pass

        if '<title>replace</title>' in self.data: # Title of page when logged out, 60 seconds
            self.loggedin = False
            self._getData()

        f.close()

    def _getStr(self, str):
        if self.data == None:
            self._getData()

        i = self.data.find(str)
        if i > 0:
            j = self.data[i + len(str):].find("'")
            return self.data[i + len(str):i + len(str) + j] if j > 0 else None
        else:
            return None

    def _getUplinkVolume(self):
        s = self._getStr("'upvolume' : '")
        return float(s) if s != None else 0.0

    def _getDownlinkVolume(self):
        s = self._getStr("'downvolume' : '")
        return float(s) if s != None else 0.0

    def _getUplinkRate(self):
        s = self._getStr("'uprate' : '")
        return float(s) if s != None else 0.0

    def _getDownlinkRate(self):
        s = self._getStr("'downrate' : '")
        return float(s) if s != None else 0.0

    def _getIPAddr(self):
        s = self._getStr("'dataip' : '")
        return s if s != None else ""

    def getSessionId(self):
        for cookie in self.cookieJar:
            if cookie.name == 'SessionID_R3':
                return int(cookie.value)

    def read(self):
        self._close()
        return {'uplink': self._getUplinkVolume(),
                'downlink': self._getDownlinkVolume(),
                'uplink rate': self._getUplinkRate(),
                'downlink rate': self._getDownlinkRate(),
                'IP address': self._getIPAddr()}

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
    def __init__(self, interval=0,  function=None):
        if type(interval) != int:
            return
        if function is not None and not isfunction(function):
            return

        if interval > 0 and isfunction(function):
            self.rtr = RtrB593()
            self.callback = function
            self.Timer = RepeatTimer(interval, self.router_timer)
            self.Timer.start()
            return

        if interval <= 0 and isfunction(function):
            function()
            return

        return

    def read(self):
        return self.rtr.read()

    def router_timer(self):
        if self.callback is not None:
            self.callback(self.read(), self.rtr.getSessionId())

def router_handler(data, id):

    data['time'] = calendar.timegm(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = id

    cgiParameters = cgi.FieldStorage()

    print "Content-type: text/html"
    print
    print json.dumps(data)

if __name__ == '__main__':
    Router(2, router_handler)
