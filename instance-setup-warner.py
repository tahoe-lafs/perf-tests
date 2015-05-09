#!/usr/bin/python

# this is run by a GCE instance at boot, as a normal user. "git" is
# available, but not necessarily anything else.

import sys
from os.path import exists, expanduser
from subprocess import call
import requests

def log(s):
    print s
    sys.stdout.flush()

def calls(s):
    return call(s.split())

if exists("instance-setup-warner.stamp"):
    log("instance-setup-warner.stamp exists, exiting")
    sys.exit(0)
with open("instance-setup-warner.stamp","w") as f:
    f.write("run\n")

def get_metadata(name, type="instance"):
    url = "http://metadata/computeMetadata/v1/%s/attributes/%s" % (type, name)
    log("fetching %s" % url)
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    if not r.ok and r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text

TAHOE = "/usr/bin/tahoe"

if False:
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

introducer_furl = get_metadata("introducer-furl", "project")

for nodename in get_metadata("tahoeperf-nodes").split(","):
    if nodename.startswith("storage"):
        if not exists(nodename):
            log("creating %s" % nodename)
            call([TAHOE, "create-node", "-n", nodename, "-i", introducer_furl,
                  "-p", "none", nodename])
        call([TAHOE, "start", nodename])
        log("started %s" % nodename)

    if nodename == "client":
        pass
        ## TAHOE = expanduser("~/bin/tahoe")
        ## if not exists(expanduser("~/.tahoe")):
        ##     log("creating %s" % nodename)
        ##     call([TAHOE, "create-client", "-n", nodename, "-i", introducer_furl])
        ## call([TAHOE, "start"])
        ## log("started %s" % nodename)
        ## log("running start-client.py")
        ## call([sys.executable, expanduser("~/perf-tests/./start-client.py")])

log("instance-setup.py complete")
