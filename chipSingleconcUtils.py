import numpy as N
import types
from plotting import plotUtils
from statistics import statsUtils
# from lab import sequence
from fitting import fitUtils
import operator
from matplotlib import pylab as plt
from scipy import stats

def makeSpot2OligoFile(chipToPlateFileName, plate384To96FileName, plateToOligoFileName):
     """This program takes 3 files as input: (1) contains the mapping between the spots on the chip and
     384-well plate wells, (2) contains the mapping between the wells in the 384-well plates and the
     96-well plates, and (3) converts the original 96-well plate location to an oligo name.  It
     then outputs a single text file with columns for (1) row position, (2) column position,
     and (3) oligo name."""

     fileNameList = [chipToPlateFileName,plate384To96FileName,plateToOligoFileName]
     chipToPlateD, plate384To96D, plateToOligoD = {},{},{}
     dictList = [chipToPlateD, plate384To96D, plateToOligoD]
     chipToPlateList = []

     for n in range(0,len(fileNameList)):
          tempFile = open(fileNameList[n],'r')
          for line in tempFile:
              tempList = line.split("\t")
              dictList[n][tempList[0].strip()] = tempList[1].strip()
              if n == 0:
                  chipToPlateList.append(tempList[0].strip())

     spotList = []

     for item in chipToPlateList:
          row = item.split(".")[0].strip()
          spot = item.split(".")[1].strip()
          well384Plate = chipToPlateD[item]

          if plate384To96D.has_key(well384Plate):
               well96Plate = plate384To96D[well384Plate]
               if plateToOligoD.has_key(well96Plate):
                    oligoName = plateToOligoD[well96Plate]
               else:
                    print "plateToOligoD does not have key "+well96Plate
          else:
               print "plate384To96D does not have key "+well384Plate
          outList = [row,spot,oligoName]
          spotList.append(outList)

     return spotList

def makeSpot2OligoDict(spot2OligoFileName):
     """This program takes a spot2Oligo file and creates a
     dictionary containing the oligo names for each spot."""

     spot2OligoFile = open(spot2OligoFileName,'r')
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
 
def dimsFromSpot2OligoFile(spot2OligoFileName):
    
    numCols,numSpots,lineIndex = 0,0,0
    spot2OligoFile = open(spot2OligoFileName,'r')
    for line in spot2OligoFile:
        lineIndex = lineIndex + 1
        tempList = line.split("\t")
        if lineIndex == 1:
            pass
        else:
            col = int(tempList[0].strip())
            row = int(tempList[1].strip())
            if col >= numCols:
                numCols = col
            if row >= numSpots:
                numSpots = row
    
    return numCols,numSpots

def convertGprFileToSingleBlock(gprFileName):
     """This program takes gpr files that were gridded using multiple blocks
     and converts them to files gridded in a single block format for later analysis."""

     gprFile = open(gprFileName,'r')
     # first take the gpr file and make a backup called "_MB.gpr"
     oldFileName = gprFileName[:-4]+"_MB.gpr"
     oldFile = open(oldFileName,'w')
     for line in gprFile:
          oldFile.write(line)
     oldFile.close()
     gprFile.close()

     # now open the old file and figure out the number of columns per block
     oldFile = open(oldFileName,'r')
     maxCol = 0
     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split("\t")
               if int(tempList[1]) > maxCol:
                    maxCol = int(tempList[1])
               else:
                    pass
     oldFile.close()

     # now go through, renumber columns, and output to the original filename
     oldFile = open(oldFileName,'r')
     gprFile = open(gprFileName,'w')
     lineIndex = 0
     totalCols,totalSpots = 0,0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               gprFile.write(line)
          else:
               tempList = line.split('\t')
               block = int(tempList[0])
               col = int(tempList[1])
               spot = int(tempList[2])
               newCol = (block-1)*maxCol+col
               tempList[1] = str(newCol)
               outLine = '\t'.join(tempList)
               gprFile.write(outLine)
               # figure out the number of columns and spots
               if newCol > totalCols:
                    totalCols = newCol
               if spot > totalSpots:
                    totalSpots = spot

     oldFile.close()
     gprFile.close()

     return totalCols, totalSpots

def convertGprFileToSingleBlock_v2(gprFileName):
     """This program takes gpr files that were gridded using multiple blocks
     and converts them to files gridded in a single block format for later analysis.
     This new version of the program leaves the original files alone."""

     # open the file and figure out the number of columns per block
     gprFile = open(gprFileName,'r')
     maxCol = 0
     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split("\t")
               if int(tempList[1]) > maxCol:
                    maxCol = int(tempList[1])
               else:
                    pass
     oldFile.close()

     # now go through, renumber columns, and output to the original filename
     newFile = open(gprFileName[:-4]+'_rn.gpr')
     gprFile = open(gprFileName,'r')
     lineIndex = 0
     totalCols,totalSpots = 0,0
     for line in gprFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               newFile.write(line)
          else:
               tempList = line.split('\t')
               block = int(tempList[0])
               col = int(tempList[1])
               spot = int(tempList[2])
               newCol = (block-1)*maxCol+col
               tempList[1] = str(newCol)
               outLine = '\t'.join(tempList)
               newFile.write(outLine)
               # figure out the number of columns and spots
               if newCol > totalCols:
                    totalCols = newCol
               if spot > totalSpots:
                    totalSpots = spot

     newFile.close()
     gprFile.close()

     return totalCols, totalSpots

 
def numColsAndSpotsPerCol(gprFileName):
    
    tempFile = open(gprFileName,'r')
    numCols,spotsPerCol = 0,0
    lineIndex = 0
    for line in tempFile:
        lineIndex = lineIndex + 1
        if lineIndex <= 32:
            pass
        else:
            tempList = line.split('\t')
            if int(tempList[1]) > numCols:
                numCols = int(tempList[1])
            if int(tempList[2]) > spotsPerCol:
                spotsPerCol = int(tempList[2])
    
    tempFile.close()
    return numCols,spotsPerCol


