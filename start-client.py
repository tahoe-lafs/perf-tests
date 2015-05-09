#!/usr/bin/python

import sys, re, time
from os.path import expanduser
from subprocess import call
import requests

print "in start-client.py"

def log(s):
    print s
    sys.stdout.flush()

def calls(s):
    return call(s.split())

TAHOE = expanduser("~/bin/tahoe")
EXPECTED_SERVERS = 6

def wait_for_connections():
    # now we need to wait until all servers are connected
    timeout = 600
    while True:
        timeout -= 1
        if timeout <= 0:
            print "gave up waiting for restart"
            sys.exit(1)
        time.sleep(1)
        r = requests.get("http://localhost:3456/")
        r.raise_for_status()
        d2 = [l for l in r.text.splitlines()
              if "Connected to" in l and
              "introducer" not in l and "helper" not in l]
        if len(d2) != 1:
            continue
        mo = re.search(r'<span>(\d+)</span>', d2[0])
        if not mo:
            continue
        count = int(mo.group(1))
        if count < EXPECTED_SERVERS:
            continue
        break

wait_for_connections()

#call([TAHOE, "create-alias", "perf"])
