#!/usr/local/bin/python
########################################
#
# qblast.py
#
# Uses gridBlast to quickly run a BLAST
# on multiple queries across the cluster.
#
# Dale Webster
# 9/13/07
#
#########################################

import sys
from lab.utils import CommandLine
from lab.sequence import gridBlast as gb
import os
import subprocess

class QBlastError( Exception ):
    pass

def log( stuff, logFile ):
    if logFile:
        out = open( logFile, "a" )
        out.write( stuff )
        out.close()

cl = CommandLine.CommandLine()
inFile = cl.requiredArg("inputFile")
outFile = cl.requiredArg("outputFile")
database = cl.requiredArg("database")
logFile = cl.optionalArg("logFile", None, "-l")
tmpDir = cl.optionalArg("tmpDir", os.getcwd(), "-t")
n = cl.optionalArg("NodesToUse", 12, "-n")
params = cl.optionalArg("BLASTParameters", "-p blastn", "--params")
interactive = cl.optionalFlag("-i","Interactive Mode: Use if you can monitor the job")
messy = cl.optionalFlag("-m","Messy Mode: Do not clean up temporary files in case of an error")
persistent = cl.optionalFlag("-p","Persistent Mode: Restarts failed jobs. Use with Messy Mode to get as many Blast results as possible without supervision. Does not work when the -i flag is specified.")
cl.execute()

n = int(n)

if not os.path.lexists( inFile ):
    print("Error: file %s not found." % ( inFile ))
    sys.exit(0)

restarts = 0
gbm = gb.GridBlast( tmpDir, logFile=logFile )

try:
    gbm.submitBlast( inFile, database, N=n, parameters=params )
except:
    log( "qblast failed during the submission process.", logFile )
    if not messy:
        gbm.cleanup()
    raise

while not gbm.success():
    try:
        gbm.wait( interactive=interactive )
    except gb.GridThreadError:
        if not interactive and persistent:
            if restarts <= n:
                gbm.restartBrokenThread()
                restarts += 1
        if not interactive and not persistent:
            if not messy:
                gbm.cleanup()
            raise
        raise
        
                    
gbm.saveBlastResults( outFile )
gbm.cleanup()
