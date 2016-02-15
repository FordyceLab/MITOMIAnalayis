from numpy import *
import matplotlib
from mpl_toolkits.mplot3d import Axes3D

matplotlib.use('Agg')

from matplotlib import pylab as plt


def createAndSaveFig(xData, yData, figFileRoot, xLabel="", yLabel="",
                     fileExt='.png', xMin=-1, xMax=-1, yMin=-10, yMax=-1,
                     log2Y=0, log2X=0, plotType='bo', axisFontSize=20,
                     tickFontSize=16, svgFlag=0):

    figFileName = figFileRoot + fileExt
    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    if log2Y == 1:
        tempPlot = plt.semilogy(xData, yData, plotType, basey=2, hold='False')
    else:
        if log2X == 0:
            tempPlot = plt.plot(
                xData, yData, plotType, hold="False", alpha=0.5)
        else:
            tempPlot = plt.semilogx(
                xData, yData, plotType, basey=2, hold='False')
    plt.xlabel(xLabel, fontsize=axisFontSize)
    plt.ylabel(yLabel, fontsize=axisFontSize)
    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    if xMin == -1:
        xMin = min(xData.tolist())
    if xMax == -1:
        xMax = max(xData.tolist())
    if yMin == -10:
        yMin = min(yData.tolist())
        if isnan(yMin):
            yMin = 0
    if yMax == -1:
        yMax = 0
        yDataList = yData.tolist()
        for item in yDataList:
            if not isnan(item):
                if item > yMax:
                    yMax = item
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.savefig(figFileName, dpi=150)
    if svgFlag == 1:
        figFileName = figFileRoot + '.svg'
        plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveLogLogPlot(xData, yData, figFileRoot, xLabel="", yLabel="",
                            fileExt='.png', xMin=-1, xMax=-1, yMin=-1,
                            yMax=-1, plotType='bo', axisFontSize=20,
                            tickFontSize=16, svgFlag=0):

    figFileName = figFileRoot + fileExt
    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    tempPlot = plt.loglog(xData, yData, plotType, hold="False")
    plt.xlabel(xLabel, fontsize=axisFontSize)
    plt.ylabel(yLabel, fontsize=axisFontSize)
    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    if xMin == -1:
        xMin = min(xData.tolist())
    if xMax == -1:
        xMax = max(xData.tolist())
    if yMin == -1:
        yMin = min(yData.tolist())
        if isnan(yMin):
            yMin = 0
    if yMax == -1:
        yMax = 0
        yDataList = yData.tolist()
        for item in yDataList:
            if not isnan(item):
                if item > yMax:
                    yMax = item
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.savefig(figFileName, dpi=150)
    if svgFlag == 1:
        figFileName = figFileRoot + '.svg'
        plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveScatterPlot(xData, yData, xLabel="", yLabel="",
                             figFileRoot="", fileExt='.png', xMin=0, xMax=-1,
                             yMin=0, yMax=-1, svgFlag=0):

    figFileName = figFileRoot + fileExt
    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    tempPlot = plt.errorbar(xData, yData, fmt='bo')
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    if xMax == -1:
        xMax = max(xData)
    if yMax == -1:
        yMax = max(yData)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.savefig(figFileName, dpi=150)
    if svgFlag == 1:
        figFileName = figFileRoot + '.svg'
        plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveScatterPlotXYErrors(xData, yData, xError, yError, xLabel,
                                     yLabel, figFileRoot, fileExt, svgFlag=0):

    figFileName = figFileRoot + fileExt
    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    xError = convert_list_to_array(xError)
    yError = convert_list_to_array(yError)
    tempPlot = errorbar(xData, yData, yerr=yError, xerr=xError, fmt='bo')
    xlabel(xLabel)
    ylabel(yLabel)
    savefig(figFileName, dpi=300)
    if svgFlag == 1:
        figFileName = figFileRoot + '.svg'
        savefig(figFileName, dpi=150)
    clf()


