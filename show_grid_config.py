import sys
from gcloud import datastore

grid_config_id = int(sys.argv[1])

q = datastore.Query(kind="GridConfig")
q.add_filter("grid_config_id", "=", grid_config_id)
gc = list(q.fetch())[0]
print "GridConfig #%d:" % grid_config_id
for field in sorted(gc.keys()):
    value = gc[field]
    if field == "server_latencies":
        value = ["%.6g" % v for v in value]
    if field in ["avg_server_latency", "max_server_latency"]:
        value = "%.6g" % value
    print " %s: %s" % (field, value)
