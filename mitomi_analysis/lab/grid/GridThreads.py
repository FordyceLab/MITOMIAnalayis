####################################################
#
# GridThreads is a module which allows the user to
# effectively spawn and monitor threads across the
# GridEngine cluster.
#
# Dale Webster, adapted from Kael's GridScreen
# 2/22/07
#
# Todo:
# - Add paging to the interactive console.
# - Add command history to the interactive console.
# - Add QueueStatusError and related functionality
# - Dict-ify the Manager and Thread classes.
# - Clean up data accessibility after an exception
#   is raised.
# - Add a join(interval) and/or check() function to the
#   manager. 
#
####################################################

import os, sys
import threading
import subprocess
import datetime
import time
import random
import re
import copy
import cmd
from .Exceptions import *

###############################
# Settings

logLock = threading.Lock()

def logMessage( message, logFile ):
    """Given a log file and a message, writes it and
    flushes the file."""

    logLock.acquire()
    out = open( logFile, 'a' )
    out.write( message + '\n' )
    out.flush()
    out.close()
    logLock.release()

class GridThreadManager:
    """GridThreadManager is a class which allows the user to effectively
    spawn and monitor threads across the GridEngine cluster."""

    def __init__( self, logFile=None, spewLevel=1, qPath="" ):
        """Init function takes in optional global settings.

        - Specify a log file for detailed output of status on
            all threads and jobs.
        - Spew Levels 1 and 2 log a single status output each time
            check() is called.
        - Spew Level 3 logs detailed progress for every thread and job.
        """
        
        # list of active threads
        self.threads = {}
        self.logFile = logFile
        self.spewLevel = spewLevel
        self.brokenThread = None
        self.qPath = qPath

    def __getitem__( self, threadName ):
        """Accesses the internal dict of GridThread onjects."""
        if threadName in self.threads:
            return self.threads[ threadName ]
        raise InvalidArgumentError("Unable to find specified thread: %s." % threadName )	

    def __iter__(self):
        """A generator of threads.
        """
        for t in copy.copy(self.threads):
            #print t
            yield self[t]
            
    def countAlive(self):
        """return number of running threads.
        """ 
        return sum([t.isAlive() for t in self])

    def log( self, message, spew ):
        """Logs the given message iff the manager was constructed with a non-None logFile."""
        if self.logFile and spew <= self.spewLevel:
            lines = message.split("\n")
            for line in lines:
                logMessage( "GTM: " + line, self.logFile )

    def wait( self, interval=20, maxWaitTime=None, interactive=False ):
        """Wait takes in a polling interval (in seconds) for error and timeout
        checking, and blocks until maxWaitTime or until all jobs on all threads
        are completed, whichever comes first. It raises exceptions on failures
        of jobs, nodes or threads. 

        - Use the wait() function of a specific thread to block only on that thread.
        - Set interactive=True to spawn a control thread on Exception as in check().
        """

        startTime = datetime.datetime.now()
        self.log( "Wait loop started on %s" % str( startTime ), 3 )
        while True:
            
            success = self.check( interactive )
            
            if success:
                endTime = datetime.datetime.now()
                self.log( "Wait loop ended with success on %s" % str( endTime ), 3 )
                break

            if maxWaitTime:
                elapsedTime = datetime.datetime.now() - startTime
                if elapsedTime.seconds > maxWaitTime:
                    self.log( "Wait loop ended due to maxWaitTime timeout %ds." % maxWaitTime, 3 )
                    break

            time.sleep( interval )
            self.log( str(self), 1 )

    def check( self, interactive=False ):
        """Check returns True if all threads have completed all jobs successfully. Otherwise it returns
        False. Check will raise an Exception if something has gone wrong.
        Turning the interactive flag on means that when an exception occurs, a new thread will be spawned
        with a command-line interface to the manager before the exception is passed up above this level.
        (ie you still need to handle the exception)"""

        self.log( "Check initiated at  %s" % str( datetime.datetime.now() ), 3 )
        self.updateQStat()
        if self.success():
            self.log( "Check succeeded, success.", 3 )
            return True

        try:
            for name in self.threads:
                self.threads[name].check( )
        except GridThreadError as e:
            self.log( "Error raised: %s" % e, 3 )
            if interactive:
                print("Error: %s" % e)
                self.manageThreads()
            raise

        self.log( "Check succeeded, no success yet.", 3 )
        return False

    def manageThreads( self ):
        """Spawns a control object in a new thread which allows the user
        to interact with the manager. This does *not* call check(), and so
        will not raise exceptions on errors. Use wait() with the interactive
        flag on for that functionality."""

        control = GridThreadControl( self )
        control.start()

    def success( self ):
        """Returns true iff all submitted jobs have been successfully
        completed. It is a bad idea to do 'while( !gtm.success() ) wait',
        as this will never evaluate to true if something goes wrong in
        a thread or job."""

        for thrd in list(self.threads.values()):
            if not thrd.success():
                return False
        return True

    def restartThread( self, threadName, startAtLastUnfinishedJob=False, startAtJobN=None ):
        """Restarts the specified thread, re-submitting it to the queue.

        - If StartAtLastUnfinishedJob is set to True, then all jobs which
        returned exit status of zero will be skipped in this new thread.

        - If startAtJobN is set to a job ID, all jobs after that job are
        reset, all before are not.
        """
        
        if not threadName in self.threads:
            raise ThreadNameError("Invalid thread name (%s) supplied to restartThread function." % (threadName) )

        if startAtLastUnfinishedJob:
            startAtJobN = self.threads[ threadName ].currentJob

        self.log("Restarting thread %s. StartAtLastUnfinishedJob: %s" % (threadName, startAtLastUnfinishedJob), 3 )
        toRestart = self.threads[ threadName ]
        toRestart.kill()

        # This is annoyingly complicated.
        jobs = []
        for (i, job) in enumerate( toRestart.jobs ):
            parentPointer = job.parent
            job.parent = None
            newJob = copy.deepcopy( job )
            job.parent = parentPointer
            jobs.append( newJob )
            
        timeoutSeconds = toRestart.timeoutSeconds
        qrshArgs = toRestart.qrshArgs

        del self.threads[ threadName ]

        newThread = GridThread( "", jobs, timeoutSeconds, threadName, qrshArgs, self, self.qPath )
        for job in jobs:
            job.parent = newThread

        for (i,job) in enumerate(jobs):
            if not( startAtJobN and i<startAtJobN ):
                job.reset()

        self.threads[ threadName ] = newThread
        self.threads[ threadName ].start()
        self.log("Thread %s successfully restarted." % threadName, 3 )

    def restartBrokenThread( self, startAtLastUnfinishedJob=False ):
        """Performs as 'restartThread', but specifically restarts the
        thread which raised the most recent exception on a wait() or check()."""
        self.restartThread( self.brokenThread.getName(), startAtLastUnfinishedJob )

    def submitThread( self, command, argList=[], timeoutSeconds=-1, name=None, qrshArgs="", prefix="gt" ):
        """Given a command, and an optional list of arguments
        to substitute into the command string, spawns a new
        thread to perform the task(s). A name for the
        job may be specified for later specific retrieval.
        **NOTE: Name must be 10 chars or less due to qstat lameness.

        command must be a string, and may optionally contain
        '%s' where arguments from argList will be substituted.

        argList may be in one of two forms. If a single task
        is to be run, then argList should simply be a list of
        arguments to substitute in for the '%s's in the command.

        Example:
            command = 'cat %s %s > %s'
            argList = [ 'a', 'b', 'c' ]
            result:
                cat a b > c

        If the command is to be run more than once, however, then
        argList should be a list of sets of arguments. Each element
        of argList will be substituted in to the command string, one
        at a time.

        Example:
            command = 'cat %s %s > %s'
            argList = [ ['a','b','c'], ['d','e','f'], ['g','h','i'] ]
            result:
                cat a b > c
                cat d e > f
                cat g h > i

        An optional timeout in seconds can be provided, if not specified
        it defaults to infinity. Threads which timeout will raise a
        ThreadTimeoutError on a wait() or check() call.

        Additional arguments to pass to the qrsh call should be passed
        as a string in 'qrshArgs'.
        
        The name of the job is returned.
        """

        if name and len( name ) > 10:
            raise ThreadNameError("Names of thread (%s) must be no more than 10 characters long." % name)

        if name and ( name in self.getAllThreadNames() ):
            raise ThreadNameError("Error, specified thread name (%s) is already in use on the cluster." % name)

        if prefix and len( prefix ) > 5:
            raise ThreadNameError("Prefix for thread (%s) must be no more than 5 characters long." % prefix)
        
        if not name:
            name = "%s%d" % ( prefix, random.randint(0, 99999) )
            while name in self.getAllThreadNames():
                name = "%s%d" % ( prefix, random.randint(0, 99999) )
            
        thrd = GridThread( command, argList, timeoutSeconds, name, qrshArgs, self, self.qPath )
        self.threads[name] = thrd
        self.threads[name].start()
        self.log( "Thread %s submitted." % name, 3 )
        return name

    def killThread( self, name ):
        """Attempts to stop/kill the specified thread using qdel
        and removes it from the list of managed threads."""

        if not name in self.threads:
            raise ThreadNameError("Invalid thread name (%s) supplied to killThread function." % (name) )
        
        self.threads[name].kill()
        self.log("Killed thread %s." % name, 3 )
        del self.threads[name]

    def killBrokenThread( self ):
        """Kills the thread which most recently raised an error on a wait()
        or check() call as in killThread."""
        self.killThread( self.brokenThread.getName() )

    def getAllThreadNames( self ):
        """Returns a list of the names of all threads currently running
        on the cluster."""
        self.updateQStat()
        return [x[0] for x in self.qstat]

    def getOutput( self, threadName ):
        """Given the name of a previously submitted thread, returns the output
        of the job(s) running in this thread as a list of strings.
        If one or more jobs executed in the thread has not yet completed, the
        output returned for that job will be None."""

        return self.threads[threadName].getOutput()

    def getStatus( self, threadName ):
        """Returns the status of the given thread, based off of qstat.
        Returns None if the specified thread is not found."""
        self.updateQStat()
        for ( tName, tID, tStatus, tQueue ) in self.qstat:
            if tName == threadName:
                return tStatus
        return None

    def updateQStat( self ):
        """Internal method which calls qstat and updates internal variables
        accordingly. This is used just before any status lookups. Returns
        True/False to indicate success."""

        retriesLeft = 100
        while retriesLeft > 0:

            failed, data = subprocess.getstatusoutput( os.path.join( self.qPath, "qstat" ) )

            if failed:
                retriesLeft -= 1
                self.log("Qstat failed. %s retries left." % retriesLeft, 3)
                continue

            self.qstat = []        
            for line in data.split("\n"):
                result = re.search("\s+".join( ["(\d+)", "[\d\.]+", "(\w+)", "\w+", "(\w+)", "[\d\/]+", "[\d\:]+", "(\S+)", "\d+"] ), line)
                if result:
                    self.qstat.append( (result.group(2), result.group(1), result.group(3), result.group(4)) )

            self.log( "Qstat update completed successfully.", 3 )
            return

        raise QStatFailureError("call to qstat failed, unable to monitor thread status: " + str(data))

    def getBrokenThread( self ):
        """Returns the last thread that caused an exception."""
        return self.brokenThread

    def __str__( self ):
        """The string representation for this class is meant to serve
        as a relatively comprehensive debug output of the current state
        of the manager and all of its threads."""

        return self.getStr()

    def getStr( self, hideSuccessful=False ):
        """This function is similar to __str__, but provides the
        option of hiding successful threads in the output."""

        out = "Grid Thread Manager (%d threads)\n" % len( self.threads )
        out = out + "============================================\n"
        out = out + " ".join( ["Name".ljust(10), "Total Time".ljust(12), "Job Time".ljust(12), "Status".ljust(8), "Progress".ljust(16), "Success".ljust(8)] ) + "\n"
        out = out + " ".join( ["----".ljust(10), "----------".ljust(12), "--------".ljust(12), "------".ljust(8), "--------".ljust(16), "-------".ljust(8)] ) + "\n"
        for name in copy.copy(self.threads):
            thrd = self.threads[name]
            if not ( hideSuccessful and thrd.success() ):
                out = out + " ".join( [thrd.getName().ljust(10),
                                        (str( thrd.getExecTime().seconds ) + "s").ljust(12),
                                        (str( thrd.getJobTime().seconds ) + "s").ljust(12),
                                        str(self.getStatus( name )).ljust(8),
                                        thrd.progressString().ljust(16),
                                        str( thrd.success() ).ljust(8)] ) + "\n"
        return out + "\n"

    def getThreadNames( self ):
        """Returns a list of the names of all threads spawned from
        this manager."""

        return list(self.threads.keys())


