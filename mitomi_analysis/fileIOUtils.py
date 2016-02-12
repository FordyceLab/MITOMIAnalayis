import os


def createNewDir(dirName):

    if os.path.isdir(dirName):
        pass
    else:
        os.mkdir(dirName)


def createNewSeqDir(dirName):

    if os.path.isdir(dirName):
        pass
    else:
        os.mkdir(dirName)
        chromatDir = dirName+"/chromat_dir"
        editDir = dirName+"/edit_dir"
        phdDir = dirName+"/phd_dir"
        os.mkdir(chromatDir)
        os.mkdir(editDir)
        os.mkdir(phdDir)


def fastaToDict(inFileName):

    inFile = open(inFileName, 'r')
    outD = {}
    curSeq = ''
    lineIndex = 0
    for line in inFile:
        lineIndex = lineIndex + 1
        if lineIndex == 1:
            curGeneID = line.split("|")[0][1:].strip()
        else:
            if '>' in line:
                outD[curGeneID] = curSeq
                curGeneID = line.split("|")[0][1:].strip()
                curSeq = ''
            else:
                curSeq = curSeq + line.strip()
    outD[curGeneID] = curSeq
    inFile.close()
    return outD


def dictToFasta(outDict, outFileName):

    outFile = open(outFileName, 'w')
    for item in outDict:
        outFile.write(">"+item+"\n")
        for n in range(0, (len(outDict[item])/60+1)):
            outFile.write(outDict[item][n*60:((n+1)*60)]+"\n")
    outFile.close()


def fastaToDictMITOMI(inFileName):

    inFile = open(inFileName, 'r')
    outD = {}
    curSeq = ''
    lineIndex = 0
    for line in inFile:
        lineIndex = lineIndex + 1
        if lineIndex == 1:
            curGeneID = line.strip().split("_")[1]
        else:
            if '>' in line:
                outD[curGeneID] = curSeq
                curGeneID = line.strip().split("_")[1]
                curSeq = ''
            else:
                curSeq = curSeq + line.strip()
    outD[curGeneID] = curSeq
    inFile.close()
    return outD


def fileToList(inFileName):

    inFile = open(inFileName, 'r')
    outList = []
    for line in inFile:
        outList.append(line.strip())
    inFile.close()
    return outList


def removeTabBeforeCarriageReturn(inFileName):

    fIn = open(inFileName, 'r')
    fOut = open(inFileName[:-4]+'_Clean.txt', 'w')
    for line in fIn:
        tempL = line.split('\t')
        for a in range(0, len(tempL)-2):
            fOut.write(tempL[a]+'\t')
        lastTab = tempL.pop()
        lastCol = tempL.pop()
        fOut.write(lastCol+'\n')
    fIn.close()
    fOut.close()