def createAndSaveBarChart(xData, yData, xLabel="", yLabel="", figFileRoot="",
                          fileExt='.png', xMin=0, xMax=0, yMin=0, yMax=0):

    figFileName = figFileRoot + fileExt
    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    tempPlot = bar(xData, yData)
    xlabel(xLabel, fontsize=16)
    ylabel(yLabel, fontsize=16)
    if xMax == 0:
        xMax = max(xData)
    if yMax == 0:
        yMax = max(yData)
    xlim(xMin, xMax)
    ylim(yMin, yMax)
    savefig(figFileName, dpi=300)
    figFileName = figFileRoot + '.svg'
    savefig(figFileName, dpi=150)
    clf()


def createAndSaveBarChartWithErrors(yData, yError, xLabel="", yLabel="",
                                    figFileRoot="", fileExt='.png', xMin=0,
                                    xMax=0, yMin=0, yMax=0):

    figFileName = figFileRoot + fileExt
    xData = arange(len(yData))
    yData = convert_list_to_array(yData)
    yError = convert_list_to_array(yError)
    tempPlot = bar(xData, yData, yerr=yError)
    xlabel(xLabel, fontsize=16)
    ylabel(yLabel, fontsize=16)
    xlim(xMin, xMax)
    ylim(yMin, yMax)
    savefig(figFileName, dpi=300)
    figFileName = figFileRoot + '.svg'
    savefig(figFileName, dpi=150)
    clf()


def createAndSave2BarChart(yData1, yData2, xLabel="", yLabel="",
                           figFileRoot="", fileExt='.png', xMin=0, xMax=0):

    figFileName = figFileRoot + fileExt
    xData = arange(len(yData1))
    yData1 = convert_list_to_array(yData1)
    yData2 = convert_list_to_array(yData2)
    width = 0.5
    plot1 = bar(xData, yData1, width, color='r')
    plot2 = bar(xData + width, yData2, width, color='y')
    xlabel(xLabel)
    ylabel(yLabel)
    if xMax == 0:
        xMax = max(xData)
    xlim(xMin, xMax)
    savefig(figFileName, dpi=300)
    clf()


def createAndSave2BarChartWithErrors(yData1, yData2, yError1, yError2, xLabel,
                                     yLabel, figFileRoot, fileExt):

    figFileName = figFileRoot + fileExt
    xData = arange(len(yData1))
    yData1 = convert_list_to_array(yData1)
    yData2 = convert_list_to_array(yData2)
    width = 0.5
    plot1 = bar(xData, yData1, width, color='r', yerr=yError1)
    plot2 = bar(xData + width, yData2, width, color='y', yerr=yError2)
    xlabel(xLabel)
    ylabel(yLabel)
    savefig(figFileName, dpi=300)
    clf()


def createAndSaveMultitraceFig(pairedDataList, xLabel="", yLabel="",
                               figFileRoot="", fileExt='.png'):

    figFileName = figFileRoot + fileExt
    plotDict = create_multiple_trace_dict()

    for n in range(0, len(pairedDataList)):
        xData = convert_list_to_array(pairedDataList[n][0])
        yData = convert_list_to_array(pairedDataList[n][1])
        tempPlot = plot(xData, yData, plotDict[str(n + 1)], hold="True")

    xlabel(xLabel)
    ylabel(yLabel)
    savefig(figFileName, dpi=150)
    figFileName = figFileRoot + '.svg'
    savefig(figFileName, dpi=150)
    clf()


