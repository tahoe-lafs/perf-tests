#! /usr/bin/python

import os, sys, re, random, time, requests, subprocess
from gcloud import datastore
from rewrite_config import restart_node, wait_for_connections

grid_config_id = int(sys.argv[1])
notes = sys.argv[2].decode("ascii")

TAHOE = os.path.expanduser("~/bin/tahoe")
BASEDIR = os.path.expanduser("~/.tahoe")
EXPECTED_SERVERS = 6
GATEWAY = "http://localhost:3456/"

restart_node(TAHOE, BASEDIR)
wait_for_connections(GATEWAY, EXPECTED_SERVERS)
print "restarted"
tahoe_version_string = subprocess.check_output([TAHOE, "--version"]).splitlines()[0].decode("ascii")
mo = re.search(r'(\S+):\s(\S+)\s\[(\S+):\s(\S+)\]', tahoe_version_string)
if mo:
    tahoe_appname, tahoe_version, tahoe_branch, tahoe_git_hash = mo.groups()
else:
    mo = re.search(r'allmydata-tahoe: ([\d\.]+)', tahoe_version_string)
    if mo:
        tahoe_appname = u"allmydata-tahoe"
        tahoe_version = mo.group(1)
        tahoe_branch = None
        tahoe_git_hash = None
assert tahoe_version, (tahoe_version_string,)
print "found version", tahoe_appname, tahoe_version, tahoe_branch, tahoe_git_hash


rootcap = "URI:DIR2:wnjcvliaektnjll7cqsly7fdvm:zdusnqxtf6iwvy2q5ps7irj7vplzueqcq2v2todred6b6v5r2pcq"
M = 1000*1000

SIZES = {M: "1MB",
         10*M: "10MB",
         100*M: "100MB"}

SHARES = range(1, 60+1)
def make_name(size, shares):
    return "CHK-%s--%d-of-%d" % (SIZES[size], shares, shares)

s = requests.Session()
def fetch(path, offset=None, readsize=None, discard=False):
    url = GATEWAY + "uri/" + path
    headers = {}
    if offset is not None and readsize is not None:
        headers["Range"] = "bytes=%d-%d" % (offset, offset+readsize-1)
    if discard:
        r = s.get(url, headers=headers, stream=True)
        r.raise_for_status()
        for d in r.iter_content(64*1024):
            pass
    else:
        r = s.get(url, headers=headers)
        r.raise_for_status()
        return r.content

d = requests.get(GATEWAY+"uri/"+rootcap+"?t=json").json()
ntype, attrs = d
childcaps = {} # key is (size, k)
for size in SIZES:
    for k in SHARES:
        name = make_name(size, k)
        cap = attrs["children"][unicode(name)][1]["ro_uri"]
        childcaps[(size,k)] = str(cap)

#print childcaps

ids = set([en["trial_id"]
           for en in datastore.Query(kind="DownloadTrial",
                                     projection=["trial_id"],
                                     ).fetch()])
ids.add(0)
trial_id = max(ids)+1
perf_test_git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("ascii")

dt = datastore.Entity(datastore.Key("DownloadTrial"))
dt.update({"trial_id": trial_id,
           "notes": notes,
           "perf_test_git_hash": perf_test_git_hash,
           "client_tahoe_appname": tahoe_appname,
           "client_tahoe_version": tahoe_version,
           "client_tahoe_branch": tahoe_branch,
           "client_tahoe_git_hash": tahoe_git_hash,
           })
datastore.put([dt])

key = datastore.Key("DownloadPerf")

mode = "partial"

ITERATIONS = 10*M
for i in range(ITERATIONS):
    if mode == "vs-k":
        size = random.choice(SIZES.keys())
        k = random.choice(SHARES)
        N = k
        readsize = None
        offset = None
    elif mode == "partial":
        size = random.choice([M, 10*M])
        k = random.choice([1,3,6,30,60])
        N = k
        readsize = random.randint(0, size) # includes endpoints
        offset = random.randint(0, size-readsize)
    else:
        raise ValueError("bad mode '%s'" % mode)

    name = make_name(size, k)
    cap = childcaps[(size, k)]

    start = time.time()
    fetch(cap, offset=offset, readsize=readsize, discard=True)
    download_time = time.time() - start
    c = datastore.Entity(key)
    c.update({
        "grid_config_id": grid_config_id,
        "trial_id": trial_id,
        "filetype": u"CHK",
        "filesize": size,
        "offset": 0 if offset is None else offset,
        "readsize": size if readsize is None else readsize,
        "k": k,
        "N": N,
        #"max_segsize": "default", # use no-such-key to mean default
        "filecap": cap.decode("ascii"),
        "download_time": download_time,
        })
    datastore.put([c])
    print "download", SIZES[size], k, readsize, download_time
