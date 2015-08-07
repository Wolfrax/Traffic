#!/usr/bin/env python

import urllib, urllib2, base64, cookielib
import cgi, cgitb
import sys
import json
import datetime
import calendar

class RtrB593():
    url1 = "http://192.168.1.1/index/login.cgi"
    url2 = "http://192.168.1.1/html/status/waninfo.asp"
    Name = 'admin'
    PW = 'admin'
    
    def __init__(self):
        self.data = None
    
    def open(self, sessionId):
        self.cookieJar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar), urllib2.HTTPHandler())
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:19.0) Gecko/20100101 Firefox/19.0'),
                                  ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                                  ('Accept-Language', 'en-US, en;q=0.5'),
                                  ('Accept-Encoding', 'gzip, deflate'),
                                  ('Cookie', 'Language=en; SessionID_R3=' + str(sessionId) + '; FirstMenu=Admin_0; SecondMenu=Admin_0_0; ThirdMenu=Admin_0_0_0'),
                                  ('Connection', 'keep-alive')]
        urllib2.install_opener(self.opener)
        
        if sessionId == 0:
            # First login through url1
            params = urllib.urlencode(dict(Username=self.Name, Password=base64.b64encode(self.PW)))
            f = self.opener.open(self.url1, params)
            f.close()
        
    def getSessionId(self):
        for cookie in self.cookieJar:
            if cookie.name == 'SessionID_R3':
                return int(cookie.value)
        
    def getData(self):
        # self.cookieJar.clear()
            
        # Read data through url2
        f = self.opener.open(self.url2)
        self.data = f.read()
        #print self.data
        f.close()

    def getStr(self, str):
        if self.data == None:
            self.getData()
        
        i = self.data.find(str)
        if i > 0:
            j = self.data[i + len(str):].find("'")
            if j > 0:
                return self.data[i + len(str):i + len(str) + j]
            else:
                return None
        else:
            return None
        
    def getUplinkVolume(self):
        s = self.getStr("'upvolume' : '")
        if s != None:
            return float(s)
        else:
            return 0.0     
         
    def getDownlinkVolume(self):
        s = self.getStr("'downvolume' : '")
        if s != None:
            return float(s)
        else:
            return 0.0
    
    def getUplinkRate(self):
        s = self.getStr("'uprate' : '")
        if s != None:
            return float(s)
        else:
            return 0.0
    
    def getDownlinkRate(self):
        s = self.getStr("'downrate' : '")
        if s != None:
            return float(s)
        else:
            return 0.0
         
    def get(self, sessionId):         
        self.open(sessionId)
        tm = calendar.timegm(datetime.datetime.now().timetuple()) * 1000
        return self.getSessionId(), tm, self.getUplinkVolume(), self.getDownlinkVolume(), self.getUplinkRate(), self.getDownlinkRate() 
        
if __name__ == '__main__':
    #print json.dumps(RtrB593().get(0))
    cgiParameters = cgi.FieldStorage()
    
    print "Content-type: text/html"
    print
    print json.dumps(RtrB593().get(0))
    #print json.dumps(RtrB593().get(cgiParameters.getvalue('sessionId')))

    

