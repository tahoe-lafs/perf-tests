#! /usr/bin/python

import sys, httplib, json, random, time
import pprint

#gateway = "http://localhost:3456/"
#baseurl = gateway + "uri/"
host = "localhost"
port = 3456
rootcap = "URI:DIR2-RO:7ouzgdjht6vofds7mwrxc3tuzq:tuqxb27hw774vfr3lpr26rpy5uwospeta5h6rzwqqgxmgtl2gvda"
M = 1000*1000

SIZES = {M: "1MB",
         10*M: "10MB",
         100*M: "100MB"}

SHARES = range(1, 60+1)
def make_name(size, shares):
    return "%s--%d-of-%d" % (SIZES[size], shares, shares)

# use just one connection for everything, might remove the TCP setup/shutdown
# overhead. Also, might explode.
connection = None

def make_connection():
    global connection
    connection = httplib.HTTPConnection(host, port)
    connection.connect()
make_connection()

def fetch(path):
    connection.request("GET", path)
    r = connection.getresponse()
    if r.status < 200 or r.status >= 300:
        print r.status, r.reaspon, r.read()
        raise RuntimeError("HTTP failure")
    return r.read()

def discard_and_time(path):
    start = time.time()
    connection.request("GET", path)
    r = connection.getresponse()
    if r.status < 200 or r.status >= 300:
        print r.status, r.reaspon, r.read()
        raise RuntimeError("HTTP failure")
    while True:
        discard = r.read(64*1024)
        if not discard:
            break
    elapsed = time.time() - start
    return elapsed

d = json.loads(fetch("/uri/"+rootcap+"?t=json"))
ntype, attrs = d
childcaps = {} # key is (size, k)
for size in SIZES:
    for k in SHARES:
        name = make_name(size, k)
        cap = attrs["children"][unicode(name)][1]["ro_uri"]
        childcaps[(size,k)] = str(cap)

#print childcaps

ITERATIONS = 10*M
datafile = open("timing.out", "a")
for i in range(ITERATIONS):
    size = random.choice(SIZES.keys())
    k = random.choice(SHARES)
    name = make_name(size, k)
    cap = childcaps[(size, k)]
    if connection is None:
        make_connection()
    try:
        download_time = discard_and_time("/uri/"+cap)
        #print "total_download", size, SIZES[size], k, download_time
        print >>datafile, "total_download", size, SIZES[size], k, download_time
        datafile.flush()
    except httplib.HTTPException, e:
        print >>sys.stderr, time.ctime()
        print >>sys.stderr, e
        print >>sys.stderr, pprint.pformat(connection.__dict__)
        connection = None
        
