import numpy as N
import types
from plotting import plotUtils
from statistics import statsUtils
from fitting import fitUtils
import operator
from matplotlib import pylab as plt
from scipy import stats


def makeSpot2OligoDict(spot2OligoFileName):
    """This program takes a spot2Oligo file and creates a
    dictionary containing the oligo names for each spot."""

    spot2OligoFile = open(spot2OligoFileName, 'r')
    oligoD = {}

    lineIndex = 0
    for line in spot2OligoFile:
        lineIndex = lineIndex + 1
        # this next part just skips the header
        if lineIndex == 1:
            pass
        else:
            tempList = line.split('\t')
            col = tempList[0].strip()
            row = tempList[1].strip()
            oligo = tempList[2].strip()
            spotIndex = col+"."+row
            oligoD[spotIndex] = oligo

    spot2OligoFile.close()
    return oligoD


def concatGprFiles_v3(pFN, cFN, dFN, oFN, singleF=0, rlF=0, tbF=0):

    dF = open(dFN, 'r')
    cF = open(cFN, 'r')

    blockL, colL, rowL, diaL, flagL, pFL, pBL, dFL, dBL, cFL = \
        [], [], [], [], [], [], [], [], [], []

    # open up protein file and read in data
    lI = 0
    colsPerBlock = 0
    pF = open(pFN, 'r')
    for line in pF:
        lI = lI + 1
        if lI <= 32:
            pass
        else:
            tempL = line.strip().split('\t')
            blockL.append(int(tempL[0]))
            colL.append(int(tempL[1]))
            rowL.append(int(tempL[2]))
            diaL.append(int(tempL[7]))
            pFL.append(int(tempL[8]))
            pBL.append(int(tempL[13]))
            flagL.append(int(tempL[37]))
            if int(tempL[1]) > colsPerBlock:
                colsPerBlock = int(tempL[1])

    pF.close()

    # open up DNA file and read in data
    lI, rI = 0, -1
    dF = open(dFN, 'r')
    for line in dF:
        lI = lI + 1
        if lI <= 32:
            pass
        else:
            rI = rI + 1
            tempL = line.strip().split('\t')
            dFL.append(int(tempL[8]))
            dBL.append(int(tempL[13]))
            if int(tempL[37]) != 0:
                flagL[rI] = int(tempL[37])
    dF.close()

    # open up chamber DNA file and read in data
    lI, rI = 0, -1
    cF = open(cFN, 'r')
    for line in cF:
        lI = lI + 1
        if lI <= 32:
            pass
        else:
            rI = rI + 1
            tempL = line.strip().split('\t')
            cFL.append(int(tempL[8]))
            if int(tempL[37]) != 0:
                flagL[rI] = int(tempL[37])
    cF.close()

    # if files were not gridded as a single block, renumber to fix this
    tempColL = []
    for a in range(0, len(blockL)):
        if singleF != 0:
            tempColL.append((blockL[a]-1)*colsPerBlock+colL[a])
        else:
            tempColL.append(colL[a])

    # figure out the total number of columns and rows
    numCols, numRows = 0, 0
    for a in range(0, len(blockL)):
        if tempColL[a] > numCols:
            numCols = tempColL[a]
        if rowL[a] > numRows:
            numRows = rowL[a]

    # renumber columns in case file must be renumbered left to right
    outColL = []
    for a in range(0, len(blockL)):
        if rlF != 0:
            outColL.append(numCols+1-tempColL[a])
        else:
            outColL.append(tempColL[a])

    # renumber columns in case file must be renumbered top to bottom
    outRowL = []
    for a in range(0, len(blockL)):
        if tbF != 0:
            outRowL.append(numRows+1-rowL[a])
        else:
            outRowL.append(rowL[a])

    oF = open(oFN, 'w')
    str1 = "Block\tColumn\tRow\tOutColumn\tOutRow\tDia\tFlag\tP_FG\tDNA_FG\t\
        P_BG\tDNA_BG\tCH_FG\n"
    oF.write(str1)
    for a in range(0, len(blockL)):
        oL = [str(blockL[a]), str(colL[a]), str(rowL[a]), str(outColL[a]),
              str(outRowL[a]), str(diaL[a]), str(flagL[a]), str(pFL[a]),
              str(dFL[a]), str(pBL[a]), str(dBL[a]), str(cFL[a])]
        oF.write('\t'.join(oL))
        oF.write('\n')


