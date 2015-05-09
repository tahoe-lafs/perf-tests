import os, sys, time, re, urllib, subprocess

def reconfig(fn, key, newvalue):
    newfn = fn+".new"
    new = open(newfn, "w")
    found = False
    for line in open(fn,"r").readlines():
        if line.startswith(key) or line.startswith("#"+key):
            line = "%s = %s\n" % (key, newvalue)
            found = True
        new.write(line)
    new.close()
    if not found:
        raise ValueError("did not find %s in %s" % (key, fn))
    os.rename(newfn, fn)

def restart_node(tahoe, basedir):
    p = subprocess.Popen([tahoe, "restart", basedir])
    p.communicate()
    if p.returncode != 0:
        print "unable to restart tahoe"
        sys.exit(1)

def wait_for_connections(url, expected_servers):
    # now we need to wait until all servers are connected
    timeout = 60
    while True:
        timeout -= 1
        if timeout <= 0:
            print "gave up waiting for restart"
            sys.exit(1)
        time.sleep(1)
        d = urllib.urlopen(url).readlines()
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
