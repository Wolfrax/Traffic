# MongoDB
## OSX

Install using brew, see Caveats

    $ brew update
    $ brew install mongodb
    ==> Downloading https://homebrew.bintray.com/bottles/mongodb-3.0.4.mavericks.bottle.tar.gz
    ######################################################################## 100.0%
    ==> Pouring mongodb-3.0.4.mavericks.bottle.tar.gz
    ==> Caveats
    To have launchd start mongodb at login:
      ln -sfv /usr/local/opt/mongodb/*.plist ~/Library/LaunchAgents
    Then to load mongodb now:
      launchctl load ~/Library/LaunchAgents/homebrew.mxcl.mongodb.plist
    Or, if you don't want/need launchctl, you can just run:
      mongod --config /usr/local/etc/mongod.conf
    ==> Summary
    🍺  /usr/local/Cellar/mongodb/3.0.4: 17 files, 154M
    
The content of `/usr/local/etc/mongodb.conf`

    systemLog:
      destination: file
      path: /usr/local/var/log/mongodb/mongo.log
      logAppend: true
    storage:
      dbPath: /usr/local/var/mongodb
    net:
      bindIp: 127.0.0.1
      
For installation see [https://emersonveenstra.net/mongodb-raspberry-pi/] (MongoDB)
I did

    $ mkdir mongodb
    $ git clone https://github.com/svvitale/mongo4pi
    $ cd mongodb/mongo4pi
    $ sudo sh install.sh

# Development environment
## Virtualenv

Make use of virtualenv, in PyCharm use `PyCharm/Preferences.../Project Interpreter` and use the dialog box
The root for virtual environments are located under `~/.virtualenvs` with a separate root for `Traffic` that have 
inherited all global packages using Python 2.7.

See [http://virtualenvwrapper.readthedocs.org/en/latest/install.html] (virtualenvwrapper)

For Raspberry Pi

    $ sudo apt-get update
    $ sudo apt-get upgrade
    $
    $ sudo apt-get install python-setuptools
    $ sudo easy_install pip
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper

# Domain

I use the domain `viltstigen.se` with the obvious subdomain `www.viltstigen.se`.
It is registered at [Binero] (http://www.binero.se). To this I am using their dynamic DNS service as I don't 
have a static by my ISP (Telia). My router does not have a dynamic DNS client included.

An alternative (not tested) is to use the free [namecheap] (https://www.namecheap.com/) service, see this blog entry 
[http://mwholt.blogspot.se/2013/09/how-to-set-up-dynamic-dns-in-5-minutes.html]

My router is currently configured to allow HTTP traffic on these ports (these will change)

- 80: To my Mac Mini
- 8080: To my EMONCMS RPi
- 8008: To my ordinary RPi (it is configured to be in DMZ)

To see the Swedish Wind map on my RPi use [http://www.viltstigen.se:8008/Swind]
to keep the dynamic WAN IP address of my router updated to Binero DNS I have added this to my RPi crontab
`00 *    * * *   root    curl -u 'Username:Password' -d 'hostname=www.viltstigen.se' 'https://dyndns.binero.se/nic/update' >/dev/null 2>&1`
This is inline with Binero documentation, running every hour. It will make a POST using the information after the -d option.

In the Binero DNS configuration I use the A record for `www.viltstigen.se`