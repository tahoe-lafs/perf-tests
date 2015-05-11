import webapp2
from google.appengine.ext import ndb

class DownloadTrial(ndb.Model):
    trial_id = ndb.IntegerProperty()
    perf_test_git_hash = ndb.StringProperty()
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
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World! 2\n')

        trials = DownloadTrial.query(DownloadTrial.trial_id == 2).fetch()
        self.response.write("%d items in trial %d\n" % (len(trials), 2))

app = webapp2.WSGIApplication([
    ('/api', MainPage),
], debug=True)
