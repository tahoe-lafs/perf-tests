#! /usr/bin/python

import os, sys, time, subprocess
from gcloud import datastore

from rewrite_config import reconfig, restart_node, wait_for_connections

TAHOE = os.path.expanduser("~/bin/tahoe")
BASEDIR = os.path.expanduser("~/.tahoe")
EXPECTED_SERVERS = 6

def restart(basedir, k, N, expected_servers):
    fn = os.path.join(basedir, "tahoe.cfg")
    reconfig(fn, "shares.needed", str(k))
    reconfig(fn, "shares.happy", str(min(N,expected_servers)))
    reconfig(fn, "shares.total", str(N))

    restart_node(TAHOE, basedir)
    wait_for_connections("http://localhost:3456/", expected_servers)
    print "restarted"

def upload(fn, size):
    size = int(size)
    assert size > 8
    data = os.urandom(8) + "\x00" * (size-8)
    p = subprocess.Popen([TAHOE, "put", "-", "perf:%s" % fn],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout = p.communicate(data)[0]
    if p.returncode != 0:
        print "unable to upload"
        sys.exit(1)
    return stdout.strip()

def upload_kN(grid_config_id, trial_id):
    key = datastore.Key("UploadPerf")
    unpushed = []
    for k in range(1,60+1):
        N = k
        restart(BASEDIR, k, N, EXPECTED_SERVERS)
        for size,sizename in [(1e6,"1MB"), (10e6,"10MB"), (100e6,"100MB")]:
            fn = "CHK-%s--%d-of-%d" % (sizename, k, N)
            start = time.time()
            filecap = upload(fn, size)
            elapsed = time.time() - start
            c = datastore.Entity(key)
            c.update({
                "grid_config_id": grid_config_id,
                "trial_id": trial_id,
                "filetype": u"CHK",
                "filesize": size,
                "k": k,
                "N": N,
                #"max_segsize": "default", # use no-such-key to mean default
                "filecap": filecap.decode("ascii"),
                "elapsed": elapsed,
                })
            unpushed.append(c)
            if len(unpushed) > 5:
                datastore.put(unpushed)
                unpushed[:] = []
    if unpushed:
        datastore.put(unpushed)
        unpushed[:] = []

if __name__ == '__main__':
    grid_config_id = int(sys.argv[1])
    trial_id = int(sys.argv[2])
    upload_kN(grid_config_id, trial_id)
