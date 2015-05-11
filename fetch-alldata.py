import os, sys, json
from gcloud import datastore

data = {}
for kind in ("DownloadTrial", "DownloadPerf", "GridConfig",
             "UploadPerf", "UploadTrial"):
    q = datastore.Query(kind=kind)
    data[kind] = [dict(r.items()) for r in q.fetch()]
with open("all-data.json", "wb") as f:
    json.dump(data, f)
