#!/usr/bin/python

# this is run by a GCE instance at boot, as a normal user. "git" and
# python-requests are available, but not necessarily anything else.

import sys
from os.path import exists, expanduser
from subprocess import call
import requests

def log(s):
    print s
    sys.stdout.flush()

def calls(s):
    return call(s.split())

TAHOE = expanduser("~/bin/tahoe")

if exists(TAHOE):
    log("~/bin/tahoe exists")
else:
    # download a pre-built Tahoe tree. takes 15s
    log("downloading pre-built tahoe")
    calls("gsutil cp gs://tahoeperf/tahoe-1.10.0-built.tar.bz2 ./")
    log("unpacking")
    # unpack +version takes 16s
    calls("tar xf tahoe-1.10.0-built.tar.bz2")
    calls("./tahoe-1.10.0/bin/tahoe --version")
    call(["ln", "-s", expanduser("~/tahoe-1.10.0/bin/tahoe"), expanduser("~/bin/tahoe")])
    log("--")
    log("~/bin/tahoe now ready")
log("")
sys.stdout.flush()

def get_metadata(name):
    url = "http://metadata/computeMetadata/v1/instance/attributes/" + name
    log("fetching %s" % url)
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    r.raise_for_status()
    return r.text

introducer_furl = get_metadata("introducer-furl")

for nodename in get_metadata("tahoeperf-nodes").split(","):
    if nodename.startswith("storage"):
        log("creating %s" % nodename)
        call([TAHOE, "create-node", "-n", nodename, "-i", introducer_furl,
              "-p", "none", nodename])
        call([TAHOE, "start", nodename])
        log("started %s" % nodename)

log("instance-setup.py complete")
