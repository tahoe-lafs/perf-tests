import os

def reconfig(fn, value, new):
    newfn = fn+".new"
    new = open(newfn, "w")
    found = False
    for line in open(fn,"r").readlines():
        if line.startswith(value) or line.startswith("#"+value):
            line = "%s = %s\n" % (value, new)
            found = True
        new.write(line)
    new.close()
    if not found:
        raise ValueError("did not find %s in %s" % (value, new))
    os.rename(newfn, fn)
