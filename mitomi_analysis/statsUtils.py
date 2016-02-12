
import os
import sys
import numpy as N
import operator as O
from scipy import stats


def correlation_coef(list1, list2):
    """This program calculates the Spearman's correlation coefficient
    between two lists."""

    if len(list1) != len(list2):
        print("Lists are different lengths!  User is a bozo!")

    array1 = array(list1)
    array2 = array(list2)
    diffArray = array1 - array2
    diffSqArray = diffArray*diffArray

    lenArray = len(list1)
    diffSqSum = sum(diffSqArray)

    numerator = 6*diffSqSum
    denominator = lenArray*(lenArray*lenArray - 1)
    if denominator != 0:
        rho = 1 - float(numerator)/float(denominator)
    else:
        rho = 'NAN'

    # now calculate the student's t
    if rho != 'NAN':
        denomA = lenArray - 2
        numA = 1 - rho*rho
        if denomA != 0:
            denomB = sqrt(float(numA)/float(denomA))
            tValue = float(rho)/denomB
        else:
            tValue = 'NAN', 'NAN'
    else:
        tValue = 'NAN'

    return lenArray, diffSqSum, numerator, denominator, rho, tValue


def standardError(inList):

    tempStd = std(inList)
    tempSem = float(tempStd)/((len(inList))**0.5)

    return tempSem


def pearsonsCorrelation(startList1, startList2):

    list1, list2 = [], []

    for n in range(0, len(startList1)):
        if str(startList1[n]) != 'nan' and str(startList2[n]) != 'nan':
            list1.append(startList1[n])
            list2.append(startList2[n])

    productList = []
    squaredList1 = []
    squaredList2 = []

    for n in range(0, len(list1)):
        productList.append(list1[n]*list2[n])
        squaredList1.append(list1[n]*list1[n])
        squaredList2.append(list2[n]*list2[n])

    numPoints = len(list1)
    sumList1 = sum(list1)
    sumList2 = sum(list2)
    sumList1Squared = sumList1*sumList1
    sumList2Squared = sumList2*sumList2
    sumProductList = sum(productList)
    sumSquaredList1 = sum(squaredList1)
    sumSquaredList2 = sum(squaredList2)

    numerator = numPoints*sumProductList - sumList1*sumList2
    denomPart1 = (numPoints*sumSquaredList1-sumList1Squared)**0.5
    denomPart2 = (numPoints*sumSquaredList2-sumList2Squared)**0.5

    correlationCoeff = float(numerator)/(denomPart1*denomPart2)

    return correlationCoeff


def pearsonsCorrelation_v2(startList1, startList2):

    list1, list2 = [], []

    for n in range(0, len(startList1)):
        if str(startList1[n]) != 'nan' and str(startList2[n]) != 'nan':
            list1.append(startList1[n])
            list2.append(startList2[n])

    array1, array2 = N.array(list1), N.array(list2)

    rVal, rProb = stats.pearsonr(array1, array2)
    rSquared = rVal**2

    return rVal, rSquared, rProb


def calcMed(inputList):

    if len(inputList) == 0:
        median = N.NAN
    elif len(inputList) == 1:
        median = inputList[0]
    else:
        if len(inputList) % 2 == 1:
            median = sorted(inputList)[int(len(inputList)/2)]
        else:
            valOne = sorted(inputList)[int(len(inputList)/2)]
            valTwo = sorted(inputList)[int(len(inputList)/2-1)]
            median = (valOne+valTwo)/2

    return median


def criticalValDict():

    onePercentD = {1: 318.313, 2: 22.327, 3: 10.215, 4: 7.173, 5: 5.893,
                   6: 5.208, 7: 4.782, 8: 4.499, 9: 4.296, 10: 4.143,
                   11: 4.024, 12: 3.929, 13: 3.852, 14: 3.787}
    fivePercentD = {1: 63.657, 2: 9.925, 3: 5.841, 4: 4.604, 5: 4.032,
                    6: 3.707, 7: 3.499, 8: 3.355, 9: 3.250, 10: 3.169,
                    11: 3.106, 12: 3.055, 13: 3.012, 14: 2.977}

    return onePercentD, fivePercentD


def calcZScore(value, avg, sdev):

    G = float(abs(value-avg))/float(sdev)

    return G


def checkForOutlier(value, avg, sdev, numPoints, percent):

    oneD, fiveD = criticalValDict()
    G = calcZScore(value, avg, sdev)

    if percent == 1:
        if G > oneD[numPoints-2]:
            outcome = 1
        else:
            outcome = 0
    elif percent == 5:
        if G > fiveD[numPoints-2]:
            outcome = 1
        else:
            outcome = 0
    else:
        print("You have chosen to use an invalid statistical cutoff for your\
            t-test!")

    return outcome


def removeOutliers(inList):

    for n in range(0, len(inList)):
        avg = waveStatsWithNAN(inList)[0]
        sdev = waveStatsWithNAN(inList)[1]
        if sdev != 0:
            numPoints = 0
            for n in range(0, len(inList)):
                if N.isnan(inList[n]):
                    pass
                else:
                    numPoints = numPoints + 1
            if not N.isnan(inList[n]):
                qualityScore = checkForOutlier(
                    inList[n], avg, sdev, numPoints, 5)
                if qualityScore == 1:
                    print("old then new")
                    print(inList)
                    inList[n] = N.nan
                    print(inList)
                else:
                    pass

    return inList