def concatGprFiles(buttonFileName,chamberFileName,outFileName,DNAFileName="",pBgFileName="",numCols=1,numSpots=1):
     """This program requires 2 different GenePix results files from
     a MITOMI experiment.  The intensities read in by this file are
     the MEDIAN values.  The button file should be from spots that are
     located over the buttons (protein and bound DNA intensities).  The chamber
     file should be from spots that are located on top of adjacent
     chambers (chamber intensities).  An optional DNAFileName can be used
     if the protein and DNA scans are slightly offset from one another; in this
     case, the features should be centered on the DNA signals below the buttons.
     An option pBgFileName can be used if there is unwashed protein in the channels
     that is leading to an overestimation of the protein signal underneath the button;
     in this case, the features should be centered on a region of the chip that is
     not a flow channel."""
     
     buttonFile = open(buttonFileName,'r')
     chamberFile = open(chamberFileName,'r')
     outFile = open(outFileName,'w')
     str1 = "Row\tColumn\tDia\tFlag\tP_FG\tDNA_FG\tP_BG\tDNA_BG\tCH_FG\n"
     outFile.write(str1)

     dimensions = (numSpots,numCols)

     diaArray, flagArray = N.zeros(dimensions), N.zeros(dimensions)
     pFgArray, DNAFgArray = N.zeros(dimensions), N.zeros(dimensions)
     pBgArray, DNABgArray = N.zeros(dimensions), N.zeros(dimensions)
     chFgArray = N.zeros(dimensions)

     if DNAFileName == "":
          DNAFileName = buttonFileName
          
     buttonFile = open(buttonFileName,'r')
     lineIndex = 0
     for line in buttonFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split('\t')
               tempCol = int(tempList[1])
               tempSpot = int(tempList[2])
               tempDia = int(tempList[7])
               tempPFg = int(tempList[20])
               tempFlag = int(tempList[53])
               tempPBg = int(tempList[25])
               diaArray[tempSpot-1][tempCol-1] = tempDia
               if int(tempFlag) != 0:
                    flagArray[tempSpot-1][tempCol-1] = tempFlag 
               pFgArray[tempSpot-1][tempCol-1] = tempPFg
               if pBgFileName == "":
                    pBgArray[tempSpot-1][tempCol-1] = tempPBg
               
     buttonFile.close()

     chamberFile = open(chamberFileName,'r')
     lineIndex = 0
     for line in chamberFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split('\t')
               tempCol = int(tempList[1])
               tempSpot = int(tempList[2])
               tempChFg = int(tempList[8])
               chFgArray[tempSpot-1][tempCol-1] = tempChFg
     chamberFile.close()

     DNAFile = open(DNAFileName,'r')
     lineIndex = 0
     for line in DNAFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split('\t')
               tempCol = int(tempList[1])
               tempSpot = int(tempList[2])
               tempDNAFg = int(tempList[8])
               tempDNABg = int(tempList[12])
               tempFlag = int(tempList[53])
               DNAFgArray[tempSpot-1][tempCol-1] = tempDNAFg
               DNABgArray[tempSpot-1][tempCol-1] = tempDNABg
               if int(tempFlag) != 0:
                    flagArray[tempSpot-1][tempCol-1] = tempFlag
     DNAFile.close()

     if pBgFileName != "":
          pBgFile = open(pBgFileName,'r')
          lineIndex = 0
          for line in pBgFile:
               lineIndex = lineIndex + 1
               if lineIndex <= 32:
                    pass
               else:
                    tempList = line.split('\t')
                    tempCol = int(tempList[1])
                    tempSpot = int(tempList[2])
                    tempPBg = int(tempList[20])
                    pBgArray[tempSpot-1][tempCol-1] = tempPBg
          pBgFile.close()

     for m in range(0,numCols):
          for l in range(0,numSpots):
               outFile.write(str(l+1)+'\t')
               outFile.write(str(m+1)+'\t')
               outFile.write(str(diaArray[l][m])+'\t')
               outFile.write(str(flagArray[l][m])+'\t')
               outFile.write(str(pFgArray[l][m])+'\t')
               outFile.write(str(DNAFgArray[l][m])+'\t')
               outFile.write(str(pBgArray[l][m])+'\t')
               outFile.write(str(DNABgArray[l][m])+'\t')
               outFile.write(str(chFgArray[l][m])+'\n')
     outFile.close()

def concatGprFiles_v2(buttonFileName,chamberFileName,outFileName,DNAFileName="",pBgFileName="",DNABgFileName="",numCols=1,numSpots=1,griddingFlag=0,pGridFlag=0,dGridFlag=0,cGridFlag=0):
     """This program requires 2 different GenePix results files from
     a MITOMI experiment.  The intensities read in by this file are
     the MEDIAN values.  The button file should be from spots that are
     located over the buttons (protein and bound DNA intensities).  The chamber
     file should be from spots that are located on top of adjacent
     chambers (chamber intensities).  An optional DNAFileName can be used
     if the protein and DNA scans are slightly offset from one another; in this
     case, the features should be centered on the DNA signals below the buttons.
     An option pBgFileName can be used if there is unwashed protein in the channels
     that is leading to an overestimation of the protein signal underneath the button;
     in this case, the features should be centered on a region of the chip that is
     not a flow channel."""
     
     buttonFile = open(buttonFileName,'r')
     chamberFile = open(chamberFileName,'r')
     outFile = open(outFileName,'w')
     str1 = "Row\tColumn\tDia\tFlag\tP_FG\tDNA_FG\tP_BG\tDNA_BG\tCH_FG\n"
     outFile.write(str1)

     dimensions = (numSpots,numCols)

     diaArray, flagArray = N.zeros(dimensions), N.zeros(dimensions)
     pFgArray, DNAFgArray = N.zeros(dimensions), N.zeros(dimensions)
     pBgArray, DNABgArray = N.zeros(dimensions), N.zeros(dimensions)
     chFgArray = N.zeros(dimensions)

     if DNAFileName == "":
          DNAFileName = buttonFileName
          
     buttonFile = open(buttonFileName,'r')
     lineIndex = 0
     for line in buttonFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split('\t')
               if griddingFlag == 0 and pGridFlag == 0:
                   tempCol = int(tempList[1])
                   tempSpot = int(tempList[2])
                   tempDia = int(tempList[7])
                   tempPFg = int(tempList[20])
                   tempFlag = int(tempList[53])
                   tempPBg = int(tempList[25])
                   diaArray[tempSpot-1][tempCol-1] = tempDia
                   if int(tempFlag) != 0:
                       flagArray[tempSpot-1][tempCol-1] = tempFlag
                   pFgArray[tempSpot-1][tempCol-1] = tempPFg
                   if pBgFileName == "":
                       pBgArray[tempSpot-1][tempCol-1] = tempPBg
               else:
                   tempCol = int(tempList[1])
                   tempSpot = int(tempList[2])
                   tempDia = int(tempList[7])
                   tempPFg = int(tempList[8])
                   tempFlag = int(tempList[37])
                   tempPBg = int(tempList[13])
                   diaArray[tempSpot-1][tempCol-1] = tempDia
                   if int(tempFlag) != 0:
                       flagArray[tempSpot-1][tempCol-1] = tempFlag
                   pFgArray[tempSpot-1][tempCol-1] = tempPFg
                   if pBgFileName == "":
                       pBgArray[tempSpot-1][tempCol-1] = tempPBg
                   
     buttonFile.close()

     chamberFile = open(chamberFileName,'r')
     lineIndex = 0
     for line in chamberFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
              pass
          else:
              tempList = line.split('\t')
              tempCol = int(tempList[1])
              tempSpot = int(tempList[2])
              tempChFg = int(tempList[8])
              chFgArray[tempSpot-1][tempCol-1] = tempChFg
                  
     chamberFile.close()

     DNAFile = open(DNAFileName,'r')
     lineIndex = 0
     for line in DNAFile:
          lineIndex = lineIndex + 1
          if lineIndex <= 32:
               pass
          else:
               tempList = line.split('\t')
               tempCol = int(tempList[1])
               tempSpot = int(tempList[2])
               tempDNAFg = int(tempList[8])
               tempDNABg = int(tempList[12])
               if griddingFlag == 0 and dGridFlag == 0:
                   tempFlag = int(tempList[53])
               else:
                   tempFlag = int(tempList[37])
               DNAFgArray[tempSpot-1][tempCol-1] = tempDNAFg
               DNABgArray[tempSpot-1][tempCol-1] = tempDNABg
               if int(tempFlag) != 0:
                    flagArray[tempSpot-1][tempCol-1] = tempFlag
     DNAFile.close()

     if pBgFileName != "":
          pBgFile = open(pBgFileName,'r')
          lineIndex = 0
          for line in pBgFile:
               lineIndex = lineIndex + 1
               if lineIndex <= 32:
                    pass
               else:
                    tempList = line.split('\t')
                    tempCol = int(tempList[1])
                    tempSpot = int(tempList[2])
                    if griddingFlag == 0:
                        tempPBg = int(tempList[25])
                    else:
                        tempPBg = int(tempList[13])
                    pBgArray[tempSpot-1][tempCol-1] = tempPBg
          pBgFile.close()

     if DNABgFileName != "":
          DNABgFile = open(DNABgFileName,'r')
          lineIndex = 0
          for line in DNABgFile:
               lineIndex = lineIndex + 1
               if lineIndex <= 32:
                    pass
               else:
                    tempList = line.split('\t')
                    tempCol = int(tempList[1])
                    tempSpot = int(tempList[2])
                    tempDNABg = int(tempList[12])
                    DNABgArray[tempSpot-1][tempCol-1] = tempDNABg
          DNABgFile.close()


     for m in range(0,numCols):
          for l in range(0,numSpots):
               outFile.write(str(l+1)+'\t')
               outFile.write(str(m+1)+'\t')
               outFile.write(str(diaArray[l][m])+'\t')
               outFile.write(str(flagArray[l][m])+'\t')
               outFile.write(str(pFgArray[l][m])+'\t')
               outFile.write(str(DNAFgArray[l][m])+'\t')
               outFile.write(str(pBgArray[l][m])+'\t')
               outFile.write(str(DNABgArray[l][m])+'\t')
               outFile.write(str(chFgArray[l][m])+'\n')
     outFile.close()
     
