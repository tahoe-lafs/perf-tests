#!/usr/bin/python

# this is run by a GCE instance at boot, as root, from /. "git" is available,
# but not necessarily anything else.

import sys
from os.path import exists, expanduser
from subprocess import call

def log(s):
    print s
    sys.stdout.flush()

def calls(s):
    return call(s.split())

first_time = True
if exists("instance-setup-root.stamp"):
    log("instance-setup-root.stamp exists")
    first_time = False
with open("instance-setup-root.stamp","w") as f:
    f.write("run\n")

if first_time:
    calls("apt-get update")
    calls("apt-get dist-upgrade -y")
    calls("apt-get install -y python-requests")

import requests

def get_metadata(name, type="instance"):
    url = "http://metadata/computeMetadata/v1/%s/attributes/%s" % (type, name)
    log("fetching %s" % url)
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    if not r.ok and r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text

if first_time and get_metadata("install-tahoe"):
    print "installing tahoe (.dpkg)"
    calls("apt-get install -y tahoe-lafs")

if first_time and "client" in get_metadata("tahoeperf-nodes"):
    calls("apt-get install -y python-pip python-dev libssl-dev libffi-dev")
    calls("pip install -U pip")
    calls("pip install -U virtualenv gcloud")

def mount(diskname, mountpoint):
    log("mounting/formatting %s" % mountpoint)
    if first_time:
        calls("mkdir %s" % mountpoint)
    call(["/usr/share/google/safe_format_and_mount", "-m", "mkfs.ext4 -F",
          "/dev/disk/by-id/google-%s" % diskname, mountpoint])
    calls("chown -R warner:warner %s" % mountpoint)

for nodename in get_metadata("tahoeperf-nodes").split(","):
    if nodename.startswith("storage"):
        mount(nodename, expanduser("~warner/%s" % nodename))

log("instance-setup-root.py complete")
