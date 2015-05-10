#! /usr/bin/python

import os, sys, json, random, time, requests
from gcloud import datastore
from rewrite_config import restart_node, wait_for_connections

grid_config_id = int(sys.argv[1])
trial_id = int(sys.argv[2])

TAHOE = os.path.expanduser("~/bin/tahoe")
BASEDIR = os.path.expanduser("~/.tahoe")
EXPECTED_SERVERS = 6
GATEWAY = "http://localhost:3456/"

restart_node(TAHOE, BASEDIR)
wait_for_connections(GATEWAY, EXPECTED_SERVERS)
print "restarted"

rootcap = "URI:DIR2:wnjcvliaektnjll7cqsly7fdvm:zdusnqxtf6iwvy2q5ps7irj7vplzueqcq2v2todred6b6v5r2pcq"
M = 1000*1000

SIZES = {M: "1MB",
         10*M: "10MB",
         100*M: "100MB"}

SHARES = range(1, 60+1)
def make_name(size, shares):
    return "CHK-%s--%d-of-%d" % (SIZES[size], shares, shares)

def fetch(path):
    url = GATEWAY + "uri/" + path
    r = requests.get(url)
    r.raise_for_status()
    return r.text

d = json.loads(fetch(rootcap+"?t=json"))
ntype, attrs = d
childcaps = {} # key is (size, k)
for size in SIZES:
    for k in SHARES:
        name = make_name(size, k)
        cap = attrs["children"][unicode(name)][1]["ro_uri"]
        childcaps[(size,k)] = str(cap)

#print childcaps

key = datastore.Key("DownloadPerf")
unpushed = []

ITERATIONS = 10*M
for i in range(ITERATIONS):
    size = random.choice(SIZES.keys())
    k = random.choice(SHARES)
    N = k
    name = make_name(size, k)
    cap = childcaps[(size, k)]

    start = time.time()
    fetch(cap)
    download_time = time.time() - start
    c = datastore.Entity(key)
    c.update({
        "grid_config_id": grid_config_id,
        "trial_id": trial_id,
        "filetype": u"CHK",
        "filesize": size,
        "offset": 0,
        "readsize": size,
        "k": k,
        "N": N,
        #"max_segsize": "default", # use no-such-key to mean default
        "filecap": cap.decode("ascii"),
        "download_time": download_time,
        })
    unpushed.append(c)
    if len(unpushed) > 5:
        datastore.put(unpushed)
        unpushed[:] = []
    print "total_download", size, SIZES[size], k, download_time

if unpushed:
    datastore.put(unpushed)
    unpushed[:] = []