def concatGprFiles_v3(pFN,cFN,dFN,oFN,singleF=0,rlF=0,tbF=0):
    
    dF = open(dFN,'r')
    cF = open(cFN,'r')
     
    blockL,colL,rowL,diaL,flagL,pFL,pBL,dFL,dBL,cFL = [],[],[],[],[],[],[],[],[],[]
     
    # open up protein file and read in data
    lI = 0
    colsPerBlock = 0
    pF = open(pFN,'r')
    for line in pF:
        lI=lI+1
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
    lI,rI = 0,-1
    dF = open(dFN,'r')
    for line in dF:
        lI=lI+1
        if lI <= 32:
            pass
        else:
            rI=rI+1
            tempL = line.strip().split('\t')
            dFL.append(int(tempL[8]))
            dBL.append(int(tempL[13]))
            if int(tempL[37]) != 0:
                flagL[rI]=int(tempL[37])
    dF.close()
        
    # open up chamber DNA file and read in data
    lI,rI = 0,-1
    cF = open(cFN,'r')
    for line in cF:
        lI=lI+1
        if lI <= 32:
            pass
        else:
            rI=rI+1
            tempL = line.strip().split('\t')
            cFL.append(int(tempL[8]))
            if int(tempL[37]) != 0:
                flagL[rI]=int(tempL[37])
    cF.close()
    
    # if files were not gridded as a single block, renumber to fix this
    tempColL = []
    for a in range(0,len(blockL)):
        if singleF != 0:
            tempColL.append((blockL[a]-1)*colsPerBlock+colL[a])
        else:
            tempColL.append(colL[a])
            
    # figure out the total number of columns and rows
    numCols, numRows = 0,0
    for a in range(0,len(blockL)):
        if tempColL[a] > numCols:
            numCols = tempColL[a]
        if rowL[a] > numRows:
            numRows = rowL[a]
    
    # renumber columns in case file must be renumbered left to right
    outColL = []
    for a in range(0,len(blockL)):
        if rlF != 0:
            outColL.append(numCols+1-tempColL[a])
        else:
            outColL.append(tempColL[a])
    
    # renumber columns in case file must be renumbered top to bottom
    outRowL = []
    for a in range(0,len(blockL)):
        if tbF != 0:
            outRowL.append(numRows+1-rowL[a])
        else:
            outRowL.append(rowL[a])

    oF = open(oFN,'w')
    str1 = "Block\tColumn\tRow\tOutColumn\tOutRow\tDia\tFlag\tP_FG\tDNA_FG\tP_BG\tDNA_BG\tCH_FG\n"
    oF.write(str1)
    for a in range(0,len(blockL)):
        oL = [str(blockL[a]),str(colL[a]),str(rowL[a]),str(outColL[a]),str(outRowL[a]),str(diaL[a]),str(flagL[a]),\
              str(pFL[a]),str(dFL[a]),str(pBL[a]),str(dBL[a]),str(cFL[a])]
        oF.write('\t'.join(oL))
        oF.write('\n')

def concatGprFiles_QuakePrinter(pFN,cFN,dFN,oFN,singleF=0,rlF=0,tbF=0):
    
    dF = open(dFN,'r')
    cF = open(cFN,'r')
     
    blockL,colL,rowL,diaL,flagL,pFL,pBL,dFL,dBL,cFL = [],[],[],[],[],[],[],[],[],[]
     
    # open up protein file and read in data
    lI = 0
    colsPerBlock = 0
    pF = open(pFN,'r')
    for line in pF:
        lI=lI+1
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
    lI,rI = 0,-1
    dF = open(dFN,'r')
    for line in dF:
        lI=lI+1
        if lI <= 32:
            pass
        else:
            rI=rI+1
            tempL = line.strip().split('\t')
            dFL.append(int(tempL[8]))
            dBL.append(int(tempL[13]))
            if int(tempL[37]) != 0:
                flagL[rI]=int(tempL[37])
    dF.close()
        
    # open up chamber DNA file and read in data
    lI,rI = 0,-1
    cF = open(cFN,'r')
    for line in cF:
        lI=lI+1
        if lI <= 32:
            pass
        else:
            rI=rI+1
            tempL = line.strip().split('\t')
            cFL.append(int(tempL[8]))
            if int(tempL[37]) != 0:
                flagL[rI]=int(tempL[37])
    cF.close()
    
    # if files were not gridded as a single block, renumber to fix this
    tempColL = []
    for a in range(0,len(blockL)):
        if singleF != 0:
            tempColL.append((blockL[a]-1)*colsPerBlock+colL[a])
        else:
            tempColL.append(colL[a])
            
    # figure out the total number of columns and rows
    numCols, numRows = 0,0
    for a in range(0,len(blockL)):
        if tempColL[a] > numCols:
            numCols = tempColL[a]
        if rowL[a] > numRows:
            numRows = rowL[a]
    
    # renumber columns in case file must be renumbered left to right
    outColL = []
    for a in range(0,len(blockL)):
        if rlF != 0:
            outColL.append(numCols+1-tempColL[a])
        else:
            outColL.append(tempColL[a])
    
    # renumber columns in case file must be renumbered top to bottom
    outRowL = []
    for a in range(0,len(blockL)):
        if tbF != 0:
            outRowL.append(numRows+1-rowL[a])
        else:
            outRowL.append(rowL[a])

    oF = open(oFN,'w')
    str1 = "Block\tRow\tColumn\tOutRow\tOutColumn\tDia\tFlag\tP_FG\tDNA_FG\tP_BG\tDNA_BG\tCH_FG\tP_BSUB\tD_BSUB\tRATIO\tD_BSUB_N\tRATIO_N\n"
    oF.write(str1)
    for a in range(0,len(blockL)):
        pBSUB = pFL[a]-pBL[a]
        dBSUB = dFL[a]-dBL[a]
        ratio = float(dBSUB)/pBSUB
        dBSUBN = float(dBSUB)/cFL[a]
        ratioN = float(ratio)/cFL[a]
        oL = [str(blockL[a]),str(rowL[a]),str(colL[a]),str(outRowL[a]),str(outColL[a]),str(diaL[a]),str(flagL[a]),\
              str(pFL[a]),str(dFL[a]),str(pBL[a]),str(dBL[a]),str(cFL[a]),str(pBSUB),str(dBSUB),str(ratio),str(dBSUBN),str(ratioN)]
        oF.write('\t'.join(oL))
        oF.write('\n')

def renumberConcatFile(concatFileName):
     """This program just renumbers the data in a concat file so that column
     1 is on the right hand side of the tif file (instead of on the left)."""

     # first go through and save a copy of the concat file
     concatFile = open(concatFileName,'r')
     oldFileName = concatFileName[:-4]+"_OLD.txt"
     oldFile = open(oldFileName,'w')
     for line in concatFile:
          oldFile.write(line)
     oldFile.close()
     
     oldFile = open(oldFileName,'r')
     # first count the total number of columns in the file
     colD = {}
     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempCol = int(line.split("\t")[1].strip())
               if colD.has_key(tempCol):
                    pass
               else:
                    colD[tempCol] = 1
     numCols = len(colD)
     oldFile.close()

     # now go through and renumber the columns and rewrite the original file
     concatFile = open(concatFileName,'w')
     oldFile = open(oldFileName,'r')

     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               concatFile.write(line)
          else:
               tempList = line.split("\t")
               tempList[1]=str(numCols+1-int(tempList[1]))
               outString = "\t".join(tempList)
               concatFile.write(outString)
               
     concatFile.close()
     oldFile.close()