class GridThread( threading.Thread ):
    """GridThread represents a single thread being run on the cluster.
    This thread will execute one or more jobs in series, and will maintain
    states and output information for each job."""
    
    def __init__ ( self, command, argList, timeoutSeconds, tName, qrshArgs, manager, qPath ):
        """Init with the command to be run, an argList as described in the
        GridThreadManager.submitJob() documentation, and an optional name
        for this thread. If not specified, a name will be assigned.

        If argList is a list of GridJobs, then command is ignored and the
        list of gridJobs is directly imported into the thread."""
            
        threading.Thread.__init__( self, name=tName )

        self.manager = manager
        self.jobs = []
        self.qPath = qPath
        # No argList => run the command alone.
        if len( argList ) == 0:
            self.jobs.append( GridJob( command, self, self.qPath ) )
        # Each element of argList is a string =>
        #               Run command once for each string.
        elif not ( False in [isinstance( x, str ) for x in argList]):
            for args in argList:
                self.jobs.append( GridJob( command % (args), self, self.qPath ) )
        # Each element of argList is a list of strings =>
        #               Run command once for each set of arguments.
        elif not ( False in [isinstance( x, (list,tuple) ) for x in argList]):
            for args in argList:
                self.jobs.append( GridJob( command % tuple(args), self, self.qPath ) )
        # Each element of argList is a GridJob =>
        #               Import them all directly and continue.
        elif not ( False in [isinstance( x, (GridJob) ) for x in argList]):
            self.jobs = argList
        # Otherwise, the argList and/or command was specified incorrectly.
        else:
            raise InvalidArgumentError("Invalid command/argList passed to GridThreadManager: %s" % argList)

        # Let the job know where it stands.
        for (i, job) in enumerate( self.jobs ):
            job.setID(i)

        self.timeoutSeconds = timeoutSeconds
        self.qrshArgs = qrshArgs
        self.mostRecentJobStart = None
        self.currentJob = None
        self.started = False
        self.finished = False
        self.stop = False
        self.brokenJob = None

    def __getitem__( self, jobNumber ):
	"""Accesses the internal list of GridJob objects."""
	if isinstance( jobNumber, int ) and len( self.jobs ) > jobNumber and jobNumber >= 0:
		return self.jobs[ jobNumber ]
	raise InvalidArgumentError("Unable to find specified job. Make sure you're passing an int. (%s)." % str(jobNumber) )

    def run( self ):
        """Run is called when the thread is started."""

        self.started = True
        self.startTime = datetime.datetime.now()
        self.log( "Started on %s." % str(self.startTime), 3 )
        
        for (i, job) in enumerate( self.jobs ):
            if self.stop:
                self.log( "Stopped by an external controller.", 3 )
                sys.exit()
            self.mostRecentJobStart = datetime.datetime.now()
            self.currentJob = i
            self.log( "Executing job %d." % i, 3 )
            job.execute( self.getName(), extraArgs=self.qrshArgs )

            if job.getStatus() != 0:
                self.log( "Job %d returned non-zero status, thread stopping.", 3 )
                # if exit status is not zero, we bail out and let the manager deal with it.
                return

        self.finishTime = datetime.datetime.now()
        self.finished = True
        self.log( "Finished on %s." % str(self.finishTime), 3 )

    def log( self, message, spew ):
        """Given a message and logFile != None, logs the message
        with an identifier for this thread."""

        lines = message.split("\n")
        for line in lines:
            self.manager.log( self.getName() + ": " + line, spew )

    def wait( self,interval=0.1 ):
        """Wait takes in a polling interval (in seconds) for error and timeout
        checking, and blocks until all jobs on this thread are completed. It
        raises exceptions on failures of jobs, nodes or threads. Use the wait()
        function of the Manager class to monitor all threads at once."""

        self.log("Wait loop started.", 3)
        while True:
            self.manager.updateQStat()
            self.check( )
            if self.success( ):
                break
            time.sleep( interval )
        self.log("Wait loop terminated successfully.", 3)

    def check( self  ):
        """Check will check for any errors associated with this thread, and will
        raise the appropriate exception if necessary. NOTE: for performance reasons,
        check() does not call updateQStat(). Saved qstat data is used, so call
        GridThreadManager.updateQStat( ) before you call check().

        If the thread has completed successfully, this is a no-op."""

        self.log("Checking self.", 3)
        if self.success():
            self.log("Completed, so check passes.", 3)
            return

        try:
            # Check for qstat errors
            self.log("Checking Thread Status.", 3)
            self.checkThreadStatus()
            # Check for timeout errors
            self.log("Checking Thread Timeout.", 3)
            self.checkTimeout()
            # Check for job status errors
            self.log("Checking Job Status.", 3)
            self.checkJobStatus()
        except (ThreadStatusError, ThreadTimeoutError, JobStatusError):
            self.log("Exception raised in check.", 3)
            self.manager.brokenThread = self
            raise

        self.log( str(self), 2 )
            
    def checkThreadStatus( self ):
        """Checks for bad status through qstat. Raises a
        ThreadStatusError if it finds something bad."""
    
        for ( tName, tID, tStatus, tQueue ) in self.manager.qstat:
            if self.getName() == tName:
                if tStatus in ("E", "a", "A", "c" ):
                    self.manager.brokenThread = self.getName()
                    raise ThreadStatusError("Thread %s(%s) has status %s on queue %s." % (tName, tID, tStatus, tQueue) )
                else:
                    return
            
    def checkTimeout( self ):
        """Checks to see if this thread has been stuck on the same job with no change
        for longer than the specified timeout. Raises a ThreadTimeoutError."""
        if self.timeoutSeconds > 0 and self.mostRecentJobStart:
            elapsedTime = datetime.datetime.now() - self.mostRecentJobStart
            if elapsedTime.seconds > self.timeoutSeconds:
                raise ThreadTimeoutError("Thread %s timed out (%d s) while executing a job." % ( self.getName(), self.timeoutSeconds ))
    
    def checkJobStatus( self ):
        """Checks the status of all completed jobs in this thread, raising a JobStatusError
        if one has returned a non-zero status."""

        for (i, job) in enumerate(self.jobs):
            if job.status and job.status != 0:
                self.brokenJob = job
                raise JobStatusError("Job %d in thread %s returned error status %s." % ( i, self.getName(), job.status ) )

    def success( self ):
        """Returns true iff all jobs in this thread were completed successfully."""
        for job in self.jobs:
            if not job.success():
                return False
        return self.finished

    def signalStop( self ):
        """This function sets a flag in the thread, telling it to exit ASAP. This
        will not occur until the currently running job has completed."""
        self.stop = True

    def restart( self, startAtLastUnfinishedJob=False ):
        """Functions exactly as restartThread in the manager."""
        self.manager.restartThread( self.name, startAtLastUnfinishedJob )

    def getExecTime( self ):
        """Returns the elapsed time since this thread was started, in the form
        of a datetime.timedelta object. Use the .seconds or .microseconds attributes
        of the timedelta object to get the elapsed time in seconds or microseconds."""
        
        if self.finished:
            return self.finishTime - self.startTime
        else:
            return datetime.datetime.now() - self.startTime

    def getJobTime( self ):
        """Returns the elapsed time in seconds since the most recent job was
        started, in the form of a datetime.timedelta object. Use the .seconds or
        .microseconds attributes of the timedelta object to get the elapsed time
        in seconds or microseconds."""

        if self.finished:
            return self.finishTime - self.mostRecentJobStart
        else:
            return datetime.datetime.now() - self.mostRecentJobStart

    def getProgress( self ):
        """Returns the progress of the thread through its job list.
        ( # jobs completed / total # jobs )"""
        return float( sum( [x.finished and 1 or 0 for x in self.jobs] ) ) / float( len( self.jobs ) )

    def progressString( self ):
        """Returns a pretty string representing the progress of
        this thread through its job list."""

        prog = self.getProgress() * 100.0
        total = len( self.jobs )
        done = sum( [x.finished and 1 or 0 for x in self.jobs] )
        return "%.2f%% (%d/%d)" % (prog, done, total)

    def getOutput( self ):
        """Returns the output of the job(s) running in this thread,
        in the form of a list of strings. Jobs which have not yet
        been completed will return None as their output."""

        return [x.getOutput() for x in self.jobs]

    def getBrokenJob( self ):
        """Returns the last job that caused an exception."""
        return self.brokenJob

    def __str__( self ):
        """The string representation of a GridThread shows information
        about each job that should run in this thread."""

        return self.getStr()

    def getStr( self, hideSuccessful=False ):
        """This function implements __str__, but provides the option
        of hiding successful jobs."""
        
        out = "Thread " + self.getName() + ":\n"
        out = out + "Progress: %s\n" % self.progressString()
        out = out + "================================\n"
        out = out + " ".join( ["JobID".ljust(7), "Command".ljust(40),"Status".ljust(12),"qrsh Status".ljust(12),"Success?".ljust(9)] ) + "\n"
        out = out + " ".join( ["-----".ljust(7), "-------".ljust(40),"------".ljust(12),"-----------".ljust(12),"--------".ljust(9)] ) + "\n"
        for (i,job) in enumerate(self.jobs):
            if not( hideSuccessful and job.success() ):
                out = out + " ".join( [str(job.getID()).ljust(7),
                                       str(job.getCommand()[-40:]).ljust(40),
                                       str(job.getStatus()).ljust(12),
                                       str(job.getQrshStatus()).ljust(12),
                                       str(job.success()).ljust(9)] ) + "\n"
        return out + "\n" 

    def kill( self ):
        """Attempts to kill this thread using qDel. Raises an error on failure.
        This should probably only be run from inside the manager unless you know
        what you are doing."""

        self.signalStop()
        ( status, output ) = subprocess.getstatusoutput( "qdel %s" % self.getName() )
        if status:
            raise ThreadControlError( "Unable to kill thread %s. (status %d)" % ( self.getName(), status ) )
        self.log("Successfully killed self.", 3)
        
