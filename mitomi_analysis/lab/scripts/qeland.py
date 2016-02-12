#!/usr/local/bin/python
########################################
#
# qeland.py
#
# Uses GridThreads to split an Eland
# run across multiple nodes. Breaks down
# the eland input file into chunks
# and knits the results back together.
#
# Dale Webster
# 8/16/07
#
#########################################

import sys
from utils import CommandLine
from lab.grid import GridThreads as gt
import os
import commands

class QElandError( Exception ):
    pass

cl = CommandLine.CommandLine()
maxNodes = cl.optionalArg("maxNodes", 80, "-n")
chunkSize = cl.optionalArg("chunkSize(lines)", 500000, "-s")
genomeFN = cl.requiredArg("genomeDir")
oligoFNs = cl.infiniteArg("inputFile1 [inputFile2...]")
cl.execute()

genomeFN = os.path.abspath( genomeFN )
oligoFNs = map( os.path.abspath, oligoFNs )

maxNodes = int(maxNodes)
chunkSize = int(chunkSize)

PATH_TO_ELAND="/usr/local/SolexaPipeline/Eland/eland_30"

def tear( oligoFN ):
    """Tears the specified oligo name into chunks, returning
    a list of the resulting filenames."""
    linesSoFar = 0
    currentFile = None
    oligoFiles = []
    for line in open( oligoFN, "r" ):
        if linesSoFar % chunkSize == 0:
            currentFilename = oligoFN + "." + "%010d" % (linesSoFar) + ".part"
            oligoFiles.append( currentFilename )
            if currentFile:
                currentFile.close()
            currentFile = open( currentFilename, "w" )
        currentFile.write( line )
        linesSoFar = linesSoFar + 1

    if currentFile:
        currentFile.close()

    return oligoFiles

def knit( oligoFN, tornFiles ):
    """Re-knits the output files derrived from the torn
    files into a single output file. Removes the torn
    files and their output files."""

    for fn in tornFiles:
        if not os.access( fn+".out", os.F_OK ):
            raise QElandError("Output file %s was not generated." % fn)

    (o, s) = commands.getstatusoutput("cat " + " ".join( map( lambda x: x+".out", tornFiles ) ) + "> " + oligoFN + ".eland" )

    for fn in tornFiles:
        os.remove( fn )
        os.remove( fn + ".out" )


tornFiles = {}
for oligoFN in oligoFNs:
    tornFiles[ oligoFN ] = tear( oligoFN )

gtm = gt.GridThreadManager()
command = PATH_TO_ELAND + " %s " + genomeFN + " %s" 

commandLists = []
for i in range( maxNodes ):
    commandLists.append( [] )

fileCount = 0
for oligoFN in oligoFNs:
    tfList = tornFiles[ oligoFN ]
    for fn in tfList:
        node = fileCount % maxNodes
        commandLists[node].append( [ fn, fn+".out" ] )
        fileCount = fileCount + 1

for cl in commandLists:
    if len(cl) > 0:
        gtm.submitThread( command, argList=cl, qrshArgs="-l mem_free=370M" )
        # gtm.submitThread( command, argList=cl, qrshArgs="-l arch='lx24-x86' -l mem_free=370M" )

gtm.wait( interactive=True )

for oligoFN in oligoFNs:
    knit( oligoFN, tornFiles[ oligoFN ] )
