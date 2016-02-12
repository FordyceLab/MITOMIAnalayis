##########################
# Rpyc SGE integration module
# Kael Fischer
# 2008-
#
# $Id: rpyc.py,v 1.3 2008/03/04 22:05:18 kael Exp $
#########################

import sys
import time
from .__init__ import *

from . import Rpyc
rpycRoot = os.path.split(Rpyc.__file__)[0]
serverPath = os.path.join(rpycRoot,'Servers','grid_forking_server.py')

from . import Rpyc
from .Rpyc import *


class GridServers(GridSubmission):
    """A class which starts (and deletes)
    a group of Rpyc servers on the Sun Grid Engine.
    """
    
    def __init__ (self, serverCt, qsubOptions='',savePath=False):
        """Submits Rpyc server jobs to the SGE queue.
        """
        self.serverCt = serverCt
        command = ("echo python %s | qsub -t 1-%s -N Rpyc -e /dev/null -o /dev/null %s"%
                   (serverPath, serverCt,qsubOptions))

        GridSubmission.__init__(self,command)
        try:
            self.waitForServers()            
            self.servers = []
            hosts = self.jobHosts()
            print(hosts)

            for i in range(len(hosts)):
                print(hosts[i],self.taskPort(i))
                self.servers.append(SocketConnection(hosts[i],
                                    self.taskPort(i+1)))
                if savePath:
                    self.servers[-1].modules.sys.path = sys.path
                
        except:
            self.kill()
            raise
                         
    
    def taskPort(self,taskID):
        """returns the suggested port number for the given taskID.
        """
        port = Rpyc.Utils.Serving.DEFAULT_PORT + self.jobID%1000 + 100 + taskID
        return port
        

    def waitForServers(self,timeout=30,polling=5):
        """Block until servers are running or timeout in seconds is reached,
        polling every 5 seconds.
        """
        while self.timeSinceSubmit().seconds < timeout:
            time.sleep(polling)
            print(Qstat().stateCount('r',self.jobID))
            try:
                if Qstat().stateCount('r',self.jobID) == self.serverCt:
                    time.sleep(3)  # wait for the server to start
                    return True
            except:
                pass
        self.kill()
        raise RuntimeError("Timeout waiting for Rpyc servers")


    def connect(self):
        pass

    def __del__ (self):
        """Delete extant Rpyc server jobs.
        """
        self.kill()

    def __getitem__ (self,idx):
        """return server object: idx
        """

        return self.servers[idx]
        