class GridJob:
    """A GridJob is a single task to be performed by a GridThread.
    It knows its command text, status, and output."""

    def __init__( self, commandString, parentThread, qPath ):
        """Initialize with the command string to be run."""
        self.command = commandString
        self.parent = parentThread
        self.id = None
        self.reset()
        self.qPath = qPath

    def setID( self, i ):
        """Sets the internal id for this job."""
        self.id = i

    def getID( self ):
        """Returns the job's internal ID."""
        return self.id

    def log( self, message, spew ):
        """Given a message, and that manager.logFile != None, logs the
        message with a job-specific identifier."""

        lines = message.split("\n")
        for line in lines:
            self.parent.log( str(self.getID()) + ": " + line, spew )

    def execute( self, name, extraArgs="" ):
        """Executes the command associated with this job. If this job has already
        been run once successfully and was not reset since, this is a no-op.

        If status == -1, then something went wrong with the extraction of the
        return status of the job, and the output should be examined."""

        self.log( str(self), 3)
        self.log("Job Executing.",3)
        if self.success():
            self.log("Job complete, so no need to run it again, returning.",3)
            return

        qrshPath = os.path.join( self.qPath, "qrsh" )
        
        cmd = "%s -nostdin -now no -N %s %s \'%s; echo \"%s\"\'" % ( qrshPath, name, extraArgs, self.command, "|%s|$?|%s|" % (name, name) )
        self.log("Running command. (%s)" % cmd,3 )
        ( self.qrshStatus, output ) = subprocess.getstatusoutput( cmd )
        self.log("Command completed, extracting output and status.",3)
        self.log("Raw Output: |||||%s||||||" % output, 3 )
        matches = re.search("^(.*)\|%s\|(\d+)\|%s\|(.*)" % (name,name), output, re.DOTALL )
        if matches:
            self.log("Status found, recording.",3)
            self.status = int( matches.group(2) )
            self.output = matches.group(1) + matches.group(3)
        else:
            self.log("Status not found. Setting to -1 and storing output.",3)
            self.status = -1
            self.output = output
            
        self.finished = True
        self.log("Job Finished, returning.",3)
        self.log( str(self), 3)
        return self.output

    def getStatus( self ):
        """Returns the current status of this job."""
        return self.status

    def getQrshStatus( self ):
        """Returns the status of the qrsh run for this job."""
        return self.qrshStatus

    def getOutput( self ):
        """Returns the output of this job."""
        return self.output

    def getCommand( self ):
        """Returns the command this job is to run."""
        return self.command

    def success( self ):
        """Returns True iff this job was successfully completed."""
        return self.finished and (self.status == 0)       
        
    def reset( self ):
        """Resets this job to its original state, ready to run with no
        recorded status or output."""

        # Skip the reset called in init.
        if self.id:
            self.log("Resetting job.", 3)
        
        self.finished = False
        self.output = None
        self.status = None
        self.qrshStatus = None

    def __str__( self ):
        """Returns a string with all data from this job."""

        return self.getStr()

    def getStr( self, hideSuccessful=False ):
        """This function performs as __str__, but provides
        the option to print nothing if the job was successful.
        This isn't very useful, but is necessary in order to
        provide a consistant interface for getStr() in the
        manage, threads, and jobs."""

        if hideSuccessful:
            return ""
        
        out = ""
        if self.output:
            #out = self.output[:40].replace("\n"," ")
            out = self.output
        return """Command: %s
        Qrsh Status: %s
        Job Status: %s
        Finished?: %s
        Output: %s""" % ( self.command, self.qrshStatus, self.status, self.finished, out )