def newCreateAndSaveMultitraceFig(xDataList, yDataList, xLabel="", yLabel="",
                                  figFileRoot="", fileExt='.png', xMin=-10,
                                  xMax=0, yMin=-10, yMax=-1, nameList=[]):

    figFileName = figFileRoot + fileExt
    plotDict = create_multiple_trace_dict()

    if xMax == 0:
        curMax = 0
        for n in range(0, len(xDataList)):
            if type(xDataList[n]) == list:
                if max(xDataList[n]) > curMax:
                    curMax = max(xDataList[n])
            else:
                if xDataList[n].any() > curMax:
                    curMax = max(xDataList[n])
        xMax = curMax

    if xMin == -10:
        curMin = 10000000
        for n in range(0, len(xDataList)):
            if type(xDataList[n]) == list:
                if min(xDataList[n]) < curMin:
                    curMin = min(xDataList[n])
            else:
                if xDataList[n].any() > curMin:
                    curMin = min(xDataList[n])
        xMin = curMin

    if yMax == -1:
        curMax = 0
        for n in range(0, len(yDataList)):
            if type(yDataList[n]) == list:
                if max(yDataList[n]) > curMax:
                    curMax = max(yDataList[n])
            else:
                if yDataList[n].any() > curMax:
                    curMax = max(yDataList[n])
        yMax = curMax

    if yMin == -10:
        curMin = 10000000
        for n in range(0, len(yDataList)):
            if type(yDataList[n]) == list:
                if min(yDataList[n]) < curMin:
                    curMin = min(yDataList[n])
            else:
                if yDataList[n].any() > curMin:
                    curMin = min(yDataList[n])
        yMin = curMin

    for n in range(0, len(xDataList)):
        xData = convert_list_to_array(xDataList[n])
        yData = convert_list_to_array(yDataList[n])
        tempPlot = plt.plot(
            xData, yData, plotDict[str(n + 1)], hold="True", alpha=0.5)

    if nameList == []:
        for n in range(0, len(xDataList)):
            nameList.append("Trace_" + str(n))

    plt.xlabel(xLabel, size=20)
    plt.ylabel(yLabel, size=20)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveMultilineFig(pairedDataList, xLabel="", yLabel="",
                              figFileRoot="", fileExt='.png', xMin=0, xMax=0):
    """This subroutine saves a figure with multiple lines."""

    figFileName = figFileRoot + fileExt
    colorDict = createColorDict()

    if xMax == 0:
        curMax = 0
        for n in range(0, len(pairedDataList)):
            if type(pairedDataList[n][0]) == list:
                if max(pairedDataList[n][0]) > curMax:
                    curMax = max(pairedDataList[n][0])
            else:
                if pairedDataList[n][0].any() > curMax:
                    curMax = max(pairedDataList[n][0])
        xMax = curMax

    for n in range(0, len(pairedDataList)):
        xData = convert_list_to_array(pairedDataList[n][0])
        yData = convert_list_to_array(pairedDataList[n][1])
        tempPlot = plot(xData, yData, colorDict[str(n + 1)], hold="True")

    xlabel(xLabel)
    ylabel(yLabel)
    xlim(xMin, xMax)
    savefig(figFileName, dpi=300)
    clf()


def newCreateAndSaveMultilineFig(xDataList, yDataList, xLabel="", yLabel="",
                                 figFileRoot="", fileExt='.png', xMin=0,
                                 xMax=0, yMin=0, yMax=0, legendFlag=1,
                                 legendFont=12, traceNameList=[],
                                 legLoc=(0, 0)):
    """This subroutine saves a figure with multiple lines."""

    figFileName = figFileRoot + fileExt
    colorDict = createColorDictWithDashes()

    if xMax == 0:
        curMax = 0
        for n in range(0, len(xDataList)):
            if type(xDataList[n]) == list:
                if max(xDataList[n]) > curMax:
                    curMax = max(xDataList[n])
            else:
                if xDataList[n].any() > curMax:
                    curMax = max(xDataList[n])
        xMax = curMax

    if yMax == 0:
        curMax = 0
        for n in range(0, len(yDataList)):
            if type(yDataList[n]) == list:
                if max(yDataList[n]) > curMax:
                    curMax = max(yDataList[n])
            else:
                if yDataList[n].any() > curMax:
                    curMax = max(yDataList[n])
        yMax = curMax

    plt.axes([0.1, 0.1, 0.71, 0.8])
    if traceNameList == []:
        for n in range(0, len(xDataList)):
            traceNameList.append("Trace_" + str(n))

    for n in range(0, len(xDataList)):
        xData = convert_list_to_array(xDataList[n])
        yData = convert_list_to_array(yDataList[n])
        tempPlot = plt.plot(
            xData, yData, colorDict[str(n + 1)], hold="True",
            label=traceNameList[n])

    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.rc("legend", fontsize=legendFont)

    if legendFlag == 1:
        if legLoc != (0, 0):
            print(legLoc)
            plt.legend(loc=legLoc)
        else:
            plt.legend()
    plt.savefig(figFileName, dpi=300)
    plt.clf()