def waveStatsWithNAN(inList):

    tempList = []
    for item in inList:
        if N.isnan(item):
            pass
        else:
            tempList.append(item)

    avg = N.mean(tempList)
    sdev = N.std(tempList)

    return avg, sdev


def calcMeanNoNaN(inList):

    tempList = []
    for item in inList:
        if N.isnan(item):
            pass
        else:
            tempList.append(item)

    avg = N.mean(tempList)

    return avg


def calcMedNoNaN(inList):

    newList = []
    for item in inList:
        if not N.isnan(item):
            newList.append(item)

    outMed = calcMed(newList)

    return outMed


def calcMeanNoNaNNoInf(inList):

    tempList = []
    for item in inList:
        if N.isnan(item) or N.isinf(item):
            pass
        else:
            tempList.append(item)

    avg = N.mean(tempList)

    return avg


def calcMedNoNaNNoInf(inList):

    newList = []
    for item in inList:
        if not N.isnan(item) and not N.isinf(item):
            newList.append(item)

    outMed = calcMed(newList)

    return outMed


def calcMinNoNaN(inList):

    newList = []
    for item in inList:
        if not N.isnan(item):
            newList.append(item)

    outMin = min(newList)

    return outMin


def calcMaxNoNaN(inList):

    newList = []
    for item in inList:
        if not N.isnan(item):
            newList.append(item)

    outMax = max(newList)

    return outMax


def calcRankSumU(R, n):

    U = R-0.5*n*(n+1)

    return U


def calcRankSumMeanAndVar(n1, n2):

    gaussMean = 0.5*(n1*n2)
    gaussVar = N.sqrt(float(n1*n2*(n1+n2+1))/12)

    return gaussMean, gaussVar


def calcRankSumSigma(U, gaussMean, gaussVar):

    gaussSigma = float(U-gaussMean)/gaussVar

    return gaussSigma


def calcGaussProb(x, gaussMean, gaussSigma):

    ampCoef = float(1.0)/(gaussSigma*2*N.pi)
    expValue = N.exp(-float((x-gaussMean)**2)/(2*gaussSigma**2))
    probOut = ampCoef*expValue

    return probOut


def calcMeanNoZeros(inList):

    newList = []
    for item in inList:
        if item != 0:
            if not N.isnan(item):
                newList.append(item)

    outMean = N.mean(newList)

    return outMean


def calcStdNoZeros(inList):

    newList = []
    for item in inList:
        if item != 0:
            if not N.isnan(item):
                newList.append(item)

    outStd = N.std(newList)

    return outStd


def calcSemNoZeros(inList):

    newList = []
    for item in inList:
        if item != 0:
            if not N.isnan(item):
                newList.append(item)

    outStd = N.std(newList)
    outSem = float(outStd)/(N.sqrt(len(inList)-1))

    return outSem


def calcMedNoZeros(inList):

    newList = []
    for item in inList:
        if item != 0:
            if not N.isnan(item):
                newList.append(item)

    outMed = calcMed(newList)

    return outMed


def calcStatsNoZeros(inList):

    newList = []
    for item in inList:
        if item != 0:
            if not N.isnan(item):
                newList.append(item)

    outMed = calcMed(newList)
    outMean = N.mean(newList)
    outStd = N.std(newList)
    outSem = float(outStd)/(N.sqrt(len(inList)-1))

    return outMed, outMean, outStd, outSem


def getRanks(totalDict, partDict):
    # first get the top half of partial dictionary
    topHalf = selectTopHalfOfDict(partDict)

    # now sort the main dictionary
    sortedTotal = sorted(totalDict, reverse=True, key=O.itemgetter)

    # now get the ranks of the top half of the dictionary
    rankD = {}
    for n in range(0, len(topHalf)):
        rankD[sortedTotal.index(topHalf[n])] = 1

    return rankD


def selectTopHalfOfDict(inDict, reverse=False):

    sortedDict = sorted(inDict, reverse=reverse, key=O.itemgetter)
    midLen = int(N.ceil(float(len(sortedDict)/2)))
    outDict = sortedDict[0:midLen]

    return outDict

# i'm not sure yet which of these ways is correct!


def calcEScore(totalDict, fgDict, bgDict):

    fgRanks = getRanks(totalDict, fgDict)
    bgRanks = getRanks(totalDict, fgDict)

    normFactor = float(1/(len(fgRanks)+len(bgRanks)))
    bgFraction = float(N.average(list(bgRanks.keys())))/len(bgRanks)
    fgFraction = float(N.average(list(fgRanks.keys())))/len(fgRanks)

    eScore = normFactor*(bgFraction-fgFraction)

    return eScore


def calcGaussProb(value, mu, sigma):

    fracA = float(1)/(sigma*N.sqrt(2*pi))
    exponent = -0.5*(float(value-mu)/sigma) ^ 2
    outProb = fracA*exp(exponent)

    return outProb


def calcGeneListOverlapProb(n, m, n1, n2):
    """
    This function usess a hypergeometric probability distribution to
    calculate the probability of obtaining a number of overlapping genes (m)
    between 2 lists of length n1 and n2 out of a total set of n genes.
    """

    numA = calcCFun(n1, m)
    numB = calcCFun((n-n1), (n2-m))
    denom = calcCFun(n, n2)

    return (numA*numB)/denom


def calcCFun(a, b):

    outNum = (fact(a))/(fact(b)*fact(a-b))

    return outNum


def fact(x):
    f = 1
    while (x > 0):
        f = f * x
        x = x - 1
    return f