class GridThreadControl( threading.Thread, cmd.Cmd ):
    """GridThreadControl gives the user control of the GridThreadManager, 
    allowing them to inspect and minimally manage the running threads and
    jobs."""

    def __init__( self, manager ):
	"""Simply stores the manager for later use."""
	threading.Thread.__init__( self, name="GridThreadControl" )
	cmd.Cmd.__init__( self )
	self.manager = manager
	self.prompt = "GridThreadControl$ "

    def run( self ):
	"""Called when control is passed to this controller, this method
        loops through user inputs, taking appropriate actions when needed.
	Returns when the user decides to finish her control."""

        self.cmdloop("""
	GridThreads Interactive Thread Manager Control
	==============================================
	Type ? for help.
	""")

    def do_resume( self, args ):
        """Returns control to the GridThreadManager"""
        return True

    def help_resume( self ):
        """Returns control to the GridThreadManager"""
        print("""
                resume:
                    Returns control to the GridThreadManager
                    """)

    def do_print( self, args ):
        """Prints information about [A]ll work in the specified object."""

        hideSuccessful = False
        if re.search("-i", args):
            args = args.replace("-i","")
            hideSuccessful = True

        print()
        self.printObj( args, hideSuccessful )
        return False

    def help_print( self ):
        """Prints information about [A]ll work in the specified object."""
        print("""
                print [-i] [thread] [jobNum]:
                    Prints information about the specified object.
                    Options:
                        -i: restricts the output to jobs or threads which are incomplete.
                        """)

    def do_kill( self, args ):
        """Kills the specified thread."""
        arg = args.strip()
        if arg == "":
            print("Please specify a thread name.")
            return False
        self.manager.killThread( arg )
        return False

    def help_kill( self ):
        """Kills the specified thread."""
        print("""
                kill thread:
                    Kills the specified thread.
                    """)

    def do_restart( self, args ):
        """Restarts the specified thread. If jobNum is specified, execution begins there."""

        argList = args.strip().split()

        if len( argList ) == 0:
            print("Invalid arguments.")
            return False
        
        jobToStartOn = None
        if len( argList ) == 2:
            try:
                jobToStartOn = int( argList[1] )
            except ValueError:
                print("Please specify an integer value for Job ID.")
                return False
        
        self.manager.restartThread( argList[0], startAtJobN=jobToStartOn )

    def help_restart( self ):
        """Restarts the specified thread. If jobID is specified, execution begins there."""
        print("""
                restart thread [jobID]:
                    Restarts the specified thread. If jobNum is specified, execution begins there.
                    """)
        
    def do_quit( self, args ):
        """Calls system.exit() in the control thread, killing the GridThreadManager."""
        for name in self.manager.getThreadNames():
            self.manager.killThread( name )
        sys.exit()

    def help_quit( self ):
        """Calls system.exit() in the control thread, killing the GridThreadManager."""
        print("""
                quit:
                    Calls system.exit() in the control thread, killing the GridThreadManager.
                    It will attempt to kill the child threads, but this is not guaranteed to work.
                    """)

    def do_exit( self, args ):
        """Calls system.exit() in the control thread, killing the GridThreadManager."""
        for name in self.manager.getThreadNames():
            self.manager.killThread( name )
        sys.exit()

    def help_exit( self ):
        """Calls system.exit() in the control thread, killing the GridThreadManager."""
        print("""
                exit:
                    Calls system.exit() in the control thread, killing the GridThreadManager.
                    It will attempt to kill the child threads, but this is not guaranteed to work.
                    """)
    

    def printObj( self, args, hideSuccessful ):
	"""Called by the user with arguments, this method will print out
	the objects specified in args."""

	argList = args.strip().split()
	if len( argList ) == 0:
		print(self.manager.getStr( hideSuccessful ))
	if len( argList ) >= 1:
		if argList[0] in self.manager.threads:
			thrd = self.manager.threads[ argList[0] ]
			if len( argList ) == 1:
				print(thrd.getStr( hideSuccessful ))
			if len( argList ) == 2:
				try:
					jobNum = int( argList[1] )
				except ValueError:
					print("Job ID must be an integer. Please check your input")
					return
				if jobNum >= len( thrd.jobs ) or jobNum < 0:
					print("Unable to locate this job. Please check your input")
					return
				print(thrd.jobs[ jobNum ])
		else:
			print("Unable to locate thread %s. Please check your spelling." % argList[0])			