def renumberRowConcatFile(concatFileName):
     """This program just renumbers the data in a concat file so that row
     1 is on the bottom of the tif file (instead of on the top)."""

     # first go through and save a copy of the concat file
     concatFile = open(concatFileName,'r')
     oldFileName = concatFileName[:-4]+"_OLD.txt"
     oldFile = open(oldFileName,'w')
     for line in concatFile:
          oldFile.write(line)
     oldFile.close()
     
     oldFile = open(oldFileName,'r')
     # first count the total number of columns in the file
     rowD = {}
     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempRow = int(line.split("\t")[0].strip())
               if rowD.has_key(tempRow):
                    pass
               else:
                    rowD[tempRow] = 1
     numRows = len(rowD)
     oldFile.close()

     # now go through and renumber the columns and rewrite the original file
     concatFile = open(concatFileName,'w')
     oldFile = open(oldFileName,'r')

     lineIndex = 0
     for line in oldFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               concatFile.write(line)
          else:
               tempList = line.split("\t")
               tempList[0]=str(numRows+1-int(tempList[0]))
               outString = "\t".join(tempList)
               concatFile.write(outString)
               
     concatFile.close()
     oldFile.close()
          
def concatFileToLists(concatFileName):
     """This program takes a concatenated Genepix results file
     and creates dictionaries of all of the data for further analysis."""

     rowList,colList,diaList,flagList = [],[],[],[]
     pFgList,DNAFgList,pBgList,DNABgList,chFgList = [],[],[],[],[]

     inFile = open(concatFileName,'r')
     lineIndex = 0
     
     for line in inFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempList = line.split('\t')
               rowList.append(int(tempList[0]))
               colList.append(int(tempList[1]))
               diaList.append(float(tempList[2]))
               flagList.append(float(tempList[3]))
               pFgList.append(float(tempList[4]))
               DNAFgList.append(float(tempList[5]))
               pBgList.append(float(tempList[6]))
               DNABgList.append(float(tempList[7]))
               chFgList.append(float(tempList[8]))

     listOfLists = [rowList,colList,diaList,flagList,pFgList,DNAFgList,pBgList,DNABgList,chFgList]
     return listOfLists

def concatFileToLists_v2(concatFileName):
     """This program takes a concatenated Genepix results file
     and creates dictionaries of all of the data for further analysis."""
     
     blockL,oRL,oCL = [],[],[]
     rowL,colL,diaL,flagL = [],[],[],[]
     pFL,dFL,pBL,dBL,cFL = [],[],[],[],[]

     inFile = open(concatFileName,'r')
     lineIndex = 0
     
     for line in inFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempL = line.split('\t')
               blockL.append(int(tempL[0]))
               oRL.append(int(tempL[1]))
               oCL.append(int(tempL[2]))
               rowL.append(int(tempL[3]))
               colL.append(int(tempL[4]))
               diaL.append(float(tempL[5]))
               flagL.append(float(tempL[6]))
               pFL.append(float(tempL[7]))
               dFL.append(float(tempL[8]))
               pBL.append(float(tempL[9]))
               dBL.append(float(tempL[10]))
               cFL.append(float(tempL[11]))

     return blockL,oRL,oCL,rowL,colL,diaL,flagL,pFL,dFL,pBL,dBL,cFL

def concatFileToLists_v3(concatFileName):
     """This program takes a concatenated Genepix results file
     and creates dictionaries of all of the data for further analysis."""
     
     blockL,oRL,oCL = [],[],[]
     rowL,colL,diaL,flagL = [],[],[],[]
     pFL,dFL,pBL,dBL,cFL = [],[],[],[],[]

     inFile = open(concatFileName,'r')
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

     return blockL,oRL,oCL,rowL,colL,diaL,flagL,pFL,dFL,pBL,dBL,cFL

def concatFileToLists_QuakePrinter(concatFileName):
     """This program takes a concatenated Genepix results file
     and creates dictionaries of all of the data for further analysis."""
     
     blockL,oRL,oCL = [],[],[]
     rowL,colL,diaL,flagL = [],[],[],[]
     pFL,dFL,pBL,dBL,cFL = [],[],[],[],[]
     oL = []

     inFile = open(concatFileName,'r')
     lineIndex = 0
     
     for line in inFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempL = line.split('\t')
               blockL.append(int(tempL[0]))
               oRL.append(int(tempL[1]))
               oCL.append(int(tempL[2]))
               rowL.append(int(tempL[3]))
               colL.append(int(tempL[4]))
               diaL.append(float(tempL[5]))
               flagL.append(float(tempL[6]))
               pFL.append(float(tempL[7]))
               dFL.append(float(tempL[8]))
               pBL.append(float(tempL[9]))
               dBL.append(float(tempL[10]))
               cFL.append(float(tempL[11]))
               oL.append(int(tempL[17]))

     return blockL,oRL,oCL,rowL,colL,diaL,flagL,pFL,dFL,pBL,dBL,cFL,oL


def zeroFlaggedSpots(flagList,pFgList,DNAFgList,pBgList,DNABgList,chFgList):
    """This program checks to see if any spots have non-zero flags.
    If they do, the program enters 'NaN' for their values."""
       
    newPFg,newDNAFg,newPBg,newDNABg,newChFg = [],[],[],[],[]
    listOfLists = [pFgList,DNAFgList,pBgList,DNABgList,chFgList]
    listOfNewLists = [newPFg,newDNAFg,newPBg,newDNABg,newChFg]
    
    for m in range(0,len(flagList)):
        if int(flagList[m]) != 0:
            for n in range(0,len(listOfNewLists)):
                listOfNewLists[n].append(N.NaN)
        else:
            for n in range(0,len(listOfNewLists)):
                listOfNewLists[n].append(listOfLists[n][m])

    return flagList,newPFg,newDNAFg,newPBg,newDNABg,newChFg

def zeroNoDNASpots(pFgList,DNAFgList,pBgList,DNABgList,chFgList,chTh):
    """This program checks to see if any spots have chamber intensities below
    a user-defined threshold ."""
       
    newPFg,newDNAFg,newPBg,newDNABg,newChFg = [],[],[],[],[]
    listOfLists = [pFgList,DNAFgList,pBgList,DNABgList,chFgList]
    listOfNewLists = [newPFg,newDNAFg,newPBg,newDNABg,newChFg]
    
    for m in range(0,len(chFgList)):
        if int(chFgList[m]) < chTh:
            for n in range(0,len(listOfNewLists)):
                listOfNewLists[n].append(N.NaN)
        else:
            for n in range(0,len(listOfNewLists)):
                listOfNewLists[n].append(listOfLists[n][m])

    return newPFg,newDNAFg,newPBg,newDNABg,newChFg

def zeroNoDNASpots_v2(pBSub,DNABSub,chBSub,zeroTh):
    """This program checks to see if any spots have chamber intensities below
    a user-defined threshold ."""
       
    newPBSub,newDNABSub,newChBSub = [],[],[]
    #print "here!"
    for n in range(0,len(chBSub)):
        #print n
        if chBSub[n] <= zeroTh:
            #print "too low!"
            newPBSub.append(N.NaN)
            newDNABSub.append(N.NaN)
            newChBSub.append(N.NaN)
        else:
            #print "high enough!"
            newPBSub.append(pBSub[n])
            newDNABSub.append(DNABSub[n])
            newChBSub.append(chBSub[n])
    
    return newPBSub,newDNABSub,newChBSub

