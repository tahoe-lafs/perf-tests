
import os, sys
from os.path import exists, expanduser
from subprocess import call
import requests

NODENAME = sys.argv[1]

def log(s):
    print s
    sys.stdout.flush()

def calls(s, cwd=None):
    return call(s.split(), cwd=cwd)

def get_metadata(name, type="instance"):
    url = "http://metadata/computeMetadata/v1/%s/attributes/%s" % (type, name)
    log("fetching %s" % url)
    r = requests.get(url, headers={"Metadata-Flavor": "Google"})
    if not r.ok and r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text

introducer_furl = get_metadata("introducer-furl", "project")
print "introducer.furl:", introducer_furl

if not exists(expanduser("tahoe-lafs")):
    calls("git clone https://github.com/tahoe-lafs/tahoe-lafs.git")
    calls("python setup.py build", cwd=expanduser("~/tahoe-lafs"))
    os.symlink(expanduser("~/tahoe-lafs/bin/tahoe"), expanduser("~/bin/tahoe"))
    call([expanduser("~/bin/tahoe"), "--version"])
    print "tahoe installed (from git)"

if not exists(expanduser("~/.tahoe")):
    calls("tahoe create-client -n %s -i %s" % (NODENAME, introducer_furl))
