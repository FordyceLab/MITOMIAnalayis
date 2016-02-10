from __future__ import division
import sys
import os
from getopt import getopt
from M_initialAnalysis import chipSingleconcUtils
from plotting import plotUtils
from statistics import stats_utils
import numpy as N
from fileIOScripts import fileIOUtils
from operator import itemgetter
from scipy import stats

HELP_STRING = """
scatterPlotRep1vsRep2_v4.py

Authored by: Polly Fordyce, August 2008
Updated by: Tyler Shimko, February 2016

This program is designed to plot replicate 1 vs replicate 2
for all oligos in a scatter plot.

     -h    print this help message
     -c    concat_Processed.txt filename

"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    dirName = ''

    try:
        optlist, args = getopt(argv[1:], "hc:")
    except:
        print ""
        print HELP_STRING
        sys.exit(1)

    if len(optlist) == 0:
        print ""
        print HELP_STRING
        sys.exit(1)

    for (opt, opt_arg) in optlist:
        print opt
        print opt_arg
        if opt == '-h':
            print ""
            print HELP_STRING
            sys.exit(1)
        elif opt == '-c':
            cFN = opt_arg

    if cFN == "":
        print HELP_STRING
        sys.exit(1)

    # make array to hold data
    dimensions = (1458, 2)
    rA = N.zeros(dimensions)
    dA = N.zeros(dimensions)

    dD, rD = {}, {}
    cF = open(cFN, 'r')
    lI = 0
    for line in cF:
        lI = lI + 1
        if lI == 1:
            pass
        else:
            tempL = line.strip().split('\t')
            if dD.has_key(int(tempL[16])):
                if len(dD[int(tempL[16])]) < 2:
                    dD[int(tempL[16])].append(float(tempL[18]))
                else:
                    if N.isnan(dD[int(tempL[16])][0]) and
                    not N.isnan(dD[int(tempL[16])][1]) and
                    not N.isnan(float(tempL[18])):
                        dD[int(tempL[16])][0] = (float(tempL[18]))
                    elif not N.isnan(dD[int(tempL[16])][0]) and
                    N.isnan(dD[int(tempL[16])][1]) and
                    not N.isnan(float(tempL[18])):
                        dD[int(tempL[16])][1] = (float(tempL[18]))
                    else:
                        pass
            if rD.has_key(int(tempL[16])):
                if len(rD[int(tempL[16])]) < 2:
                    rD[int(tempL[16])].append(float(tempL[20]))
                else:
                    if N.isnan(rD[int(tempL[16])][0]) and
                    not N.isnan(rD[int(tempL[16])][1]) and
                    not N.isnan(float(tempL[20])):
                        rD[int(tempL[16])][0] = (float(tempL[20]))
                    elif not N.isnan(rD[int(tempL[16])][0]) and
                    N.isnan(rD[int(tempL[16])][1]) and
                    not N.isnan(float(tempL[20])):
                        rD[int(tempL[16])][1] = (float(tempL[20]))
                    else:
                        pass
            else:
                dD[int(tempL[16])] = [float(tempL[18])]
                rD[int(tempL[16])] = [float(tempL[20])]
    cF.close()

    dDL = sorted(dD.items(), key=itemgetter(0))
    rDL = sorted(rD.items(), key=itemgetter(0))

    for b in range(0, len(dDL)):
        dA[b][0] = dDL[b][1][0]
        dA[b][1] = dDL[b][1][1]
        rA[b][0] = rDL[b][1][0]
        rA[b][1] = rDL[b][1][1]

    oDir = os.path.split(cFN)[0] + '/OligoAnalysis/TextFiles'
    if os.path.exists(oDir):
        pass
    else:
        fileIOUtils.createNewDir(oDir)

    oFN1 = oDir + '/rNN_Rep1.dat'
    oF1 = open(oFN1, 'w')
    oFN2 = oDir + '/rNN_Rep2.dat'
    oF2 = open(oFN2, 'w')
    for b in range(0, 1458):
        oF1.write(str(rA[b][0]) + '\n')
        oF2.write(str(rA[b][1]) + '\n')
    oF1.close()
    oF2.close()

    oFN1 = oDir + '/DNAN_Rep1.dat'
    oF1 = open(oFN1, 'w')
    oFN2 = oDir + '/DNAN_Rep2.dat'
    oF2 = open(oFN2, 'w')
    for b in range(0, 1458):
        oF1.write(str(dA[b][0]) + '\n')
        oF2.write(str(dA[b][1]) + '\n')
    oF1.close()
    oF2.close()

    # create scatter plots of replicates vs each other
    scatD = os.path.split(cFN)[0] + '/ScatterPlots/'
    if os.path.exists(scatD):
        pass
    else:
        fileIOUtils.createNewDir(scatD)

    d1 = dA[:, 0].tolist()
    d2 = dA[:, 1].tolist()
    d1o, d2o = [], []
    for a in range(0, len(d1)):
        if not N.isnan(d1[a]) and not N.isnan(d2[a]):
            d1o.append(d1[a])
            d2o.append(d2[a])

    plotUtils.createAndSaveFig(d1o, d2o, scatD + 'DNAN', xLabel="Rep 1",
                               yLabel="Rep 2", xMin=0, yMin=0)
    plotUtils.createAndSaveLogLogPlot(d1o, d2o, scatD + 'DNAN_log',
                                      xLabel="Rep 1", yLabel="Rep 2", xMin=1,
                                      yMin=1)

    r1 = rA[:, 0].tolist()
    r2 = rA[:, 1].tolist()
    r1o, r2o = [], []
    for a in range(0, len(r1)):
        if not N.isnan(r1[a]) and not N.isnan(r2[a]):
            r1o.append(r1[a])
            r2o.append(r2[a])

    plotUtils.createAndSaveFig(r1o, r2o, scatD + 'rNN', xLabel="Rep 1",
                               yLabel="Rep 2", xMin=0, xMax=1, yMin=0, yMax=1)
    plotUtils.createAndSaveLogLogPlot(r1o, r2o, scatD + 'rNN_log',
                                      xLabel="Rep 1", yLabel="Rep 2",
                                      xMin=0.001, xMax=1, yMin=0.001, yMax=1)

    dCorr = stats.pearsonr(d1o, d2o)
    rCorr = stats.pearsonr(r1o, r2o)
    oF = open(os.path.split(cFN)[0] + '/Corr.txt', 'w')
    oF.write('DCorr\tRCorr\n')
    oF.write(str(dCorr[0]) + '\t' + str(rCorr[0]) + '\n')
    oF.close()

    return 0


##############################################
if __name__ == "__main__":
    sys.exit(main())