def backgroundSubtract(pFgList,DNAFgList,pBgList,DNABgList,chFgList,pTh=1,DNATh=1,chTh=1,nanFlag=0):
    """This program takes a list of dictionaries (see concatFileToDict)
    and parses them into data by oligo.  Any values below 0 are converted
    to 0."""

    pFgArray = N.array(pFgList)
    pBgArray = N.array(pBgList)
    DNAFgArray = N.array(DNAFgList)
    DNABgArray = N.array(DNABgList)
    chFgArray = N.array(chFgList)

    pBSubArray = pFgArray - pBgArray
    DNABSubArray = DNAFgArray - DNABgArray
    chBSubArray = chFgArray - DNABgArray
    
    pBSubList = pBSubArray.tolist()
    DNABSubList = DNABSubArray.tolist()
    chBSubList = chBSubArray.tolist()
     
    newPBSubList, newDNABSubList, newChBSubList = [], [], []
    listOfLists = [pBSubList,DNABSubList,chBSubList]
    listOfNewLists = [newPBSubList,newDNABSubList,newChBSubList]
    listOfThresholds = [pTh,DNATh,chTh]

    for m in range(0,len(listOfLists)):
        for n in range(0,len(listOfLists[m])):
            if int(listOfLists[m][n]) > int(listOfThresholds[m]):
                listOfNewLists[m].append(listOfLists[m][n])
            else:
                if N.isnan(listOfLists[m][n]) == True:
                    listOfNewLists[m].append(N.NaN)
                else:
                    if nanFlag == 1:
                        listOfNewLists[m].append(N.NaN)
                    else:
                        listOfNewLists[m].append(int(listOfThresholds[m]))
                    
    return newPBSubList,newDNABSubList,newChBSubList

def backgroundSubtract_v2(pFg,pBg,DNAFg,DNABg,chFg,chBg,pTh=0,dTh=0,cTh=0,nanF=0):
    
    pBSub,dBSub,chBSub = [],[],[]
    
    for a in range(0,len(pFg)):
        if N.isnan(pFg[a]) or N.isnan(pBg[a]) or N.isnan(DNAFg[a]) or N.isnan(DNABg[a]) or N.isnan(chFg[a]) or N.isnan(chBg[a]):
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
                    

def writeThresholdsToFile(fileName,pTh,DNATh,chTh):
     """This program just records what thresholds were used in the analysis and writes
     them to file."""

     thFile = open(fileName,'w')
     thFile.write("Protein threshold = "+str(pTh)+"\n")
     thFile.write("DNA threshold = "+str(DNATh)+"\n")
     thFile.write("Chamber threshold = "+str(chTh)+"\n")
     thFile.close()

def calculateRatios(pBSubList,DNABSubList,chBSubList):
    """This program calculates (1) fluorescence intensity ratios
    and (2) normalized fluorescence intensity ratios."""

    ratioList,ratioNormList,ratioNormNormList = [],[],[]

    newChBSubList = []
     
    for a in chBSubList:
        if N.isnan(float(a)) == False:
            newChBSubList.append(a)
    chBSubMean = N.mean(newChBSubList)

    for n in range(0,len(pBSubList)):
        if N.isnan(pBSubList[n]) == False and pBSubList[n] != 0:
            tempRatio=float(DNABSubList[n])/float(pBSubList[n])
            if chBSubList[n]>0:
                tempRatioNorm=(float(tempRatio)/float(chBSubList[n]))
                tempRatioNormNorm=float(tempRatioNorm)*float(chBSubMean)
            else:
                tempRatioNorm = N.NaN
                tempRatioNormNorm = N.NaN
        else:
            tempRatio=N.NaN
            tempRatioNorm=N.NaN
            tempRatioNormNorm=N.NaN
        ratioList.append(tempRatio)
        ratioNormList.append(tempRatioNorm)
        ratioNormNormList.append(tempRatioNormNorm)
            

    return ratioList,ratioNormList,ratioNormNormList,chBSubMean

def normalizeValues(inList,analysisDir,outFileName,dataLabel,xLabel,inLo,inHi,inBin):
    """This program normalizes values so that they are centered
    around zero."""
    
    outFileName = analysisDir+outFileName
    fitUtils.gaussianFitHistogram(inList,outFileName,dataLabel,xLabel=xLabel,loBound=inLo,hiBound=inHi,binSize=inBin)
    outParams = fitUtils.gaussianFitParams(outFileName)
    
    normList = []
    for n in range(0,len(inList)):
        normList.append(float(inList[n])-float(outParams[1]))
    return normList

def normalizeValues_v2(inList,analysisDir,outFileName,inHi=0,numBins=100):
    """This program normalizes values so that they are centered
    around zero using python least squares minimization."""
    
    outFileName = analysisDir+outFileName
    cleanL = []
    for a in inList:
        if N.isnan(a) == False:
            cleanL.append(a)
    
    inHi = 3*N.std(cleanL)
    inLo = -inHi
           
    fitParams = fitUtils.gaussianFit(cleanL,numBins=numBins,figFileName=outFileName,loBound=inLo,hiBound=inHi)
    rFitMean, rFitStd = fitParams[1], fitParams[2]
    
    normL = []
    for a in inList:
        if N.isnan(a) == False:
            normL.append(a-rFitMean)
        else:
            normL.append(N.nan)

    return normL

def normalizeMaxValue(inList):
    """This program values so that the maximum is 1."""
    
    normList = []
    maxVal = 0
    for n in inList:
        if N.isnan(n) == False and n > maxVal:
            maxVal = n
    for n in range(0,len(inList)):
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
                    numOligoD[oligoD[item]]=1
     numOligos = len(numOligoD)-1

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
     
def dataArray(spot2OligoFileName,colList,rowList,itemList):
     """This program creates an array of the data in itemList
     with each row representing data from a single oligo."""

     oligoD = makeSpot2OligoDict(spot2OligoFileName)
     numOligos = calcNumOligos(spot2OligoFileName)+1
     numSpotsPerOligo = calcNumSpotsPerOligo(spot2OligoFileName)

     dimensions = (numOligos,numSpotsPerOligo)
     #print "dimensions = "+str(dimensions)
     outArray = N.zeros(dimensions,float)
     
     #correct data array so that values start as NaN
     for n in range(0,numOligos):
         for m in range(0,numSpotsPerOligo):
             outArray[n][m] = N.NaN

     repIndexD = {}
     for n in range(0,len(itemList)):
          spotIndex = str(colList[n])+"."+str(rowList[n])
          oligo = oligoD[spotIndex]
          if oligo == 'Empty' or oligo == 'EMPTY':
               pass
          else:
               oligoIndex = int(oligo.split("_")[1].split(".")[0])-1
               #print "oligoIndex = "+str(oligoIndex)
               if repIndexD.has_key(oligo):
                    arrayIndex = repIndexD[oligo]
                    repIndexD[oligo]=(repIndexD[oligo]+1)
               else:
                    arrayIndex = 0
                    repIndexD[oligo]=1

          if arrayIndex < numSpotsPerOligo:
               outArray[oligoIndex][arrayIndex]=itemList[n]

     return outArray

