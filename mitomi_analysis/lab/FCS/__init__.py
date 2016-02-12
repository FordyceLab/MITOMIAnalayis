#!/usr/local/bin/python
#
#
# 	$Id: __init__.py,v 1.1.1.1 2008/03/10 18:48:55 kael Exp $	
#
import sys,re
from scipy import *
#import Numeric
#import MA
#import matplotlib
#matplotlib.use('WXAgg')
#from pylab import *
#import pylab

MIN_TIME_THRESHOLD = 1.1
MEDIAN=100
MEAN=101


validKey = re.compile('^\$?[A-Za-z0-9 \-_]*$')


def array2strings(ary):
    rv = []
    for thing in ary:
        rv.append(str(thing))
    return rv

def array2tuple(ary):
    rv = ()
    for thing in ary:
        rv = rv + (thing,)
    return rv


class FCS:
    def __init__ (self):

        self.textStart=None
        self.textEnd=None

        self.dataStart=None
        self.dataEnd=None

        self.analysisStart=None
        self.analysisEnd=None

        self.byteswaped=None

        self.originalData=None
        self.undoData=None
        self.filteredData=None
        self.filters=None
        
        self.parameters=[]
        self.ranges=[]
        self.gains=[]

        self.displayParameters=[]
        self.displayFormat=None

    def __str__(self):

        outMat = None
        for parameter in self.displayParameters:
            if outMat == None:
                outMat = self.values(parameter,squeeze=False)
            else:
                outMat = concatenate((outMat,self.values(parameter,squeeze=False)),1)
        
        outlines=['\t'.join(self.displayParameters)]
        if self.displayFormat != None:
            strFormat = self.displayFormat
        else:
            strFormat = '\t'.join(('%s',)*len(self.displayParameters))
        
        
        for event in outMat:
            outlines.append(strFormat%array2tuple(event))

        return '\n'.join(outlines)
        

    def parseFCSfile(self, fileName):
        f = file(fileName,'rb')

        # check file type
        TYPE = f.read(6)
        if TYPE != 'FCS3.0':
            raise Exception

        # get the raw HEADER
        HEADER = TYPE + f.read(52)
        header = HEADER.split()

        # the only boundries that that are gaurnteed to
        # be in the header are the primary TEXTAREA
        textStart = int(header[1])
        textEnd = int(header[2])
        if textStart == 0 or textEnd == 0:
            raise Exception

        # raw TEXT segment
        f.seek(textStart)
        TEXT=f.read(1+textEnd-textStart)

        # the delimeter is the first char
        # of the TEXTAREA
        delim=TEXT[0]
        textSplit = TEXT.split(delim)
        #print textSplit

        # skip first (empty) field
        textSplit.pop(0)

        # populate TEXTAREA key value dictionary
        self.text={}
        while(len(textSplit) > 1):
            key=textSplit.pop(0)
            # there is garbage 
            if validKey.match(key) == None:
                break
            #print key
            value=textSplit.pop(0)
            self.text[key.upper()]=value

        # the number of 'things'
        self.eventCount=int(self.text['$TOT'].rstrip().lstrip())
        self.paramCount=int(self.text['$PAR'].rstrip().lstrip())

        # the type of the things
        self.dataType = self.text['$DATATYPE'].rstrip().lstrip()
        if self.dataType == 'I':
            # unsigned integer
            numTypeCode='u'
            expectedBits = 32
        elif self.dataType == 'F':
            # float
            numTypeCode='f'
            expectedBits = 32
        elif self.dataType == 'D':
            # double
            numTypeCode='d'
            expectedBits = 64
        elif self.dataType == 'A':
            raise Exception, "ASCII data encoding not supported"
        else:
            raise Exception, "Data encoding not understood"

        # check the # of parameter bits and
        # initilize parameter,range and gain lists
        #gains = []
        for n in range(1,self.paramCount+1):
            if '$P%sS'%n in self.text:
                paramStr=self.text['$P%sS'%n]
            else:
                paramStr=self.text['$P%sN'%n]
                
            self.parameters.append(paramStr)
            
            bitCount=int(self.text['$P%sB'%n].rstrip().lstrip())
            if bitCount != expectedBits:
                raise Exception, "Parameter '%s' has the wrong number of bits." % paramStr

            paramMax = int(self.text['$P%sR'%n].rstrip().lstrip())
            self.ranges.append(paramMax)

            paramGain = float(self.text['$P%sG'%n].rstrip().lstrip())
            self.gains.append(paramGain)
            
        # default text repr is all columns
        self.displayParameters = self.parameters
            
        # get the DATA
        if self.text['$MODE'].rstrip().lstrip() != 'L':
            raise Exception, "Only LIST format data supported"
        
        self.dataStart = int(self.text['$BEGINDATA'].rstrip().lstrip())
        self.dataEnd = int(self.text['$ENDDATA'].rstrip().lstrip())
        f.seek(self.dataStart)
        DATA=f.read(1+self.dataEnd-self.dataStart)
        data=fromstring(DATA,numTypeCode)
        print shape(data)
        self.originalData=data.resize((self.eventCount,self.paramCount))
        print shape(self.originalData)
        print self.eventCount,self.paramCount
        # system dependant byte order 
        self.dataLittleEndian = self.text['$BYTEORD'].startswith('1')
        machineLittleEndian = LittleEndian
        if machineLittleEndian != self.dataLittleEndian:
            self.originalData = self.originalData.byteswapped()
            print 'bytes swapped'

        # apply $PnG gain/scale factors
        scaleMat = array(self.gains*self.eventCount,typecode='d')
        scaleMat = scaleMat.resize((self.eventCount,self.paramCount))
        self.originalData = scaleMat*self.originalData

        # setup for undo functionality
        self.filters=[]
        self.filteredData=self.originalData.copy()
        self.setUndoPoint()

        # TODO: analysis parsing
        self.analysisStart = int(self.text['$BEGINANALYSIS'].rstrip().lstrip())
        self.analysisEnd = int(self.text['$ENDANALYSIS'].rstrip().lstrip())

    # data lookup
    def pLookup(self,parameter):
        return  self.parameters.index(parameter)

    def median(self,parameter,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return median(take(self.originalData,(pIdx,),1))[0]
        else:
            return median(take(self.filteredData,(pIdx,),1))[0]

    def mean(self,parameter,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return meam(take(self.originalData,(pIdx,),1))[0]
        else:
            return mean(take(self.filteredData,(pIdx,),1))[0]

    def std(self,parameter,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return std(take(self.originalData,(pIdx,),1))[0]
        else:
            return std(take(self.filteredData,(pIdx,),1))[0]
    
    def values(self,parameter,squeeze=True,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            tmpMat=take(self.originalData,(pIdx,),1)
        else:
            tmpMat=take(self.filteredData,(pIdx,),1)
        if squeeze:
            return squeeze(tmpMat)
        else:
            return tmpMat
        

        #return take(self.filteredData,(pIdx,),1)

    def max(self,parameter,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return amax(take(self.originalData,(pIdx,),1))[0]
        else:
            return amax(take(self.filteredData,(pIdx,),1))[0]

    def min(self,parameter,unfiltered=False):
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return amin(take(self.originalData,(pIdx,),1))[0]
        else:
            return amin(take(self.filteredData,(pIdx,),1))[0]

    def cutoff (self,parameter,
                fraction=None,count=None,
                unfiltered=False):

        pIdx = self.pLookup(parameter)

        trimCount=count

        values = self.values(parameter,unfiltered=unfiltered)
        sort(values)

        if trimCount == None:
            trimCount = int(float(len(values))*fraction)

        return (values[trimCount],values[-trimCount])


    def pMax(self,parameter):
        pIdx = self.pLookup(parameter)
        return self.ranges[pIdx]
       

    # some rudimentry ploting
    # written for pylab
##     def densityMatrix(self,p1,p2, size = (200,200)):
    
##         xVal = self.values(p1)
##         xRange = (min(xVal),max(xVal))
##         yVal = self.values(p2)
##         yRange = (min(yVal),max(yVal))
        

##         mat = Numeric.zeros((size[0]+1,size[1]+1),
##                             typecode='f')

##         # last row and col use to store bin boundries
##         xBins=linspace(xRange[0],xRange[1],size[0])
##         yBins=linspace(yRange[0],yRange[1],size[1])
##         for i in range(len(xBins)):
##             mat[-1,i] = xBins[i]
##         for y in range(len(yBins)):
##             mat[i,-1] = yBins[i]

##         # map data to bins
##         xs = Numeric.searchsorted(xBins,xVal)
##         ys = Numeric.searchsorted(yBins,yVal)

##         for i in range(len(xs)):
##             mat[xs[i],ys[i]] = mat[xs[i],ys[i]] + 1

        
        
##         return rot90(mat)

##     def scatter(self,p1,p2):
##         pylab.scatter(self.values(p1),
##                       self.values(p2))
##         pylab.show()

##     def imshow(self,p1,p2):
##         mat = self.densityMatrix(p1,p2)
##         matMin = min(min(mat))
##         matMax = max(max(mat))

##         pylab.imshow(mat[:-1,:-1],vmin=matMin, vmax=matMax)
##         pylab.xlabel(p1)
##         pylab.ylabel(p2)

##         pylab.setp(pylab.gca(),'xticklabels',array2strings(pylab.squeeze(mat[:,-1])))
##         pylab.setp(pylab.gca(),'yticklabels',array2strings(pylab.squeeze(mat[-1,:])))
        
##         print array2strings(pylab.squeeze(mat[:,-1]))
##         print array2strings(pylab.squeeze(mat[-1,:]))
                
##         pylab.jet()
##         pylab.colorbar()
##         pylab.show()

    # UNDO
    def setUndoPoint (self):
        self.undoData=self.filteredData.copy()

    def undo (self):
        self.filteredData=self.undoData.copy()

    def reset (self):
        self.filteredData=self.originalData.copy()


    # maskEvents is the workhorse method for all the
    # filtering methods
    def maskEvents(self, eventMask):
        """Removes events from self.filteredData according to
        the eventMask. The eventMask must be a 1D array where
        each element represents one even in the current order.
        Events with nonzero mask values are retained.
        """
        
        self.filteredData=take(self.filteredData,
                                       nonzero(eventMask==0))
        return shape(self.filteredData)[0]

    # Data Filtering - 
    # remove events based on numerical analysis
    #
    # A list of parameters can be specified.  If no list is specified,
    # any matching parameters in a event cause the event to be filtered.
    #

    def filterEqualTo(self,parameters=None,value=None,setUndo=True):
        if setUndo:
            self.setUndoPoint()

        if parameters == None:
            parameters = self.parameters

        mask = None
        for parameter in parameters:
            if mask ==None:
                mask = (self.values(parameter) == value)
            else:
                mask = mask + (self.values(parameter) == value)
        return self.maskEvents(mask)
            
    def filterZeros(self,parameters=None,setUndo=True):
        return self.filterEqualTo(parameters=parameters,value=0,setUndo=setUndo)

    def filterPeggedValues(self,parameters=None,setUndo=True):
        if setUndo:
            self.setUndoPoint()
        if parameters == None:
            parameters = self.parameters

        mask = None
        for parameter in parameters:
            if mask == None:
                mask = (self.values(parameter) == self.pMax(parameter))
            else:
                mask = mask + (self.values(parameter) == self.pMax(parameter))

        return self.maskEvents(mask)
 
        
    def filterOutliers(self,parameters=None,
                       fraction=None,count=None,
                       highEnd=True, lowEnd=True,
                       setUndo=True):
        """Remove events with the top and/or bottom n (or n%)
        values for given parameters.
        """
        if setUndo:
            self.setUndoPoint()

        if parameters == None:
            parameters = self.parameters

        mask = None
        for parameter in parameters:
            cutoffs = self.cutoff(parameter,fraction=fraction,count=count)
            if highEnd and not lowEnd:
                if mask ==None:
                    mask = (self.values(parameter) >= cutoffs[1])
                else:
                    mask = mask + (self.values(parameter) >= cutoffs[1])
            elif lowEnd and not highEnd:
                if mask ==None:
                    mask = (self.values(parameter) <= cutoffs[0])
                else:
                    mask = mask + (self.values(parameter) <= cutoffs[0])

            elif highEnd and lowEnd:
                if mask ==None:
                    mask = (self.values(parameter) <= cutoffs[0] and
                            self.values(parameter) >= cutoffs[1])
                else:
                    mask = mask + (self.values(parameter) <= cutoffs[0] and
                                   self.values(parameter) >= cutoffs[1])

        return self.maskEvents(mask)

    def smoothConstantData(self,parameters=None, windowSize=None,
                           metric=MEDIAN, thresholdFactor=20,setUndo=True):
        """Remove event windows there the window mean is > thresholdFactor
        times larger than the overall mean for a parameter.
        If window size is not specified, %1 of the filtered events are used.
        """

        if metric != MEDIAN and metric != MEAN:
            raise ValueError, "metric unknown"

        fEventCount = shape(self.filteredData)[0]
        if windowSize == None:
            windowSize = fEventCount/100

        if setUndo:
            self.setUndoPoint()

        if parameters == None:
            parameters = self.parameters
        
        mask=zeros((fEventCount,),'u')
        for parameter in parameters:
            if metric == MEDIAN:
                overallM = self.median(parameter)
            else:
                overallM = self.mean(parameter)
            values = self.values(parameter)
            for start in range(fEventCount-windowSize):
                end = start+windowSize
                if metric == MEDIAN:
                    windowM = median(values[start:end])
                else:
                    windowM = mean(values[start:end])
                if windowM >= overallM * thresholdFactor:
                    put(mask,range(start,end),[1]*windowSize)
                    
        return self.maskEvents(mask)
               
                                           
        

    def timeChop (self):
        pass

    def timeChopSymetric(self):
        pass

    

class FCSparameter:

    def __init__(column):
        self.name=None




if __name__ == '__main__':
    f = file('D:/Documents and Settings/kael/Desktop/specimen_001/tube_001.fcs','rb')
    fcs=FCS()
    fcs.parseFCSfile()
    print fcs.ranges
    #print Numeric.shape(fcs.parameterMatrix('Time','FITC-A'))
    fcs.imshow('Time','FITC-A')
    




    
