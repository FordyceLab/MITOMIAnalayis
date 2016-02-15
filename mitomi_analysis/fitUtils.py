import os
import numpy as N
from matplotlib import pylab as plt
from scipy import optimize


def gaussian(p, x):
    return p[0]*N.exp(-((x-p[1])**2)/(2*p[2]**2))


def exponential(p, x):
    return p[0]*N.exp(-(x*p[1]))


def residualsG(p, y, x):
    err = y-gaussian(p, x)
    return err


def residualsE(p, y, x):
    err = y-exponential(p, x)
    return err


def gaussianFit(data, numBins, figFileName, loBound=0, hiBound=0):

    cleanL = []
    for a in data:
        if not N.isnan(a):
            cleanL.append(a)

    if hiBound == 0:
        hiB = 3*N.std(cleanL)
    else:
        hiB = hiBound

    if loBound == 0:
        loB = -hiB
    else:
        loB = loBound

    n, bins, patches = plt.hist(cleanL, bins=numBins, range=(loB, hiB))
    amp = max(n.tolist())
    mean = N.mean(cleanL)
    width = N.std(cleanL)
    p0 = [amp, mean, width]
    # get midpoint of bins to standardize length
    startL = bins.tolist()
    outL = []
    for b in range(0, len(startL)-1):
        outL.append(0.5*(startL[b]+startL[b+1]))
    xA = N.array(outL)

    # do least squares optimization
    plsq = optimize.leastsq(residualsG, p0, args=(n, xA))
    fitAmp, fitMean, fitStd = plsq[0][0], plsq[0][1], plsq[0][2]

    # plot to check
    check = gaussian(plsq[0], xA)
    plt.plot(xA, n, 'bo', hold="True", alpha=0.5)
    plt.plot(xA, check, 'r-')
    plt.savefig(figFileName)
    plt.clf()

    return fitAmp, fitMean, fitStd


def createFitFiles(inputData, outFileName, loBound=None, hiBound=None,
                   binSize=10):
    """This subroutine creates a data file containing information
    from creating a histogram of data for later use in fitting using
    gnuplot.  It also outputs max, mean, and std values to use as
    initial guesses in a gaussian fit."""

    newData = []
    for n in range(0, len(inputData)):
        if N.isnan(inputData[n]):
            pass
        else:
            newData.append(inputData[n])

    maxData, meanData, stdData = max(newData), N.mean(newData), N.std(newData)
    if loBound is None:
        loBound = meanData-2*stdData
    if hiBound is None:
        hiBound = maxData
    histogramBins = N.arange(loBound, hiBound, binSize).tolist()
    (events, bins, patches) = plt.hist(newData, histogramBins)
    maxEvents = max(events)

    outFile = open(outFileName, 'w')
    for n in range(0, len(events)):
        outFile.write(str(bins[n])+'\t')
        outFile.write(str(events[n])+'\n')
    outFile.close()

    return maxEvents, meanData, stdData


