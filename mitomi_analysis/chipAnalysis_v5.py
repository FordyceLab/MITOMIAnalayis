import sys
import os
from getopt import getopt
import chipSingleconcUtils
from plotting import plotUtils
from statistics import stats_utils
import numpy as N
from lab import tabbedfile
from lab.tabbedfile import tabbifyMatrix
from fileIOScripts import fileIOUtils


HELP_STRING = """
chipAnalysis.py

Authored by: Polly Fordyce, January 2008
Updated by: Tyler Shimko, February 2016

This program is designed to take a single concatenated genepix
file and output (1) graphs showing the different intensities
as a function of column position, (2) protein intensity data
files for each row, and (3) a graph showing all protein
intensities by row.  Optional threshhold values can be given
to set a lower bound on permissible background subtracted
intensities.

     -h     print this help message
     -c     concat filename (required)
     -s     spot2Oligo filename (optional, default is
            ../../MITOMI/MITOMI_Motif/8MerLibrary/Spot2OligoFile080108)
     -p     pBSub threshold value (optional)
     -d     DNABSub threshold value (optional)
     -t     chBSub threshold value (optional)
     -j     minimum y axis value for DNA Fg and Bg graphs
     -k     minimum y axis value for protein Fg and Bg graphs

Example:
python chipAnalysis.py -c concatFile_042108.txt -p 50 -d 1 -t 100 -j 600 -k 1400
"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    concatFileName = ""
    spot2OligoFileName = "../../MITOMI/MITOMI_Motif/\
                          8MerLibrary/Spot2OligoFile_080108"
    pTh = 1
    DNATh = 1
    chTh = 1000
    DNAYMin = -1
    pYMin = -1

    try:
        optlist, args = getopt(argv[1:], "hc:p:d:t:j:k:s:")
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
            DNATh = float(opt_arg)
        elif opt == '-t':
            chTh = int(opt_arg)
        elif opt == '-j':
            DNAYMin = int(opt_arg)
        elif opt == '-k':
            pYMin = int(opt_arg)

    if concatFileName == "":
        print HELP_STRING
        sys.exit(1)

    # get lists from concat file
    blockL, oRL, oCL, rows, cols, diaL, flagL, pFL, dFL, pBL, dBL,
    cFL = chipSingleconcUtils.concatFileToLists_v3(concatFileName)

    # determine spots per column and number of columns
    numCols,
    spotsPerCol = chipSingleconcUtils.determineDimensions_v3(concatFileName)

    print numCols, spotsPerCol
    dimensions = (spotsPerCol, numCols)

    # create N.arrays to hold all of the data
    DNAFgArray = N.zeros(dimensions)
    DNABgArray = N.zeros(dimensions)
    DNABSubArray = N.zeros(dimensions)
    pFgArray = N.zeros(dimensions)
    pBgArray = N.zeros(dimensions)
    pBSubArray = N.zeros(dimensions)
    chBSubArray = N.zeros(dimensions)
    flagArray = N.zeros(dimensions)
    oligoArray = N.zeros(dimensions)
    ratioArray = N.zeros(dimensions, float)

    # create dictionaries linking spot index to oligo name and dilution
    oligoD = chipSingleconcUtils.makeSpot2OligoDict(spot2OligoFileName)

    # deal with flagged spots
    flags, pFg, DNAFg, pBg, DNABg,
    chFg = chipSingleconcUtils.zeroFlaggedSpots(flagL, pFL, dFL, pBL, dBL, cFL)

    # create pBSub, DNABSub, and chBSub lists
    pBSub, DNABSub,
    chBSub = chipSingleconcUtils.backgroundSubtract_v2(pFL,
                                                       pBL,
                                                       dFL,
                                                       dBL,
                                                       cFL,
                                                       dBL,
                                                       pTh=pTh,
                                                       dTh=DNATh,
                                                       cTh=chTh)

    # create ratio and ratioNorm lists
    ratio, ratioNorm, ratioNormNorm,
    chBSubMean = chipSingleconcUtils.calculateRatios(pBSub, DNABSub, chBSub)

    # fill arrays with data
    for n in range(0, len(rows)):
        DNAFgArray[rows[n] - 1][cols[n] - 1] = DNAFg[n]
        DNABgArray[rows[n] - 1][cols[n] - 1] = DNABg[n]
        DNABSubArray[rows[n] - 1][cols[n] - 1] = DNABSub[n]
        pFgArray[rows[n] - 1][cols[n] - 1] = pFg[n]
        pBgArray[rows[n] - 1][cols[n] - 1] = pBg[n]
        pBSubArray[rows[n] - 1][cols[n] - 1] = pBSub[n]
        chBSubArray[rows[n] - 1][cols[n] - 1] = chBSub[n]
        if flags[n] != 0:
            flagArray[rows[n] - 1][cols[n] - 1] = 1
        spotIndex = str(cols[n]) + "." + str(rows[n])
        oligo = oligoD[spotIndex]
        oligoArray[rows[n] - 1][cols[n] - 1] = int(oligo.split("_")[1])
        ratioArray[rows[n] - 1][cols[n] - 1] = ratio[n]

    # create a new directory to hold the chip analysis graphs
    dataDir = os.path.split(concatFileName)[0]
    analysisDir = str(dataDir) + "/ChipAnalysis/"
    fileIOUtils.createNewDir(analysisDir)
    threshFileName = analysisDir + "Thresholds.txt"
    chipSingleconcUtils.writeThresholdsToFile(threshFileName, pTh, DNATh, chTh)

    # display the data
    listOfArrays = [DNAFgArray, DNABgArray, DNABSubArray, pFgArray,
                    pBgArray, pBSubArray, chBSubArray, flagArray,
                    oligoArray, ratioArray]
    listOfFilenames = ["DNAFgArray", "DNABgArray", "DNABSubArray", "pFgArray",
                       "pBgArray", "pBSubArray", "chBSubArray", "flagArray",
                       "oligoArray", "ratioArray"]
    listOfColormaps = [1, 1, 1, 2, 2, 2, 1, 1, 1, 1]
    for n in range(0, len(listOfArrays)):
        figFileRoot = analysisDir + listOfFilenames[n]
        plotUtils.createAndSaveHeatMap(listOfArrays[n], figFileRoot,
                                       xLabel="Columns", yLabel="Spots",
                                       xMax=0, xMin=numCols, yMax=0,
                                       yMin=spotsPerCol,
                                       colorMap=listOfColormaps[n],
                                       vMin=0, majorFontSize=16)

    # ok, now write out the arrays to text files to use for creating heat maps
    # in igor.
    for n in range(0, len(listOfArrays)):
        outFileName = analysisDir + listOfFilenames[n] + '.txt'
        outFile = open(outFileName, 'w')
        for m in range(0, dimensions[0]):
            for l in range(0, dimensions[1]):
                outFile.write(str(listOfArrays[n][m][l]) + '\t')
            outFile.write('\n')
        outFile.close()

    graphDataList = [rows, pFg, DNAFg, pBg, DNABg,
                     chFg, pBSub, DNABSub, chBSub, ratio, ratioNorm]
    graphNameList = ["rows", "pFg", "DNAFg", "pBg", "DNABg",
                     "chFg", "pBSub", "DNABSub", "chBSub", "ratio",
                     "ratioNorm"]
    xLabel = "Column Position"
    yMinList = [-1, pYMin, DNAYMin, pYMin, DNAYMin, -1, -1, -1, 0, -1, -1]

    for n in range(1, len(graphDataList)):
        if (n <= 8):
            yLabel = "Intensity"
        else:
            if n == 9:
                yLabel = "Ratio"
            if n == 10:
                yLabel = "Normalized Ratio"
        figFileName = analysisDir + graphNameList[n]
        plotUtils.createAndSaveFig(graphDataList[0], graphDataList[n],
                                   xLabel=xLabel, yLabel=yLabel,
                                   figFileRoot=figFileName, yMin=yMinList[n])

    return 0


##############################################
if __name__ == "__main__":
    sys.exit(main())
