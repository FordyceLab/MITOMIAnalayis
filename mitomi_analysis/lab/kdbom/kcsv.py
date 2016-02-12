#!/usr/local/bin/python
#
# scan a Comma Separated Values file
#
#     $Id: kcsv.py,v 1.4 2008/01/24 18:29:40 kael Exp $    
#


import csv,re,string
import os.path
import types

from copy import copy
from .kdbom import SqlAmericanDate


notNumeric = re.compile(r'[^\d\.]')


class table:
    """Class for a CSV file that is to be turned in to a MySQL table.
    The file is read and prepared for table creation and data insertion,
    both of which are accomplished by methods of this class.

    The resulting MySQL table will not have columns that have no data in
    them in the original file, because the data yype for such files
    cant't be determined automatically.
    """

    def __init__(self,name=None,csvPath=None,csvFile=None,engine='MYISAM',
                 columnTypes = None,columnNames = None,indicies=None):
        """Determine stucture of CSV data, type of fields, etc.
        MySQL is not effected in any way, nor is the file.  The
        returned object is capable of doing these things. 
        """
        self.csvPath = csvPath
        self.columns = []

        self.engine = engine
        self.db = None

        if name == None:
            self.name = os.path.splitext(os.path.basename(csvPath))
        else:
            self.name = name

        if csvFile == None:
            csvFile = file(csvPath)
        
        parserLines = csv.reader(csvFile)

        #print "read %d lines" & (len(parserLines))

        data = []
        lines = []
        lineFields = []
        fieldCounts = {}

        i = 0
        for fields in parserLines:

            lines += [fields]
            
            i += 1
            #print len(fields)

            lineFields.append(len(fields))
            if len(fields) in fieldCounts:
                fieldCounts[len(fields)] += 1
            else:
                fieldCounts[len(fields)] = 1

        counts = list(fieldCounts.values())
        counts.sort()
        bigCount = counts[-1]

        numberOfFields = None
        for k in list(fieldCounts.keys()):
            if fieldCounts[k] == bigCount:
                numberOfFields = k
        

        print("probably " + str(numberOfFields) + " fields")
        #print i
        csvFile.close()

        print(columnTypes)

        if columnTypes == None:
            columnTypes = [None] * numberOfFields
        else:
            columnTypes = (list(columnTypes) +
                           ([None]* (numberOfFields - len(columnTypes))))
        if columnNames == None:
            columnNames = [None] * numberOfFields
        else:
            columnNames = (list(columnNames) +
                           ([None]* (numberOfFields - len(columnNames))))

        print(columnTypes)

        data = []
        for i in range(numberOfFields):
            data.append([])

        #print len(lines)

        #raise Exception # STOP for debugging
        
        #
        # make vectors with data in them
        # only take values from lines with
        # the correct number of fields
        #
        print(numberOfFields)
        print(lines[0])
        for l in lines:
            if len(l) >= numberOfFields:
                #print l
                for i in range(numberOfFields):
                    data[i].append(l[i])
                    #print i, l[i]
                    #print data
            
                    
        print(len(data))
        print(len(data[0]))

                        
        
        for i in range(len(data)):
            print("processing col %d" % i)

            print("First Row: %s" % data[1][0])
            print(columnTypes[i])
            
            self.columns.append(column(data[i],name=columnNames[i]
                                       ,_type=columnTypes[i]))


        if indicies != None:
            self.indicies=[]
            for idx in indicies:
                if (type(idx) == bytes or
                    (type(idx) in (tuple, list) and
                     types(idx[0] == bytes))):

                    self.indicies.append((idx,))

                elif type(idx) == int:

                     self.indicies.append((self.columns[idx].name,))

                elif (type(idx) in (tuple, list) and
                      types(idx[0] == int)):
                    thisIndex = []
                    for col in idx:
                        thisIndex.append(self.columns[col])
                        self.indicies.append(thisIndex[:])
        else:
            self.indicies = []
        print(self.indicies)

        # that's it

    def addFile (self,newFileName):
        """Appends the records from a csv file with the same data
        structure as the table object was initilized with.
        
        The MySQL table must have been created with createTable,
        before using addFile.
        """
        fieldNames = []
        columnIdxes = []
        valueHolders = []
        
        for i in range(len(self.columns)):
            if self.columns[i].hasData:
                fieldNames.append(self.columns[i].name)
                columnIdxes.append(i)
                valueHolders.append('%s')

        insertQuery = "INSERT `%s` (%s) VALUES (%s)" % ( self.name,
                                                         "`" + string.join(fieldNames,'`,`') + "`",
                                                         string.join(valueHolders,','))


        csvFile = file(newFileName)
        parserLines = csv.reader(csvFile)


        cur = self.db.cursor()
        
        for fields in parserLines:
            if len(fields) != len(self.columns):
                continue
            if fields[columnIdxes[0]] == self.columns[0].name:
                continue
            
            values = []
            for idx in columnIdxes:
                values.append(fields[idx])
            cur.execute(insertQuery,values)

        
        


    def showCreateTable(self,addPK=True, addTimestamp=True,makeTemporary=False):
        """returns an SQL query to created the new MySQL table.
        """

        colDefs = []
        indexDefs = []

        if makeTemporary:
            temporary = 'TEMPORARY'
        else:
            temporary = ''
        
        idxClause = ''
        if self.indicies != None:
            keys = []
            for idx in self.indicies:
                keys.append("INDEX (`%s`)"%
                            ('`, `'.join(idx)))


        if addPK:
            pkDef = "`%s_ID` INTEGER AUTO_INCREMENT PRIMARY KEY" % self.name
            colDefs.append(pkDef)
        
        for col in self.columns:
            if col.hasData:
                colDefs.append("`%s` %s" % (col.name,col.type))

        if addTimestamp:
            colDefs.append("`timestamp` TIMESTAMP")

        print('CREATE %s TABLE `%s` (%s) ENGINE=%s' % (temporary,
                                                      self.name,
                                                      ", ".join(colDefs + keys),
                                                      self.engine))
        
        rv = 'CREATE %s TABLE `%s` (%s) ENGINE=%s' % (temporary,
                                                      self.name,
                                                      ", ".join(colDefs + keys),
                                                      self.engine)
        return rv

    
    def createTable(self,db,makeTemporary=False):
        """Create MySQL table in a database (must be a
        kdbom.db object) and insert records.
        """
        self.db = db
        db.execute(self.showCreateTable(makeTemporary=makeTemporary))

        fieldNames = []
        columnIdxes = []
        valueHolders = []

        for i in range(len(self.columns)):
            if self.columns[i].hasData:
                fieldNames.append(self.columns[i].name)
                columnIdxes.append(i)
                valueHolders.append('%s')

        cur = db.cursor()    
        insertQuery = "INSERT `%s` (%s) VALUES (%s)" % ( self.name,
                                                         "`" + string.join(fieldNames,'`,`') + "`",
                                                         string.join(valueHolders,','))

        rows = []
        for i in range(len(self.columns[columnIdxes[0]].data)):
            values = []
            for idx in columnIdxes:
                values.append(self.columns[idx].data[i])
                #print values
            rows.append(values)
            if i % 30000 == 0 and i != 0:
                print("%s records inserted" % (i+1))
                cur.executemany(insertQuery,rows)
                rows = []
        
        cur.executemany(insertQuery,rows)
        print("insert complete")
        db.refresh()