def createAndSaveMultilineFigSemilogX(pairedDataList, xLabel, yLabel,
                                      figFileRoot, fileExt):
    """This subroutine saves a figure with multiple lines."""

    figFileName = figFileRoot + fileExt
    colorDict = createColorDict()

    for n in range(0, len(pairedDataList)):
        xData = convert_list_to_array(pairedDataList[n][0])
        yData = convert_list_to_array(pairedDataList[n][1])
        tempPlot = semilogx(
            xData, yData, colorDict[str(n + 1)], basex=2, hold="True")

    xlabel(xLabel)
    ylabel(yLabel)
    savefig(figFileName, dpi=300)
    clf()


def createAndSaveMultilineFigSemilog10X(pairedDataList, xLabel, yLabel,
                                        figFileRoot, fileExt):
    """This subroutine saves a figure with multiple lines."""

    figFileName = figFileRoot + fileExt
    colorDict = createColorDict()

    for n in range(0, len(pairedDataList)):
        xData = convert_list_to_array(pairedDataList[n][0])
        yData = convert_list_to_array(pairedDataList[n][1])
        tempPlot = semilogx(xData, yData, colorDict[str(n + 1)], hold="True")

    xlabel(xLabel)
    ylabel(yLabel)
    savefig(figFileName, dpi=300)
    clf()


def create_multiple_trace_dict():

    colorList = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    markerList = ['o', 's', 'D', 'v', '+', 'x',
                  '^', '>', '<', 'p', '1', '2', '3', '4']
    symbolList = []
    for m in range(0, 14):
        marker = markerList[m]
        for l in range(0, 7):
            color = colorList[l]
            symbol = color + marker
            symbolList.append(symbol)

    plotDict = {}
    for n in range(0, 98):
        plotDict[str(n)] = symbolList[n]
    for n in range(98, 196):
        plotDict[str(n)] = symbolList[n - 98]
    for n in range(196, 294):
        plotDict[str(n)] = symbolList[n - 196]

    return plotDict


def createColorDict():

    colorList = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    colorDict = {}

    for n in range(0, 300):
        m = (n % len(colorList))
        colorDict[str(n)] = colorList[m] + '-'

    return colorDict


def createColorDict_v2():

    red = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    green = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    blue = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

    colorDict = {}
    cI = 0
    for a in red:
        for b in green:
            for c in blue:
                colorDict[cI] = (a, b, c)
                cI = cI + 1

    return colorDict


def createColorDictWithDashes():

    colorList = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    dashList = ['-', ':', '--', '-.']

    outDict = {}

    for n in range(0, 300):
        m = (n % len(colorList))
        l = ((n / len(colorList)) % len(dashList))
        outDict[str(n)] = colorList[m] + dashList[l]

    return outDict


def convert_list_to_array(inData):
    """This program just checks to see if data is a list and
    if so, converts it to an array."""

    if isinstance(inData, list):
        inData = array(inData)

    return inData


def make_plot(xData, yData, xFit, yFit):
    """This program just plots the yData, xData, yFit, and xFit
    from a single file on one graph and labels the axes appropriately."""

    tempPlot = plot(xData, yData, 'bo', hold=True)
    tempPlot = plot(xFit, yFit, 'b-', hold=True)

    return tempPlot


def make_plot_with_error(xData, yData, yError, xFit, yFit):
    """This program just plots the yData, xData, yFit, and xFit
    from a single file on one graph and labels the axes appropriately.
    This program also includes y Error bars."""

    xData = convert_list_to_array(xData)
    yData = convert_list_to_array(yData)
    yError = convert_list_to_array(yError)
    xFit = convert_list_to_array(xFit)
    yFit = convert_list_to_array(yFit)

    tempPlot = errorbar(xData, yData, yError, 'bo', hold=True)
    tempPlot = plot(xFit, yFit, 'b-', hold=True)

    return tempPlot


def append_multiple_traces_to_graph(yValuesList, xValuesList):

    curIndex = 0
    plotArgDict = create_multiple_trace_dict()
    listLen = len(yValuesList)
    if len(xValuesList) != listLen:
        print("X and Y data are different lengths! User is a bozo!")
        pass
    else:
        for n in range(0, listLen):
            curIndex = curIndex + 1
            curColorIndex = str(curIndex % 48)
            tempPlot = plot(
                xValuesList[n], yValuesList[n], plotArgDict[curColorIndex],
                hold=True)
    hold = False
    return tempPlot


