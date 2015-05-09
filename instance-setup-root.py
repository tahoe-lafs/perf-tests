#!/usr/bin/python

# this is run by a GCE instance at boot, as root, from /. "git" is available,
# but not necessarily anything else.

import sys
from os.path import exists, expanduser
from subprocess import call
import requests

def log(s):
    print s
    sys.stdout.flush()

def calls(s):
    return call(s.split())

if exists("instance-setup-root.stamp"):
    log("instance-setup-root.stamp exists, exiting")
    sys.exit(0)
with open("instance-setup-root.stamp","w") as f:
    f.write("run\n")

calls("apt-get update")
calls("apt-get dist-upgrade -y")
calls("apt-get install -y python-requests")

def get_metadata(name, type="instance"):
    url = "http://metadata/computeMetadata/v1/%s/attributes/%s" % (type, name)
    log("fetching %s" % url)
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    if not r.ok and r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text

if get_metadata("install-tahoe"):
    print "installing tahoe (.dpkg)"
    calls("apt-get install -y tahoe-lafs")

log("instance-setup-root.py complete")
