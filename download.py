#! /usr/bin/python

import os, sys, re, random, time, requests, subprocess, socket, argparse
from gcloud import datastore, exceptions
from rewrite_config import restart_node, wait_for_connections

parser = argparse.ArgumentParser(description="download performance test")
parser.add_argument("-g", "--grid-config", type=int, required=True,
                    help="grid config id")
parser.add_argument("--notes")
parser.add_argument("--max-time", type=int)
parser.add_argument("--max-iterations", type=int, default=5000)
parser.add_argument("mode", choices=["k60", "k6",
                                     "partial-banding", "partial-100MB"])
args = parser.parse_args()

grid_config_id = args.grid_config
notes = args.notes.decode("ascii")
mode = args.mode

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
print "-- Starting trial id %d, mode=%s, gridconfig=%d" % (trial_id, mode, grid_config_id)

key = datastore.Key("DownloadPerf")

if mode == "k60":
    values_of_filesize = SIZES.keys()
    values_of_k = SHARES
elif mode == "k6":
    values_of_filesize = SIZES.keys()
    values_of_k = range(1,6+1)
elif mode == "partial-banding":
    values_of_filesize = [M]
    values_of_k = range(1,6+1) + [30,60]
elif mode == "partial-100MB":
    values_of_filesize = [100*M]
    values_of_k = [1,3,6]
else:
    assert "bad mode", mode


trial_start = time.time()
last_pushed = 0
unpushed = []

for i in range(args.max_iterations):
    filesize = random.choice(values_of_filesize)
    k = random.choice(values_of_k)
    N = k
    name = make_name(filesize, k)
    cap = childcaps[(filesize, k)]

    readsize = None
    offset = None
    if mode == "partial":
        readsize = random.randint(0, filesize) # includes endpoints
        offset = random.randint(0, filesize-readsize)

    start = time.time()
    fetch(cap, offset=offset, readsize=readsize, discard=True)
    download_time = time.time() - start
    print "download #%d: filesize=%s k=%d readsize=%s time=%.2f" % \
          (i, SIZES[filesize], k, readsize, download_time)

    c = datastore.Entity(key)
    c.update({
        "grid_config_id": grid_config_id,
        "trial_id": trial_id,
        "filetype": u"CHK",
        "filesize": filesize,
        "offset": 0 if offset is None else offset,
        "readsize": filesize if readsize is None else readsize,
        "k": k,
        "N": N,
        #"max_segsize": "default", # use no-such-key to mean default
        "filecap": cap.decode("ascii"),
        "download_time": download_time,
        })
    unpushed.append(c)
    now = time.time()
    if now - last_pushed > 30:
        try:
            datastore.put(unpushed)
            print " pushed (%d records)" % len(unpushed)
            unpushed[:] = []
            last_pushed = now
            trial_elapsed = time.time() - trial_start
            if args.max_time and trial_elapsed > args.max_time:
                print "max_time reached, terminating"
                sys.exit(0)
        except (exceptions.GCloudError, socket.error):
            print " push error, will retry"