def dataArrayPT(spot2OligoFileName,colList,rowList,itemList):
     """This program creates an array of the data in itemList
     with each row representing data from a single oligo."""

     oligoD = makeSpot2OligoDict(spot2OligoFileName)
     numOligos = 8
     numSpotsPerOligo = 12
     oligoNumD = {'19':0,'36':1,'100':2,'143':3,'194':4,'210':5,'235':6,'243':7}
     concD = {'5':0,'2.5':1,'1.25':2,'0.625':3}
     enzymeD = {'N':0,'E':1,'EC':2}

     dimensions = (numOligos,numSpotsPerOligo)
     #print "dimensions = "+str(dimensions)
     #print "itemList length = "+str(len(itemList))
     
     repArrayList = []
     for n in range(0,6):
         outArray = N.zeros(dimensions,float)
         #print "n = "+str(n)
         #print outArray
         repArrayList.append(outArray)

     repIndexD = {}
     #print repArrayList
     
     for n in range(0,len(itemList)):
          spotIndex = str(colList[n])+"."+str(rowList[n])
          condition = oligoD[spotIndex]
          
          if condition.split("_")[0] == 'EMPTY':
              print "This well is empty!"
              pass
          else:
              if repIndexD.has_key(condition):
                  repIndexD[condition]=repIndexD[condition]+1
              else:
                  repIndexD[condition] = 1    
              
              oligoIndex = oligoNumD[condition.split("_")[1]]
              enzymeIndex = enzymeD[condition.split("_")[2]]
              concIndex = concD[condition.split("_")[3]]
              horizontalIndex = concIndex*len(enzymeD)+enzymeIndex
              
              #print "n = "+str(n)
              #print "oligoIndex = "+str(oligoIndex)
              #print "horizontalIndex = "+str(horizontalIndex)
              #print "repIndex = "+str(repIndexD[condition])
              repArrayList[repIndexD[condition]-1][oligoIndex][horizontalIndex]=itemList[n]
              
     return repArrayList

def avgDataArrayPT(arrayList):
    
    arrayShape = arrayList[0].shape
    
    outArray = N.zeros(arrayShape,float)
    
    for item in arrayList:
        outArray = outArray + item
    
    print len(arrayList)
    outArray = outArray/len(arrayList)
    
    return outArray

def removeOutliersFromArray(dataArray):
    
    for n in range(0,dataArray.shape[0]):
        tempList = dataArray[n,:].tolist()
        newList = statsUtils.removeOutliers(tempList)
        for m in range(0,dataArray.shape[1]):
            dataArray[n][m]=newList[m]
            
    return dataArray
     
def avgData(dataArray):
    """This subroutine returns an array containing the average
    values for each oligo."""
    
    avgList,medList = [],[]
    
    for n in range(0,dataArray.shape[0]):
        tempList = dataArray[n,:].tolist()
        newList = []
        for item in tempList:
            if N.isnan(item) == False and item != 0:
                newList.append(item)
            else:
                pass
            
        tempAvg = N.mean(newList)
        tempMed = statsUtils.calcMed(newList)
        avgList.append(float(tempAvg))
        medList.append(float(tempMed))
        
    return avgList,medList

def stdData(dataArray):
    """This subrouting returns an array containing the std
    values for each oligo."""
     
    stdList = []
    
    for n in range(0,dataArray.shape[0]):
        tempList = dataArray[n,:].tolist()
        newList = []
        for item in tempList:
            if N.isnan(item) == False:
                newList.append(item)
            else:
                pass
            
        tempStd = N.std(newList)
        stdList.append(float(tempStd))
        
    return stdList
 
def extractColumnData(concatFileName,fileNameRoot,analysisDir,rows,cols,inputData,dataName,yLabel,yMin):
    """This program is designed to output text files and graphs
    for each column of data to allow us to compare our analyses by
    eye with the computer analyses."""

    # first determine the number of spots per column
    numCols, spotsPerCol = determineDimensions(concatFileName)

    # create an array of all possible spots
    dimensions = (spotsPerCol,numCols)
    spotData = N.zeros(dimensions)

    # go through data and put it in the right place in the array
    for n in range(0,len(inputData)):
        spotData[(rows[n]-1)][(cols[n]-1)]=inputData[n]

    # now slice the data and create text files and graphs for the output by column
    spotIndex = arange(1,(spotsPerCol+1))
    colList, avgList = [],[]
    for n in range(0,numCols):
        colNum = n+1
        colList.append(colNum)
        colSlice = spotData[:,n]
        colAvg = N.mean(colSlice)
        avgList.append(colAvg)
        # output a text file
        outFileRoot = fileNameRoot+'_Col'+str(n+1)
        outFileName = outFileRoot+'.txt'
        outFile = open(outFileName,'w')
        for m in range(0,spotsPerCol):
            # write out the spot index and the data
            outFile.write(str(spotIndex[m])+'\t')
            outFile.write(str(spotData[m][n])+'\n')
        outFile.close()
        # output a graph
        xLabel = "Spot Index"
        #plotUtils.createAndSaveFig(spotIndex,colSlice,xLabel=xLabel,yLabel=yLabel,figFileRoot=outFileRoot,xMin=0,xMax=spotsPerCol,yMin=yMin)
        tempYList = []
        
    outFileName = analysisDir+dataName+'.txt'
    outFile = open(outFileName,'w')
    outFile.write('Col\t'+dataName+'_Avg\n')
    for n in range(0,len(colList)):
        outFile.write(str(colList[n])+'\t'+str(avgList[n])+'\n')
    outFile.close()
          
def extractHighSpotInfo(thresh,inData,rows,cols,oligoD):
     """This program extracts the oligo name for any spot
     that exceeds a certain threshold for some type of data."""

     oList,valList = [],[]

     for n in range(0,len(inData)):
          spot = rows[n]
          col = cols[n]
          spotIndex = str(col)+"."+str(spot)
          if oligoD[spotIndex] == 'Empty':
               pass
          else:
               if float(inData[n]) > float(thresh):
                    oList.append(oligoD[spotIndex])
                    valList.append(inData[n])

     return oList,valList
 
def determineDimensions(concatFileName):
     """This program reads in a concat file and automatically determines
     the number of spots in each column."""

     concatFile = open(concatFileName,'r')
     spotsPerCol,numCols = 1,1

     lineIndex = 0
     for line in concatFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempList = line.split('\t')
               currSpot = int(tempList[0])
               currCol = int(tempList[1])
               if currSpot > spotsPerCol:
                    spotsPerCol = currSpot
               if currCol > numCols:
                    numCols = currCol

     return numCols,spotsPerCol
 
def determineDimensions_v2(concatFileName):
     """This program reads in a concat file and automatically determines
     the number of spots in each column."""

     concatFile = open(concatFileName,'r')
     spotsPerCol,numCols = 1,1

     lineIndex = 0
     for line in concatFile:
          lineIndex = lineIndex + 1
          if lineIndex == 1:
               pass
          else:
               tempList = line.split('\t')
               currSpot = int(tempList[3])
               currCol = int(tempList[4])
               if currSpot > spotsPerCol:
                    spotsPerCol = currSpot
               if currCol > numCols:
                    numCols = currCol

     return numCols,spotsPerCol

def determineDimensions_v3(concatFileName):
     """This program reads in a concat file and automatically determines
     the number of spots in each column."""

     concatFile = open(concatFileName,'r')
     spotsPerCol,numCols = 1,1

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

     return numCols,spotsPerCol
 
 
def makeOligoNum2SeqDict(oligoFileName):
    
    """This program reads in a file containing oligo names and sequences and creates a dictionary linking them."""

    oligoDict = {}
    oligoFile = open(oligoFileName,'r')
    for line in oligoFile:
        tempList = line.split('\t')
        oligoName = tempList[0].strip()
        oligoSeq = tempList[1].strip()
        oligoDict[oligoName]=oligoSeq
    oligoFile.close()
    
    return oligoDict

def makeOligoNum2RatioDicts(resultsFileName):
    """This program reads in a results file and creates dictionaries linking oligo number to ratios and normalized ratios."""
    
    ratioDict, ratioNormDict = {},{}
    resultsFile = open(resultsFileName,'r')
    lineIndex = 0
    for line in resultsFile:
        if lineIndex == 0:
            pass
        else:
            tempList = line.split('\t')
            oligoNum = tempList[0].split("_")[1].strip()
            ratioDict[oligoNum]=tempList[6].strip()
            ratioNormDict[oligoNum]=tempList[10].strip()
        lineIndex = lineIndex + 1
    resultsFile.close()
    
    return ratioDict, ratioNormDict

