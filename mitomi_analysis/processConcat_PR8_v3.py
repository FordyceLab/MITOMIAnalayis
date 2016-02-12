from __future__ import division
import sys
import os
from getopt import getopt
import chipSingleconcUtils
import plotUtils
import statsUtils
import numpy as N
import fileIOUtils
import fitUtils
from scipy import stats


HELP_STRING = """
processConcat_PR8_v2.py

Authored by: Polly Fordyce, August 2010
Updated by: Tyler Shimko, February 2016

This program is designed to take a single concatenated genepix
file and a spot2Oligo file and output:
1.  individual text files containing values sorted by oligo and by replicate
2.  graphs showing values for each oligo and histograms
3.  a processed concat file with oligo numbers and sequences assigned to each
    spot

Optional threshhold values can be given to set a lower bound on permissible
background subtracted intensities.

     -h     print this help message
     -c     concat filename (required)
     -s     spot2oligo filename (optional, default is
            /Users/pollyfordyce/Documents/lib/perl/PR8MerSpot2OligoFile.txt)
     -p     pBSub threshold value (optional)
     -d     DNABSub threshold value (optional)
     -t     chBSub threshold value (optional)
     -n     flag spots below thresholds (optional)
     -f     filename containing oligo numbers and sequences
            (default = /Users/pollyfordyce/Documents/lib/perl/8MerLib.txt)
     -y     do not truncate sequences to eliminate common ends (optional)

Example:
python processConcat_PR8_v1.py -c concatFile_042108.txt
"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    concatFileName = ""
    spot2OligoFileName = "/Users/pollyfordyce/Documents/lib/\
                          perl/PR8MerSpot2OligoFile.txt"
    pTh = -500
    DNATh = -500
    chTh = -1000
    nanFlag = 0
    oligoSeqFileName = "/Users/pollyfordyce/Documents/lib/perl/8MerLib.txt"
    truncFlag = 1

    try:
        optlist, args = getopt(argv[1:], "hc:s:p:d:t:nf:y")
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
            concatFileName = opt_arg
        elif opt == '-s':
            spot2OligoFileName = opt_arg
        elif opt == '-p':
            pTh = int(opt_arg)
        elif opt == '-d':
            DNATh = int(opt_arg)
        elif opt == '-t':
            chTh = int(opt_arg)
        elif opt == '-n':
            nanFlag = 1
        elif opt == '-f':
            oligoSeqFileName = opt_arg
        elif opt == '-y':
            truncFlag = 1

    if concatFileName == "":
        print HELP_STRING
        sys.exit(1)

    # get lists from concat file
    blocks, oRows, oCols, rows, cols, flags, pFg, DNAFg, pBg, DNABg, chFg,
    pBSub, DNABSub, chBSub, ratio, ratioNorm, oligoNum = \
        chipSingleconcUtils.outputInfoFromConcatFile_v3(concatFileName,
                                                        spot2OligoFileName,
                                                        pTh=pTh,
                                                        DNATh=DNATh,
                                                        chTh=chTh,
                                                        nanFlag=nanFlag)

    # make a dictionary linking oligo number and sequence
    oligoSeqD = chipSingleconcUtils.createDictFromSeqFile(
        oligoSeqFileName, truncFlag=truncFlag)

    # create another list containing all possible oligo sequences
    oligoSeq = []
    for n in range(0, len(oligoNum)):
        if oligoSeqD.has_key(oligoNum[n]):
            oligoSeq.append(oligoSeqD[oligoNum[n]])
        else:
            oligoSeq.append('EMPTY')

    # histogram DNABSub and PBSub waves and fit them to a Gaussian
    dataDir = os.path.split(concatFileName)[0]
    analysisDir = str(dataDir) + "/NormalizationInfo/"
    fileIOUtils.createNewDir(analysisDir)

    # normalize waves so that they are centered around zero, normalize ratio
    # to a max of 1
    DNAN = chipSingleconcUtils.normalizeValues_v2(
        DNABSub, analysisDir, "DNABSub.png", inHi=0, numBins=100)
    pN = chipSingleconcUtils.normalizeValues_v2(
        pBSub, analysisDir, "pBSub.png", inHi=0, numBins=100)
    rN = chipSingleconcUtils.normalizeValues_v2(
        ratio, analysisDir, "ratio.png", inHi=0, numBins=100)
    rNN = chipSingleconcUtils.normalizeMaxValue(rN)

    # check results of normalization to see if they're reasonable
    checkDir = analysisDir + "CheckFits/"
    fileIOUtils.createNewDir(checkDir)
    dParams = fitUtils.gaussianFit(DNAN, numBins=100,
                                   figFileName=checkDir + 'DNAN.png',
                                   loBound=0,
                                   hiBound=0)
    pParams = fitUtils.gaussianFit(pN, numBins=100, loBound=0, hiBound=0,
                                   figFileName=checkDir + 'pN.png')
    rParams = fitUtils.gaussianFit(
        rNN, numBins=100, loBound=0, hiBound=0,
        figFileName=checkDir + 'rNN.png')

    zScore, pVal = [], []
    for a in rNN:
        if not N.isnan(a):
            zS = float(a - rParams[1]) / rParams[2]
            zScore.append(zS)
            pVal.append(stats.norm.sf(zS))
        else:
            zScore.append(N.nan)
            pVal.append(N.nan)

    # output all of these results to a new file to see what happened
    outFileName = concatFileName[:-4] + '_Processed.txt'
    outFile = open(outFileName, 'w')
    outFile.write(
        'Block\tOrigRow\tOrigCol\tRow\tCol\tFlag\tpFg\tDNAFg\tpBg\tDNABg\t\
        chFg\tpBSub\tDNABSub\tchBSub\tRatio\tRatioNorm\tOligoNum\tOligoSeq\t\
        DNAN\trN\trNN\tZScore\tpVal\n')
    outLists = [blocks, oRows, oCols, rows, cols, flags, pFg, DNAFg, pBg,
                DNABg, chFg, pBSub, DNABSub, chBSub, ratio, ratioNorm,
                oligoNum, oligoSeq, DNAN, rN, rNN, zScore, pVal]
    for m in range(0, len(outLists[0])):
        for n in range(0, len(outLists)):
            outFile.write(str(outLists[n][m]) + '\t')
        outFile.write('\n')
    outFile.close()

    # determine the number of oligos and concentrations
    numOligos = chipSingleconcUtils.calcNumOligos(spot2OligoFileName)
    # determine the number of spots per oligo
    numSpotsPerOligo = chipSingleconcUtils.calcNumSpotsPerOligo(
        spot2OligoFileName)
    print "Number of oligos = " + str(numOligos)
    print "Number of spots per oligo = " + str(numSpotsPerOligo)

    # create a new directory to hold oligo analysis output
    dataDir = os.path.split(concatFileName)[0]
    analysisDir = str(dataDir) + "/OligoAnalysis/"
    fileIOUtils.createNewDir(analysisDir)
    thFileName = analysisDir + "Threshholds.txt"
    chipSingleconcUtils.writeThresholdsToFile(thFileName, pTh, DNATh, chTh)

    # create a directory to hold text files
    textDir = analysisDir + "TextFiles/"
    fileIOUtils.createNewDir(textDir)

    # create 2D arrays for DNAN and rNN data
    chBSubArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, chBSub)
    colArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, cols)
    rowArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, rows)
    DNANArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, DNAN)
    pBSubArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, pBSub)
    rNNArray = chipSingleconcUtils.dataArray(
        spot2OligoFileName, cols, rows, rNN)

    # slice arrays to create text files for each oligo
    for n in range(0, numOligos):
        # create text file
        outFileName = textDir + "Oligo_" + str(n + 1) + ".dat"
        outFile = open(outFileName, 'w')
        outFile.write('#Rep\tpBSub\tDNAN\trNN\tchBSub\tRow\tCol\n')
        DNANByOligo = DNANArray[n, :].tolist()
        pBSubByOligo = pBSubArray[n, :].tolist()
        rNNByOligo = rNNArray[n, :].tolist()
        chBSubByOligo = chBSubArray[n, :].tolist()
        rowByOligo = rowArray[n, :].tolist()
        colByOligo = colArray[n, :].tolist()
        repNum = (N.arange(numSpotsPerOligo + 1)).tolist()
        # write out the text
        for m in range(0, len(rNNByOligo)):
            writeList = [str(repNum[m] + 1), '\t', str(pBSubByOligo[m]), '\t',
                         str(DNANByOligo[m]), '\t', str(rNNByOligo[m]), '\t',
                         str(chBSubByOligo[m]), '\t', str(rowByOligo[m]), '\t',
                         str(colByOligo[m]), '\n']
            for item in writeList:
                outFile.write(item)
        outFile.close()

    # create a directory to hold graphs
    graphDir = analysisDir + "Graphs/"
    fileIOUtils.createNewDir(graphDir)

    # create 2D arrays to hold oligo information
    dimensions = (numOligos + 1, numSpotsPerOligo)
    oligoNumArray = N.zeros(dimensions, float)
    for n in range(0, numOligos):
        oligoNumArray[n, :] = (n + 1)

    # reshape arrays for plotting
    numPoints = DNANArray.shape[0] * DNANArray.shape[1]
    oligoNumPlotting = N.reshape(oligoNumArray, (numPoints,))
    DNANPlotting = N.reshape(DNANArray, (numPoints,))
    rNNPlotting = N.reshape(rNNArray, (numPoints,))

    figFileRoot = graphDir + "DNANVsOligo"
    plotUtils.createAndSaveFig(oligoNumPlotting, DNANPlotting, figFileRoot,
                               xLabel="Oligo", yLabel="Intensity", yMin=0,
                               xMin=0, xMax=numOligos)
    figFileRoot = graphDir + "rNNVsOligo"
    plotUtils.createAndSaveFig(oligoNumPlotting, rNNPlotting, figFileRoot,
                               xLabel="Oligo", yLabel="Ratio", yMin=0, xMin=0,
                               xMax=numOligos)

    # now go through and make histograms of all DNABSub, Ratio, and RatioNorm
    # values
    figFileRoot = graphDir + '/DNANHist'
    plotUtils.makeHist(DNAN, figFileRoot, numBins=1000, xLabel='DNAN',
                       yLabel='Number of Events', log=False, removeNaNFlag=1)
    figFileRoot = graphDir + '/DNANHistLog'
    plotUtils.makeHist(DNAN, figFileRoot, numBins=1000, xLabel='DNAN',
                       yLabel='Number of Events', log=True, removeNaNFlag=1)
    figFileRoot = graphDir + '/rNNHist'
    plotUtils.makeHist(rNN, figFileRoot, numBins=1000, xLabel='rNN',
                       yLabel='Number of Events', log=False, removeNaNFlag=1)
    figFileRoot = graphDir + '/rNNHistLog'
    plotUtils.makeHist(rNN, figFileRoot, numBins=1000, xLabel='rNN',
                       yLabel='Number of Events', log=True, removeNaNFlag=1)
    return 0


##############################################
if __name__ == "__main__":
    sys.exit(main())
