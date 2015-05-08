from gcloud import datastore

key = datastore.Key("GridConfig")
c = datastore.Entity(key)
c.update({
    "num_server_instances": 3,
    "server_instance_types": ["n1-standard-1"]*3,
    "num_servers": 6,
    "server_versions": ["1.10.0"]*6,
    "server_latencies": [0]*6,
    "client_instance_type": "n1-standard-1",
    "client_version": "1.10.0",
    })
datastore.put(c)
print "configid:", c.key.id
