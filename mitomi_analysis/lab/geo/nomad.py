#!/usr/local/bin/python2.2
#
# Classes for NOMAD
#
# 	$Id: nomad.py,v 1.1.1.1 2007/02/15 22:13:25 mdimon Exp $	
#

import os
import re
import string
import time
import MySQLdb
from kdbom import kdbom
import Numeric
from math import ceil
from Axon import ATF


# default NOMAD Connection
defaulthost = 'derisilab12'
defaultDB = 'NOMAD'

# some filters
SPOTFLAG = "Spot_Flag >= 0"


# this is just an object with type = instance
INSTANCE = type(Exception())
STR = type("")
LIST = type([])
DICT = type({})
INT = type(1)
LONG = type(1L)
FLOAT = type(1.)
TUPLE = type(())

TRUE = 1
FALSE = 0

#Nomad exceptions#
class NomadR_Error (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NomadExternalProgram_Error (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NomadConversionError (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class NomadIndexError (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NomadDataError (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# General Functions

def oligoMedianHistory_635(db,uid=None,resultIDs=(),whereClause=SPOTFLAG):
    """Return list of background subtracted oligo history in red channel.
    Flaged sopts (<0) are excluded unless SPOTFLAG is not used as the
    WhereClause argument. whereClause must be a valid MySQL condition,
    e.g. 1=1 minimally. 
    """
    # trap bad input
    if type(db) != INSTANCE or \
           db.__class__ != nomadDB:
        raise TypeError, "Database must be an instance of NomadDB class"

    rv = []
    for rID in resultIDs:
        dataTable=result(db,rID).getDataTable()
        valueQry = """SELECT 635_Median_Intensity, 635_Median_Background
        FROM %s WHERE Result_ID = %%s AND ID = %%s
        AND %s""" % (dataTable,whereClause)
        
        for i,bg in db.fetchall(valueQry,(rID,uid)):
            rv.append(i-bg)
    return rv


def printUIDs(db,printIDs=()):
    """Return a list of (UID,count) tupples for all the oligo UIDs
    found in NOMAD from any results from print runs specified by the
    printIDs. Count is the number of times the UID is referenced in
    all the results.
    """
    # trap bad input
    if type(db) != INSTANCE or \
           db.__class__ != nomadDB:
        raise TypeError, "Database must be an instance of NomadDB class"

    uidD = {}
    for pID in printIDs:
        resultIDs = printRun(db,pID).resultIDs()
        for uid, count in resultUIDs(db,resultIDs).items():
            if uid not in uidD:
                uidD[uid] = 0
            uidD[uid] += count

    return uidD



def resultUIDs(db,resultIDs=()):
    """Return a dictionary of UID:count pairs for all the oligo UIDs
    found in NOMAD from any results specified by the resultIDs. Count
    is the number of times the UID is referenced in all the results.
    """
    # trap bad input
    if type(db) != INSTANCE or \
           db.__class__ != nomadDB:
        raise TypeError, "Database must be an instance of NomadDB class"

    uidD = {}
    for rID in resultIDs:
        dataTable=result(db,rID).getDataTable()
        valueQry = """SELECT ID FROM %s WHERE Result_ID = %%s""" % (dataTable)

        for (uid,) in db.fetchall(valueQry,rID):
            if uid not in uidD:
                uidD[uid] = 0

            uidD[uid] += 1
            
    return uidD
                
    

def elemID(db, UNIQUE_ID):
    """Return the Element_ID for a given Unique_ID"""

    # trap bad input
    if type(db) != INSTANCE or \
           db.__class__ != nomadDB:
        raise TypeError, "Database must be an instance of NomadDB class"

    UNIQUE_ID = re.sub('[\-\'\`\"\s]','',UNIQUE_ID)
    cur=db.con.cursor()
    cur.execute("SELECT Element_ID FROM Element WHERE UNIQUE_ID = %s", (UNIQUE_ID))
    rslt = cur.fetchone()
    if rslt == None:
        return None
    else:
        return rslt[0]



def Rencode(params = {}):
    """Encode params in a dictionary for a call to an R object"""
    result = ''
    for key in params.keys():
        if type(params[key])  == STR:
            #quote strings
            result = "%s, %s=\"%s\"" % (result, key, params[key])
        else:
            #don't quote lists, tuples, arrays, etc...
            result  = "%s, %s=%s" % (result, key, params[key])
        
    return result




# Classes
class nomadDB (kdbom.db):
    def __init__(self,host=defaulthost):
##        kdbom.db.__init__(self, host=defaulthost,user=defaultuser,
##                          passwd=defaultpw,db='NOMAD')
        kdbom.db.__init__(self, db='NOMAD',host=host,getTables=False)
        #
        # Result Relationships
        #
        kdbom.relationship(child=self.Result.Table_Index_ID,
                           parent=self.Table_Index.Table_Index_ID).insert()

        kdbom.relationship(self.Parameter.Parameter_ID,
                       self.Result_Parameter.Parameter_ID).insert()
        
        kdbom.relationship(self.Result.Result_ID,
                           self.Result_Parameter.Result_ID).insert()

        kdbom.relationship(self.Array.Array_ID,
                           self.Array_Result.Array_ID).insert()

        kdbom.relationship(self.Result.Result_ID,
                           self.Array_Result.Result_ID).insert()

        kdbom.relationship(self.Array.User_ID,
                           self.User.User_ID).insert()
        #
        # Experiment Relationships
        #
        kdbom.relationship(child=self.Experiment_Sample.Experiment_ID,
                           parent=self.Experiment.Experiment_ID).insert()
        kdbom.relationship(child=self.Experiment.Experiment_ID,
                           parent=self.Experiment_Array.Experiment_ID).insert()
        kdbom.relationship(child=self.Array.Array_ID,
                           parent=self.Experiment_Array.Array_ID).insert()


        #
        # Project Relationships
        #
        kdbom.relationship(child=self.Experiment.Experiment_ID,
                           parent=self.Project_Experiment.Experiment_ID).insert()
        kdbom.relationship(child=self.Project.Project_ID,
                           parent=self.Project_Experiment.Project_ID).insert()

        #
        # Array Relationships
        #

        # samples
        kdbom.relationship(self.Array.Array_ID,
                           self.Array_Sample.Array_ID).insert()
        kdbom.relationship(self.Sample.Sample_ID,
                           self.Array_Sample.Sample_ID).insert()
        # parameters
        kdbom.relationship(self.Array.Array_ID,
                           self.Array_Parameter.Array_ID).insert()
        kdbom.relationship(self.Parameter.Parameter_ID,
                           self.Array_Parameter.Parameter_ID).insert()


        #
        # Sample Relationships
        #

        # Labels (Dyes)
        kdbom.relationship(self.Label_Type.Label_Type_ID,
                           self.Array_Sample.Label_Type_ID)
                           
        
    def getArray(self,arrayName):
        return array(self,arrayName)
        

    def getResult(self,resultID):
        return result(self,resultID)
        
        pass

    def getPrint(self,printID):
        return printRun(self,printID)


    def dataTables (self, resultClass):
        """Return a list of the tables containing data
        for results of the specified result class."""

        # trap bad input
        if type(resultClass) != INT:
            raise TypeError, "resultClass must be an integer"

        tblList = []

        for name in self.table_names:
            classMatch = re.match('Result_Class_(?P<class>\d+)_Data_(?P<tableNumber>\d+)',name)
            if classMatch:
                if int(classMatch.groupdict()['class']) == resultClass :
                    tblList.append(self[name])
                
        return tblList

    def experiments(self):
        return self.Experiment.Experiment_Name.values
        

class project (kdbom.record):
    def __init__(self,db,projectName=None,projectID=None):
        
        # trap bad input
        if type(db) != INSTANCE or \
               db.__class__ != nomadDB:
            raise TypeError, "Database must be an instance of NomadDB class."

        if type(projectName) != type('') and type(projectName) != type(None):
            raise TypeError, "projectName must be a string."

        if type(projectID) != type(1) and type(projectID) != type(None):
            raise TypeError, "projectID must be a integer."

        if projectName != None:
            try:
                projectID = db.Project(Project_Name=projectName)[0].Project_ID
            except AttributeError,IndexError:
                raise  NomadIndexError, "Project (%s) not found" % (projectName)
        try:
            kdbom.record.__init__(self,db['Project'],projectID)
        except:
            raise  NomadIndexError, "Project (%d) not found" % (projectID)

    def experimentIDs(self):
        try:
            experiments = self.children(self.db.Experiment)
            experimentIDs = []
            for ex in experiments:
                experimentIDs.append(ex.Experiment_ID)
        except:
            raise  NomadIndexError, "Result for Project (%s) not found" % (self.Experiment_Name)

        return experimentIDs


class experiment (kdbom.record):
    def __init__(self,db,experimentName=None,experimentID=None):
        
        # trap bad input
        if type(db) != INSTANCE or \
               db.__class__ != nomadDB:
            raise TypeError, "Database must be an instance of NomadDB class."

        if type(experimentName) != type('') and type(experimentName) != type(None):
            raise TypeError, "experimentName must be a string."

        if type(experimentID) != type(1) and type(experimentID) != type(None):
            raise TypeError, "experimentID must be a integer."

        if experimentName != None:
            try:
                experimentID = db.Experiment(Experiment_Name=experimentName)[0].Experiment_ID
            except AttributeError,IndexError:
                raise  NomadIndexError, "Experiment (%s) not found" % (experimentName)
        try:
            kdbom.record.__init__(self,db['Experiment'],experimentID)
        except:
            raise  NomadIndexError, "Experiment (%d) not found" % (experimentID)

    def arrayIDs(self):
        try:
            arrays = self.children(self.db.Array)
            arrayIDs = []
            for arr in arrays:
                arrayIDs.append(arr.Array_ID)
        except:
            raise  NomadIndexError, "Result for Experiment (%s) not found" % (self.Array_Name)
        return arrayIDs


class array (kdbom.record):
    def __init__(self,db,arrayName=None,arrayID=None):
        
        # trap bad input
        if type(db) != INSTANCE or \
               db.__class__ != nomadDB:
            raise TypeError, "Database must be an instance of NomadDB class."

        if type(arrayName) != type('') and type(arrayName) != type(None):
            raise TypeError, "arrayName must be a string."

        if type(arrayID) != type(1) and type(arrayID) != type(None):
            raise TypeError, "arrayID must be a integer."

        if arrayName != None:
            try:
                arrayID = db.Array(Array_Name=arrayName)[0].Array_ID
            except AttributeError,IndexError:
                raise  NomadIndexError, "Array (%s) not found" % (arrayName)
        try:
            kdbom.record.__init__(self,db['Array'],arrayID)
        except:
            raise  NomadIndexError, "Array (%d) not found" % (arrayID)

    def result(self):
        try:
            resultID = self.children(self.db.Array_Result)[0].Result_ID
        except:
            raise  NomadIndexError, "Result for Array (%s) not found" % (self.Array_Name)

        return result(self.db, resultID)

    def resultID (self):
        try:
            resultID = self.children(self.db.Array_Result)[0].Result_ID
        except:
            raise  NomadIndexError, "Result for Array (%s) not found" % (self.Array_Name)
        return resultID


    def purgeArray(self):

        R = self.result()
        R.deleteData()
        R.deleteParameters()
        R.delete()

        self.Array_Result[0].delete()
        self.delete()
        
    def user(self):
        return self.children(self.db.User)[0]

    def cy3Sample(self):
        sampleIDs = self.db.fetchall("""select Sample_ID from Array_Sample
        Natural Join Label_Type Where Array_ID = %s
        and Label_Type_Name Like "Cy3%%" """, self['Array_ID'])
        try:
            return self.db.Sample[sampleIDs[0][0]]
        except:
            return sampleIDs

    def cy5Sample(self):
        sampleIDs = self.db.fetchall("""select Sample_ID from Array_Sample
        Natural Join Label_Type Where Array_ID = %s
        and Label_Type_Name Like "Cy5%%" """, self['Array_ID'])
        return self.db.Sample[sampleIDs[0][0]]
    
        

class result (kdbom.record):
    def __init__(self,db,resultID,dataTableName = None, blockCount=None,
             rowsPerBlock=None, colsPerBlock=None):

        # trap bad input
        if type(db) != INSTANCE or \
               db.__class__ != nomadDB:
            raise TypeError, "Database must be an instance of NomadDB class"


        # results are really records in the
        # NOMAD.Results table so this instance
        # subclasses the record class
        try:
            kdbom.record.__init__(self,db['Result'],resultID)
        except AttributeError:
            raise  NomadIndexError, "data for Result_ID(%s) not found" % (resultID)

        self.resultID = resultID

        if  dataTableName:
            self.dataTableName = dataTableName
        else:
            self.dataTableName = self.getDataTable()


        self.dataTable = eval("self.db.%s"%(self.dataTableName))

        self.array = self.getArray()
        self.printRun = self.getPrint()

        self.__Geometry = None


    def __getGeometry__(self):
        # get some array geometery
        self.blockCount = self.getBlockCount()
        
        if (self.blockCount == 1):
            self.columnsOfBlocks = 1
        elif (self.blockCount == 4):
            self.columnsOfBlocks = 2
        else:
            self.columnsOfBlocks = 4


        if (self.blockCount == 1): 
            self.rowsOfBlocks = 1
        elif (self.blockCount == 4):
            self.rowsOfBlocks = 2
        elif (self.blockCount == 16):
            self.rowsOfBlocks = 4
        elif (self.blockCount == 32):
            self.rowsOfBlocks = 8
        elif (self.blockCount == 48):
            self.rowsOfBlocks = 12
        else:
            raise NomadDataError, "Number of blocks in array (%s )is weird" % (self.blockCount)



        self.rowsPerBlock = self.getRowsPerBlock()

        self.colsPerBlock = self.getColsPerBlock()

        self.totalRows = self.rowsOfBlocks * self.rowsPerBlock
        self.totalCols = self.columnsOfBlocks * self.colsPerBlock
        self.__Geometry = TRUE

    def spots(self):
        """Returns a list of NOMAD data table records for this result."""
        return self.dataTable.Result_ID.search(self.resultID)


    def getDataTable(self):
        cur=self.db.con.cursor()
        cur.execute("Select Table_Name from Table_Index\
                     left join Result using (Table_Index_ID) \
                     where Result_ID = %s",
                    (self.resultID))
        rslt = cur.fetchone()

        if rslt == None:
            raise NomadIndexError, "data for Result_ID(%s) not found" % (self.resultID)
        else:
            return rslt[0]


    def deleteData(self):
        self.db.execute("""DELETE FROM %s
                           WHERE Result_ID = %s""" %
                        (self.getDataTable(), self.resultID))


    def deleteParameters(self):
        self.db.execute("""DELETE FROM Result_Parameter
                           WHERE Result_ID = %s""" %  (self.resultID))

    

       
    def getBlockCount(self):
        if self.dataTableName == None:
            self.dataTableName = self.getDataTable(db)

        cur=self.db.con.cursor()
        cur.execute("Select max(Array_Block) from %s where Result_ID = '%s'" %
                    (self.dataTableName,self.resultID))
        rslt = cur.fetchone()
        if rslt == None:
            raise NomadIndexError, "data for Result_ID(%s) not found in NOMAD.%s" \
                  % (self.resultID,self.dataTableName)
        else:
            return rslt[0]

    def getRowsPerBlock (self):
        if self.dataTableName == None:
            self.dataTableName = self.getDataTable()
        cur=self.db.con.cursor()
        cur.execute("Select max(Array_Row) from %s where Result_ID = '%s'" %
                    (self.dataTableName,self.resultID))
        rslt = cur.fetchone()
        if rslt == None:
            raise NomadIndexError, "data for Result_ID(%s) not found in NOMAD.%s" \
                  % (self.resultID,self.dataTableName)
        else:
            return rslt[0]


    def getColsPerBlock (self):
        if self.dataTableName == None:
            self.dataTableName = self.getDataTable()
        cur=self.db.con.cursor()
        cur.execute("Select max(Array_Column) from %s where Result_ID = '%s'" %
                    (self.dataTableName,self.resultID))
        rslt = cur.fetchone()
        if rslt == None:
            raise NomadIndexError, "data for Result_ID(%s) not found in NOMAD.%s" \
                  % (self.resultID,self.dataTableName)
        else:
            return rslt[0]

    def getFeatureRange(self):
        pass

    def arrayMapXYZ(self,feature = "Array_Block") :
        """return a dict of arrays a,x,z"""

        if not self.__Geometry:
            self.__getGeometry__()


        minimum = -50000

        map = {}
        
        map['x'] = Numeric.ones((self.totalCols*self.totalRows),Numeric.Float) * minimum
        map['y'] = Numeric.ones((self.totalCols*self.totalRows),Numeric.Float) * minimum
        map['z'] = Numeric.ones((self.totalCols*self.totalRows),Numeric.Float) * minimum
        

        cur=self.db.con.cursor()
        cur.execute( "Select Array_Block, Array_Column, Array_Row, %s \
                      from %s where Result_ID = '%s'\
                      order by Array_Block, Array_Row, Array_Column"
                     % (feature, self.dataTableName,self.resultID))


        record = cur.fetchone()
        minimum = record[3]
        maximum = minimum
        i=0
        while record:
            (block,col,row,f) = record
            record = cur.fetchone()
            
            block_remainder = block % self.columnsOfBlocks

            if (block_remainder == 0) :
                columnBlock = self.columnsOfBlocks
            else:
                columnBlock = block_remainder

            # determine offsets from block number
            x = int( col - 1 +((columnBlock-1) * self.colsPerBlock))
            rowBlock = ceil(float(block) / self.columnsOfBlocks)
            y = self.totalRows - int( row + ((rowBlock-1) * self.rowsPerBlock)) 

            if f < minimum:
                minimum = f
            elif f > maximum:
                maximum = f
            
            map['x'][i] = x
            map['y'][i] = y
            map['z'][i] = f
            i=i + 1

        return (map)


    def dislinFeatureMap(self, feature = "Array_Block",
                         colors="grey", fileName=None):
        try:
            import dislin
        except:
             raise NomadExternalProgram_Error, "Can't find 'dislin' graphics library."
            

        if not self.__Geometry:
            self.__getGeometry__()

        map = self.arrayMapXYZ(feature)
        Xmin = min(map['x'])
        Xmax = max(map['x'])
        Ymin = min(map['y'])
        Ymax = max(map['y'])
        Zmin = min(map['z'])
        Zmax = max(map['z'])
        
        dX = Xmax-Xmin
        dY = Ymax-Ymin
        dZ = Zmax-Zmin

        featurePixels = 10
        
        if fileName == None:
            dislin.metafl('xwin')
            dislin.clrmod('FULL')

        else:
            dislin.metafl('png')
            
            
        dislin.scrmod('REVERS')
        dislin.disini()
        dislin.pagera ()

#        dislin.revscr()
        title1 = 'yow Are We Having Fun Yet'

        dislin.name   ('Z-axis', 'Z')

        dislin.axclrs(254,'ALL','XYZ')
        dislin.labels('NONE','XY')
        dislin.intax()
        dislin.ticks(1,'XY')
        dislin.ticks(1,'Z')
        dislin.ticlen(10,5)

        dislin.frmclr(254)
#        dislin.setrgb(.5,.5,.5)        

 

        dislin.setvlt('RGREY')


        dislin.autres(dX, dY)
        dislin.ax3len(dX*featurePixels,
                      dY*featurePixels,
                      dY*featurePixels)

#        dislin.color('WHITE')
        dislin.height (30)        
        dislin.titlin(title1,4)        

        dislin.graf3(Xmin,Xmax,Xmin,self.colsPerBlock,
                     Ymin,Ymax,Ymin,self.rowsPerBlock,
                     Zmin,Zmax,Zmin,int(dZ/5))


        dislin.curve3(map['x'],map['y'],map['z'],len(map['z']))
        dislin.title()
        dislin.disfin()



    def disipylFeatureMap(self, feature = "Array_Block",
                         colors="grey", fileName=None, title=None):

        try:
            from disipyl import plots, contours, pxdislin,pydislin
        except:
             raise NomadExternalProgram_Error, "Can't find 'disipyl' graphics library."
         
        if not self.__Geometry:
            self.__getGeometry__()


        map = self.arrayMap(feature)
        (Xmin, Ymin) = (1,1)
        (Xmax, Ymax) = map[0].shape
        Zmin = map[1]
        Zmax = map[2]
        
        dX = Xmax-Xmin
        dY = Ymax-Ymin
        dZ = Zmax-Zmin

        if not title:
            title=self.array.Array_Name+"\n"+feature


        featurePixels = 10


        plot=contours.ColorPlot()
#        plot.setTickLength(5,10)
        plot.title = pxdislin.Title(title)

        plot.axes(lengths = (featurePixels*dX,
                             featurePixels*dY,
                             featurePixels*dY ),
###                  pageposition = (300,1850),
                  autoresolution = (dX,dY))
                  


        plot.axes.xaxis( min=Xmin,
                         max=Xmax,
                         tickstart=Xmin,
                         tickstep=self.colsPerBlock,
                         ticklength=(10,0),
                         labeltype='none')
        
        plot.axes.yaxis(min=Ymin,
                        max=Ymax,
                        tickstart=Ymin,
                        tickstep=self.rowsPerBlock,
                        labeltype='none')

        plot.axes.zaxis(min=Zmin, 
                        max=Zmax, 
                        tickstart= Zmin, 
                        tickstep = int(dZ/5))
                         
        nr, nc = map[0].shape
        colormatrix = contours.ColorMatrix(map[0],nr,nc)
        plot.add(colormatrix)

        
        canvas = pxdislin.Canvas(plot)
        canvas.draw()

    def vector(self,feature = "F635_Median_Net"):
        """return a Scipy vector with the requested feature in
        Block, Row, Column order."""
        cur=self.db.con.cursor()
        cur.execute( "Select %s \
                      from %s where Result_ID = '%s'\
                      order by Array_Block, Array_Row, Array_Column"
                     % (feature, self.dataTableName,self.resultID))

        data = cur.fetchall()
        return Numeric.array(data,Numeric.Float)
        
        
    def idList (self):
        """return a list of (ID,occurrence) tuples in
        Block, Row, Column order.
        """
        cur=self.db.con.cursor()
        cur.execute( "Select ID,Element_Occurrence  \
                      from %s where Result_ID = '%s'\
                      order by Array_Block, Array_Row, Array_Column"
                     % (self.dataTableName,self.resultID))

        return cur.fetchall()
        
        

    def arrayMap(self,feature = "Array_Block") :
        """return a a lists of x, y and z ->  col, row, <result feature>"""

        if not self.__Geometry:
            self.__getGeometry__()

        minimum = -50000


        data = Numeric.ones((self.totalCols,self.totalRows),Numeric.Float) * minimum


        cur=self.db.con.cursor()
        cur.execute( "Select Array_Block, Array_Column, Array_Row, %s \
                      from %s where Result_ID = '%s'\
                      order by Array_Block, Array_Row, Array_Column"
                     % (feature, self.dataTableName,self.resultID))


        record = cur.fetchone()
        minimum = record[3]
        maximum = minimum
        
        while record:
            (block,col,row,f) = record
            record = cur.fetchone()
            
            block_remainder = block % self.columnsOfBlocks

            if (block_remainder == 0) :
                columnBlock = self.columnsOfBlocks
            else:
                columnBlock = block_remainder

            # determine offsets from block number
            x = int( col - 1 +((columnBlock-1) * self.colsPerBlock))
            rowBlock = ceil(float(block) / self.columnsOfBlocks)
            y = self.totalRows - int( row + ((rowBlock-1) * self.rowsPerBlock)) 

            if f < minimum:
                minimum = f
            elif f > maximum:
                maximum = f
            
            data[x,y] = f

        return (data, minimum, maximum)

    
    
    def drawFeatureMap(self, feature = "Array_Block",
                       map = None,fileName = None ,title=None,
                       Zrange = None, grey = 1,pctClipTop=None, pctClipBottom=None, show=False):
        
        if not self.__Geometry:
            self.__getGeometry__()

        try:
            import Gnuplot
        except:
            pass
            raise NomadExternalProgram_Error, "Can't work with Gnuplot."
        
        if not map:
            data,mapMin,mapMax = self.arrayMap(feature=feature)

        clippingTxt = []
        clippingText = ''
        (Xmin, Ymin) = (1,1)
        (Xmax, Ymax) = data.shape

        if not Zrange:
            Zmin = mapMin
            Zmax = mapMax
            if pctClipBottom != None or pctClipTop != None:
                tempVector = Numeric.resize(data,(1,Xmax*Ymax))[0]
                orderedIndicies = Numeric.argsort(tempVector)
                n = len(orderedIndicies)

                if pctClipBottom != None:
                    clippingTxt.append('bottom %4.1f%% of spots clipped ' % float(pctClipBottom))
                    clipN = int(float(pctClipBottom)/100.0 * float(n))
                    Zmin = tempVector[orderedIndicies[clipN]]
                    for i in range (0,clipN-1):
                        tempVector[orderedIndicies[i]] = Zmin

                if pctClipTop != None:
                    clippingTxt.append('top %4.1f%% of spots clipped ' % float(pctClipTop))
                    clipN = int(float(pctClipTop)/100.0 * float(n))
                    print n, clipN
                    Zmax = tempVector[orderedIndicies[-clipN+1]]
                    for i in range(-clipN,-1):
                        tempVector[orderedIndicies[i]] = Zmax

                clippingText = string.join((clippingTxt),'; ')
                data = Numeric.resize(tempVector,data.shape)
                
            
        else:
            Zmin = Zrange[0]
            Zmax = Zrange[1]
            clippingText = ''
        
        Xscale = float(self.totalCols)/max((self.totalCols,self.totalRows))*0.5
        Yscale = float(self.totalRows)/max((self.totalCols,self.totalRows))

        overallScale = 2

        if not title:
            title=self.array.Array_Name+": "+feature +"\\n" + clippingText + "\\n "
            

        Gnuplot.GnuplotOpts.prefer_inline_data=1
        Gnuplot.GnuplotOpts.recognizes_binary_splot=0
        gp = Gnuplot.Gnuplot()

        gp("set pm3d map")

        gpdata = Gnuplot.GridData(data,range(1,Xmax+1),range(1,Ymax+1),inline=True)

        gp("set key off")
        gp('set title "%s"' % (title))

        if grey == 1:
            gp('set palette gray negative')
            
        gp('set format xy "" ')
        gp('set ytics 0, %s' % (self.rowsPerBlock))  
        gp('set xtics 0, %s' % (self.colsPerBlock))
        gp('set tmargin 2')
        gp('set bmargin 2')

        gp('set zrange [%s:%s]' % (Zmin,Zmax))
        
        gp('set size %s,%s' %(Xscale*overallScale, Yscale*overallScale))
        


        gp('set terminal x11')
        
        if fileName != None:
            # this is so that gp will use png!
            #
            gp('set terminal gif')
            gp('set out "%s"' % (fileName))

        gp.splot(gpdata)

        if fileName == None:
            raw_input("press key to continue...")
        elif show:
            del gp
            os.system("display %s" % fileName)
   
    def drawScatterPlot(self, x=None, y=None, xlab=None, ylab=None, 
                        title=None, fileName=None, log = ""):
        if not self.__Geometry:
            self.__getGeometry__()

        try:
            import Gnuplot
        except:
            raise NomadExternalProgram_Error, "Can't work with gnuplot."

        if not xlab:
            xlab = x
            
        if not ylab:
            ylab = y

        Gnuplot.GnuplotOpts.prefer_inline_data=1
        Gnuplot.GnuplotOpts.recognizes_binary_splot=0 
        gp = Gnuplot.Gnuplot()
       
        if not title:
            title=self.array.Array_Name

        gp('set title "%s"' % (title))
        gp('set xlabel "%s"' % (xlab))
        gp('set ylabel "%s"' % (ylab))
        
        data = self.arrayFeatures((x,y))
        d = Gnuplot.Data(data)

        if log == "xy":
            gp('set logscale xy 10')
        elif log == "x":
            gp('set logscale x 10')
        elif log == "y":
            gp('set logscale y 10')
        else:
            gp('set nologscale')

        gp('set size square')
        gp('unset key')

        gp('set terminal x11')
        
        if fileName != None:
            gp('set terminal gif')
            gp('set out "%s"' % (fileName))

        gp.plot(d)
        


    def drawRFeatureMap(self, feature = "Array_Block",
                        map = None,fileName = None ,title=None, **Rkeywds):

        if not self.__Geometry:
            self.__getGeometry__()

        try:
            # r plotting requirements
            from rpy import r
            #uselessOutput = r.library('fields')
        except:
            raise NomadR_Error, "Can't work with R."
        
        if not map:
            map = self.arrayMap(feature=feature)
            if not title:
                title=self.array.Array_Name+"\n"+feature

        keywds = {}
        keywds['col'] = r.gray(r.seq(1,0,-0.01))
        keywds['zlim'] = (map[1], map[2])
        keywds['pty'] = 's'
        keywds['axes'] = 0

        keywds.update(Rkeywds)
            
        r.par(mai=[0.2,0.2,0.6,0.2])
        if fileName != None:
             r.postscript(file=fileName+'.ps',horizontal=0)

        eval("r.image(map[0],main=title %s)" % Rencode(keywds))
        r.box()
        
        if fileName != None:
            r.dev_off()
            os.system("convert -rotate +90 %s.ps %s.png" % (fileName,fileName))

        

    def drawRScatterPlot(self, x=None, y=None, xlab=None, ylab=None,
                        title=None, fileName=None, log = "", **Rkeywds):
        if not self.__Geometry:
            self.__getGeometry__()

        try:
            # r plotting requirements
            from rpy import r
            r.graphics_off()
        except:
            raise NomadR_Error, "Can't work with R."

        if not title:
            title=self.array.Array_Name

        if not xlab:
            xlab = x
            
        if not ylab:
            ylab = y

        data = self.arrayFeatures((x,y),vectors=1)
        xyRange = (min(min(data[0],data[1]))[0],max(max(data))[0])

        kwstring = Rencode(Rkeywds)

        if fileName != None:
            r.graphics_off()
            r.png(filename=fileName,width=750,height=750)

        eval("r.plot(data[0],data[1],xlab=x,xlim=xyRange,ylim=xyRange,pty='s', ylab=y, main=title, log=log%s)" % (kwstring) )
        
        if fileName != None:
            r.graphics_off()




    def arrayFeatures(self,features, vectors=0,ID=None):
        """Return a 2D Numeric array with number of columns = number of features and as
        many rows as spots with non null values for each feature.  If vectors=1 returns
        a list of 1D Numeric vectors filed filled with the result feature values."""

        if (type(features) != LIST and type(features) != TUPLE )\
               or len(features) < 1:
            raise TypeError, "features must be a list or tuple."

        f_range = range(len(features))
        
        # build SQL
        SQLfields = ' `' + string.join(features,'`, `') + '` '
        SQLwheres = ' WHERE `' + string.join(features,'` IS NOT NULL AND `') +\
                    '` IS NOT NULL AND `result_ID` = %s '  
        if ID != None:
            SQLwheres += "AND `ID` = '%s' " % ID 

        SQLquery = "Select" + SQLfields + "FROM `%s`" +\
                   SQLwheres + "order by Array_Block, Array_Row, Array_Column" 

        #send query
        cur=self.db.con.cursor()
        r_count = cur.execute(SQLquery % (self.dataTableName,self.resultID))

        #make vectors or array
        if vectors == 1:
            result = []
            for fi in f_range:      
                result.append(Numeric.zeros((r_count,1),Numeric.Float))
        else:
            result = Numeric.zeros((r_count,len(features)),Numeric.Float)
            
        #fill vectors
        for ri in range(r_count):
            record = cur.fetchone()
            for fi in f_range:
                if vectors == 1:
                    result[fi][ri] = record[fi]
                else:
                    result[ri][fi] = record[fi]
                    
        return result

 
        
    def features(self, range = None, min=None, max=None):
        pass
        return self.db[self.dataTableName].fields.keys()
        

    def getArray (self):
        SQLquery = "SELECT Array.Array_ID FROM \
                    Array_Result NATURAL JOIN Array \
                    WHERE Result_ID = %s"

        cur=self.db.con.cursor()
        cur.execute(SQLquery,(self.resultID))
        arrayID = cur.fetchone()[0]
        return array(self.db,arrayID=arrayID)
        

    def getPrint  (self):
        SQLquery = "SELECT Print_ID \
                    FROM `Result` NATURAL JOIN `Array_Result` \
                    NATURAL JOIN `Array` \
                    NATURAL JOIN `Chip` \
                    WHERE Result.Result_ID = %s "
        cur=self.db.con.cursor()
        cur.execute(SQLquery,(self.resultID))
        arrayID = cur.fetchone()[0]
        return self.db['Print'][arrayID]

    def getValues(self, uids=None, fields = ['635_Median_Intensity'],
                  ignoreFlag = False):

        rv = []

        if ignoreFlag:
            fWhere = ''
        else:
            fWhere = 'AND Spot_Flag >= 0'


        fieldList = string.join(fields,',')

        if uids == None:
            qry = ("""SELECT %s FROM %s WHERE Result_ID = %%s %s""" %
                   (fieldList,self.getDataTable(),fWhere))
            return self.db.fetchall(qry,(self.resultID))

         
        qry = """SELECT %s FROM %s NATURAL JOIN Element
        WHERE Result_ID = %s AND UNIQUE_ID = %%s""" \
        % (fieldList,self.getDataTable(),self.resultID)

        
        for uid in uids:
            cur = self.db.con.cursor()
            cur.execute(qry,(uid))
            rv.extend(cur.fetchall())
        return rv


    def getAverageValues(self, fields = ['635_Median_Intensity'],
                  ignoreFlag = False, groupBy='Element_ID'):
        
         rv = []

         if ignoreFlag:
             fWhere = ''
         else:
             fWhere = 'AND Spot_Flag >= 0'


         for i in range(len(fields)):
             fields[i] = "AVG(%s)"%fields[i]

         fieldList = ','.join(fields)

         qry = ("""SELECT %s,%s FROM %s WHERE Result_ID = %%s %s GROUP BY %s""" %
                (groupBy,fieldList,self.getDataTable(),fWhere,groupBy))
         return self.db.fetchall(qry,(self.resultID))

         
    def sumValue(self,field = '635_Median_Intensity',filter=[]):
        rv = None
        cur = self.db.cursor()
        cur.execute("SELECT SUM(%s) FROM %s WHERE Result_ID = '%s'" % (field,self.getDataTable(),self.resultID))
        rv = cur.fetchone()[0]
        return rv

    def getSumNormValues(self, uids, fields = ['635_Median_Intensity']):

        rv = []

        sums = []
        for f in fields:
            sums.append(self.sumValue(f))

        
        fieldList = string.join(fields,',')
        
        qry = """SELECT %s FROM %s NATURAL JOIN Element
        WHERE Result_ID = %s AND UNIQUE_ID = %%s""" \
        % (fieldList,self.getDataTable(),self.resultID)

        
        for uid in uids:
            cur = self.db.con.cursor()
            cur.execute(qry,(uid))
            
            for row in cur.fetchall():
                normR = []
                for i in range(len(fields)):
                    normR.append(row[i]/sums[i])

                if len(fields) == 1:
                    rv += normR
                else:
                    rv.append(normR)
        return rv

    def GPRData(self,spot):
        rDict = {}
        spotDict = spot.data

        qry = """SELECT Field_Name,Vendor_Label
        FROM  Result_Class_Field NATURAL JOIN Field_Index
        WHERE Result_Class_ID = 1 ORDER BY Vendor_Order"""

        cur = self.db.con.cursor()
        cur.execute(qry)
        for nomadName, gprName in cur.fetchall():
            if nomadName in spotDict:
                rDict[gprName]=spotDict[nomadName]
            else:
                rDict[gprName] = None
        return rDict
        
    def GPRColumns(self):
        rList = []


        qry = """SELECT Vendor_Label
        FROM  Result_Class_Field
        WHERE Result_Class_ID = 1 ORDER BY Vendor_Order"""

        cur = self.db.con.cursor()
        cur.execute(qry)
        for (gprName,) in cur.fetchall():
            rList.append(gprName)
        return rList
        




    def getResultParameters(self):
        """Return a dictionary of result parameters.
        """

        rDict={}

        qry = """SELECT Parameter_Name, Value
              FROM Parameter NATURAL JOIN Result_Parameter
              WHERE Result_ID = %s
        """
        cur = self.db.cursor()
        cur.execute(qry,(self.resultID))
        for paramName,paramValue in cur.fetchall():
            rDict[paramName] = paramValue 
                
        return rDict
        

    def GPR(self):
        """Return a GPR instance that is (hopefully) equivalent to this result.
        """
        
        
        rsltParams = self.getResultParameters()

        rObj = ATF.GPR()
        rObj.version = 1.0

        rObj.addHeader('Type')
        rObj.addHeader('DateTime')
        rObj.addHeader('Settings')
        rObj.addHeader('GalFile')
        rObj.addHeader('Scanner')
        rObj.addHeader('Comment')
        rObj.addHeader('PixelSize')
        rObj.addHeader('ImageName')
        rObj.addHeader('FileName')
        rObj.addHeader('PMTVolts')
        rObj.addHeader('ScanPower')
        rObj.addHeader('FocusPosition')
        rObj.addHeader('NormalizationFactor:RatioOfMedians')
        rObj.addHeader('NormalizationFactor:RatioOfMeans')
        rObj.addHeader('NormalizationFactor:MedianOfRatios')
        rObj.addHeader('NormalizationFactor:MeanOfRatios')
        rObj.addHeader('NormalizationFactor:RegressionRatio')
        rObj.addHeader('JpegImage')
        rObj.addHeader('RatioFormulation')
        rObj.addHeader('Barcode')
        rObj.addHeader('ImageOrigin')
        rObj.addHeader('JpegOrigin')
        rObj.addHeader('Creator')
        rObj.addHeader('Recreator')
        rObj.addHeader('Temperature')
        rObj.addHeader('LaserPower')
        rObj.addHeader('LaserOnTime')
        rObj.addHeader('Supplier')

        try:
            rObj.optionalHeaders['Type']=rsltParams['GP3_Type']
        except:
            pass
        try:
            year,month,day = rsltParams['GP3_Scan_Date'].split('-')
            rObj.optionalHeaders['DateTime']="%s/%s/%s %s" % (year,month,day,rsltParams['GP3_Scan_Time'])
        except:
            pass
        try:
            rObj.optionalHeaders['Settings']=rsltParams['GP3_Settings_File']
        except:
            pass
        try:
            rObj.optionalHeaders['GalFile']=rsltParams['GP3_GAL_File']
        except:
            pass
        try:
            rObj.optionalHeaders['Scanner']=rsltParams['GP3_Scanner']
        except:
            pass
        try:
            rObj.optionalHeaders['Comment']=rsltParams['GP3_Comment']
        except:
            pass
        try:
            rObj.optionalHeaders['PixelSize']=rsltParams['GP3_Pixel_Size']
        except:
            pass
        try:
            rObj.optionalHeaders['ImageName']="%s\t%s" % (rsltParams['GP3_532_TIFF_File'],
                                                          rsltParams['GP3_635_TIFF_File'])
        except:
            pass
        try:
            rObj.optionalHeaders['FileName']="%s nm\t%s nm" % (rsltParams['GP3_532_Wavelength'],
                                                               rsltParams['GP3_635_Wavelength'])
        except:
            pass
        try:
            rObj.optionalHeaders['PMTVolts']="%s\t%s" % (rsltParams['GP3_532_PMT_Voltage'],
                                                         rsltParams['GP3_635_PMT_Voltage'])
        except:
            pass
        try:
            rObj.optionalHeaders['ScanPower']="%s\t%s" % (rsltParams['GP3_532_Laser_Power'],
                                                          rsltParams['GP3_635_Laser_Power'])
        except:
            pass
        try:
            rObj.optionalHeaders['FocusPosition']=rsltParams['GP3_Focus_Position']
        except:
            pass
        try:
            rObj.optionalHeaders['NormalizationFactor:RatioOfMedians']=rsltParams['GP3_Ratio_Of_Medians_NF']
        except:
            pass
        try:
            rObj.optionalHeaders['NormalizationFactor:RatioOfMeans']=rsltParams['GP3_Ratio_Of_Means_NF']
        except:
            pass
        try:
            rObj.optionalHeaders['NormalizationFactor:MedianOfRatios']=rsltParams['GP3_Median_Of_Ratios_NF']
        except:
            pass
        try:
            rObj.optionalHeaders['NormalizationFactor:MeanOfRatios']=rsltParams['GP3_Mean_Of_Ratios_NF']
        except:
            pass
        try:
            rObj.optionalHeaders['NormalizationFactor:RegressionRatio']=rsltParams['GP3_Regression_Ratio_NF']
        except:
            pass
        try:
            rObj.optionalHeaders['JpegImage']=rsltParams['GP3_JPEG_File']
        except:
            pass
        try:
            rObj.optionalHeaders['RatioFormulation']=rsltParams['GP3_Ratio_Formulation']
        except:
            pass
        try:
            rObj.optionalHeaders['Barcode']=rsltParams['GP3_Barcode']
        except:
            pass
        try:
            rObj.optionalHeaders['ImageOrigin']="%s,\t%s" % (rsltParams['GP3_Image_Origin_X_Coordinate'],
                                                             rsltParams['GP3_Image_Origin_Y_Coordinate'])
        except:
            pass
        try:
            rObj.optionalHeaders['JpegOrigin']="%s,\t%s" % (rsltParams['GP3_JPEG_Origin_X_Coordinate'],
                                                            rsltParams['GP3_JPEG_Origin_Y_Coordinate'])
        except:
            pass
        try:
            rObj.optionalHeaders['Creator']=rsltParams['GP3_Creator']
        except:
            pass
        try:
            rObj.optionalHeaders['Recreator'] = '$Id: nomad.py,v 1.1.1.1 2007/02/15 22:13:25 mdimon Exp $'
        except:
            pass
        try:
            rObj.optionalHeaders['Temperature']=rsltParams['GP3_Temperature']
        except:
            pass
        try:
            rObj.optionalHeaders['LaserPower']="%s\t%s" % (rsltParams['GP3_532_Laser_Power'],
                                                           rsltParams['GP3_635_Laser_Power'])
        except:
            pass
        try:
            rObj.optionalHeaders['LaserOnTime']="%s\t%s" % (rsltParams['GP3_532_Laser_On_Time'],
                                                            rsltParams['GP3_635_Laser_On_Time'])
        except:
            pass
        try:
            rObj.optionalHeaders['Supplier']=rsltParams['GP3_Supplier']
        except:
            pass

        spots = self.dataRecords()
        for col in self.GPRColumns():
            rObj.addColumn(col)

        for spot in spots:
            try:
                rObj.dataLines.append(ATF.DataRecord(rObj,
                                                     dataDict = self.GPRData(spot)))
            except:
                print self.GPRData(spot)
                print spot
                raise NomadConversionError, "Can't convert NOMAD spot to a Genepix Result data record."
        rObj.rebuildIndexes()
        return rObj
        
    def dataRecords(self):
        
        rv = self.db[self.getDataTable()](Result_ID=self.resultID)
        return rv
        


class printRun (kdbom.record):
    def __init__(self,db,printID):
        
        # trap bad input
        if type(db) != INSTANCE or \
               db.__class__ != nomadDB:
            raise TypeError, "Database must be an instance of NomadDB class"

        kdbom.record.__init__(self,table=db.Print, PKvalue = printID)
        self.printID = printID

    def results(self):
        """return a list of result objects from a given print run"""
        cur = self.db.con.cursor()
        cur.execute("SELECT Result_ID FROM `Print` \
                     NATURAL JOIN `Chip` \
                     NATURAL JOIN `Array` \
                     NATURAL JOIN `Array_Result` \
                     WHERE Print.Print_ID = %s", self.printID)
        rv = []
        for (rID,) in cur.fetchall():
            rv.append(result(self.db,rID))
        return rv
    

    def resultIDs(self):
        """Return a list of Result_IDs for this print"""
        cur = self.db.con.cursor()
        cur.execute("SELECT Result_ID FROM `Print` \
                     NATURAL JOIN `Chip` \
                     NATURAL JOIN `Array` \
                     NATURAL JOIN `Array_Result` \
                     WHERE Print.Print_ID = %s", self.printID)
        rv = []
        for (rID,) in cur.fetchall():
            rv.append(rID)
        return rv
   

