#!/usr/bin/python

# this is run by a GCE instance at boot, as a normal user. "git" is
# available, but not necessarily anything else.

import sys
from os.path import exists, expanduser, join
from os import symlink
from subprocess import check_call
import requests

def log(s):
    print s
    sys.stdout.flush()

def calls(s, cwd=None):
    return check_call(s.split(), cwd=None)

calls("printenv")

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
    check_call(["ln", "-s", expanduser("~/tahoe-1.10.0/bin/tahoe"), expanduser("~/bin/tahoe")])
    log("--")
    log("~/bin/tahoe now ready")
log("")

from rewrite_config import reconfig

introducer_furl = get_metadata("introducer-furl", "project")
perf_rootcap = get_metadata("perf-rootcap", "project")

for nodename in get_metadata("tahoeperf-nodes").split(","):
    if nodename.startswith("storage"):
        nodedir = "%s/%s" % (nodename, nodename)
        if not exists(nodedir):
            log("creating %s" % nodedir)
            check_call([TAHOE, "create-node", "-n", nodename, "-i", introducer_furl,
                  "-p", "none", nodedir])
            reconfig(join(nodedir, "tahoe.cfg"), "reserved_space", "")
        check_call([TAHOE, "start", nodedir])
        log("started %s" % nodedir)

    if nodename == "client":
        # fetch tahoe tarball, unpack, setup.py build
        if not exists("allmydata-tahoe-1.10.0"):
            calls("wget https://tahoe-lafs.org/source/tahoe-lafs/releases/allmydata-tahoe-1.10.0.zip")
            calls("unzip allmydata-tahoe-1.10.0.zip")
            calls("python setup.py build",
                  cwd=expanduser("~/allmydata-tahoe-1.10.0"))
            if not exists(expanduser("~/bin/tahoe")):
                symlink(expanduser("~/allmydata-tahoe-1.10.0/bin/tahoe"),
                        expanduser("~/bin/tahoe"))
                TAHOE = expanduser("~/bin/tahoe")
        if not exists(expanduser("~/.tahoe")):
            # create client
            log("creating/starting %s" % nodename)
            check_call([TAHOE, "create-client", "-n", nodename, "-i",introducer_furl])
            # start node
            check_call([TAHOE, "start"])
            # configure perf: alias
            check_call([TAHOE, "add-alias", "perf", perf_rootcap])
            log("started %s" % nodename)
        ## log("running start-client.py")
        ## check_call([sys.executable, expanduser("~/perf-tests/./start-client.py")])

log("instance-setup.py complete")
