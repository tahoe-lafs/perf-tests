import webapp2
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
    tahoe_appname = ndb.StringProperty()
    tahoe_version = ndb.StringProperty()
    tahoe_branch = ndb.StringProperty()
    tahoe_git_hash = ndb.StringProperty()

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
        perfs = [(p.k, p.filesize) #p.to_dict()
                 for p in DownloadPerf.query(DownloadPerf.trial_id == trial_id).fetch()]
        return {"trial_data": trial_data.to_dict(),
                "perfs": perfs}

    def get(self):
        trial_id = self.request.get("trial_id", None)
        if trial_id is not None:
            trial_id = int(trial_id)
        self.response.json = self.process(trial_id)
        self.response.headers["Content-Type"] = "application/json; charset=utf-8"

class TestModel(ndb.Model):
    foo = ndb.IntegerProperty()

class Test(webapp2.RequestHandler):
    def get(self):
        #print "in txn", ndb.in_transaction()
        t = TestModel(foo=12)
        t.put()
        rows = TestModel.query().fetch()
        print "len(TestModel):", len(rows)
        t1 = rows[0]
        print "row[0]:", t1, type(t1)
        print "to_dict", t1.to_dict()
        self.response.write("ok")

app = webapp2.WSGIApplication([
    ("/api", MainPage),
    ("/api/downloads", DownloadTrialData),
    ("/api/test", Test),
], debug=True)
