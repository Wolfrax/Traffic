#!/usr/bin/env python

__author__ = 'Wolfrax'

"""
Mats Melander (Wolfrax) 2015-07-21, Copyright.
Licensed under BSD

Read up/downlink traffic volume, up/downlink rate and WAN IP address from Huawei B593 router recurrently
Works with router FW version V100R001C07SP102, using RSA PKCS1 encryption of password
Previous version of the router used only base64 encoding of password
"""

import urllib
import urllib2
import base64
import cookielib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from inspect import isfunction
import json
import datetime
import time
import sys
import os
import timer


class RtrB593():

    def __init__(self, url='http://192.168.1.1', name='admin', pw='admin'):
        if url[-1] == '/':
            url = url[:-1]  # Remove any trailing /

        self.url1 = url + "/index/login.cgi"
        self.url2 = url + "/html/status/waninfo.asp"

        self.Name = name
        self.PW = pw

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
        enc = cipher.encrypt(self.PW)
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

    def _getdata(self):
        if not self.loggedin:
            self._login()

        # Read data through url2
        try:
            f = self.opener.open(self.url2)
            self.data = f.read()
        except:
            pass

        if '<title>replace</title>' in self.data:  # Title of page when logged out, 60 seconds
            self.loggedin = False
            self._getdata()

        f.close()

    def _getstr(self, str):
        if self.data is None:
            self._getdata()

        i = self.data.find(str)
        if i > 0:
            j = self.data[i + len(str):].find("'")
            return self.data[i + len(str):i + len(str) + j] if j > 0 else None
        else:
            return None

    def _getuplinkvolume(self):
        s = self._getstr("'upvolume' : '")
        return float(s) if s is not None else 0.0

    def _getdownlinkvolume(self):
        s = self._getstr("'downvolume' : '")
        return float(s) if s is not None else 0.0

    def _getuplinkrate(self):
        s = self._getstr("'uprate' : '")
        return float(s) if s is not None else 0.0

    def _getdownlinkrate(self):
        s = self._getstr("'downrate' : '")
        return float(s) if s is not None else 0.0

    def _getipaddr(self):
        s = self._getstr("'dataip' : '")
        return s if s is not None else ""

    def getsessionid(self):
        for cookie in self.cookieJar:
            if cookie.name == 'SessionID_R3':
                return int(cookie.value)

    def read(self):
        self._close()
        return {'uplink': self._getuplinkvolume(),
                'downlink': self._getdownlinkvolume(),
                'uplink rate': self._getuplinkrate(),
                'downlink rate': self._getdownlinkrate(),
                'IP address': self._getipaddr()}


class Router():
    def __init__(self, interval=0,  function=None):
        if type(interval) != int:
            return
        if function is not None and not isfunction(function):
            return

        if interval > 0 and isfunction(function):
            # delay until the hour
            t = datetime.datetime.now()
            delay = (t.replace(t.year, t.month, t.day, t.hour+1, 0, 0, 0) - t).total_seconds()
            time.sleep(delay)

            self.rtr = RtrB593()
            self.callback = function
            self.Timer = timer.RepeatTimer(interval, self.router_timer)
            self.Timer.start()
            return

        if interval <= 0 and isfunction(function):
            self.rtr = RtrB593()
            function(self.rtr.read(), self.rtr.getsessionid())
            return

        return

    def read(self):
        return self.rtr.read()

    def router_timer(self):
        if self.callback is not None:
            self.callback(self.rtr.read(), self.rtr.getsessionid())


def router_handler(data, id):

    data['time'] = time.mktime(datetime.datetime.now().timetuple()) * 1000
    data['session id'] = id
    print json.dumps(data)

if __name__ == '__main__':
    # Change working directory to where the script is, needed for B593 to read rt.pem when running as a daemon
    # See http://stackoverflow.com/questions/595305/python-path-of-script
    pathname = os.path.dirname(sys.argv[0])
    os.chdir(os.path.abspath(pathname))

    Router(0, router_handler)
