import sys
from gcloud import datastore

trial_id = int(sys.argv[1])

q = datastore.Query(kind="DownloadPerf")
q.add_filter("trial_id", "=", trial_id)
count = len(list(q.fetch()))
print "%d records in DownloadPerf trial #%d" % (count, trial_id)
dt = list(datastore.Query(kind="DownloadTrial", filters=[("trial_id","=",trial_id)]).fetch())[0]
print "git_hash: %s" % dt["git_hash"]
print "notes: %s" % dt["notes"]