def append_multiple_traces_to_graph_yValuesOnly(yValuesList):

    curIndex = 0
    plotArgDict = create_multiple_trace_dict()
    listLen = len(yValuesList)
    for n in range(0, listLen):
        curIndex = curIndex + 1
        curColorIndex = str(curIndex % 48)
        tempPlot = plot(yValuesList[n], plotArgDict[curColorIndex], hold=True)
    hold = False
    return tempPlot


def barchart_with_errors(yValues, yErrors, barNames):

    yDataArray = convert_list_to_array(yValues)
    yErrorArray = convert_list_to_array(yErrors)

    numBars = len(yValues)
    xDataArray = arange(numBars)

    tempPlot = bar(xDataArray, yDataArray, yerr=yErrorArray)
    xticks(xDataArray, barNames, rotation=-90)

    return tempPlot


def gnuplotScript(fileName, title, xLabel, yLabel):

    scriptName = fileName[:-4] + '_gnuplot.p'

    graphName = fileName[:-4] + '.ps'
    titleCommand = 'set title "' + title + '"\n'
    xLabelCommand = 'set xlabel "' + xLabel + '"\n'
    yLabelCommand = 'set ylabel "' + yLabel + '"\n'
    outputCommand = 'set output "' + graphName + '"\n'
    plotCommand = 'plot "' + fileName + '" with points lt 1 pt 7 ps 2\n'

    scriptFile = open(scriptName, 'w')
    scriptFile.write(titleCommand)
    scriptFile.write(xLabelCommand)
    scriptFile.write(yLabelCommand)
    scriptFile.write('set terminal postscript\n')
    scriptFile.write(outputCommand)
    scriptFile.write(plotCommand)
    scriptFile.write('set term pop\n')
    scriptFile.close()

    return scriptName


def gnuplotScriptManyFilesOneGraph(scriptName, fileList, title, xLabel, yLabel,
                                   graphName):

    titleCommand = 'set title ' + title + '\n'
    xLabelCommand = 'set xlabel ' + xLabel + '\n'
    yLabelCommand = 'set ylabel ' + yLabel + '\n'
    outputCommand = 'set output ' + graphName + '\n'
    plotCommand = 'plot '
    for n in range(0, (len(fileList) - 1)):
        plotCommand = plotCommand + \
            str(fileList[n]) + ' with points lt ' + str(n + 1) + ' pt 7 ps 2, '
    plotCommand = plotCommand + \
        str(fileList(len(fileList))) + ' with points lt ' + \
        str(len(fileList) + 1) + ' pt 7 ps 2\n'

    scriptFile = open(scriptName, 'w')
    scriptFile.write(titleCommand)
    scriptFile.write(xLabelCommand)
    scriptFile.write(yLabelCommand)
    scriptFile.write('set terminal postscript\n')
    scriptFile.write(outputCommand)
    scriptFile.write(plotCommand)
    scriptFile.write('set term pop\n')

    scriptFile.close()


def makeHist(dataIn, figFileRoot, numBins=None, normed=0, facecolor='green',
             xLabel='', yLabel='', log=False, xMin=-10, xMax=-10, yMin=-10,
             histtype='bar', removeNaNFlag=0, axisFontSize=22, tickFontSize=18,
             svgFlag=0):
    if removeNaNFlag == 1:
        newData = []
        for item in dataIn:
            if not isnan(item):
                newData.append(item)
        dataIn = newData
    if xMin == -10:
        xMin = min(dataIn)
    if xMax == -10:
        xMax = max(dataIn)
    if numBins is None:
        n, bins, patches = plt.hist(dataIn, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolor,
            histtype=histtype)
    else:
        n, bins, patches = plt.hist(dataIn, bins=numBins, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolor,
            histtype=histtype)
    plt.xlabel(xLabel, fontsize=axisFontSize)
    plt.ylabel(yLabel, fontsize=axisFontSize)
    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    if yMin != -10:
        yMax = max(n)
        plt.ylim(yMin, yMax)
    figFileName = figFileRoot + '.png'
    plt.savefig(figFileName, dpi=150)
    if svgFlag == 1:
        figFileName = figFileRoot + '.svg'
        plt.savefig(figFileName, dpi=150)
    plt.clf()


