import webapp2, numpy
from collections import defaultdict
from google.appengine.ext import ndb

class GridConfig(ndb.Model):
    grid_config_id = ndb.IntegerProperty()
    num_server_instances = ndb.IntegerProperty()
    server_instance_type = ndb.StringProperty()
    num_servers = ndb.IntegerProperty()
    server_disk = ndb.StringProperty()
    server_version = ndb.StringProperty()
    server_latencies = ndb.FloatProperty(repeated=True)
    avg_server_latency = ndb.FloatProperty()
    max_server_latency = ndb.FloatProperty()
    client_instance_type = ndb.StringProperty()
    client_version = ndb.StringProperty()

class UploadPerf(ndb.Model):
   grid_config_id = ndb.IntegerProperty()
   trial_id = ndb.IntegerProperty()
   filetype = ndb.StringProperty()
   filesize = ndb.IntegerProperty()
   k = ndb.IntegerProperty()
   N = ndb.IntegerProperty()
   max_segsize = ndb.IntegerProperty(default=128*1024)
   #"max_segsize":default", # use no-such-key to mean default
   filecap = ndb.StringProperty()
   elapsed = ndb.FloatProperty()


class DownloadTrial(ndb.Model):
    trial_id = ndb.IntegerProperty()
    perf_test_git_hash = ndb.StringProperty()
    notes = ndb.StringProperty()
    client_tahoe_appname = ndb.StringProperty()
    client_tahoe_version = ndb.StringProperty()
    client_tahoe_branch = ndb.StringProperty()
    client_tahoe_git_hash = ndb.StringProperty()

class DownloadPerf(ndb.Model):
    grid_config_id = ndb.IntegerProperty()
    trial_id = ndb.IntegerProperty()
    filetype = ndb.StringProperty()
    filesize = ndb.IntegerProperty()
    offset = ndb.IntegerProperty()
    readsize = ndb.IntegerProperty()
    k = ndb.IntegerProperty()
    N = ndb.IntegerProperty()
    filecap = ndb.StringProperty()
    download_time = ndb.FloatProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers["Content-Type"] = "text/plain"
        self.response.write("Hello, World!\n")

class DownloadTrialData(webapp2.RequestHandler):
    def process(self, trial_id):
        if trial_id is None:
            q = DownloadTrial.query()
            trials = [t.trial_id
                      for t in q.fetch(projection=[DownloadTrial.trial_id])]
            return {"trials": trials}
        trial_data = DownloadTrial.query(DownloadTrial.trial_id == trial_id).get()
        if not trial_data:
            return {"error": "no DownloadTrial for trial_id=%d" % trial_id}
        perfs = [p.to_dict()
                 for p in DownloadPerf.query(DownloadPerf.trial_id == trial_id).fetch()
                 ]
        if trial_id in (1,2,3,5,6,7,8,9,10):
            by = "k"
        else:
            by = "readsize"
        return {"trial_data": trial_data.to_dict(),
                "perfs": perfs,
                "rates": self.calc_rates(by, perfs),
                }

    def calc_rates(self, by, perfs):
        series = defaultdict(list)
        rates = []
        for p in perfs:
            if by == "readsize":
                s = (p["k"], p["filesize"])
            else:
                s = p["filesize"]
            series[s].append(p)

        for key in sorted(series.keys()):
            data = series[key]
            x_data = [p[by] for p in data]
            max_x = max(x_data)
            y_data = [p["download_time"] for p in data]
            x = numpy.array(x_data)
            y = numpy.array(y_data)
            A = numpy.vstack([x, numpy.ones(len(x))]).T
            m,c = numpy.linalg.lstsq(A, y)[0]
            if by == "readsize":
                k,filesize = key
                speed = 1.0/m / 1e6 # MBps
                text = "%dMB k=%d: %.2f MBps + %.3f sec" \
                       % (int(filesize/1e6), k, speed, c)
                rates.append({"k": k,
                              "filesize": filesize,
                              "speed": speed,
                              "c": c,
                              "p0": [0,c],
                              "p1": [max_x, m*max_x+c],
                              "text": text,
                              })
            elif by == "k":
                filesize = key
                slope = m # sec/k
                text = "%dMB: %.02f sec/k + %.3f sec" \
                       % (int(filesize/1e6), slope, c)
                rates.append({"filesize": filesize,
                              "slope": slope,
                              "c": c,
                              "p0": [0,c],
                              "p1": [max_x, m*max_x+c],
                              "text": text,
                              })

            #print "time = %.2f MBps + %.3f s" % (speed, c)
        return rates

    def get(self):
        trial_id = self.request.get("trial_id", None)
        if trial_id is not None:
            trial_id = int(trial_id)
        self.response.json = self.process(trial_id)
        self.response.headers["Content-Type"] = "application/json; charset=utf-8"

class TestModel(ndb.Model):
    foo = ndb.IntegerProperty()

class Test(webapp2.RequestHandler):
    def log(self, msg):
        print msg
        self.response.write(msg+"\n")

    def do_import(self, data, klass, old_plural_names=[]):
        self.log("%s: %d old records, %d new" % (klass.__name__,
                                                 klass.query().count(),
                                                 len(data)))
        total = 0
        q = klass.query()
        if False:
            offset = 0
            while True:
                keys = q.fetch(500, keys_only=True, offset=offset)
                if not keys:
                    break
                offset += 500
                total += len(keys)
                ndb.delete_multi(keys)
        elif False:
            keys, next_cursor, more = klass.query().fetch_page(500,
                                                               keys_only=True)
            ndb.delete_multi(keys)
        else:
            #ndb.delete(klass.all(keys_only=True))
            q = klass.query()
            q.keys_only()
            ndb.delete_multi(q)

        self.log(" deleted %d records" % total)
        if not self.request.get("discard", None):
            for start in range(0, len(data), 50):
                entities = []
                for d in data[start:start+50]:
                    for name in old_plural_names:
                        names = name+"s"
                        if names in d:
                            d[name] = d[names][0]
                            del d[names]
                    for name in d:
                        if isinstance(getattr(klass,name), ndb.IntegerProperty):
                            d[name] = int(d[name])
                    e = klass(parent=ndb.Key("Parent", "?"))
                    e.populate(**d)
                    entities.append(e)
                ndb.put_multi(entities)
                entities[:] = []
            self.log(" populated %d records" % len(data))
        else:
            self.log(" discarded")
        self.log(" now have %d records" % klass.query().count())

    def get(self):
        import os, json
        self.response.headers["Content-Type"] = "text/plain"
        self.response.write(os.getcwd()+"\n")
        data = json.load(open("all-data.json", "rb"))
        self.response.write(str(data.keys())+"\n")
        self.do_import(data["GridConfig"], GridConfig,
                       ["server_version", "server_instance_type"])
        self.do_import(data["UploadPerf"], UploadPerf)
        self.do_import(data["DownloadTrial"], DownloadTrial)
        self.do_import(data["DownloadPerf"], DownloadPerf)
        self.response.write("done\n")

    def OFFget(self):
        #print "in txn", ndb.in_transaction()
        t = TestModel(foo=12)
        t.put()
        print "len(TestModel):", TestModel.query().count()
        rows = TestModel.query().fetch()
        print "len(TestModel):", len(rows)
        t1 = rows[0]
        print "row[0]:", t1, type(t1)
        print "to_dict", t1.to_dict()
        self.response.write("ok")

app = webapp2.WSGIApplication([
    ("/api", MainPage),
    ("/api/downloads", DownloadTrialData),
    #("/api/test", Test),
], debug=True)
