"""A general interface to Axon Formatted Text (ATF) files.

ATF files have the following structure:
      i. 2 mandatory header lines (specify the ATF version and number
                                   of header lines and data columns )
     ii. optional headers (any number, as specified above)
    iii. one line that has the names of the data columns
     iv. the data records

For more information about the format see:
     http://www.axon.com/gn_GenePix_File_Formats.html


The ATF class provides the following interface:
  Initialization -
       The classes constructor accepts an optional path that is assumed
       to correspond to an ATF file.  That ATF file is parsed and an
       instance is returned that corresponds to the data in the file.

  Output -
       The classes dump() method returns a string representation of the object
       which is a valid ATF string.

  Accessing and changing the data -
       Optional headers are accessible through the dictionary
       object.optionalHeaders.

       DataRecords are available directly using the object.dataLines list.
       Lists of DataRecords that match ID strings or (Block,Column,Row)
       specifications are available using object[IDstring] or
       object[(Block,Column,Row)], respectively.  Note that if Block,
       Column or Row are set to None, it serves as a wildcard and matches
       all values.

The DataRecord Class is a wrapper for Dict.
       
version: $Id: ATF.py,v 1.1.1.1 2008/01/28 18:51:14 kael Exp $	

"""



import string,shelve,re
try:
    from kf_util import plots
except:
    pass
from types import *
import Numeric

from traceback import print_exc
uid_parameters = shelve.open('/sumo/home/kael/lib/oligos.shelve')

