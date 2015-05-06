#! /usr/bin/python

import os, sys, time, re, subprocess, urllib

TAHOE = os.path.expanduser("~/bin/tahoe")
BASEDIR = os.path.expanduser("~/.tahoe")
EXPECTED_SERVERS = 6

def restart(basedir, k, N, expected_servers):
    fn = os.path.join(basedir, "tahoe.cfg")
    newfn = fn+".new"
    new = open(newfn, "w")
    for line in open(fn,"r").readlines():
        if line.startswith("shares.needed") or line.startswith("#shares.needed"):
            line = "shares.needed = %d\n" % k
        if line.startswith("shares.happy") or line.startswith("#shares.happy"):
            line = "shares.happy = %d\n" % min(N,EXPECTED_SERVERS)
        if line.startswith("shares.total") or line.startswith("#shares.total"):
            line = "shares.total = %d\n" % N
        new.write(line)
    new.close()
    os.rename(newfn, fn)

    p = subprocess.Popen([TAHOE, "restart", BASEDIR])
    p.communicate()
    if p.returncode != 0:
        print "unable to restart tahoe"
        sys.exit(1)
    # now we need to wait until all servers are connected
    timeout = 60
    while True:
        timeout -= 1
        if timeout <= 0:
            print "gave up waiting for restart"
            sys.exit(1)
        time.sleep(1)
        d = urllib.urlopen("http://localhost:3456/").readlines()
        d2 = [l for l in d
              if "Connected to" in l and
              "introducer" not in l and "helper" not in l]
        if len(d2) != 1:
            continue
        mo = re.search(r'<span>(\d+)</span>', d2[0])
        if not mo:
            continue
        count = int(mo.group(1))
        if count < expected_servers:
            continue
        break

    print "restarted"

def upload(fn, size):
    size = int(size)
    assert size > 8
    data = os.urandom(8) + "\x00" * (size-8)
    p = subprocess.Popen([TAHOE, "put", "-", "perf:%s" % fn],
                         stdin=subprocess.PIPE)
    p.communicate(data)
    if p.returncode != 0:
        print "unable to upload"
        sys.exit(1)

for k in range(1, 60+1):
    N = k
    restart(BASEDIR, k, N, EXPECTED_SERVERS)
    for size,sizename in [(1e6,"1MB"), (10e6,"10MB"), (100e6,"100MB")]:
        fn = "CHK-%s--%d-of-%d" % (sizename, k, N)
        upload(fn, size)
