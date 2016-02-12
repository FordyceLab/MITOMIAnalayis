#!/usr/local/bin/python
########################################
#
# qmegablast.py
#
# Uses gridMegaBlast to quickly run a megaBLAST
# on multiple queries across the cluster.
#
# Dale Webster
# 9/13/07
#
#########################################

import sys
from utils import CommandLine
from sequence import gridBlast as gb
import os
import subprocess

class QBlastError( Exception ):
    pass

cl = CommandLine.CommandLine()
inFile = cl.requiredArg("inputFile")
outFile = cl.requiredArg("outputFile")
database = cl.requiredArg("database")
logFile = cl.optionalArg("logFile", None, "-l")
tmpDir = cl.optionalArg("tmpDir", os.getcwd(), "-t")
n = cl.optionalArg("NodesToUse", 12, "-n")
params = cl.optionalArg("BLASTParameters", "", "--params")
cl.execute()

n = int(n)

gbm = gb.GridMegaBlast( tmpDir, logFile=logFile )
gbm.submitBlast( inFile, database, N=n, parameters=params )
gbm.wait( interactive=False )
gbm.saveResults( outFile )
gbm.cleanup()