class column:
    """Column in CSV file
    """
    def __init__ (self,data,_type=None,name=None):
        """Take a list.  and return a column object. The first element
        is the name of the column, followed by the data elements.

        The object knows:
        An appropriate MySQL column type.
        The range of lengths and precision of the column.
        If the column is alphanumeric.
        If the column is all dates.
        If the column should be a ENUM column.
        If the column is a good candidate for db normalization.
        """

        if name != None:
            self.name = name
        else:
            self.name = data.pop(0).replace(' ','_')
            
        print(self.name)
        self.data = copy(data)


        if _type != None:
            self.type = _type
        else:
            self.type = None
            
        self.enumCandidates = {}

        
        self.alpha = False
        self.dateFound = None # this changes to true or false on first non blank record
                              # True can change to false on non-date non-blank records
        self.precision = -1
        self.maxLength = None
        self.minLength = None
        self.probEnum = False

        alpha_count = 0

        if self.type == None:
            print('no type specified, inferring from data')
            for d in self.data:

                if not d in self.enumCandidates and d != self.name:
                    self.enumCandidates[d]=None

                if d == '' or d == self.name:
                    continue

                if SqlAmericanDate(d) != None:
                    if self.dateFound == None:
                        self.dateFound = True

                else:
                    self.maxLength = len(d)
                    self.dateFound = False

                if notNumeric.search(d) != None or d.count('.') > 1:
                    self.alpha = True
                    if self.name == "Length":
                        alpha_count += 1
                        print(alpha_count)
                        print(d)
                        print(notNumeric.search(d))

                    if self.maxLength == None \
                           or len(d) > self.maxLength:
                        self.maxLength = len(d)

                    if self.minLength == None \
                           or len(d) < self.minLength:
                        self.minLength = len(d)


                else:
                    dotPos = d.find('.')

                    if dotPos != -1:
                        precision = len(d) - dotPos - 1
                        if precision > self.precision:
                            self.precision = precision



                    


            #
            # figure out some design parameters
            #
            if len(self.data) > 100:
                #should I be an ENUM field?
                if len(self.enumCandidates) <= 5:
                    self.probEnum = True
                else:
                    self.probEnum = False

                #should I be factored out?
                if not self.probEnum \
                   and len(self.enumCandidates)/len(self.data) < 0.75:
                    self.probFactor = True
                else:
                    self.probFactor = False

            else:
                # be less optimistic on small tables
                if len(self.enumCandidates) <= 5 \
                       and len(self.enumCandidates)/len(self.data) < 0.33:
                    self.probEnum = True
                else:
                    self.probEnum = False


                if not self.probEnum \
                   and len(self.enumCandidates)/len(self.data) < 0.75:
                     self.probFactor = True
                else:
                    self.probFactor = False

        print(self.type)
        # are there any data?
        if self.enumCandidates != [ '' ]:
            self.hasData = True
        else:
            self.hasData = False

        if self.type=='ENUM':
            for d in self.data:
                self.enumCandidates[d]=None

        # I am some data type, bassed on what
        # was in my data   
        if self.probEnum or self.type == 'ENUM':
            self.type = "ENUM('%s')" % string.join(self.enumCandidates,"','")

        print(self.type)
        if self.type == None:
            if self.alpha:
                if self.maxLength < 255:
                    self.type = "VARCHAR(255)"
                else:
                    self.type = "TEXT"

            elif self.dateFound:
                self.type = "DATE"

            else:
                if self.precision == -1:
                    self.type = "INTEGER"
                else:
                    self.type = "DOUBLE"

        print(self.type)
        print('---')

        
