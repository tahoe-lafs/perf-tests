#!/usr/bin/python

# this is run by a GCE instance at boot, as a normal user. "git" and
# python-requests are available, but not necessarily anything else.

from os.path import expanduser
from subprocess import call
import requests

def calls(s):
    return call(s.split())

# download a pre-built Tahoe tree. takes 15s
calls("gsutil cp gs://tahoeperf/tahoe-1.10.0-built.tar.bz2 ./")
# unpack +version takes 16s
calls("tar xf tahoe-1.10.0-built.tar.bz2")
calls("./tahoe-1.10.0/bin/tahoe --version")
call(["ln", "-s", expanduser("~/tahoe-1.10.0/bin/tahoe"), expanduser("~/bin/tahoe")])
TAHOE = expanduser("~/bin/tahoe")

def get_metadata(name):
    url = "http://metadata/computeMetadata/v1/instance/attributes/" % name
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    r.raise_for_status()
    return r.text

for nodename in get_metadata("tahoeperf-nodes").split(","):
    if nodename.startswith("storage"):
        introducer_furl = get_metadata("introducer-furl")
        call([TAHOE, "create-node", "-n", nodename, "-i", introducer_furl,
              "-p", "none", nodename])
        call([TAHOE, "start", nodename])