def concatFileToLists_v3(concatFileName):
    """This program takes a concatenated Genepix results file
    and creates dictionaries of all of the data for further analysis."""

    blockL, oRL, oCL = [], [], []
    rowL, colL, diaL, flagL = [], [], [], []
    pFL, dFL, pBL, dBL, cFL = [], [], [], [], []

    inFile = open(concatFileName, 'r')
    lineIndex = 0

    for line in inFile:
        lineIndex = lineIndex + 1
        if lineIndex == 1:
            pass
        else:
            tempL = line.split('\t')
            blockL.append(int(tempL[0]))
            oCL.append(int(tempL[1]))
            oRL.append(int(tempL[2]))
            colL.append(int(tempL[3]))
            rowL.append(int(tempL[4]))
            diaL.append(float(tempL[5]))
            flagL.append(float(tempL[6]))
            pFL.append(float(tempL[7]))
            dFL.append(float(tempL[8]))
            pBL.append(float(tempL[9]))
            dBL.append(float(tempL[10]))
            cFL.append(float(tempL[11]))

    return blockL, oRL, oCL, rowL, colL, diaL, flagL, pFL, dFL, pBL, dBL, cFL


def zeroFlaggedSpots(flagList, pFgList, DNAFgList, pBgList, DNABgList,
                     chFgList):
    """This program checks to see if any spots have non-zero flags.
    If they do,  the program enters 'NaN' for their values."""

    newPFg, newDNAFg, newPBg, newDNABg, newChFg = [], [], [], [], []
    listOfLists = [pFgList, DNAFgList, pBgList, DNABgList, chFgList]
    listOfNewLists = [newPFg, newDNAFg, newPBg, newDNABg, newChFg]

    for m in range(0, len(flagList)):
        if int(flagList[m]) != 0:
            for n in range(0, len(listOfNewLists)):
                listOfNewLists[n].append(N.NaN)
        else:
            for n in range(0, len(listOfNewLists)):
                listOfNewLists[n].append(listOfLists[n][m])

    return flagList, newPFg, newDNAFg, newPBg, newDNABg, newChFg


def backgroundSubtract_v2(pFg, pBg, DNAFg, DNABg, chFg, chBg, pTh=0, dTh=0,
                          cTh=0, nanF=0):

    pBSub, dBSub, chBSub = [], [], []

    for a in range(0, len(pFg)):
        if (N.isnan(pFg[a]) or N.isnan(pBg[a]) or N.isnan(DNAFg[a]) or
                N.isnan(DNABg[a]) or N.isnan(chFg[a]) or N.isnan(chBg[a])):
            pBSub.append(N.nan)
            dBSub.append(N.nan)
            chBSub.append(N.nan)
        else:
            tempP = pFg[a]-pBg[a]
            tempD = DNAFg[a]-DNABg[a]
            tempC = chFg[a]-chBg[a]
            if nanF == 0:
                pBSub.append(tempP)
                dBSub.append(tempD)
                chBSub.append(tempC)
            else:
                if tempP < pTh or tempD < dTh or tempC < cTh:
                    pBSub.append(N.nan)
                    dBSub.append(N.nan)
                    chBSub.append(N.nan)
                else:
                    pBSub.append(tempP)
                    dBSub.append(tempD)
                    chBSub.append(tempC)

    return pBSub, dBSub, chBSub


def writeThresholdsToFile(fileName, pTh, DNATh, chTh):
    """This program just records what thresholds were used in the analysis and
    writes them to file."""

    thFile = open(fileName, 'w')
    thFile.write("Protein threshold = "+str(pTh)+"\n")
    thFile.write("DNA threshold = "+str(DNATh)+"\n")
    thFile.write("Chamber threshold = "+str(chTh)+"\n")
    thFile.close()


