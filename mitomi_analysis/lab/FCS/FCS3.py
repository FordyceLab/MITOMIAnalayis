#!/usr/local/bin/python
#
# FCS3.0 parsing and processing library.
#
#     $Id: FCS3.py,v 1.1.1.1 2008/03/10 18:48:54 kael Exp $    
#
# Kael Fischer - September, 2005
#
# Permission to use, modify and redistribute is allowed 
# only under the terms of the BSD license as specified 
# in the LICENSE file distributed with this file.
#
# Most of the original high level filtering functions are
# based on various programs written by John Newman
#
import sys,re
from types import *
from Numeric import *
from MLab import *
import time,datetime


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


class FCSParserError(Exception):
    """Raise this error when you find an invalid FCS3.0 file.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FCSDataError(Exception):
    """Raise this error when the FCS3.0 file has missing
    or suspect data.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FCS:
    """Representation of a FCS3.0 file.  Data are represented as a
    Numeric array of 64-bit floating point values.  Parameter (FITC-A,
    etc.) order is maintained between the FCS file and the data array.
    The order of the parameters is the same as the order of the
    parameter names in the self.parameters, so they can be looked up
    quickly in that list.

    Convenience functions for data lookup and filtering all use parameter
    names.

    FCS OBJECT PROPERTIES

    File byte offsets:
        textStart,textEnd,dataStart,dataEnd,analysisStart,analysisEnd
    Numeric stuff:
        originalData,filteredData,excludedData,undoData,excludedUndoData,
        byteswapped,dataLittleEndian,ranges,gains,dataType
    Text representation helpers:
        displayParameters,displayFormat
    All fields from TEXT section:
        text[field name]
    All parameters found:
        parameters[:]
    

    USEFUL HIGH LEVEL FUNCTIONS

    Data management:
        parseFCSfile
        undo
        reset
        setUndoPoint
        __str__

    Data look up functions:
    These take a single parameter name -
        mean
        median
        std
        min
        max
        values

    High level filtering functions optionally take a list of
    parameter names.  By default the filters are active across all
    parameters (including Time). -
        filterZeros
        filterPeggedValues
        filterOutliers
        filterEqualTo
        radialFilter
        smoothConstantData

    Lower level filtering:
        maskEvents - lower level function filters based on an event mask.
                     mask can be build with conditionals like:
                          self.values('FITC-A') <= 55000
    """
    
    def __init__ (self):
        """Returns an object with no data.
        Use parseFCSfile(filename) to read in data.
        """
        
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
        self.excludedData=None
        self.excludedUndoData=None
        
        self.parameters=[]
        self.ranges=[]
        self.gains=[]

        self.displayParameters=[]
        self.displayFormat=None

    def __str__(self, showColumnNames=True):
        """Return a string that is the flat file tab delimited
        representation of the data, where the columns are specified
        by the object property displayParameters.  If the property
        display format is not None, it will be used as the format
        string.  By default the format is:
        '\t'.join(('%s',)*len(self.displayParameters)).
        If showColumnNames is set to False the names of the parameters
        will not be displayed in the first line.
        """
        outMat = []
        for parameter in self.displayParameters:
            if outMat == []:
                outMat = self.values(parameter,squeeze=False)
            else:
                outMat = concatenate((outMat,self.values(parameter,squeeze=False)),1)

        if showColumnNames:
            outlines=['\t'.join(self.displayParameters)]
            
        if self.displayFormat != None:
            strFormat = self.displayFormat
        else:
            strFormat = '\t'.join(('%s',)*len(self.displayParameters))
        
        
        for event in outMat:
            outlines.append(strFormat%array2tuple(event))

        return '\n'.join(outlines)


    def startTime (self):
        if '$DATE' not in self.text:
            raise FCSDataError("$DATE not found in FCS file.")
        if '$BTIM' not in self.text:
            raise FCSDataError("$BTIM (data collection start time) not found in FCS file.")
       
        
        t = time.strptime("%s %s" % (self.text['$DATE'],self.text['$BTIM']),"%d-%b-%Y %H:%M:%S")
        return datetime.datetime(t[0],t[1],t[2],t[3],t[4],t[5])
        

    def parseFCSfile(self, fileName):

        if self.originalData is not None:
            raise FCSParserError("FCS object already contains parsed data.")
            

        if type(fileName) not in StringTypes:
            raise TypeError("filename must be a string.")
        f = file(fileName,'rb')

        # check file type
        TYPE = f.read(6)
        if TYPE != 'FCS3.0':
            raise ValueError('%s is not a valid FCS3.0 file' % fileName)
        #
        ##### HEADER SECTION #####
        #
        
        # get the raw HEADER
        HEADER = TYPE + f.read(52)
        header = HEADER.split()

        # the only boundaries that that are guaranteed to
        # be in the header are the primary TEXTAREA
        textStart = int(header[1])
        textEnd = int(header[2])
        if textStart == 0 or textEnd == 0:
            raise FCSParseError("TEXTAREA boundaries undefined")
        #
        ##### TEXTAREA SECTION #####
        #

        # raw TEXT segment
        f.seek(textStart)
        TEXT=f.read(1+textEnd-textStart)

        # the delimiter is the first char
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
            raise Exception("ASCII data encoding not supported")
        else:
            raise Exception("Data encoding not understood")

        # check the # of parameter bits and
        # initialize parameter,range and gain lists
        #gains = []
        for n in range(1,self.paramCount+1):
            if '$P%sS'%n in self.text:
                paramStr=self.text['$P%sS'%n]
            else:
                paramStr=self.text['$P%sN'%n]
                
            self.parameters.append(paramStr)
            
            bitCount=int(self.text['$P%sB'%n].rstrip().lstrip())
            if bitCount != expectedBits:
                raise Exception("Parameter '%s' has the wrong number of bits." % paramStr)

            paramMax = int(self.text['$P%sR'%n].rstrip().lstrip())
            self.ranges.append(paramMax)

            paramGain = float(self.text['$P%sG'%n].rstrip().lstrip())
            self.gains.append(paramGain)
            
        # default text repr is all columns
        self.displayParameters = self.parameters
            
        #
        ##### DATA SECTION #####
        #
        
        # get the DATA
        if self.text['$MODE'].rstrip().lstrip() != 'L':
            raise Exception("Only LIST format data supported")
        
        self.dataStart = int(self.text['$BEGINDATA'].rstrip().lstrip())
        self.dataEnd = int(self.text['$ENDDATA'].rstrip().lstrip())
        f.seek(self.dataStart)
        DATA=f.read(1+self.dataEnd-self.dataStart)
        # unpack data
        data=fromstring(DATA,numTypeCode)
        self.originalData=data.resize((self.eventCount,self.paramCount))

        # system dependent byte order 
        self.dataLittleEndian = self.text['$BYTEORD'].startswith('1')
        machineLittleEndian = LittleEndian
        if machineLittleEndian != self.dataLittleEndian:
            self.byteswaped = True
            self.originalData = self.originalData.byteswapped()
        else:
            self.byteswapped = False

        # apply $PnG gain/scale factors
        scaleMat = array(self.gains*self.eventCount,typecode='d')
        scaleMat = scaleMat.resize((self.eventCount,self.paramCount))
        self.originalData = scaleMat*self.originalData

        # setup for undo functionality
        self.filters=[]
        self.filteredData=self.originalData.copy()
        self.filteredEventCount = shape(self.filteredData)[0]
        self.excludedData = None
        self.setUndoPoint()

        #
        ##### ANALYSIS SECTION #####
        #

        # TODO: analysis parsing
        self.analysisStart = int(self.text['$BEGINANALYSIS'].rstrip().lstrip())
        self.analysisEnd = int(self.text['$ENDANALYSIS'].rstrip().lstrip())

    #
    ##### Misc. Functions #####
    #

    def dataTypeDescription(self):
        """Returns a human readable description of the
        data encoding used in the file"""
        if self.dataType == 'I':
            return 'Unsigned Integer'
        elif self.dataType == 'F':
            return 'Float (32-bit)'
        elif self.dataType == 'D':
            return 'Double (64-bit)'

    # UNDO support
    def setUndoPoint (self):
        """Set the undo point to represent the current filtered set."""
        self.undoData=self.filteredData.copy()
        if self.excludedData is not None:
            self.excludedUndoData=self.excludedData.copy()


    def undo (self):
        """Rollback the filtered set to the undo point."""
        self.filteredData=self.undoData.copy()
        self.filteredEventCount = shape(self.filteredData)[0]
        self.excludedData=self.excludedUndoData.copy()

    def reset (self):
        """Rollback all filters and reset the filtered set to the original data."""
        self.filteredData=self.originalData.copy()
        self.filteredEventCount = shape(self.filteredData)[0]
        self.excludedData=None

    #
    ##### Simple Data Lookup Functions #####
    #
    
    def pLookup(self,parameter):
        """Return the index of a parameter in the parameter list."""
        return  self.parameters.index(parameter)

    def pMax(self,parameter):
        """Return the maximum values for the parameter as
        specified in the file (not the observed maximum, as one
        might think from the method name)."""
        pIdx = self.pLookup(parameter)
        return self.ranges[pIdx]
       
    def max(self,parameter,unfiltered=False):
        """Return the maximum value for a parameter."""
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return max(take(self.originalData,(pIdx,),1))[0]
        else:
            return max(take(self.filteredData,(pIdx,),1))[0]

    def min(self,parameter,unfiltered=False):
        """Return the minimum value for a parameter."""
        pIdx = self.pLookup(parameter)
        if unfiltered:
            return min(take(self.originalData,(pIdx,),1))[0]
        else:
            return min(take(self.filteredData,(pIdx,),1))[0]

    def median(self,parameter,unfiltered=False):
        """Return the median value for a parameter."""
        return median(self.values(parameter,unfiltered=unfiltered,
        squeezeMat=False))[0]

    def mean(self,parameter,unfiltered=False):
        """Return the mean value for a parameter."""
        return mean(self.values(parameter,unfiltered=unfiltered,
        squeezeMat=False))[0]

    def std(self,parameter,unfiltered=False):
        """Return the standard deviation for a parameter."""
        return std(self.values(parameter,unfiltered=unfiltered,
        squeezeMat=False))[0]
        
    def cv(self,parameter,unfiltered=False):
        """Return the coefficient of variation for a parameter."""
        return (self.std(parameter,unfiltered=unfiltered)/
                self.mean(parameter,unfiltered=unfiltered))
        
    def values(self,parameter,squeezeMat=True,unfiltered=False):
        """Return a list of values for a parameter."""
        pIdx = self.pLookup(parameter)
        if unfiltered:
            tmpMat=take(self.originalData,(pIdx,),1)
        else:
            tmpMat=take(self.filteredData,(pIdx,),1)
        if squeezeMat:
            return squeeze(tmpMat)
        else:
            return tmpMat


    def excludedValues(self,parameter,squeezeMat=True,unfiltered=False):
        """Return a list of values that have been excluded by the
        filtering functions."""
        pIdx = self.pLookup(parameter)

        if self.excludedData is None:
            return ([])
        
        tmpMat=take(self.excludedData,(pIdx,),1)
        if squeezeMat:
            return squeeze(tmpMat)
        else:
            return tmpMat


    #
    ##### lower level calculations for filtering and stuff
    #

    def centroid(self,parameters=[],unfiltered=False,metric=MEDIAN):
        """Return the centroid of the data in a space with
        the dimensions defined by the parameters.
        """

        rv = []

        if metric == MEDIAN:
            for parameter in parameters:
                rv.append(self.median(parameter,unfiltered=unfiltered))
        elif metric == MEAN:
            for parameter in parameters:
                rv.append(self.mean(parameter,unfiltered=unfiltered))
        else:
            raise ValueError("metric unknown")
        
        return rv

    def distance2(self,parameters=[],unfiltered=False,metric=MEDIAN):
        """Return the centroid and an array of events _squared_
        _distances_ from the centroid in space with dimensions
        defined by the parameters.  
        """

        if unfiltered:
            d2=zeros((self.eventCount,))
        else:
            d2=zeros((self.filteredEventCount,))

        center = self.centroid(parameters,unfiltered=unfiltered,metric=metric)

        # add the square of the difference in each dimension
        for i in range(len(parameters)):
            d2 = d2 + (self.values(parameters[i],unfiltered=unfiltered)-center[i])**2

        return (center,d2)
        

    def cutoff (self,parameter,
                fraction=None,count=None,
                unfiltered=False):
        """Return the filter limit for 1 dimensional filters. 
        """
        
        pIdx = self.pLookup(parameter)

        trimCount=count

        values = self.values(parameter,unfiltered=unfiltered)
        values=sort(values)

        if trimCount == None:
            trimCount = int(float(len(values))*fraction)

        return (values[trimCount],values[-trimCount])


    #
    ##### Masking and Filtering #####
    #

    # maskEvents is the workhorse method for all the
    # filtering methods
    def maskEvents(self, eventMask):
        """Removes events from self.filteredData according to
        the eventMask. The eventMask must be a 1D array where
        each element represents one even in the current order.
        Events with zero mask values are retained.
        """

        tmpMat = self.filteredData.copy()
        self.filteredData=take(self.filteredData,
                               nonzero(eventMask==0))
        self.filteredEventCount = shape(self.filteredData)[0]
        
        if self.excludedData is None:
            self.excludedData=take(tmpMat,nonzero(eventMask!=0))
        else:
            self.excludedData = concatenate((self.excludedData,
                                             take(tmpMat, nonzero(eventMask!=0))))
            
        return self.filteredEventCount

    # Data Filtering - 
    # remove events based on numerical analysis
    #
    # A list of parameters can be specified.  If no list is specified,
    # any matching parameters in a event cause the event to be filtered.
    #

    def filterEqualTo(self,parameters=None,value=None,setUndo=True):
        """Filter events that have parameter values equal to 'value'."""

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
        """remove events for which any parameter in parameters is 0.
        """
        return self.filterEqualTo(parameters=parameters,value=0,setUndo=setUndo)

    def filterPeggedValues(self,parameters=None,setUndo=True):
        """remove events for which any parameter in parameters is equal
        to the maximum defined for that parameter.
        """
        if setUndo:
            self.setUndoPoint()
        if parameters == None:
            parameters = self.parameters

        mask = None
        for parameter in parameters:
            if mask == None:
                mask = (self.values(parameter) >= self.pMax(parameter)-1)
            else:
                mask = mask + (self.values(parameter) >= self.pMax(parameter)-1)

        return self.maskEvents(mask)
 
        
    def filterOutliers(self,parameters=None,
                       fraction=None,count=None,
                       highEnd=True, lowEnd=True,
                       setUndo=True):
        """Remove events with the highest and/or lowest n (or n%)
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
            raise ValueError("metric unknown")

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
                    put(mask,list(range(start,end)),[1]*windowSize)
                    
        return self.maskEvents(mask)
               
    def radialFilter (self,p1,p2,
                      fraction=None,count=None,sigma=None,
                      metric=MEDIAN,unfiltered=False,setUndo=True):
        """Examine and filter events in a 2D space defined by two parameters,
        p1 and p2. The return value is the maximal distance from the center of
        the data, corresponding to the the cutoff specified. The centroid can be
        calculated using the mean or median (default) of the data. 
        Returns: (# of events in filtered set,(centroid), radius in p1/p2 space)
        """
        
        if setUndo:
            self.setUndoPoint()

        trimCount=count
        
        (centroid,d) = self.distance2([p1,p2],unfiltered=unfiltered,metric=metric)
        
        dSorted = d.copy()
        dSorted=sort(dSorted)

        limit = None

        if sigma != None:
            combinedStdev = self.std(p1)**2 + self.std(p2)**2
            limit = combinedStdev * sigma
        elif fraction != None:
            trimCount = int(float(len(dSorted))*(fraction))
            limit = dSorted[-trimCount]
        elif count != None:
            limit = dSorted[-count]
        else:
            raise ValueError("fraction, count, or sigma must be specified.")
        
        mask =  (d >= limit)

        return (self.maskEvents(mask),centroid,limit)
        
                                           
    def timeChop (self):
        """Not Implemented
        """
        raise NotImplementedError

    def timeChopSymetric(self):
        """Not Implemented
        """
        raise NotImplementedError

    





