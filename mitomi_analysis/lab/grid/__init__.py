####################################################
#
# Sun Grid Engine / python package
#
# Dale Webster and Kael Fischer
# 2006-
#
#
# 	$Id: __init__.py,v 1.3 2008/03/04 22:05:18 kael Exp $	
####################################################

import subprocess
import datetime
import re
import os
import types
from .Exceptions import *

class Qstat:
    """Container for qstat results.
    """


    qwRe =      re.compile(r'^(\d+)\s+([\.\d]+)\s+(\S+)\s+(\w+)\s+(\w+)\s+([\d/]+ [\d:]+)\s+([\d]+) ?([-\d:]*)')
    runningRE = re.compile(r'^(\d+)\s+([\.\d]+)\s+(\S+)\s+(\w+)\s+(\w+)\s+'
                           '([\d/]+ [\d:]+)\s*([-\w\.@\w]*)\s+([\d]+) ?([-\d:]*)')

    

    def __init__ (self,update=True):
        """Make new instance and update qstat info, unless
        update is set to False.
        """

        self.jobs={}
        self.queues={}

        if update:
            self.update()


    def update(self,rertyInterval=1,retryAttempts=5):
        """Update qstat info.
        """

        while retryAttempts >= 0:
            s,o = subprocess.getstatusoutput("qstat")
            if s == 0:
                break
            retryAttempts -= 1

        if retryAttempts < 0:
            raise QStatFailureError("call to qstat failed")

        #reset everything

        lines = o.split("\n")
        if len(lines)>2:
            for l in lines[2:]:
                qMatch = self.qwRe.search(l)
                if qMatch == None:
                    qMatch = self.runningRE.search(l)
                if qMatch == None:
                    raise QStatFailureError("unable to parse qstat line:\n%s"
                                              % l)
                f = qMatch.groups()

                jID = int(f[0])
                pri = float(f[1])
                name,user,state = f[2:5]
                m,d,y,h,mt,s = [int(x) for x in re.split('[ /:]',f[5])]
                #h,m,s = [int(x) for x in f[6].split(';')]
                atTime = datetime.datetime(y,m,d,h,mt,s)
                slots = int(f[-2])
                tasks = f[-1]

                if tasks == '':
                    tasks = tuple()
                elif tasks.find('-') == -1:
                    tasks = (int(tasks),)
                else:
                    tStart,tEnd,tStep = [int(x) for x in re.split('[-:]',tasks)]
                    tasks = list(range(tStart,tEnd+1,tStep))
                
                if len(f) == 9:
                    queue = f[-3]
                    if queue in self.queues:
                        self.queues[queue].append((jID, tasks))
                    else:
                        self.queues[queue] = [None,(jID, tasks)]
                else:
                    queue = None

                if len(tasks) == 0:
                    self.jobs[jID] = [(state,queue)]
                else:
                    if jID not in self.jobs:
                        self.jobs[jID] = []
                    for tID in tasks:
                        while len(self.jobs[jID]) <= (tID):
                            self.jobs[jID].append(None)

                        self.jobs[jID][tID]= (state,queue)

    def allRunning(self,jobID):
        """Return is all tasks for a job are running.
        """
        return len(self.jobs[jobID])-1==[x[0] for x in self.jobs[jobID][1:]].count('r')

    def jobIDs(self):
        """return a list of all active jobIDs
        """
        return list(self.jobs.keys())

    def stateCount(self,state,jobs=None):
        """return a count of states aggregated over all jobs (default)
        or the job or jobs specified."""

        if jobs == None:
            jobs = self.jobIDs()
        if type(jobs) not in (list, tuple):
            jobs = (jobs,)
        
        ct=0
        for jID in jobs:
            ct+= [x[0] for x in self.jobs[jID][1:]].count(state)
        return ct
    
    def jobHosts(self,jobID):
        """Return a list of hosts this job is running on.
        """
        return [t[-1].split("@")[-1] for t in self.jobs[jobID][1:]]
    
    

class GridSubmission:
    """Class which takes a qsub command and when it executes
    the command the jobID and taskIDs are then attributes of the class
    """

    def __init__ (self,command=None):
        """If command is given, it is executed and the
        job and task ids must be recovered from attributes:
        jobID and taskIDs.
        """
        self.allMyJobs=[]
        self.jobID = None
        self.taskIDs = None
        self.command = command
        self.submitTime = None
        if self.command != None:
            self.execute()
        

    def execute(self,command=None):
        """Execute command (should be qsub, qrsh or similar)
        setting .jobID and taskIDs.
        """

        self.jobID = None
        self.taskIDs = None
        
        if command != None:
            self.command = command

        if self.command != None:
            s,o = subprocess.getstatusoutput(self.command)

            if s == 0:
                jtStr =  o.split()[2]
                jtSplit = jtStr.split('.')
                self.jobID = int(jtSplit[0])
                self.allMyJobs.append(self.jobID)
                
                if len(jtSplit) > 1:
                    tStr = jtSplit[1]
                    tMatch=re.search('(\d+)-(\d+):(\d+)',tStr)
                    tStart,tEnd,tStep = [int(x) for x in tMatch.groups()]
                    self.taskIDs = tuple(range(tStart,tEnd+1,tStep))
                else:
                    self.taskIDs = tuple()
            else:
                raise GridRuntimeError("Grid submission failed: %s" %
                                         self.command)

            self.submitTime=datetime.datetime.now()
        return self.jobID,self.taskIDs
                               
    def jobHosts(self):
        """Return a list of hosts this job is running on,
        in TaskID order.
        """
        return Qstat().jobHosts(self.jobID)


    def timeSinceSubmit(self):
        """return a datetime.timedelta object containing the elapsed time 
        since the job went to the grid. 
        """
        return datetime.datetime.now()-self.submitTime


    def kill(self):
        """Delete all the jobs spawned from the queue.
        """
        for j in self.allMyJobs:
            subprocess.getstatusoutput("qdel %s" % j)
        self.allMyJobs=[]
        

        