def calculateRatios(pBSubList, DNABSubList, chBSubList):
    """This program calculates (1) fluorescence intensity ratios
    and (2) normalized fluorescence intensity ratios."""

    ratioList, ratioNormList, ratioNormNormList = [], [], []

    newChBSubList = []

    for a in chBSubList:
        if not N.isnan(float(a)):
            newChBSubList.append(a)
    chBSubMean = N.mean(newChBSubList)

    for n in range(0, len(pBSubList)):
        if not N.isnan(pBSubList[n]) and pBSubList[n] != 0:
            tempRatio = float(DNABSubList[n]) / float(pBSubList[n])
            if chBSubList[n] > 0:
                tempRatioNorm = (float(tempRatio) / float(chBSubList[n]))
                tempRatioNormNorm = float(tempRatioNorm) * float(chBSubMean)
            else:
                tempRatioNorm = N.NaN
                tempRatioNormNorm = N.NaN
        else:
            tempRatio = N.NaN
            tempRatioNorm = N.NaN
            tempRatioNormNorm = N.NaN
        ratioList.append(tempRatio)
        ratioNormList.append(tempRatioNorm)
        ratioNormNormList.append(tempRatioNormNorm)

    return ratioList, ratioNormList, ratioNormNormList, chBSubMean


def normalizeValues_v2(inList, analysisDir, outFileName, inHi=0, numBins=100):
    """This program normalizes values so that they are centered
    around zero using python least squares minimization."""

    outFileName = analysisDir+outFileName
    cleanL = []
    for a in inList:
        if not N.isnan(a):
            cleanL.append(a)

    inHi = 3*N.std(cleanL)
    inLo = -inHi

    fitParams = fitUtils.gaussianFit(cleanL, numBins=numBins,
                                     figFileName=outFileName, loBound=inLo,
                                     hiBound=inHi)
    rFitMean, rFitStd = fitParams[1], fitParams[2]

    normL = []
    for a in inList:
        if not N.isnan(a):
            normL.append(a-rFitMean)
        else:
            normL.append(N.nan)

    return normL


def normalizeMaxValue(inList):
    """This program values so that the maximum is 1."""

    normList = []
    maxVal = 0
    for n in inList:
        if not N.isnan(n) and n > maxVal:
            maxVal = n
    for n in range(0, len(inList)):
        normList.append(float(inList[n])/maxVal)
    return normList


def calcNumOligos(spot2OligoFileName):
    """This program determines the number of oligos in an experiment
    using the spot2oligo file."""

    oligoD = makeSpot2OligoDict(spot2OligoFileName)

    # determine the number of oligos
    numOligoD = {}
    for item in oligoD:
        if numOligoD.has_key(oligoD[item]):
            pass
        else:
            if oligoD[item] == 'EMPTY':
                pass
            else:
                numOligoD[oligoD[item]] = 1
    numOligos = len(numOligoD) - 1

    return numOligos


def calcNumSpotsPerOligo(spot2OligoFileName):
    """This program determines the number of replicates in an experiment
    using the spot2oligo file."""

    oligoD = makeSpot2OligoDict(spot2OligoFileName)
    numSpots = 0

    for item in oligoD:
        if oligoD[item] == 'Oligo_1':
            numSpots = numSpots + 1

    return numSpots