def overlapHist(dataA, dataB, figFileRoot, numBinsA=None, numBinsB=None,
                normed=0, facecolorA='green', facecolorB='0.8', xLabel='',
                yLabel='', log=False, xMin=-10, xMax=-10, yMin=-10,
                histtype='bar', removeNaNFlag=0, axisFontSize=22,
                tickFontSize=18):
    if removeNaNFlag == 1:
        newDataA, newDataB = [], []
        for item in dataA:
            if not isnan(item):
                newDataA.append(item)
        for item in dataB:
            if not isnan(item):
                newDataB.append(item)
        dataA, dataB = newDataA, newDataB
    if xMin == -10:
        xMin = min(dataA)
        if min(dataB) < xMin:
            xMin = min(dataB)
    if xMax == -10:
        xMax = max(dataA)
        if max(dataB) > xMax:
            xMax = max(dataB)
    if numBinsA is None and numBinsB is None:
        nA, binsA, patchesA = plt.hist(dataA, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolorA,
            histtype=histtype, hold=True)
        nB, binsB, patchesB = plt.hist(dataB, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolorB,
            histtype=histtype)
    else:
        nA, binsA, patchesA = plt.hist(dataA, bins=numBinsA, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolorA,
            histtype=histtype, hold=True)
        nB, binsB, patchesB = plt.hist(dataB, bins=numBinsB, range=(
            xMin, xMax), normed=normed, log=log, facecolor=facecolorB,
            histtype=histtype)
    plt.xlabel(xLabel, fontsize=axisFontSize)
    plt.ylabel(yLabel, fontsize=axisFontSize)
    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(tickFontSize)
    if yMin == -10:
        yMin = min(nA)
        if min(nB) < yMin:
            yMin = min(nB)
    yMax = max(nA)
    if max(nB) > max(nA):
        yMax = max(nB)
    plt.ylim(yMin, yMax)
    figFileName = figFileRoot + '.png'
    plt.savefig(figFileName, dpi=150)
    plt.clf()


def histOutline(dataIn, binsIn=None):
    """
    Make a histogram that can be plotted with plot() so that
    the histogram just has the outline rather than bars as it
    usually does.
    """
    if (binsIn is None):
        (en, eb, ep) = hist(dataIn, normed=1)
        binsIn = eb
    else:
        (en, eb, ep) = hist(dataIn, bins=binsIn, normed=1)

    stepSize = binsIn[1] - binsIn[0]

    bins = zeros(len(eb) * 2 + 2, float)
    data = zeros(len(eb) * 2 + 2, float)

    for bb in range(len(binsIn)):
        bins[2 * bb + 1] = binsIn[bb]
        bins[2 * bb + 2] = binsIn[bb] + stepSize
        data[2 * bb + 1] = en[bb]
        data[2 * bb + 2] = en[bb]

    bins[0] = bins[1]
    bins[-1] = bins[-2]
    data[0] = 0
    data[-1] = 0
    clf()

    return (bins, data)


def histOutlineLogX(dataIn, binsIn=None):
    """
    Make a histogram that can be plotted with plot() so that
    the histogram just has the outline rather than bars as it
    usually does.
    """
    if (binsIn is None):
        (en, eb, ep) = hist(dataIn, normed=1, log='True')
        binsIn = eb
    else:
        (en, eb, ep) = hist(dataIn, bins=binsIn, normed=1, log='True')

    stepSize = binsIn[1] - binsIn[0]

    bins = zeros(len(eb) * 2 + 2, float)
    data = zeros(len(eb) * 2 + 2, float)
    clf()

    for bb in range(len(binsIn)):
        bins[2 * bb + 1] = binsIn[bb]
        bins[2 * bb + 2] = binsIn[bb] + stepSize
        data[2 * bb + 1] = en[bb]
        data[2 * bb + 2] = en[bb]

    bins[0] = bins[1]
    bins[-1] = bins[-2]
    data[0] = 0
    data[-1] = 0

    return (bins, data)