class NCBIdmp:
    """Class for converting ncbi database dumps to StringIO csv structures so they
    can be used by the table class.  
    """


    columnNames = { 'nodes.dmp' : ('tax_id','parent_tax_id','rank',
                                   'embl_code','division_id','inherited div flag',
                                   'genetic code id','inherited GC  flag','mitochondrial genetic code id',
                                   'inherited MGC flag','GenBank hidden flag','hidden subtree root flag',
                                   'comments'),
                    'names.dmp': ('tax_id',
                                  'name_txt',
                                  'unique name',
                                  'name class')
                    }
    
    columnTypes = { 'nodes.dmp' : ('INTEGER','INTEGER','ENUM',
                                   'INTEGER','VARCHAR(255)','INTEGER',
                                   'INTEGER','INTEGER','INTEGER',
                                   'INTEGER','INTEGER','INTEGER',
                                   'TEXT'),
                    'names.dmp' : ('INTEGER','VARCHAR(255)','VARCHAR(255)','ENUM')
                    }

    indicies = {'nodes.dmp' : (0,1,2),
                'names.dmp' : (0,3)
                }
    
    
    def __init__ (self, dmpPath,db):


        self.db = db
        
        from io import StringIO
        self.fileName = os.path.split(dmpPath)[1]
        
        dmpFile = file(dmpPath)
        self.csvFile = StringIO()
        outWriter = csv.writer(self.csvFile)

        #outFile.write(dmpFile.read().replace('\t|\t'))

        for row in dmpFile:
            outWriter.writerow(row.strip('\n\t|').split('\t|\t'))

        self.csvFile.seek(0)

    def makeTable(self,tableName):
        self.csvFile.seek(0)
        t=table(csvFile=self.csvFile,name=tableName,
                columnNames=self.columnNames[self.fileName],
                columnTypes=self.columnTypes[self.fileName],
                indicies=self.indicies[self.fileName])
        t.createTable(self.db)
        del self.csvFile
        del t
        