def dataArray(spot2OligoFileName, colList, rowList, itemList):
    """This program creates an array of the data in itemList
    with each row representing data from a single oligo."""

    oligoD = makeSpot2OligoDict(spot2OligoFileName)
    numOligos = calcNumOligos(spot2OligoFileName)+1
    numSpotsPerOligo = calcNumSpotsPerOligo(spot2OligoFileName)

    dimensions = (numOligos, numSpotsPerOligo)
    outArray = N.zeros(dimensions, float)

    # Correct data array so that values start as NaN
    for n in range(0, numOligos):
        for m in range(0, numSpotsPerOligo):
            outArray[n][m] = N.NaN

    repIndexD = {}
    for n in range(0, len(itemList)):
        spotIndex = str(colList[n])+"."+str(rowList[n])
        oligo = oligoD[spotIndex]
        if oligo == 'Empty' or oligo == 'EMPTY':
            pass
        else:
            oligoIndex = int(oligo.split("_")[1].split(".")[0])-1
            if repIndexD.has_key(oligo):
                arrayIndex = repIndexD[oligo]
                repIndexD[oligo] = (repIndexD[oligo] + 1)
            else:
                arrayIndex = 0
                repIndexD[oligo] = 1

        if arrayIndex < numSpotsPerOligo:
            outArray[oligoIndex][arrayIndex] = itemList[n]

    return outArray


def determineDimensions_v3(concatFileName):
    """This program reads in a concat file and automatically determines
    the number of spots in each column."""

    concatFile = open(concatFileName, 'r')
    spotsPerCol, numCols = 1, 1

    lineIndex = 0
    for line in concatFile:
        lineIndex = lineIndex + 1
        if lineIndex == 1:
            pass
        else:
            tempList = line.split('\t')
            currCol = int(tempList[3])
            currSpot = int(tempList[4])
            if currSpot > spotsPerCol:
                spotsPerCol = currSpot
            if currCol > numCols:
                numCols = currCol

    return numCols, spotsPerCol


def outputInfoFromConcatFile_v3(concatFileName, spot2OligoFileName, pTh=100,
                                DNATh=1, chTh=1, nanFlag=0):

    # get lists from concat file
    blocks, oRows, oCols, rows, cols, dia, flags, pFL, dFL, pBL, dBL, cFL = \
        concatFileToLists_v3(concatFileName)

    # deal with flagged spots
    flags, pFg, DNAFg, pBg, DNABg, chFg = zeroFlaggedSpots(flags, pFL, dFL,
                                                           pBL, dBL, cFL)

    # create pBSub, DNABSub, and chBSub lists
    pBSub, DNABSub, chBSub = backgroundSubtract_v2(pFg, pBg, DNAFg, DNABg,
                                                   chFg, DNABg, pTh=pTh,
                                                   dTh=DNATh, cTh=chTh,
                                                   nanF=nanFlag)

    # create ratio list
    ratio = calculateRatios(pBSub, DNABSub, chBSub)[0]

    # create normalized ratio list (just in case of printing problems)
    ratioNorm = []
    for n in range(0, len(ratio)):
        if chBSub[n] > 100:
            currRatioNorm = float(ratio[n])/float(chBSub[n])
        else:
            currRatioNorm = N.NaN
        ratioNorm.append(currRatioNorm)

    # create dictionaries linking spot index to oligo name and dilution
    oligoD = makeSpot2OligoDict(spot2OligoFileName)

    # create list of oligo numbers
    oligoNum = []
    for n in range(0, len(rows)):
        curRow = rows[n]
        curCol = cols[n]
        spotID = str(curCol)+'.'+str(curRow)
        if oligoD.has_key(spotID):
            oligo = oligoD[spotID]
        else:
            print spotID
            print "That key is not in the dictionary!"
            oligo = 'EMPTY'
        oligoNum.append(oligo.split("_")[1])

    return blocks, oRows, oCols, rows, cols, flags, pFg, DNAFg, pBg, DNABg,
    chFg, pBSub, DNABSub, chBSub, ratio, ratioNorm, oligoNum


def createDictFromSeqFile(seqFileName, truncFlag=0):
    """
    This subroutine creates a dictionary from oligo number and sequence data.
    """

    seqFile = open(seqFileName, 'r')
    seqDict = {'0': ''}
    for line in seqFile:
        tempList = line.split("\t")
        if truncFlag == 0:
            seqDict[tempList[0]] = tempList[1].strip()
        else:
            seqDict[tempList[0]] = tempList[1].strip()[3:-15]

    return seqDict
