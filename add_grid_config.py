import os, sys
from twisted.internet import reactor
from twisted.python import log
from twisted.application import service
from foolscap.api import Tub, fireEventually
from gcloud import datastore

class GetGridConfig:
    def __init__(self):
        f = open(os.path.expanduser("~/.tahoe/private/control.furl"), "r")
        self.control_furl = f.read().strip()
        f.close()
        self.base_service = service.MultiService()
        self.failed = None

    def run(self):
        d = fireEventually()
        d.addCallback(lambda res: self.setUp())
        # use RIClient.get_nodeid() to measure the foolscap-level RTT
        d.addCallback(lambda res: self.client_rref.callRemote("measure_peer_response_time"))
        d.addCallback(self.got_rtt)
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

    def got_rtt(self, rtts):
        # rtts: nodeid -> latency (in seconds)
        times = rtts.values()
        print "avg latency:", sum(times) / len(times)
        key = datastore.Key("GridConfig")
        ids = set([en["grid_config_id"]
                   for en in datastore.Query(kind="GridConfig",
                                             projection=["grid_config_id"],
                                             ).fetch()])
        ids.add(0)
        grid_config_id = max(ids)+1
        c = datastore.Entity(key)
        c.update({
            "grid_config_id": grid_config_id,
            "num_server_instances": 3,
            "server_instance_type": u"n1-standard-1",
            "num_servers": 6,
            "server_disk": u"2GB-pd-standard",
            "server_version": u"1.10.0",
            "server_latencies": times,
            "avg_server_latency": sum(times) / len(times),
            "max_server_latency": max(times),
            "client_instance_type": u"n1-standard-1",
            "client_version": u"1.10.0",
            })
        datastore.put([c])
        print "configid:", grid_config_id

    def tearDown(self, res):
        d = self.base_service.stopService()
        d.addCallback(lambda ignored: res)
        return d


if __name__ == '__main__':
    ggc = GetGridConfig()
    ggc.run()
