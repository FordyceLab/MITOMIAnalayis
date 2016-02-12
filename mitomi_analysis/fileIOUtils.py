import os
import sys
import math
from lab import sequence
import numpy as N


def fasta_to_chromosomes(infile):
    """This program reads in a fasta file containing
    multiple chromosomes and parses it into multiple text
    files with a text sequence for each chromosome."""

    in_file = open(infile, 'r')
    line_index = 0
    chrom_index = 0

    for line in in_file:

        temp_line = line.split()[0]

        if temp_line[0] == '>':
            print("Working on chromosome " + str(chrom_index))
            chrom_name = temp_line.split('|')[1]
            out_filename = "Chromosome_" + str(chrom_name)+".txt"
            out_file = open(out_filename, 'w')
            chrom_index = chrom_index + 1
            temp_seq = ''

        else:
            temp_seq = temp_line.split()[0]
            out_file.write(temp_seq)

        line_index = line_index + 1

    in_file.close()


def concatenate_fasta(infile):
    """This program reads in a fasta file with a single
    entry and concatenates the text into a single string.
    This is useful for restriction site searches."""

    in_file = open(infile, 'r')

    seq_string = ''
    line_index = 0

    for line in in_file:
        if line_index == 0:
            pass
        else:
            # print "Current line = " + str(line_index)
            seq_string = seq_string + line.split()[0]
        line_index = line_index + 1

    return seq_string


def repeat_strings(inFileName, outFileName):
    """This program reads in a tab-delimited text
    file with two columns (column 1 = str,
    column 2 = int) and the outputs a text file
    with each string repeated the number of times specified
    by the integer (and separated by a line break)."""

    inFile = open(inFileName, 'r')
    outFile = open(outFileName, 'w')

    for line in inFile:
        tempList = line.split()
        tempStr = tempList[0]
        numReps = tempList[1]
        for n in range(0, math.ceil(float(numReps))):
            outFile.write(tempStr)
            outFile.write('\n')

    inFile.close()
    outFile.close()


def sort_results_by_NNN(inFileName, outFileName):
    """This program reads in a tab-delimited text file
    with three columns.  The first column should be the
    MITOMI intensities, the second column should be the
    first letter of the NNN library, and the third column
    should be the last 3 letters.  The program
    then outputs a text file with a column
    for each of the first letters."""

    inFile = open(inFileName, 'r')
    outFile = open(outFileName, 'w')

    fileHeader = ["TRatio", "TOligo", "ARatio",
                  "AOligo", "CRatio", "COligo", "GRatio", "GOligo"]
    outFile.write('\t'.join(fileHeader))
    outFile.write('\n')

    tRatio, aRatio, cRatio, gRatio = [], [], [], []
    tOligo, aOligo, cOligo, gOligo = [], [], [], []

    for line in inFile:
        tempLine = line.split()
        print("First letter is "+tempLine[1])
        if tempLine[1] == 'T':
            tRatio.append(tempLine[0])
            tOligo.append(tempLine[2])
        elif tempLine[1] == 'A':
            aRatio.append(tempLine[0])
            aOligo.append(tempLine[2])
        elif tempLine[1] == 'C':
            cRatio.append(tempLine[0])
            cOligo.append(tempLine[2])
        elif tempLine[1] == 'G':
            gRatio.append(tempLine[0])
            gOligo.append(tempLine[2])
        else:
            print("First letter is not a DNA base!")

    listOfLists = [
        tRatio, tOligo, aRatio, aOligo, cRatio, cOligo, gRatio, gOligo]

    for n in range(0, len(tRatio)):
        for item in listOfLists:
            outFile.write(str(item[n]))
            outFile.write('\t')
        outFile.write('\n')

    inFile.close()
    outFile.close()


def average_RC_values(inFileName, outFileName):

    inFile = open(inFileName, 'r')
    outFile = open(outFileName, 'w')

    lineIndex = 0

    oligoRatios, oligoSems = {}, {}
    names, ratios, sems, ratiosWithRC, semsWithRC = [], [], [], [], []

    for line in inFile:
        lineIndex = lineIndex + 1
        # print "First run-through"
        # print "Line number = "+str(lineIndex)
        tempLine = line.split()
        oligoRatios[tempLine[0]] = tempLine[1]
        oligoSems[tempLine[0]] = tempLine[2]

    inFile.close()
    inFile = open(inFileName, 'r')

    lineIndex = 0

    for line in inFile:
        lineIndex = lineIndex + 1
        # print "Second run-through"
        # print "Line number = "+str(lineIndex)
        tempLine = line.split()
        names.append(tempLine[0])
        ratios.append(tempLine[1])
        sems.append(tempLine[2])

        oligoRC = sequence.reverseComplement(tempLine[0])
        ratioRC = oligoRatios[oligoRC]
        semRC = oligoSems[oligoRC]
        if tempLine[1] == 'NA' or tempLine[2] == 'NA' or semRC == 'NA':
            newRatio, newSem = 'NA', 'NA'
        else:
            newRatio = float(tempLine[1])+float(ratioRC)
            newSem = float(tempLine[2])+float(semRC)
        ratiosWithRC.append(newRatio)
        semsWithRC.append(newSem)

    listOfLists = [names, ratios, sems, ratiosWithRC, semsWithRC]

    for n in range(0, len(names)):
        print("n = "+str(n))
        for item in listOfLists:
            print("Item = "+str(item[n]))
            outFile.write(str(item[n]))
            outFile.write('\t')
        outFile.write('\n')

    inFile.close()
    outFile.close()


def text_file_to_dict(inFileName):
    """This program takes a tab-delimited text file and returns a dictionary
    for use in other programs.  The first column should contain the dictionary
    key and the second column should contain the dictionary value."""

    inFile = open(inFileName, 'r')
    newDict = {}

    for line in inFile:
        tempList = line.split()
        newDict[tempList[0]] = tempList[1]

    inFile.close()
    return newDict


def read_first_col_of_file(inFileName):
    """This program reads in a tab-delimited text file and returns a list
    of all of the values in the first column."""

    # open the file to read in and a file for writing the output
    inFile = open(inFileName, 'r')

    # create a new empty list to hold all of our values
    outList = []

    # now go through the input file line by line
    for line in inFile:
        # create a temporary list to hold all values on that line separated by
        # a "tab"
        tempList = line.split('\t')
        # append the first item in this temporary list to our output list
        outList.append(tempList[0])

    inFile.close()

    return outList


def create_lists_from_tabbed_file(inFileName):
    """This program reads in a tabbed file line by line and
    returns a list of lists (each line is one list)."""

    inFile = open(inFileName, 'r')
    outList = []

    for line in inFile:
        tempList = line.split()
        outList.append(tempList)

    return outList


def writeListOfLists(listOfLists, outFileName, header):
    """This program writes a list of lists
    to a tab-delimited text file in order."""

    outFile = open(outFileName, 'w')
    outFile.write(header)

    for n in range(0, len(listOfLists[0])):
        for item in listOfLists:
            if isinstance(item, str):
                outFile.write(item[n])
            else:
                outFile.write(str(item[n]))
            outFile.write('\t')
        outFile.write('\n')

    outFile.close()


def listToDict(inList):

    newDict = {}
    for n in range(0, len(inList)):
        newDict[str(n)] = inList[n]

    return newDict


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
