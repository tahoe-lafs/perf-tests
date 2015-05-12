import sys
from gcloud import datastore

trial_id = int(sys.argv[1])

q = datastore.Query(kind="DownloadPerf")
q.add_filter("trial_id", "=", trial_id)
q.keys_only()
count = len(list(q.fetch()))
print "DownloadPerf trial #%d:" % trial_id
print " %d records" % count
dt = list(datastore.Query(kind="DownloadTrial", filters=[("trial_id","=",trial_id)]).fetch())[0]
print " notes: %s" % dt["notes"]
h = dt.get("perf_test_git_hash")
if not h:
    h = dt.get("perf-test-git-hash")
print " perf_test_git_hash: %s" % h
print " client_tahoe_version:", dt.get("client_tahoe_version")
print " client_tahoe_git_hash:", dt.get("client_tahoe_git_hash")