def outputAverageValuesByNMer(outFileName,nMerDict,oligoDict):
    
    # create empty dictionaries
    ratioDict, ratioNormDict = {},{}
    
    # create the output file
    outFile = open(outFileName,'w')
    outFile.write('NMerSeq\tRatioAvg\tRatioStd\tRatioNormAvg\tRatioNormStd\tnumPoints\n')

    # go through the Nmer dictionary and create a list of where each oligo appears
    for x in nMerDict.keys():
        oligoLocList = []
        ratio, ratioNorm = [],[]
        oligoRC = sequence.reverseComplement(nMerDict[x])
        for y in oligoDict.keys():
            if oligoDict[y].count(nMerDict[x]) > 0:
                if oligoLocList.count(y) == 0:
                    oligoLocList.append(y)
            if x != oligoRC:
                if oligoDict[y].count(oligoRC) > 0:
                    if oligoLocList.count(y) == 0:
                        oligoLocList.append(y)
                        
        # now go through these and calculate the averages of all oligos with the nmer and all oligos w/o the nmer
        for item in oligoLocList:
            ratio.append(float(ratioDict[item]))
            ratioNorm.append(float(ratioNormDict[item]))
  
        avgRatio = N.mean(ratio)
        stdRatio = N.std(ratio)
        avgRatioNorm = N.mean(ratioNorm)
        stdRatioNorm = N.std(ratioNorm)
        numPts = len(ratio)
        
        outFile.write(nMerDict[x]+'\t'+str(avgRatio)+'\t'+str(stdRatio)+'\t'+str(avgRatioNorm)+'\t'+str(stdRatioNorm)+'\t'+str(numPts)+'\n')
    
    outFile.close()

def createRankDict(resultsDict):
    
    # first go through the results dictionary, create a list, and sort it
    sortingList = []
    for x in resultsDict.keys():
        tempList = [x,resultsDict[x]]
        sortingList.append(tempList)
        
    sortedList = sorted(sortingList,key=operator.itemgetter(1))
    
    # create a dictionary linking oligo numbers and ranks
    rankDict = {}
    for n in range(0,len(sortedList)):
        rankDict[sortedList[n][0]] = n
    
    return rankDict

def outputRankSumsByNMer(nMerDict,oligoDict,rankDict):
    
    outRankDict = {}
    
    # go through the Nmer dictionary and create a list of where each oligo appears
    for x in nMerDict.keys():
        oligoLocList = []
        oligoRC = sequence.reverseComplement(nMerDict[x])
        for y in oligoDict.keys():
            if oligoDict[y].count(nMerDict[x]) > 0:
                if oligoLocList.count(y) == 0:
                    oligoLocList.append(y)
            if x != oligoRC:
                if oligoDict[y].count(oligoRC) > 0:
                    if oligoLocList.count(y) == 0:
                        oligoLocList.append(y)
                        
        # now go through these and create a new list containing the ranks of all of these oligos
        rankYes,rankNo = [],[]
        for y in oligoDict.keys():
            if y in oligoLocList:
                rankYes.append(int(rankDict[y]))
            else:
                rankNo.append(int(rankDict[y]))
            
        outRankDict[nMerDict[x]]=[sum(rankYes),len(rankYes),sum(rankNo),len(rankNo)]
    
    return outRankDict

def outputStandardBaseList(motif):
    """This subroutine takes a list containing nonstandard DNA base characters and outputs a list of all possible standard base possibilities."""
    
    baseDict = {'-':['A','C','G','T'],'A':'A','C':'C','T':'T','G':'G','R':['A','G'],'Y':['C','T'],'M':['C','A'],'K':['T','G'],'W':['T','A'],'S':['C','G'],'B':['C','T','G'],'D':['A','T','G'],'H':['A','T','C'],'V':['A','C','G'],'N':['A','C','G','T']}
    
    funnyBaseLoc = []
    for n in range(0,len(motif)):
        if motif[n] not in ['A','C','G','T']:
            funnyBaseLoc.append(n)
    
    numRepeats = 1
    for n in range(0,len(funnyBaseLoc)):
        numRepeats = numRepeats*len(baseDict[(motif[funnyBaseLoc[n]])])
    
    dummyList = []
    for n in range(0,len(motif)):
        dummyList.append(motif[n])
    
    listForArray = []
    for n in range(0,numRepeats):
        listForArray.append(dummyList)
    outArray = N.array(listForArray)
    
    funnyBaseIndex = 0
    numLastReps = 1    
    for n in funnyBaseLoc:
        funnyBaseIndex = funnyBaseIndex + 1
        for m in range(0,numRepeats):
            outArray[m][n] = baseDict[motif[n]][(m/numLastReps)%(len(baseDict[motif[n]]))]
        numLastReps = numLastReps*len(baseDict[motif[n]])

    outList = []
    for n in range(0,numRepeats):
        tempSeq = ''
        for m in range(0,len(motif)):
            tempSeq=tempSeq+(outArray[n][m])
        outList.append(tempSeq)
    
    return outList

def outputStandardBaseListAndNumFunnyBases(motif):
    """This subroutine takes a list containing nonstandard DNA base characters and outputs a list of all possible standard base possibilities."""
    
    baseDict = {'-':['A','C','G','T'],'A':'A','C':'C','T':'T','G':'G','R':['A','G'],'Y':['C','T'],'M':['C','A'],'K':['T','G'],'W':['T','A'],'S':['C','G'],'B':['C','T','G'],'D':['A','T','G'],'H':['A','T','C'],'V':['A','C','G'],'N':['A','C','G','T']}
    
    funnyBaseLoc = []
    for n in range(0,len(motif)):
        if motif[n] not in ['A','C','G','T']:
            funnyBaseLoc.append(n)
    
    num2Output = 1
    for n in range(0,len(motif)):
        if motif[n] not in ['-','A','C','G','T']:
            num2Output = num2Output*len(baseDict[motif[n]])
    
    numRepeats = 1
    for n in range(0,len(funnyBaseLoc)):
        numRepeats = numRepeats*len(baseDict[(motif[funnyBaseLoc[n]])])
    
    dummyList = []
    for n in range(0,len(motif)):
        dummyList.append(motif[n])
    
    listForArray = []
    for n in range(0,numRepeats):
        listForArray.append(dummyList)
    outArray = N.array(listForArray)
    
    funnyBaseIndex = 0
    numLastReps = 1    
    for n in funnyBaseLoc:
        funnyBaseIndex = funnyBaseIndex + 1
        for m in range(0,numRepeats):
            outArray[m][n] = baseDict[motif[n]][(m/numLastReps)%(len(baseDict[motif[n]]))]
        numLastReps = numLastReps*len(baseDict[motif[n]])

    outList = []
    for n in range(0,numRepeats):
        tempSeq = ''
        for m in range(0,len(motif)):
            tempSeq=tempSeq+(outArray[n][m])
        outList.append(tempSeq)
    
    return outList,num2Output