class ATFParseError (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ATFIncompleteData (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class ATFInstanceError (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

blockPrintOrder = {
    1: (1,),
    
    4: ((2,4),
        (1,3)),

    16:((4,8,12,16),
        (3,7,11,15),
        (2,6,10,14),
        (1,5,9,13)),

    32:((4,8,12,16,20,24,28,32),
        (3,7,11,15,19,23,27,31),
        (2,6,10,14,18,22,26,30),
        (1,5, 9,13,17,21,25,29)),
    
    48:((4,8,12,16,20,24,28,32,36,40,44,48),
        (3,7,11,15,19,23,27,31,35,39,43,47),
        (2,6,10,14,18,22,26,30,34,38,42,46),
        (1,5, 9,13,17,21,25,29,33,37,41,45))
    }

def printOrderBCRs(pins,blkWidth,blkHeight,spots=None,plateCt=None):
    if spots == None:
        spots = plates*384
    rv = []
    blkSpots=blkWidth*blkHeight
    while spots > 0:
        pass

def _GeneralStringConvert (inStr):
    """Take a string, return a nonstring if approptiate. The order we try:
    int
    float
    string
    """
    dateFormats = ("%a %b %d %H:%M:%S %Y",)

    inStr = inStr.rstrip(string.whitespace + '"').lstrip(string.whitespace + '"')
    
    try:
         fv = float(inStr)
         if inStr.count('.') == 0:
             return int(fv)
         else:
             return fv
    except:
        return inStr


class PrintPlate:
	"""
	"""

	plateSize=384
	rows='ABCDEFGHIJKLMNOP'
	columns=list(range(1,25))

	rowCt = len(rows)
	colCt = len(columns)
	
	def __init__ (self,startOffset=0):
		self.pins = (4,4)
		# make block map
		self.blockMap={}
		# dip loop
		for upper in range(1,self.rowCt+1,self.pins[0]):
			for left in range(1,self.colCt+1,self.pins[1]):
				# pin loop
				block = 1
				for r in range(upper,upper+self.pins[0]):
					for c in range(left,left+self.pins[1]):
						#print r,c
						self.blockMap[(self.rows[r-1],c)] = block
						block += 1

		


	def blockNumber(self,row,col):
		return self.blockMap[(row,col)]
		


class ATF:
    """A class for Axon text files.

    See module documentation.
    """

    def __init__ (self, inFileName=None):
        """Create an ATF object.
        """

        self.fileRead = False

        self.requiredHeaders = ['Type']
        self.headerOrder = []

        self.optionalHeaders = {}

        self.colCt = 0
        self.columnNames = []
        self.requiredColumns = []
        self.requiredColumnPositions = []

        self.dataPercision = None

        self.idx = {}

        self.IDidx = None
        self.BCRidx = None
        self.dataLines = []
            
        if inFileName != None:
            inFile = file(inFileName,'r')
            try:
                self.readFile(inFile)
            finally:
                inFile.close()

    def rebuildIndexes(self):
        """Refresh BCRidx and IDidx.
        """
        self.BCRidx = {}
        self.IDidx = {}
        
        for i in range(len(self.dataLines)):
            record = self.dataLines[i]
            BCR = (record['Block'],
                   record['Column'],
                   record['Row'])
            if BCR in self.BCRidx:
                self.BCRidx[BCR].append(i)
            else:
                self.BCRidx[BCR] = [i]

            ID = record['ID']
            if ID in self.IDidx:
                self.IDidx[ID].append(i)
            else:
                self.IDidx[ID] = [i]

        

    

    def addColumn(self,colName,required=False,reqPosition=None):
        """add a data column.
        """
        if colName not in self.columnNames:
            self.columnNames.append(colName)
            self.idx[colName] = len(self.columnNames) -1
            self.colCt += 1
        if required:
            if colName not in self.requiredColumns:
                self.requiredColumns.append(colName)
            if reqPosition != None and colName not in self.requiredColumnPositions:
                self.requiredColumnPositions[colName] = reqPosition
                

    def addHeader(self,headerName,required=False):
        """add an optional header.
        """
        if headerName not in self.optionalHeaders:
            self.optionalHeaders[headerName] = ''
            self.headerOrder.append(headerName)
        if required and headerName not in requiredHeaders:
            self.requiredHeaders.append(headerName)
        
    def _headerCheck(self):
        """Return True if all required headers are present.
        Otherwise False.
        """
        for h in self.requiredHeaders:
            if h not in self.optionalHeaders:
                return False    
        return True

    def _columnCheck(self):
        """Return True if all required columns are present.
        Otherwise False.
        """
        for c in self.requiredColumns:
            if c not in self.columnNames:
                return False
            
        for undef,c in self.requiredColumnPositions:
            if c not in self.columnNames:
                return False
            
        return True


    def readFile(self,inFile):
        """Read the contents of an Axon formatted text file.
        Set header and data attributes.
        """

        try:
            requiredHeader1 = inFile.readline().rstrip()
            (ATFstring,version) = requiredHeader1.split('\t')
        except:
            print_exc()
            raise ATFParseError('Couldn\'t parse first line of file: %s' % inFile.name)
        

        if ATFstring != 'ATF':
            raise ATFParseError('ATF not found at top of file: %s' % inFile.name) 

        try:
            self.version = float(version)
        except:
            raise ATFParseError('Can\'t determine ATF version: %s' % inFile.name) 

        try:
            requiredHeader2 = inFile.readline().rstrip()
            (headerCt, colCt) = requiredHeader2.split('\t')
            headerCt = int(headerCt)
            self.colCt = int(colCt)
        except:
            print_exc()
            raise ATFParseError('Couldn\'t parse second line of file: %s' % inFile.name) 


        self.optionalHeaders = {}
        self.headerOrder = []

        for i in range(headerCt):
            line = inFile.readline().rstrip(string.whitespace + '"').lstrip(string.whitespace + '"')
            field, value = line.split('=')
            
            self.headerOrder.append(field)
            self.optionalHeaders[field]=_GeneralStringConvert(value)

        # get the column names for the data
        dataHeader = inFile.readline().rstrip('\n')
        self.columnNames = dataHeader.split('\t')
        #print len(self.columnNames) ,self.colCt
        if len(self.columnNames) != self.colCt:
            raise ATFParseError('Column count (%s) is different that number of columns found in (%s)' % ( self.colCt,len(self.columnNames)))

        for c in range(len(self.columnNames)):
            self.columnNames[c] = self.columnNames[c].rstrip(string.whitespace + '"').lstrip(string.whitespace + '"')
            self.idx[self.columnNames[c]] = c
        try:
            self.IDcol = self.idx['ID']
        except ValueError:
            self.IDcol = None

        lineNumber = 2 + headerCt + 1
        dataLineNumber = -1

        # get the rest of the file (data records)
        line = inFile.readline().rstrip('\n')
        self.dataLines = []

        if self.IDcol != None:
            self.IDidx = {}
        
        if "Block" in self.columnNames and \
           "Column" in self.columnNames and \
           "Row" in self.columnNames:
            self.BCRidx = {}
            makeBCR = True
        else:
            False
        
        while line != '':


            lineNumber += 1
            dataLineNumber += 1

            if line == '\n':
                break
            
            record = DataRecord(self,line)
            self.dataLines.append(record)

            # maintain IDidx / and Block,column
            if self.IDcol != None:
                ID = record['ID']
                if ID in self.IDidx:
                    self.IDidx[ID].append(dataLineNumber)
                else:
                    self.IDidx[ID] = [dataLineNumber]

            if makeBCR:
                BCR = (record['Block'],
                       record['Column'],
                       record['Row'])
                if BCR in self.BCRidx:
                    self.BCRidx[BCR].append(dataLineNumber)
                else:
                    self.BCRidx[BCR] = [dataLineNumber]
            
            line = inFile.readline().rstrip('\n')
            
        self.fileRead = True

    def fieldIdxOrder(self):
        """Return a list of field indicies that can be used to
        order the data records for output.
        """
        origFields = self.columnNames[:]
        outFields = []

        origOrderedFields = self.columnNames

        fieldOrder = [None] * len(self.columnNames)

        for (i,c) in self.requiredColumnPositions:
            fieldOrder[i] = self.idx[c]
            #print c
            origFields.remove(c)
            #print self.columnNames
            #print fieldOrder

        for i in range(len(fieldOrder)):
            if fieldOrder[i] == None:
                fieldOrder[i] = self.idx[origFields.pop(0)]

        return fieldOrder


    def fieldOrder(self):
        """Return the field names in the order in which they
        should be be output.        
        """
        rv = []
        for i in self.fieldIdxOrder():
             rv.append(self.columnNames[i]) 
        return rv
        
    def _FormatDataLine(self,fields):
        """Take a list of fields and return them joined by tabs,
        and enclose text fields with double quotes.
        """
        outFields = []
        for i in self.fieldIdxOrder():
            #print i, len(fields)
            f = fields[i]
            if type(f) == StringType:
                outFields.append(string.join(('"',f,'"'),''))
            elif type(f) == FloatType and self.dataPercision != None:
                formatSpec = "%%%s.%sf" % (self.dataPercision+2,self.dataPercision)
                outFields.append(formatSpec % f)
                
            else:
                outFields.append(str(f))
            
        return string.join(outFields,'\t')





    def __repr__ (self):
        return self.dump(dumpAll=False)
    

        
    def dump (self,dumpAll=True,DOS_EOL=True):
        """Returns a string that is a valid ATF formatted representation of the object.
        """

        if DOS_EOL:
            EOL = '\r\n'
        else:
            EOL = '\r'

        if not self._headerCheck():
            raise ATFIncompleteData("required header not present")
        if not self._columnCheck():
            raise  ATFIncompleteData("required column not present")

        outlines = []
        outlines.append("ATF\t%3.1f"%self.version)
        outlines.append("%s\t%s"%(len(self.optionalHeaders),self.colCt))

        for field in list(self.optionalHeaders.keys()):
            if field not in self.headerOrder:
                self.headerOrder.append(field)

        for field in self.headerOrder:
            try:
                outlines.append('"%s=%s"' % (field, self.optionalHeaders[field].strip()))
            except:
                pass

        outlines.append(self._FormatDataLine(self.columnNames))

        for record in self.dataLines:
            thisLine = str(record)
            if thisLine != '':
                outlines.append(thisLine)
                if not dumpAll:
                    break

        #outlines.append('\n')
        return string.join(outlines,EOL) 


    def writeATF(self,fileName):
        """write the ATF file to disk.
        """
        outFile = file(fileName,'w')
        outFile.write(self.dump())
        outFile.close()
        

    def __getattr__ (self,name):
        """Header values can be accessed this way.
        """
        if name in self.optionalHeaders:
            return self.optionalHeaders[name]

        else:
            raise AttributeError


    def __getitem__ (self,spec):
        """Return Data Records given a
        (Block, Column, Row) tuple, or an ID string.
        """
        rows = []

        if type(spec) == TupleType or \
           type(spec) == ListType:

            if len(spec) != 3 :
                raise KeyError("Block,Column,Row key is the wrong size")

            if self.BCRidx == None:
                raise KeyError("no Block,Column,Row index")
            
            if None not in spec:
                if spec in self.BCRidx:
                    for i in self.BCRidx[spec]:
                        rows.append(self.dataLines[i])
            else:
                (bSpec, cSpec, rSpec) = spec
                for bcr in list(self.BCRidx.keys()):
                    if bSpec != None:
                        if bSpec >= 0 and bcr[0] != bSpec:
                            continue
                        elif bSpec < 0 and abs(bcr[0]) ==  abs(bSpec):
                            continue
                        
                    if cSpec != None:
                        if cSpec >= 0 and bcr[1] != cSpec:
                            continue
                        elif cSpec < 0 and bcr[1] == abs(cSpec):
                            continue
                        
                    if rSpec != None:
                        if rSpec >= 0 and bcr[2] != rSpec:
                            continue
                        elif rSpec < 0 and bcr[2] == abs(rSpec):
                            continue
                        
                    rows += self[bcr]
            
        else:
            if self.IDidx ==  None:
                raise KeyError("no ID index")
            if spec in self.IDidx:
                for i in self.IDidx[spec]:
                    rows.append(self.dataLines[i])
        return rows

    def commonIDs (self, atf2):
        """Return a list of ID's common to this ATF and another.
        """
        if not isinstance(atf2,ATF):
            raise ATFInstanceError("Both args to commonIDs must be valid ATF objects.")

        if self.IDidx == None or \
           atf2.IDidx == None :
            raise  ATFIncompleteData("Both ATF objects must have ID columns.")

        comIDs = []

        if len(list(self.IDidx.keys())) >= len(list(atf2.IDidx.keys())):
            shortIdx = atf2.IDidx
            longIdx = self.IDidx
        else:
            shortIdx = self.IDidx
            longIdx = atf2.IDidx

        for id in list(shortIdx.keys()):
            if id in longIdx:
                comIDs.append(id)            
        return comIDs


    def IDcheck (self,atf2):
        """Return a list of block,column row positions in atf2 that
        have IDs that are different than this objects.
        """
        if not isinstance(atf2,ATF):
            raise ATFInstanceError("Both args to commonIDs must be valid ATF objects.")

        if self.BCRidx == None or \
           atf2.BCRidx == None :
            raise  ATFIncompleteData("Both ATF objects must have ID columns.")

        mismatchBCRs = []
        for bcr in self.BCRidx:
            if len(self[bcr]) > 1:
                raise ATFInstanceError("more than one data record with BCR: %s" % bcr)
            
            ID = self[bcr][0].ID

            if len(self[bcr]) > 1:
                raise ATFInstanceError("more than one data record in atf2 with BCR: %s" % bcr)
            elif len (self[bcr]) ==0:
                continue
            try:
                ID2 = atf2 [bcr][0].ID
            except :
                ID2 = None
            if ID != ID2:
                mismatchBCRs.append((bcr,ID,ID2))



        return mismatchBCRs


    


    def columns(self,fields=[], IDs=None, bcr=None,
                exIDs = None, exBcr = None, spotTestCallback = None,
                sortField = None):
        """returns a tupple of column vectors (as lists) with the requested fields
        (columns).  IDs, blocks, rows and array columns (cols) can be included or
        excluded with list arguments.
        """

        rv = []
        sortDict = {} 
        for i in range(len(fields)):
            rv.append([])
            
##         for c in fields:
##             if c not in self.columnNames:
##                 raise ValueError, "AFT has no column named %s" % c

        bcr_ID_included = {}
        bcr_BCR_included = {}

        bcr_included = {}
        bcr_excluded = {}

        # get records from IDs
        if IDs != None:
            if type(IDs) == StringType:
                IDs = [IDs]

            for ID in IDs:
                id_recs = self[ID]
                for r in id_recs:
                    if r.BCR not in bcr_included:
                        bcr_ID_included[r.BCR] = r

        if bcr != None:
            if type(bcr[0]) not in (ListType, TupleType) :
                bcr = [bcr]

        # use spot test call back is specified
        if spotTestCallback != None:
            stBCR = self.testSpots(spotTestCallback)
            if bcr == None:
                bcr = stBCR
            else:
                bcr.extend(stBCR)
        
        # get records from bcrs
        if bcr != None:
            for BCR in bcr:
                bcr_recs = self[BCR]
                for r in bcr_recs:
                    if r.BCR not in bcr_included:
                        bcr_BCR_included[r.BCR] = r


        if bcr == None and IDs == None:
           for r in self[(None,None,None)] :
               bcr_BCR_included[r.BCR] = r
               

        # if both ids and bcr specified, only accept the intersection
        # of those lists
        if IDs == None:
            bcr_included = bcr_BCR_included
        elif bcr == None:
            bcr_included = bcr_ID_included
        elif len (bcr_ID_included) < len (bcr_BCR_included):
            for (rec_bcr, rec) in bcr_ID_included.items():
                if rec_bcr in bcr_BCR_included:
                    bcr_included[rec_bcr] = rec
        else:
            for (rec_bcr, rec) in bcr_BCR_included.items():
                if rec_bcr in bcr_ID_included:
                    bcr_included[rec_bcr] = rec
        
        if exIDs != None:
            if type(exIDs) == StringType:
                IDs = [exIDs]

            for ID in exIDs:
                exID_recs = self[ID]
                for r in exID_recs:
                    if r.BCR not in bcr_excluded:
                        bcr_excluded[r.BCR] = None

        if exBcr != None:
            if type(exBcr[0]) not in (ListType, TupleType) :
                exBcr = [exBcr]

            for BCR in exBcr:
                exBcr_recs = self[BCR]
                for r in exBcr_recs:
                    if r.BCR not in bcr_excluded:
                        bcr_excluded[r.BCR] = None
                
           
        included_bcr = list(bcr_included.keys())
        # do field sort
        if sortField != None:
            for bcr in included_bcr:
                sortDict[self[bcr][0][sortField]] = bcr

            sortedKeys = list(sortDict.keys())
            sortedKeys.sort()
            included_bcr = []
            
            for val in sortedKeys :
                included_bcr.append(sortDict[val])
            
        else:
            included_bcr.sort()
        
        for checkBcr in included_bcr:
            if checkBcr not in bcr_excluded:
                for i in range(len(fields)):
##                     print checkBcr
##                     print fields[i]
                    rv[i].append(self[checkBcr][0][fields[i]])
                    
        return rv

    def scatter (self,fields=[], IDs=None, bcr=None,
                exIDs = None, exBcr = None, lnX = False, lnY=False,
                 add=False, color='black',bg=None, symbol='o',
                 printIt = False,title='',
                 xlim=None, ylim=None,pngFile=None, spotTestCallback = None):
        """Plot a scatter plot of 2 columns of data from the ATF data.
        """
    

        x,y = self.columns(fields,IDs=IDs, bcr=bcr,
                           exIDs = exIDs, exBcr = exBcr,
                           spotTestCallback=spotTestCallback)
        if len(x) == 0:
            # put a good exception here
            return False
        if len(y) == 0:
            # put a good exception here
            return False
        

        
        if lnX:
            x = Numeric.log(x)
            fields[0] = 'ln(' + fields[0] +')'
        if lnY:
            y = Numeric.log(y)
            fields[1] = 'ln(' + fields[1] +')'
            
        
        plots.scatter(x,y,xlab=fields[0],ylab=fields[1],color=color,bg=bg,symbol=symbol,
                      add=add,printIt=printIt,title=title,xlim=xlim,ylim=ylim,pngFile=pngFile)


    def IDsLike (self,pattern):
        """return a list of IDs that match, in the regexp sense
        the specified pattern. 
        """
        rv = []
        IDregexp = re.compile(pattern)
        for ID in list(self.IDidx.keys()):
            if IDregexp.search(ID) == None:
                continue
            rv.append(ID)

        return rv
            

    def resetNames(self, nameHash, keyColumn='Name'):
        """Set the names to of the DataRecords to the values in hash.
        the keys in the hash should correspond to keyColumn (Name
        by default)
        """

        for rec in self.dataLines:
            if rec.Name in nameHash:
                rec['Name'] = nameHash[rec.Name]

    def testSpots(self,callback):
        """return a list of BCRs whose spots return true
        when tested with the callback function. 
        """

        bcrs = []
        for rec in self.dataLines:
            if callback(rec):
                bcrs.append(rec.BCR)
        return bcrs


class GAL(ATF):
    """Axon Text File Format Array List File (GAL File).
    See module documentation.
    """
    def __init__ (self, inFileName=None):
        """Create a GAL object.
        Optionally read in the named file for the object's definition.
        """
        
        ATF.__init__(self,inFileName=inFileName)
        self.requiredColumns = ["Block", "Column", "Row", "Name","ID"]
        self.requiredColumnPositions.append((0, "Block"))
        self.requiredColumnPositions.append((1,"Column"))
        self.requiredColumnPositions.append((2,"Row"))
        self.requiredColumnPositions.append((4,"Name"))
        self.requiredColumnPositions.append((3,"ID"))
        if inFileName != None and self.Type[:17] !=  'GenePix ArrayList':
                raise ATFInstanceError("File (%s) is not recognized as a 'GenePix ArrayList' file." % inFileName)

        if 'BlockCount' in self.optionalHeaders:
            self.blockCount = self.optionalHeaders['BlockCount']
        else:
            self.blockCount=None

        self.blocks = []

        for k,v in list(self.optionalHeaders.items()):
            if re.match('Block[0-9]+$',k) != None:
                v = list(map(int,v.split(', ')))
                self.blocks.append(Block(k,*v))



	def addBlock (self, block):
		pass

    def printPlates(pins):
        """Return the set of print plates that gives this GAL object.
        """
        pass
    
        
class Block:
    """GAL file block.
    """
    def __init__ (self,name,xOrigin,yOrigin,diameter,
                  xFeatures,xSpacing,
                  yFeatures,ySpacing):
        
        self.blockNumber=int(name.replace('Block',''))
        self.xOrigin=xOrigin
        self.yOrigin=yOrigin
        self.diameter=diameter
        self.xFeatures=xFeatures
        self.xSpacing=xSpacing
        self.yFeatures=yFeatures
        self.ySpacing=ySpacing
        
        self.numberOfRows=self.yFeatures
        self.numberOfCols=self.xFeatures
        
        self.data = []
        self.spotIdx = 0




	def setSize (self,dim):
		self.data = []
		self.numberOfRows,self.numberOfCols = dim
		for r in range(self.numberOfRows):
			self.data.append([None] * self.numberOfCols)

	def contents (self, xxx_todo_changeme):
		(pos) = xxx_todo_changeme
		return self.data[pos[0]-1][pos[1]-1]

	def addSpot (self,spotData):

		row = (self.spotIdx)/self.numberOfCols
		col = self.spotIdx - ((row)*self.numberOfCols)
		#print row,col

		self.data[row][col] = spotData

		self.spotIdx +=1
	
	def BRCformat (self):

		lines = []

		for c in range(self.numberOfCols):
			for r in range(self.numberOfRows):
				lines.append('\t'.join((str(self.blockNumber),str(r+1),str(c+1))
									   + (self.data[r][c])))

		return '\n'.join(lines)
						  
		




class GPR(ATF):
    """ATF Format GenePix Results File.
    """

    def __init__ (self, inFileName=None):
        """Create a GPR object.
        Optionally read in the named file for the object's definition.
        """
        
        ATF.__init__(self,inFileName=inFileName)
        self.requiredColumns = ["Block", "Column", "Row", "Name","ID"]
        self.requiredColumnPositions.append((0, "Block"))
        self.requiredColumnPositions.append((1,"Column"))
        self.requiredColumnPositions.append((2,"Row"))
        self.requiredColumnPositions.append((3,"Name"))
        self.requiredColumnPositions.append((4,"ID"))
        self.dataPercision = 3
        if inFileName != None and self.Type[:15] !=  'GenePix Results' :
            raise ATFInstanceError("File (%s) is not recognized as a 'GenePix Results' file." % inFileName)

            
    
class DataRecord (dict):
    """A data line in a ATF file.
    """
    def __init__ (self,myATF,lineText=None,dataDict=None):
        self.myATF = myATF

        if dataDict == None:
            # make the record form text
            data = lineText.split('\t',self.myATF.colCt - 1)
            if len(data) != self.myATF.colCt:
                print(data)
                raise ATFParseError('Column count (%s) is different that number of columns found (%s).' % (self.myATF.colCt, len(data)))
            # pack my dictionary
            for i in range(len(data)):
                key = self.myATF.columnNames[i]
                if i == self.myATF.IDcol:
                    self[key] = data[i].rstrip(string.whitespace + '"').lstrip(string.whitespace + '"')
                else:
                    self[key] = _GeneralStringConvert(data[i])
        else:
            # no line text
            # make the record from a dictionary
            for key in self.myATF.columnNames:
                if key in dataDict:
                    self[key] = dataDict[key]
                else:
                    self[key] = None


        if self.ID in uid_parameters:
            for (key,value) in  uid_parameters[self.ID].items():
                self[key] = value

        self.BCR = (self.Block, self.Column, self.Row)
        
    def __repr__(self):

        outFields = []
        for fName in self.myATF.fieldOrder():
            f = self[fName]

            if type(f) == StringType:
                outFields.append(''.join(('"',f,'"')))
            elif type(f) == FloatType and self.myATF.dataPercision != None:
                formatSpec = "%%%s.%sf" % (self.myATF.dataPercision+2,self.myATF.dataPercision)
                outFields.append(formatSpec % f)
                
            else:
                outFields.append(str(f))


        return '\t'.join(outFields)

    def __getattr__(self,spec):
        if spec in self:
            return self[spec]
        else:
            print(list(self.__dict__.keys()))
            raise AttributeError("DataRecord has no %s column." % spec)

    
    def __eq__ (self,rec2):
        if self.myATF != rec2.myATF:
            return False

        if self.BCR != rec2.BCR:
            return False

        return True


    def probe70Energy(self, SALT = 0.150, MG=0,T=65):
        """not implemented
        """
        pass
    
