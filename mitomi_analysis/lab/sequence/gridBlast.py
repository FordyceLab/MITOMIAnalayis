#!/usr/local/bin/python -u

###########################################################
#
# Simple class to facilitate running BLAST on the cluster
#
# Author: Dale Webster
# Date: 6/10/07
#
###########################################################

import sys, os
import tempfile
import math
import commands

from grid.GridThreads import *
from sequence import fasta

class GridBlastError( Exception ):
    pass


m8 = ["name", "hit", "identity", "hitLength", "mm", "gaps", "qStart", "qEnd", "sStart", "sEnd", "p", "score"]
def parseM8( m8File, oneHspPerHit ):
    """Given the path of a blast -m 8 result file,
    returns a list of dicts, where each element
    contains all of the m8 information for one
    result(row) in the file.

    oneHspPerHit does what one would imagine, it limits
    the returned data to a single HSP per hit.

    NOTE: This parser currently also works on megablast -D 3 output.
    That assumption is used in the GridMegaBlast class."""

    results = []
    for line in open( m8File, 'r' ):
        data = line.split()
        results.append( dict( zip( m8, data ) ) )

    if oneHspPerHit:
        results.sort( cmp=lambda x,y: cmp( x["score"], y["score"] ) )
        resultHash = {}
        for r in results:
            resultHash[ (r["name"],r["hit"]) ] = r
        return resultHash.values()
    else:
        return results

class GridBlast ( GridThreadManager ):
    """Runs BLAST jobs on the blade array. This extends the GridThreadManager class, so you can use it to monitor
    the status of the grid jobs using the appropriate methods from GridThreads."""

    def __init__( self, tmpDir, logFile=None, blastPath="blastall", qPath="" ):
        """This class requires a writeable directory to function. Specify here or it defaults to /tmp.
        This directory must be accessible from all of the grid nodes, and the machine that runs this
        script."""
            
        self.tmpDir = tmpDir
        self.logFile = logFile
        self.blastPath = blastPath
        self.tempFiles = []
        self.activeQueries = []
        self.parameters = None
        self.queryFile = None
        GridThreadManager.__init__( self, logFile=logFile, qPath=qPath )

    def submitBlast( self, thingToBlast, dbPath, N=12, parameters="-p blastn", formatParameters="-m 8", prefix="GrBl"):
        """Initiates a BLAST job with the given parameters.

        thingToBlast can be:
        -   a path to a FASTA file
        -   anything or list of things that evaluates to a valid FASTA string(s) when the str() method is applied. (this includes fasta.Record objects)

        N is the maximum number of parallel BLASTs to execute.
        (the sequences will be split up into at most N files.)
        
        parameters can be either an explicit parameter string to append to the blast call (ie. '-p blastn -b 3')
        or a dictionary of { parameter:value } pairs, which will be translated to '-parameter1 value1 -parameter2 value2'

        submitBlast returns a list of the names of the threads which are running this Blast.
        """

        # Store for database use
        self.parameters = parameters
        self.dbPath = dbPath
        
        ############################
        # Build the query

        queryPath = None
        if isinstance( thingToBlast, str ) and os.path.lexists( thingToBlast ): # path to a FASTA file
            queryPath = thingToBlast
            self.queryFile = queryPath

        elif isinstance( thingToBlast, (tuple, list) ):
            ( of, queryPath ) = fasta.mystemp( suffix='.fasta', dir=self.tmpDir )
            for elt in thingToBlast:
                of.write(str(elt) + "\n")
            of.close()
            self.tempFiles.append( queryPath )
        else:
            ( of, queryPath ) = fasta.mystemp( suffix='.fasta', dir=self.tmpDir )
            of.write(str(thingToBlast))
            of.close()
            self.tempFiles.append( queryPath )

        ############################
        # Split the query
        queryFiles = fasta.splitFasta( queryPath, N, tmpDir=self.tmpDir )
        self.tempFiles = self.tempFiles + queryFiles

        ############################
        # Build the BLAST line
        blastLine = "%s %s -d %s" % ( self.blastPath, formatParameters, dbPath )
        if isinstance( parameters, str ):
            blastLine = blastLine + " " + parameters
        else:
            parameterStrings = map( lambda x: "-%s %s" % ( x, parameters[x] ), parameters.keys() )
            blastLine = blastLine + " " + " ".join( parameterStrings )

        threads = []
        for qf in queryFiles:
            outfile = qf.replace(".fasta",".br")
            self.tempFiles.append( outfile )
            command = "%s -i %s -o %s" % ( blastLine, qf, outfile )
            thread = self.submitThread( command, qrshArgs="-l arch='fbsd-amd64'", prefix=prefix )
            #thread = self.submitThread( command, qrshArgs="-l arch='fbsd-amd64' -l mf=1.0G" )
            self.activeQueries.append( ( thread, outfile ) )
            threads.append( thread )

        return threads            


    def getBlastResults( self, titles=None, oneHspPerHit=False, parser=parseM8 ):
        """If all threads succeeded, this function returns a list of dicts,
        where each dict contains all of the relevant information for a single
        line in an m8 BLAST result file.

        If titles is specified, then the method returns only data associated
        with queries exactly matching one of the specified titles.

        If there are still BLAST threads running, this function returns None.
        Use the methods inherited from GridThreadManager to check for success
        before calling this function.

        Use oneHspPerHit to limit the results returned.
        """

        if not self.success():
            return None
        results =  []
        for ( thread, outfile ) in self.activeQueries:
            data = parser( outfile, oneHspPerHit )
            for elt in data:
                if (not titles) or (elt["name"] in titles):
                    results.append( elt )

        return results

    def saveBlastResults( self, filename ):
        """Functions as getBlastResults, but instead of returning the
        results, it saves them in tablar m8 format to the specified
        filename. Uses the OS, so its really fast.

        Returns True on success, False on failure."""

        if not self.success():
            return False

        sourceFiles = map( lambda x: x[1], self.activeQueries )
        ( status, output ) = commands.getstatusoutput("cat " + " ".join( sourceFiles ) + " > " + filename)
        if status != 0:
            return False
        return True

    def storeBlastResults( self, fastaFileName=None, oneHspPerHit=False, dbDescription=None, qryDescription=None, largeDb=True ):
        """Functions as getBlastResults, but instead of returning the
        results, it stores them in the Blast_Results database.

        fastaFileName defines the file that will be inserted into the database
        as the query file. If you passed a single FASTA filename to the original
        submitBlast call, then you can leave this alone. Otherwise you need to
        specify it, or the function will raise an exception.

        dbDescription and qryDescription are simply passed along for storage in the database.
        """
        from sequence import blast

        if not self.success():
            return None

        faFile = None
        if fastaFileName:
            faFile = fastaFileName
        elif self.queryFile:
            faFile = self.queryFile
        else:
            raise GridBlastError("A Fasta File must be specified for this search in order to store the results.")

        return blast.insertBlastResults( self.dbPath,
                                         faFile,
                                         self.parameters,
                                         map( lambda x: x[1], self.activeQueries ),
                                         dbDescription,
                                         qryDescription,
                                         largeDb=largeDb,
                                         oneHspPerHit=oneHspPerHit)
        

    def cleanup( self ):
        """You should call this method explicitly to remove temporary files
        associated with the BLASTs after you've obtained your results."""

        for fPath in self.tempFiles:
            if os.path.lexists( fPath ):
                os.unlink( fPath )

    def getBlastResultsIterator( self ):
        """Slimmed down version of getBlastResults with limited functionality
        but takes very little memory overhead. This should be used for giant
        results where you'd run out of RAM if you loaded them all at once.

        Must be used with the -m 8 formatParameter in submitBlast()."""

        if not self.success():
            return

        for ( thread, outfile ) in self.activeQueries:
            for line in open( outfile, "r" ):
                yield dict( zip( m8, line.split() ) )