def outputInfoFromConcatFile(concatFileName,spot2OligoFileName,pTh=1,DNATh=1,chTh=1,nanFlag=0,chFlag=0):
    
    # get lists from concat file
    iList = concatFileToLists(concatFileName)

    # unpack iList
    rows = iList[0]
    cols = iList[1]
    flags = iList[3]
    pFg = iList[4]
    DNAFg = iList[5]
    pBg = iList[6]
    DNABg = iList[7]
    chFg = iList[8]

    # deal with flagged spots
    flags,pFg,DNAFg,pBg,DNABg,chFg = zeroFlaggedSpots(flags,pFg,DNAFg,pBg,DNABg,chFg)

    # create pBSub, DNABSub, and chBSub lists
    pBSub, DNABSub, chBSub = backgroundSubtract(pFg,DNAFg,pBg,DNABg,chFg,pTh=pTh,DNATh=DNATh,chTh=chTh,nanFlag=nanFlag)
    
    # convert all spots with chamber intensities below a threshold to NAN values
    if chFlag != 0:
        pBSub,DNABSub,chBSub = zeroNoDNASpots_v2(pBSub, DNABSub, chBSub, chFlag)

    # create ratio list
    ratio = calculateRatios(pBSub,DNABSub,chBSub)[0]
    
    # create normalized ratio list (just in case of printing problems)
    ratioNorm = []
    for n in range(0,len(ratio)):
        if chBSub[n] > 100:
            currRatioNorm = float(ratio[n])/float(chBSub[n])
        else:
            currRatioNorm = N.NaN
        ratioNorm.append(currRatioNorm)

    # create dictionaries linking spot index to oligo name and dilution
    oligoD = makeSpot2OligoDict(spot2OligoFileName)
    
    # create list of oligo numbers
    oligoNum = []
    for n in range(0,len(rows)):
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
        
    return rows,cols,flags,pFg,DNAFg,pBg,DNABg,chFg,pBSub,DNABSub,chBSub,ratio,ratioNorm,oligoNum

def outputInfoFromConcatFile_v2(concatFileName,spot2OligoFileName,pTh=100,DNATh=1,chTh=1,nanFlag=0):
    
    # get lists from concat file
    blocks,oRows,oCols,rows,cols,dia,flags,pFL,dFL,pBL,dBL,cFL = concatFileToLists_v3(concatFileName)

    # deal with flagged spots
    flags,pFg,DNAFg,pBg,DNABg,chFg = zeroFlaggedSpots(flags,pFL,dFL,pBL,dBL,cFL)

    # create pBSub, DNABSub, and chBSub lists
    pBSub,DNABSub,chBSub = backgroundSubtract_v2(pFg,pBg,DNAFg,DNABg,chFg,DNABg,pTh=pTh,dTh=DNATh,cTh=chTh,nanF=nanFlag)
    
    # create ratio list
    ratio = calculateRatios(pBSub,DNABSub,chBSub)[0]
    
    # create normalized ratio list (just in case of printing problems)
    ratioNorm = []
    for n in range(0,len(ratio)):
        if chBSub[n] > 100:
            currRatioNorm = float(ratio[n])/float(chBSub[n])
        else:
            currRatioNorm = N.NaN
        ratioNorm.append(currRatioNorm)

    # create dictionaries linking spot index to oligo name and dilution
    oligoD = makeSpot2OligoDict(spot2OligoFileName)
    
    # create list of oligo numbers
    oligoNum = []
    for n in range(0,len(rows)):
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

    return blocks,oRows,oCols,rows,cols,flags,pFg,DNAFg,pBg,DNABg,chFg,pBSub,DNABSub,chBSub,ratio,ratioNorm,oligoNum

def outputInfoFromConcatFile_v3(concatFileName,spot2OligoFileName,pTh=100,DNATh=1,chTh=1,nanFlag=0):
    
    # get lists from concat file
    blocks,oRows,oCols,rows,cols,dia,flags,pFL,dFL,pBL,dBL,cFL = concatFileToLists_v3(concatFileName)

    # deal with flagged spots
    flags,pFg,DNAFg,pBg,DNABg,chFg = zeroFlaggedSpots(flags,pFL,dFL,pBL,dBL,cFL)

    # create pBSub, DNABSub, and chBSub lists
    pBSub,DNABSub,chBSub = backgroundSubtract_v2(pFg,pBg,DNAFg,DNABg,chFg,DNABg,pTh=pTh,dTh=DNATh,cTh=chTh,nanF=nanFlag)
    
    # create ratio list
    ratio = calculateRatios(pBSub,DNABSub,chBSub)[0]
    
    # create normalized ratio list (just in case of printing problems)
    ratioNorm = []
    for n in range(0,len(ratio)):
        if chBSub[n] > 100:
            currRatioNorm = float(ratio[n])/float(chBSub[n])
        else:
            currRatioNorm = N.NaN
        ratioNorm.append(currRatioNorm)

    # create dictionaries linking spot index to oligo name and dilution
    oligoD = makeSpot2OligoDict(spot2OligoFileName)
    
    # create list of oligo numbers
    oligoNum = []
    for n in range(0,len(rows)):
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

    return blocks,oRows,oCols,rows,cols,flags,pFg,DNAFg,pBg,DNABg,chFg,pBSub,DNABSub,chBSub,ratio,ratioNorm,oligoNum


def createDictFromSeqFile(seqFileName,truncFlag=0):
    """This subroutine creates a dictionary from oligo number and sequence data."""
    
    seqFile = open(seqFileName,'r')
    seqDict = {'0':''}
    for line in seqFile:
        tempList = line.split("\t")
        if truncFlag == 0:
            seqDict[tempList[0]]=tempList[1].strip()
        else:
            seqDict[tempList[0]]=tempList[1].strip()[3:-15]

    return seqDict

def getRNSDParamsFromFile(rFileName):
    
    nameL, rMeanL, rStdL, rNSDL = [],[],[],[]
    inFile = open(rFileName,'r')
    lineIndex = 0
    for line in inFile:
        lineIndex = lineIndex + 1
        if lineIndex != 1:
            tempList = line.split('\t')
            nameL.append(tempList[0].strip())
            rMeanL.append(float(tempList[1].strip()))
            rStdL.append(float(tempList[2].strip()))
            rNSDL.append(float(tempList[3].strip()))
    inFile.close()
    
    return nameL,rMeanL,rStdL,rNSDL

def determineChInt(pix,oNum,col,row,xPos,yPos,oDir,dia=40,win=10):
    
    oL = []    
    for a in range(int(xPos-dia/2),int(xPos+dia/2)):
        for b in range(int(yPos-dia/2),int(yPos+dia/2)):
            if N.sqrt((a-xPos)**2-(b-yPos)**2) <= 0.5*dia:
                oL.append(pix[a,b])
            else:
                pass
                
    curMed = statsUtils.calcMedNoNaN(oL)
    if curMed > 30000:
        hOut = plt.hist(oL,bins=100,range=(25000,65000),facecolor='b',hold=True)
    elif curMed > 2000 and curMed < 10000:
        hOut = plt.hist(oL,bins=200,range=(1000,10000),facecolor='b',hold=True)
    elif curMed < 2000:
        hOut = plt.hist(oL,bins=200,range=(300,2000),facecolor='b',hold=True)
    else:
        hOut = plt.hist(oL,bins=200,range=(1000,50000),facecolor='b',hold=True)            
            
    # ok, now let's try and implement jiashun's idea of binning and calculating the median
    winMed,winBin = [],[]
    for n in range(0,len(hOut[0])-win+1):
        curMean = stats.mean(hOut[0][n:(n+win-1)])
        winMed.append(int(curMean))
        winBin.append(int(hOut[1][n+(win/2)]))
            
    binW = winBin[1]-winBin[0]
    hS = plt.bar(winBin,winMed,width=binW,color='g')
    plt.savefig(oDir+str(oNum)+'_'+str(col)+'_'+str(row)+'.png',dpi=150)
    plt.clf()

    # figure out the location of the maximum
    winMax,maxInd = 0,0
    for b in range(0,len(winMed)):
        if winMed[b] > winMax:
            winMax = winMed[b]
            maxInd = b
        
    # figure out what intensity this corresponds to and write to file
    maxInt = hOut[1][maxInd+win/2]

    return maxInt