def gnuplotGaussianFitScript(fitFileName, dataName, xLabel, yLabel, ampGuess,
                             meanGuess, widthGuess):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a gaussian."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_'+dataName+'(x)'
    outFile.write(funcName+' = A*exp(-((x-x0)/sigma)**2)\n')
    outFile.write("A = "+str(ampGuess)+"; x0 = " +
                  str(meanGuess)+"; sigma = "+str(widthGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' via A, x0, sigma\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2 with histeps title '" +
                  dataName+"', "+funcName+" title 'Fit'")
    outFile.close()


def gaussianFitHistogram(inputData, outFileName, dataName,
                         xLabel="Number Of Events", yLabel="", loBound=None,
                         hiBound=None, binSize=None):

    ampGuess, meanGuess, widthGuess = createFitFiles(
        inputData, outFileName, loBound, hiBound, binSize)
    gnuplotGaussianFitScript(
        outFileName, dataName, xLabel, yLabel, ampGuess, meanGuess, widthGuess)
    # open the fit.log file and overwrite it!
    tempFile = open('fit.log', 'w')
    tempFile.write('\n')
    tempFile.close()

    f = os.popen('gnuplot', 'w')
    writeCommand = "load '"+outFileName[:-4]+".gnu'"
    print(writeCommand, file=f)
    f.flush()


def gaussianFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    A, x0, sigma = 0, 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            A = line.split()[2]
        if lineIndex == startIndex + 4:
            x0 = line.split()[2]
        if lineIndex == startIndex + 5:
            sigma = line.split()[2]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("A = "+str(A)+'\n')
    paramFile.write("x0 = "+str(x0)+'\n')
    paramFile.write("sigma = "+str(sigma)+'\n')
    paramFile.close()

    return A, x0, sigma


def gnuplotExpFitScript(fitFileName, dataName, xLabel, yLabel, ampGuess,
                        widthGuess):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a gaussian."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_'+dataName+'(x)'
    outFile.write(funcName+' = A*exp(-(x-x0))\n')
    outFile.write("A = "+str(ampGuess)+"; x0 = "+str(widthGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' via A, x0\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2 title '" +
                  dataName+"', "+funcName+" title 'Fit'")
    outFile.close()


def expFitHistogram(inputData, outFileName, dataName,
                    xLabel="Number Of Events", yLabel="", loBound=None,
                    hiBound=None, binSize=None):

    ampGuess, meanGuess, widthGuess = createFitFiles(
        inputData, outFileName, loBound, hiBound, binSize)
    gnuplotExpFitScript(
        outFileName, dataName, xLabel, yLabel, ampGuess, widthGuess)
    # open the fit.log file and overwrite it!
    tempFile = open('fit.log', 'w')
    tempFile.write('\n')
    tempFile.close()

    f = os.popen('gnuplot', 'w')
    writeCommand = "load '"+outFileName[:-4]+".gnu'"
    print(writeCommand, file=f)
    f.flush()


def expFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    A, x0 = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            A = line.split()[2]
        if lineIndex == startIndex + 4:
            x0 = line.split()[2]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("A = "+str(A)+'\n')
    paramFile.write("x0 = "+str(x0)+'\n')
    paramFile.close()

    return A, x0


def gnuplotSSBindingScript(fitFileName, dataName="", xLabel="", yLabel="",
                           aGuess=0, bGuess=0, logScale=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    if logScale == 10:
        outFile.write("set log xy\n")
    if logScale == 2:
        outFile.write("set logscale x 2\nset logscale y 2\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*x)/(b+x)\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2 title '" +
                  dataName+"', "+funcName+" title 'Fit'")
    outFile.close()


def gnuplotFit(fitFileName):
    """Thie subroutine just runs whatever gnuplot script you wrote."""

    tempFile = open('fit.log', 'w')
    tempFile.write('\n')
    tempFile.close()

    f = os.popen('gnuplot', 'w')
    writeCommand = "load '"+fitFileName[:-4]+".gnu'"
    print(writeCommand, file=f)
    f.flush()


def ssBindingFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.close()

    return a, aErr, b, bErr


def ssBindingFit(xData, yData, dataName="", xLabel="", yLabel="",
                 outFileName="", logScale=0):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\n')
    for n in range(0, len(xData)):
        outFile.write(str(xData[n])+'\t'+str(yData[n])+'\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingScript(outFileName, dataName=dataName, xLabel=xLabel,
                           yLabel=yLabel, aGuess=aGuess, bGuess=bGuess,
                           logScale=logScale)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError = ssBindingFitParams(outFileName)

    return aParam, aError, bParam, bError


def gnuplotLinearFitScript(fitFileName, dataName="", xLabel="", yLabel="",
                           aGuess=0, bGuess=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a line."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = a+b*x\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2 title '" +
                  dataName+"', "+funcName+" title 'Fit'")
    outFile.close()


def linearFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.close()

    return a, aErr, b, bErr


def linearFit(xData, yData, dataName="", xLabel="", yLabel="", outFileName=""):

    outFile = open(outFileName, 'w')
    outFile.write('#xData\tyData\n')
    for n in range(0, len(xData)):
        outFile.write(str(xData[n])+'\t'+str(yData[n])+'\n')
    outFile.close()
    aGuess = min(yData)
    bGuess = float(max(yData))/max(xData)

    gnuplotLinearFitScript(outFileName, dataName=dataName,
                           xLabel=xLabel, yLabel=yLabel, aGuess=aGuess,
                           bGuess=bGuess)

    gnuplotFit(outFileName)
    aParam, aError, bParam, bError = linearFitParams(outFileName)

    return aParam, aError, bParam, bError


def gnuplotLinearFitWErrorsScript(fitFileName, dataName="", xLabel="",
                                  yLabel="", aGuess=0, bGuess=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a line."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = a+b*x\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' using 1:2:3 via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3 title '" +
                  dataName+"' with yerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def linearFitWErrorsParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("degrees of freedom = "+str(degF)+'\n')
    paramFile.write("reduced chisq = "+str(rChiSq)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, degF, rChiSq


def linearFitWErrors(xData, yData, yError, dataName="", xLabel="", yLabel="",
                     outFileName=""):

    outFile = open(outFileName, 'w')
    outFile.write('#xData\tyData\tyErr\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n])+'\t'+str(yData[n])+'\t'+str(yError[n])+'\n')
    outFile.close()
    aGuess = min(yData)
    bGuess = float(max(yData))/max(xData)

    gnuplotLinearFitWErrorsScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, degF, rChiSq = linearFitWErrorsParams(
        outFileName)

    return aParam, aError, bParam, bError, degF, rChiSq


def gnuplotLinearFitWXYErrorsScript(fitFileName, dataName="", xLabel="",
                                    yLabel="", aGuess=0, bGuess=0, logFlag=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a line."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    if logFlag == 1:
        outFile.write("set log xy\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = a+b*x\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' using 1:2:4 via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3:4 title '" +
                  dataName+"' with xyerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def linearFitWXYErrorsParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("degrees of freedom = "+str(degF)+'\n')
    paramFile.write("reduced chisq = "+str(rChiSq)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, degF, rChiSq


def linearFitWXYErrors(xData, yData, xError, yError, dataName="", xLabel="",
                       yLabel="", outFileName="", logFlag=0):

    outFile = open(outFileName, 'w')
    outFile.write('#xData\tyData\txErr\tyErr\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n]) + '\t' + str(yData[n]) + '\t' + str(xError[n]) +
            '\t' + str(yError[n]) + '\n')
    outFile.close()
    aGuess = min(yData)
    bGuess = float(max(yData))/max(xData)

    gnuplotLinearFitWXYErrorsScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess, logFlag=logFlag)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, degF, rChiSq = linearFitWXYErrorsParams(
        outFileName)

    return aParam, aError, bParam, bError, degF, rChiSq


def gnuplotAffinityFitScript(fitFileName, dataName="", xLabel="", yLabel="",
                             aGuess=0, bGuess=0):
    """
    This subroutine creates a gnuplot script file to fit ratio data to two
    motif contributions.
    """

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x,y)'
    outFile.write(funcName+' = a*x+b*y\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write(
        "fit "+funcName+"'"+fitFileName+"' using 1:2:3:(1) via a, b\n")
    outFile.write('set key below\n')
    outFile.close()


def affinityFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.close()

    return a, aErr, b, bErr


def affinityFit(xData1, xData2, yData, dataName="", xLabel="", yLabel="",
                outFileName=""):

    outFile = open(outFileName, 'w')
    outFile.write('#xData1\txData2\tyData\tWeight\n')
    for n in range(0, len(xData1)):
        outFile.write(
            str(xData1[n])+'\t'+str(xData2[n])+'\t'+str(yData[n])+'\t1\n')
    outFile.close()
    aGuess = 0.8
    bGuess = 0.4

    gnuplotAffinityFitScript(outFileName, dataName=dataName,
                             xLabel=xLabel, yLabel=yLabel, aGuess=aGuess,
                             bGuess=bGuess)

    gnuplotFit(outFileName)
    aParam, aError, bParam, bError = affinityFitParams(outFileName)

    return aParam, aError, bParam, bError


def ssBindingWOffsetFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr, x0, x0Err = 0, 0, 0, 0, 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if lineIndex == startIndex + 5:
            x0 = line.split()[2]
            x0Err = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("x0 = "+str(x0)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, x0, x0Err


def ssBindingFitWOffset(xData, yData, dataName="", xLabel="", yLabel="",
                        outFileName="", logScale=0):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\n')
    for n in range(0, len(xData)):
        outFile.write(str(xData[n])+'\t'+str(yData[n])+'\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingWOffsetScript(outFileName, dataName=dataName,
                                  xLabel=xLabel, yLabel=yLabel, aGuess=aGuess,
                                  bGuess=bGuess, x0Guess=0.001,
                                  logScale=logScale)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, x0Param, x0Error = \
        ssBindingWOffsetFitParams(outFileName)

    return aParam, aError, bParam, bError, x0Param, x0Error


def gnuplotSSBindingWOffsetScript(fitFileName, dataName="", xLabel="",
                                  yLabel="", aGuess=0, bGuess=0, x0Guess=-1000,
                                  logScale=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    if logScale == 10:
        outFile.write("set log xy\n")
    if logScale == 2:
        outFile.write("set logscale x 2\nset logscale y 2\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*(x-x0))/(b+x-x0)\n')
    outFile.write(
        "a = "+str(aGuess)+"; b = "+str(bGuess)+"; x0 = "+str(x0Guess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' via a, b, x0\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2 title '" +
                  dataName+"', "+funcName+" title 'Fit'")
    outFile.close()


def gnuplotSSBindingWYErrorsScript(fitFileName, dataName="", xLabel="",
                                   yLabel="", aGuess=0, bGuess=0, logScale=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    if logScale == 10:
        outFile.write("set log xy\n")
    if logScale == 2:
        outFile.write("set logscale x 2\nset logscale y 2\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*x)/(b+x)\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' using 1:2:3 via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3 title '" +
                  dataName+"' with yerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def ssBindingWYErrorsFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("degrees of freedom = "+str(degF)+'\n')
    paramFile.write("reduced chisq = "+str(rChiSq)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, degF, rChiSq


def ssBindingWYErrorsFit(xData, yData, yError, dataName="", xLabel="",
                         yLabel="", outFileName="", logScale=0):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\tratioError\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n])+'\t'+str(yData[n])+'\t'+str(yError[n])+'\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingWYErrorsScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess, logScale=logScale)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, degF, rChiSq = ssBindingWYErrorsFitParams(
        outFileName)

    return aParam, aError, bParam, bError, degF, rChiSq


def gnuplotSSBindingWErrorsScript(fitFileName, dataName="", xLabel="",
                                  yLabel="", aGuess=0, bGuess=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*x)/(b+x)\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' using 1:2:4 via a, b\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3:4 title '" +
                  dataName+"' with xyerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def ssBindingWErrorsFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("degrees of freedom = "+str(degF)+'\n')
    paramFile.write("reduced chisq = "+str(rChiSq)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, degF, rChiSq


def ssBindingWErrorsFit(xData, yData, xError, yError, dataName="", xLabel="",
                        yLabel="", outFileName=""):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\tchBSubError\tratioError\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n]) + '\t' + str(yData[n]) + '\t' + str(xError[n]) +
            '\t' + str(yError[n]) + '\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingWErrorsScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, degF, rChiSq = ssBindingWErrorsFitParams(
        outFileName)

    return aParam, aError, bParam, bError, degF, rChiSq


def gnuplotSSBindingWErrorsAndOffsetScript(fitFileName, dataName="", xLabel="",
                                           yLabel="", aGuess=0, bGuess=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*(x-x0))/(b+(x-x0))\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"; x0 = 1\n")
    outFile.write(
        "fit "+funcName+"'"+fitFileName+"' using 1:2:4 via a, b, x0\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3:4 title '" +
                  dataName+"' with xyerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def ssBindingWErrorsAndOffsetFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if lineIndex == startIndex + 5:
            x0 = line.split()[2]
            x0Err = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("x0 = "+str(x0)+'\n')
    paramFile.write("degrees of freedom = "+degF+'\n')
    paramFile.write("reduced chisq = "+rChiSq+'\n')
    paramFile.close()

    return a, aErr, b, bErr, x0, x0Err, degF, rChiSq


def ssBindingWErrorsAndOffsetFit(xData, yData, xError, yError, dataName="",
                                 xLabel="", yLabel="", outFileName=""):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\tchBSubError\tratioError\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n]) + '\t' + str(yData[n]) + '\t' + str(xError[n]) +
            '\t' + str(yError[n]) + '\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingWErrorsAndOffsetScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, x0, x0Error, degF, rChiSq = \
        ssBindingWErrorsAndOffsetFitParams(outFileName)

    return aParam, aError, bParam, bError, x0, x0Error, degF, rChiSq


def gnuplotSSBindingWYErrorsAndOffsetScript(fitFileName, dataName="",
                                            xLabel="", yLabel="", aGuess=0,
                                            bGuess=0, logScale=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a single site binding model."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    if logScale == 10:
        outFile.write("set log xy\n")
    if logScale == 2:
        outFile.write("set logscale x 2\nset logscale y 2\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = (a*(x-x0))/(b+(x-x0))\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"; x0 = 0.001\n")
    outFile.write(
        "fit "+funcName+"'"+fitFileName+"' using 1:2:3 via a, b, x0\n")
    outFile.write('set key below\n')
    outFile.write("plot '"+fitFileName+"' using 1:2:3 title '" +
                  dataName+"' with yerrorbars, "+funcName+" title 'Fit'")
    outFile.close()


def ssBindingWYErrorsAndOffsetFitParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if lineIndex == startIndex + 5:
            x0 = line.split()[2]
            x0Err = line.split()[4]

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("x0 = "+str(x0)+'\n')
    paramFile.write("degrees of freedom = "+degF+'\n')
    paramFile.write("reduced chisq = "+rChiSq+'\n')
    paramFile.close()

    return a, aErr, b, bErr, x0, x0Err, degF, rChiSq


def ssBindingWYErrorsAndOffsetFit(xData, yData, yError, dataName="",
                                  xLabel="", yLabel="", outFileName="",
                                  logScale=0):

    outFile = open(outFileName, 'w')
    outFile.write('#chBSub\tratio\tratioError\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n])+'\t'+str(yData[n])+'\t'+str(yError[n])+'\n')
    outFile.close()
    aGuess = max(yData)
    bGuess = float(max(xData))/2
    gnuplotSSBindingWYErrorsAndOffsetScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess, logScale=logScale)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, x0, x0Error, degF, rChiSq = \
        ssBindingWYErrorsAndOffsetFitParams(outFileName)

    return aParam, aError, bParam, bError, x0, x0Error, degF, rChiSq


def gnuplotLinearFitWErrorsNoPlotScript(fitFileName, dataName="", xLabel="",
                                        yLabel="", aGuess=0, bGuess=0):
    """This subroutine creates a gnuplot script file to fit
    an input data file to a line."""

    outFileName = fitFileName[:-4]+".gnu"
    outFile = open(outFileName, 'w')
    outFile.write('set terminal png\n')
    outputName = fitFileName[:-4]+'.png'
    outFile.write("set output '"+outputName+"'\n")
    outFile.write("set xlabel '"+xLabel+"'\n")
    outFile.write("set ylabel '"+yLabel+"'\n")
    funcName = 'f_(x)'
    outFile.write(funcName+' = a+b*x\n')
    outFile.write("a = "+str(aGuess)+"; b = "+str(bGuess)+"\n")
    outFile.write("fit "+funcName+"'"+fitFileName+"' using 1:2:3 via a, b\n")
    outFile.close()


def linearFitWErrorsNoPlotParams(outFileName):

    fitFile = open('fit.log', 'r')
    lineIndex, startIndex = 0, 1000
    a, aErr, b, bErr = 0, 0, 0, 0
    degF, rChiSq = 0, 0
    for line in fitFile:
        lineIndex = lineIndex + 1
        if "Asymptotic Standard Error" in line:
            startIndex = lineIndex
        if lineIndex == startIndex + 3:
            a = line.split()[2]
            aErr = line.split()[4]
        if lineIndex == startIndex + 4:
            b = line.split()[2]
            bErr = line.split()[4]
        if "degrees of freedom" in line:
            degF = line.split(':')[1].strip()
        if "reduced chisquare" in line:
            rChiSq = line.split(':')[1].strip()

    paramFileName = outFileName[:-4]+'.params'
    paramFile = open(paramFileName, 'w')
    paramFile.write("a = "+str(a)+'\n')
    paramFile.write("b = "+str(b)+'\n')
    paramFile.write("degrees of freedom = "+str(degF)+'\n')
    paramFile.write("reduced chisq = "+str(rChiSq)+'\n')
    paramFile.close()

    return a, aErr, b, bErr, degF, rChiSq


def linearFitWErrorsNoPlot(xData, yData, yError, dataName="Dummy", xLabel="",
                           yLabel="", outFileName="Dummy.txt"):

    outFile = open(outFileName, 'w')
    outFile.write('#xData\tyData\tyErr\n')
    for n in range(0, len(xData)):
        outFile.write(
            str(xData[n])+'\t'+str(yData[n])+'\t'+str(yError[n])+'\n')
    outFile.close()
    aGuess = min(yData)
    bGuess = float(max(yData))/max(xData)

    gnuplotLinearFitWErrorsNoPlotScript(
        outFileName, dataName=dataName, xLabel=xLabel, yLabel=yLabel,
        aGuess=aGuess, bGuess=bGuess)
    gnuplotFit(outFileName)
    aParam, aError, bParam, bError, degF, rChiSq = \
        linearFitWErrorsNoPlotParams(outFileName)

    return aParam, aError, bParam, bError, degF, rChiSq


def ssBindingFit_v2(xData, yData, figFileName, xMin=0, xMax=0, yMin=0, yMax=0):

    max = N.max(yData)
    Kd = 0.5*N.max(xData)
    p0 = [max, Kd]

    xA = N.array(xData)
    yA = N.array(yData)

    # do least squares optimization
    plsq = optimize.leastsq(residualsSSBinding, p0, args=(yA, xA))
    fitMax, fitKd = plsq[0][0], plsq[0][1]

    if xMax == 0:
        xMax = N.max(xData)
    if yMax == 0:
        yMax = N.max(yData)

    # plot to check
    check = ssBindingModel(plsq[0], xA)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.plot(xData, yData, 'bo', hold="True", alpha=0.5)
    plt.plot(xData, check, 'r-')
    plt.savefig(figFileName)
    plt.clf()

    return fitMax, fitKd


def ssBindingModel(p, x):
    return (p[0]*x)/(x+p[1])


def residualsSSBinding(p, y, x):
    err = y-ssBindingModel(p, x)
    return err
