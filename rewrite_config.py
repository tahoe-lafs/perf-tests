import os

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