class GridMegaBlast ( GridBlast ):
    """Runs megaBLAST jobs on the blade array. This extends the GridBlast class, with a few minor
    changes, so you can still check the status of the grid jobs using the appropriate methods from GridThreads."""

    def __init__( self, tmpDir, logFile=None, blastPath="/usr/local/bin/megablast", qPath="" ):
        """Per GridBlast.__init__"""

        # just change the default parameters here.
        GridBlast.__init__( self, tmpDir, logFile, blastPath, qPath )

    def submitBlast( self, thingToBlast, dbPath, N=12, parameters="", formatParameters="-m 8 -D 3 -R"):
        """Per GridBlast.submitBlast"""

        # Change the default format parameters
        return GridBlast.submitBlast( self, thingToBlast, dbPath, N, parameters, formatParameters, prefix="GrMB" )


    def getBlastResults( self, titles=None, oneHspPerHit=False, parser=parseM8 ):
        """Per GridBlast.getBlastResults"""

        return GridBlast.getBlastResults( self, titles, oneHspPerHit, parser )

    def storeBlastResults( self, fastaFileName=None, oneHspPerHit=False, dbDescription=None, qryDescription=None, storeDbSequences=True ):
        """Not functional in GridMegaBlast."""
        return None

    def saveResults(self,filename):
        """Check all output files for the terminal MEGABLAST report line.
        If present, save the results in named output file, if not present raise
        GridBlastError.
        """

        if not self.success():
            return False

        sourceFiles = map( lambda x: x[1], self.activeQueries )
        for fn in sourceFiles:
            ( status, output ) = commands.getstatusoutput("tail -1 %s | grep -q '^#Mega BLAST run finished'" % fn)
            if status != 0:
                raise GridBlastError, "output in %s is incomplete"

        return self.saveBlastResults(filename)