def createAndSaveHeatMap(dataArray, figFileRoot, xLabel="", yLabel="", xMin=0,
                         xMax=-1, yMin=0, yMax=-1, colorMap=0, maxInt=0,
                         vMin=0, vMax=0, fontSize=20, majorFontSize=18,
                         pngDPI=150, svgDPI=75, svgFlag=0):
    """Make a 2D intensity map of the data and save it to file."""

    colorList = [None, plt.cm.Reds, plt.cm.Greens, plt.cm.Greys]
    if vMin == -10:
        vMin = 0
    if vMax == 0:
        for a in dataArray.flat:
            if not isnan(a) and a > vMax:
                vMax = a

    plt.pcolor(dataArray, cmap=colorList[colorMap], vmin=vMin, vmax=vMax)
    plt.xlabel(xLabel, fontsize=fontSize)
    plt.ylabel(yLabel, fontsize=fontSize)
    plt.colorbar(orientation="vertical")
    ax = plt.gca()
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_fontsize(majorFontSize)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_fontsize(majorFontSize)

    if xMax == -1:
        plt.xlim()
    else:
        plt.xlim(xMin, xMax)
    if yMax == -1:
        plt.ylim()
    else:
        plt.ylim(yMin, yMax)
    if maxInt != 0:
        plt.clim(0, maxInt)
    plt.savefig(figFileRoot + '.png', dpi=pngDPI)
    if svgFlag == 1:
        plt.savefig(figFileRoot + '.svg', dpi=svgDPI)
    plt.clf()


def createSingleFigWithSubplots(yDataList, figFileRoot, xLabel="", yLabel="",
                                fileExt='.png', xMin=-1, xMax=-1, yMin=-1,
                                yMax=-1, log2Y=0, log2X=0):

    figFileName = figFileRoot + fileExt

    numPlots = len(yDataList)

    for n in range(0, len(yDataList)):
        subplot(numPlots, 1, n)
        xData = arange(len(yDataList[n]))
        yData = convert_list_to_array(yDataList[n])
        if log2Y == 1:
            tempPlot = semilogy(xData, yData, 'bo', basey=2, hold='False')
        else:
            if log2X == 0:
                tempPlot = plot(xData, yData, 'bo', hold="False")
            else:
                tempPlot = semilogx(xData, yData, 'bo', basey=2, hold='False')
        xlabel(xLabel, fontsize=16)
        ylabel(yLabel, fontsize=16)
        if xMin == -1:
            xMin = min(xData.tolist())
        if xMax == -1:
            xMax = max(xData.tolist())
        if yMin == -1:
            yMin = min(yData.tolist())
        if yMax == -1:
            yMax = max(yData.tolist())
        xlim(xMin, xMax)
        ylim(yMin, yMax)

    savefig(figFileName, dpi=150)
    figFileName = figFileRoot + '.svg'
    savefig(figFileName, dpi=150)
    clf()


def newLegend(*args, **kwargs):
    """
    Overwrites the pylab legend function.

    It adds another location identifier 'outer right'
    which locates the legend on the right side of the plot

    The args and kwargs are forwarded to the pylab legend function
    """

    if 'loc' in kwargs:
        loc = kwargs['loc']
        loc = loc.split()
        if loc[0] == 'outer':
            # make a legend with out the location
            # remove the location setting from the kwargs
            kwargs.pop('loc')
            leg = plt.legend(loc=(0, 0), *args, **kwargs)
            frame = leg.get_frame()
            currentAxes = plt.gca()
            currentAxesPos = currentAxes.get_position()
            # scale plot by the part which is taken by the legend
            plotScaling = frame.get_width() / 2.5 * currentAxesPos[2]

            if loc[1] == 'right':
                # scale the plot
                currentAxes.set_position((currentAxesPos[0], currentAxesPos[1],
                                          currentAxesPos[2] *
                                          (1 - plotScaling),
                                          currentAxesPos[3]))
                # set x and y coordinates of legend
                leg._loc = (1 + leg.axespad, 1 - frame.get_height())

                draw_if_interactive()
                return leg

            return legend(*args, **kwargs)


