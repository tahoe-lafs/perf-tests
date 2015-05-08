import os, sys
from twisted.internet import reactor
from twisted.python import log
from twisted.application import service
from foolscap.api import Tub, fireEventually

class SpeedTest:
    def __init__(self):
        f = open(os.path.expanduser("~/.tahoe/private/control.furl"), "r")
        self.control_furl = f.read().strip()
        f.close()
        self.base_service = service.MultiService()

    def run(self):
        d = fireEventually()
        d.addCallback(lambda res: self.setUp())
        d.addCallback(lambda res: self.measure_rtt())
        d.addBoth(self.tearDown)
        def _err(err):
            self.failed = err
            log.err(err)
            print err
        d.addErrback(_err)
        def _done(res):
            reactor.stop()
            return res
        d.addBoth(_done)
        reactor.run()
        if self.failed:
            print "EXCEPTION"
            print self.failed
            sys.exit(1)

    def setUp(self):
        self.base_service.startService()
        self.tub = Tub()
        self.tub.setOption("expose-remote-exception-types", False)
        self.tub.setServiceParent(self.base_service)
        d = self.tub.getReference(self.control_furl)
        def _gotref(rref):
            self.client_rref = rref
            print "Got Client Control reference"
        d.addCallback(_gotref)
        return d

    def measure_rtt(self):
        # use RIClient.get_nodeid() to measure the foolscap-level RTT
        d = self.client_rref.callRemote("measure_peer_response_time")
        def _got(res):
            assert len(res) # need at least one peer
            times = res.values()
            self.total_rtt = sum(times)
            self.average_rtt = sum(times) / len(times)
            self.max_rtt = max(times)
            print "num-peers: %d" % len(times)
            print "total-RTT: %f" % self.total_rtt
            print "average-RTT: %f" % self.average_rtt
            print "max-RTT: %f" % self.max_rtt
            print "all-times:" % res
        d.addCallback(_got)
        return d

    def tearDown(self, res):
        d = self.base_service.stopService()
        d.addCallback(lambda ignored: res)
        return d


if __name__ == '__main__':
    st = SpeedTest()
    st.run()