################################################################
# Test Code!

if __name__ == "__main__":
    gtm = GridThreadManager( logFile="gtm.log", spewLevel=3 )
    gtm.submitThread("ls %s", [ "/nfs/sumo/home/dale/", "/nfs/sumo/home/kael/", "/nfs/sumo/home/amy/" ] )
    gtm.submitThread("pwd")
    gtm.submitThread("ls")
    gtm.submitThread("sleep %s", [str(x) for x in range(0,4,2)] )
    gtm.submitThread("du -sh %s", ( "/sumo/home/dale/polioChip/", "/sumo/home/dale/shotgun/" ), name="du" )
    gtm.submitThread("ls -l %s", ("/sumo/home/dale/", "blah1", "blah2", "/sumo/home/dale/" ), name="badLS")
    #gtm.submitThread("sleep 9999", name="sleepy1", qrshArgs="-l hostname=SecondLife-20")
    #gtm.submitThread("sleep 9999", name="sleepy2", qrshArgs="-l hostname=SecondLife-20")
    gtm.submitThread("sleep%s", [" 4","yyyy"," 4"], name="resetTest" )
    #print gtm
    #for i in range(2):
    #	gtm.submitThread("/usr/local/genome/bin/cross_match /sumo/home/derisilab/For/dale/tmp2.fasta /mighty/sequences/hg18_UCSC/20MB_chunks/chr1_part_01.fa -screen%s", ["","",""], qrshArgs="-l hostname=derisi-b5")  
    #for i in range( 100 ):
    #    gtm.submitThread("sleep %s", map( lambda x: str( (x % 2) + 0), range(i) ))

    print(gtm["du"])
    print(gtm["du"][0])

    while not gtm.success():
    	try:
        	gtm.wait( interval=10, maxWaitTime=480, interactive=True )
    	except GridRuntimeError as err:
        	print(err)
        	bt = gtm.brokenThread
		print(bt)
        	gtm.restartBrokenThread(startAtLastUnfinishedJob=True)
    