def createAndSaveRawAndMeanData(xDataRaw, yDataRaw, xDataMean, yDataMean,
                                yDataSem, xLabel="", yLabel="", figFileRoot="",
                                fileExt='.png', xMin=-100, xMax=0, yMin=-100,
                                yMax=0):

    figFileName = figFileRoot + fileExt

    if xMax == 0:
        curMax = 0
        for n in range(0, len(xDataRaw)):
            if xDataRaw[n] > curMax:
                curMax = xDataRaw[n]
            else:
                pass
        xMax = curMax

    if xMin == -100:
        curMin = 10000000
        for n in range(0, len(xDataRaw)):
            if xDataRaw[n] < curMin:
                curMin = xDataRaw[n]
        xMin = curMin

    if yMax == 0:
        curMax = 0
        for n in range(0, len(yDataRaw)):
            if yDataRaw[n] > curMax:
                curMax = yDataRaw[n]
            else:
                pass
        yMax = curMax

    if yMin == -100:
        curMin = 10000000
        for n in range(0, len(yDataRaw)):
            if yDataRaw[n] < curMin:
                curMin = yDataRaw[n]
        yMin = curMin

    tempPlot = plt.plot(xDataRaw, yDataRaw, ls='None',
                        marker='o', markersize=1.5, color='1.0', hold="True")
    tempPlot = plt.errorbar(xDataMean, yDataMean, yerr=yDataSem, fmt='ro')

    plt.xlabel(xLabel, size=20)
    plt.ylabel(yLabel, size=20)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveRawAndMeanDataWLabels(xDataRaw, yDataRaw, xDataMean,
                                       yDataMean, yDataSem, xTicks, xLabels,
                                       xLabel="", yLabel="", figFileRoot="",
                                       fileExt='.png', xMin=-1, xMax=0,
                                       yMin=-100, yMax=0):

    figFileName = figFileRoot + fileExt

    if xMax == 0:
        curMax = 0
        for n in range(0, len(xDataRaw)):
            if xDataRaw[n] > curMax:
                curMax = xDataRaw[n]
            else:
                pass
        xMax = curMax

    if xMin == -100:
        curMin = 10000000
        for n in range(0, len(xDataRaw)):
            if xDataRaw[n] < curMin:
                curMin = xDataRaw[n]
        xMin = curMin

    if yMax == 0:
        curMax = 0
        for n in range(0, len(yDataRaw)):
            if yDataRaw[n] > curMax:
                curMax = yDataRaw[n]
            else:
                pass
        yMax = curMax

    if yMin == -100:
        curMin = 10000000
        for n in range(0, len(yDataRaw)):
            if yDataRaw[n] < curMin:
                curMin = yDataRaw[n]
        yMin = curMin

    tempPlot = plt.plot(xDataRaw, yDataRaw, ls='None',
                        marker='o', markersize=1.5, color='1.0', hold="True")
    tempPlot = plt.errorbar(xDataMean, yDataMean, yerr=yDataSem, fmt='ro')

    plt.xlabel(xLabel, size=20)
    plt.ylabel(yLabel, size=20)
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.xticks(xTicks, xLabels, size='x-large')
    plt.savefig(figFileName, dpi=150)
    plt.clf()


def createAndSaveContourPlot(zData, xData, yData, figFileName, xLabel, yLabel,
                             zLabel):

    xA = convert_list_to_array(xData)
    yA = convert_list_to_array(yData)
    zA = convert_list_to_array(zData)

    fig = plt.figure()

    ax = Axes3D(fig)
#    ax.plot3D(xA, yA, zA, c='b', marker='o', alpha=0.5)
    p = ax.scatter(xA, yA, zA, c='b', marker='o', alpha=0.5)

    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    ax.set_zlabel(zLabel)
    ax.set_xlim3d(25, 275)
    ax.set_ylim3d(30, 80)
    ax.set_zlim3d(0, 40)

    plt.savefig(figFileName, dpi=150)
    plt.savefig(figFileName + '.svg', dpi=150)
    plt.clf()


def createAndSaveContourPlotExtraD(zData, xData, yData, colorData, figFileName,
                                   xLabel, yLabel, zLabel):

    xA = convert_list_to_array(xData)
    yA = convert_list_to_array(yData)
    zA = convert_list_to_array(zData)
    cA = convert_list_to_array(colorData)

    fig = plt.figure()

    ax = Axes3D(fig)
    p = ax.scatter(xA, yA, zA, c=cA, marker='o', alpha=0.5)
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    ax.set_zlabel(zLabel)

    ax.set_xlim3d(0, 80)
    ax.set_ylim3d(0, 300)
    ax.set_zlim3d(10, 90)

    fig.colorbar(p)

    plt.savefig(figFileName, dpi=150)
    plt.savefig(figFileName + '.svg', dpi=150)
    plt.clf()
