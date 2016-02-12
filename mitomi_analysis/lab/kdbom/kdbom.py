#!/usr/bin/env python
""" Kael's Database Object Model

Classes and tools for MySQL databases, and objects that
use MySQL for persistence.

By Kael Fischer
2003-

Note that most of kdbom is broken with respect to record
operations for tables that have non-numeric or compound primary keys.

Also,if you are writing a multithreaded application note that you must have
separate connections for each thread.  Perhaps the kdbom.db should have a
connection pool rather than a single connection.   

MySQL is the only supported database type, although others could be added.

There is some graphing functionality that should probably be ripped out and
moved to another module.

After initial development of kdbom, MySQLdb changed to autocommit = False,
by default. There may still be some problems related to the transaction model,.
see db.commit below.

 	$Id: kdbom.py,v 1.72 2008/04/17 22:06:30 kael Exp $	

"""
__version__ = "$Revision: 1.72 $"

import re
import string
import time
from os.path import expanduser,normpath
from types import *
from copy import copy

import MySQLdb

from exceptions import *

YES = True
NO = False

TUPLE = type((1,2))
LIST = type([])
DICT = type({})
STRING = type('')


modules = {}
db_tables = []

pylabLoaded=False

KSqlObjectCache = {}


# list of re objects of tables to ignore
# when the number of tables is very large this
# can speed things up

IgnoreTables = []
IgnoreTables.append(re.compile('^dbdesigner4$'))

defaulthost = ''
defaultuser = None
defaultpw = None
defaultDB = ''
defaultPort=3306
defaultCnfFile = normpath(expanduser('~/.my.cnf'))


def loadPylab ():
    '''we should really rip all the graphics out of here
    '''
    try:
        import pylab
        pylabLoaded = True
    except:
        print "Can't load plotting library"


def SqlAmericanDate (americanDate):
    """take an US formatted date and transform it in to SQL format"""
    m = re.search(r'(\d{1,2})[-_/](\d{1,2})[-_/](\d{2,4})',americanDate)
    try:
        month = "%02u" % int(m.group(1))
        day = "%02u" % int(m.group(2))
        if not int(m.group(3)) < 100:
            year = "%4u" % int(m.group(3))
        elif int(m.group(3)) > 68:
            year = "%4u" % (int(m.group(3)) + 1900)
        else:
            year = "%4u" % (int(m.group(3)) + 2000)

        return "%s-%s-%s" % (year, month,day)
    except:
        return None

def union(*lists):
    """return the union of input lists of records"""

    # this should be rewritten using dictionaries
    rv = []
    rvPKs = []
    
    for aList in lists:
        if aList: # skip None
            for elem in aList:
                if elem.PKvalue not in rvPKs:
                    rv.append(elem)
                    rvPKs.append(elem.PKvalue)            
    return rv

def intersection(*lists):
    """return the intersection of input lists of records"""

    # this should be rewritten using dictionaries
    rv = []
    rvPKs = []
    notCommonPKs = []
    strippedLists = []

    # if this is a single list remove
    # duplicate records
    if len(lists) == 1:
        return union(lists[0])

    #strip duplicates
    shortest = -1
    shortest_i = -1
    for i in range(len(lists)):
        if type(lists[i]) == LIST:
            strippedLists.append(union(lists[i]))
            if len(lists[i]) < shortest or shortest == -1:
                shortest = len(lists[i])
                shortest_i = i
    
    for elem in strippedLists[shortest_i]:
        # for every element in the shortest list
        # that is not already in the return vector
        # or found to be absent in a list
        if elem.PKvalue not in rvPKs and elem.PKvalue not in notCommonPKs:
            for bList in strippedLists:
                # for every elem in each following list
                # check equality
                for elem2 in bList:
                    foundin_bList = NO
                    if elem == elem2:
                        foundin_bList = YES
                        break
                # ok thats all the elems in the next list
                # or we found it
                if foundin_bList == NO:
                    notCommonPKs.append(elem.PKvalue)
                    break

            if elem.PKvalue not in notCommonPKs:
                rvPKs.append(elem.PKvalue)
                rv.append(elem)
    return rv

def shortest(input):
    """Return shortest list/string/tuple in input list"""
    weeLength = False
    shortest = None

    for thing in input:
        if not weeLength:
            shortest = thing
            weeLength = len(thing)
        elif len(thing) < weeLength:
            shortest = thing
            weeLength = len(thing)
    return shortest
            
def collapseSingleton(x):
    return x[0]


def unique(iteratable,remove=[]):
    '''Given an iteratable of hashables return a list of
    unique members

    things in remove will be removed from the list.
    '''

    l = list(iteratable)
    rd=dict(zip(l,[None]*len(l)))
    for thing in remove:
        if thing in rd:
            del rd[thing]
    return rd.keys()

    
def flatten(iterable):
    return reduce(lambda x,y: list(x)+list(y),list(iterable))

class db:
    """MySQL database class
    Holds connection information and information about
    the tables in the database.
    """
    def __init__ (self, host=defaulthost,user=defaultuser,
                  passwd=defaultpw,db=defaultDB,
                  cnf=defaultCnfFile,port=defaultPort, getTables=YES,
                  reuseDBconnection=None,password=None,retryTimes=2,retryInterval=30,
                  warnOnRetry=False):
        """Return a db object.  Make a database connection, and discover
        the names of the tables in the db.  The tables are accessible as db[TableName],
        db.TableName or db.tables[TableName].  You may reuse a connection (by specifying a db
        object that has already connected to the server as reuseDBconnection) to the same 
        server but a different database to prevent overloading the server with threads. 

        If neither user nor passwd are specified, the specified defaults file is read,
        by default. ~/.my.cnf . If you specify either user or password, both are taken
        from the parameters you specify.  If you specify one but not the other, the
        unspecified value will be an empty string.  'password' is accepted as a alias for
        'passwd'.  'passwd' is the MySQLdb-python preferred variant. 

        If getTables is True, the structure of the tables and the their relationships
        are completely determined.  The relationships can be discovered automatically
        only if the tables are InnoDB type and are based on foreign key constraints.

        If getTables is False, the first time a particular table is accessed via
        db.tables[TableName] it will raise an attribute error.  This can be avoided
        by using one of the other forms mentioned above.
        
        If a connection is dropped and needs to be reestablished, by default the 
        connection attempt will be retired twice if necessary with 30 seconds between
        tries.  That behavior is tunable using retryTimes and retryInterval. Connections 
        are not retired on the initial connection only after a connection has been 
        established and then lost for some reason.
        
        """

        self.retryTimes=0
        self.retryInterval=0

        if password !=None:
            passwd = password

        if reuseDBconnection != None:
            self.name = db
            self.defaultDB = reuseDBconnection
            self.con = reuseDBconnection.con
            self.host = reuseDBconnection.host
            self.user = reuseDBconnection.user
            self.passwd = reuseDBconnection.passwd
            self.port=reuseDBconnection.port
            self.verifyConnection()
            
        else:
            self.host = host
            self.user = user
            self.passwd = passwd
            self._origUser = user
            self._origPasswd = passwd
            self.name = db
            self.defaultDB=self
            self.port=port
            self.cnf = cnf

            self.con = None

            self._establishConnection()

        self.retryTimes = retryTimes
        self.retryInterval = retryInterval
        
        self.tables = {}
        self.table_names = self.GetTableNames()
        if getTables != NO:
            for tn in self.table_names:
                if not self.tables.has_key(tn):
                    self.tables[tn] = Table(db=self, name=tn)


    def changeUser(self,user=None,passwd=None):
        """Reconnect as a different user.
        """
        self.user=user
        self.passwd=passwd
        self._establishConnection()

    def revertUser(self):
        """Reconnect as the user the connetion was originally established with.
        """
        if self.user != self._origUser:
            self.changeUser(user=self._origUser,passwd=self._origPasswd)

    def _establishConnection(self):
        """Establish or reestablish the connection to the server.
        """
        if self.defaultDB.name != self.name:
            if self.retryTimes > self.defaultDB.retryTimes:
                self.defaultDB.retryTimes = self.retryTimes
            if self.retryInterval > self.defaultDB.retryInterval:
                self.defaultDB.retryInterval = self.retryInterval
            self.defaultDB._establishConnection()
            self.con = self.defaultDB.con
        else:
            retryAttempt = 0
            while True:
                try:
                    if self.user != None or self.passwd != None:
                        if self.user==None:
                            user = ''
                        else:
                            user = self.user
                        if self.passwd == None:
                            passwd = ''
                        else:
                            passwd = self.passwd
                        
                        self.con = MySQLdb.Connection(host=self.host,
                                                      user=user,passwd=passwd,
                                                      db=self.name,port=self.port)
                        break
                    else:
                        self.con = MySQLdb.Connection(host=self.host,
                                                      db=self.name, read_default_file=self.cnf)
                        break
                    
                except MySQLdb.OperationalError,MySQLdb.DatabaseError:
                    retryAttempt += 1
                    if retryAttempt > self.retryTimes:
                        raise
                    time.sleep(self.retryInterval)
                    
                except:
                    raise

                                          
    def alive(self):
        """return true if connection is pingable.
        """
        try:
            self.con.ping()
        except:
            return False
        return True


    def verifyConnection(self):
        """Attempt to reconnect if necessary.
        """
        if not self.alive():
            self._establishConnection()
        

    def refresh(self,getTables=YES):
        """Reread tables and refresh relationships.
        """
        self.verifyConnection()
        self.table_names = self.GetTableNames()
        if getTables != NO:
            self.tables = {}
            for tn in self.table_names:
                if not self.tables.has_key(tn):
                    self.tables[tn] = Table(db=self, name=tn)


    def GetTableNames (self):
        """Returns a list of tables.  Tables in the IgnoreTables
        global variable are not reoprted.
        """
        global IgnoreTables

        tables = []
        cur = self.cursor()
        cur.execute("SHOW TABLES FROM `%s`" % self.name)
        SQLrows = cur.fetchall()

        for row in SQLrows:
            # filter out ignored tables
            BadRow = 0 
            for baddie in IgnoreTables:
                if baddie.search(row[0]):
                    BadRow = 1
                    break
            
            if BadRow == 0:
                tables.append(row[0])
        return tables


    def execute (self,sqlText,parameters=None):
        """execute a query with a temporary cursor.
        """

        tempCursor = self.cursor()
        rv=tempCursor.execute(sqlText,parameters) # commit problem?
        return rv
            

    def executemany (self,sqlText,parameters=None,
                     disableFKcheck=False,chunkSize=10000):
        """use execute many for faster inserts
        """

        
        tempCursor = self.cursor()
        if disableFKcheck:
            tempCursor.execute("SET FOREIGN_KEY_CHECKS=0")
        if parameters == None or len(parameters) < chunkSize:
            tempCursor.executemany(sqlText,parameters)
        else:
            start = 0
            indicies = range(0,len(parameters),chunkSize)+[None]
            for chunk in range(1,len(indicies)):
                end = indicies[chunk]
                if end != None:
                    end += 1
                tempCursor.executemany(sqlText,parameters[start:end])
                start = end

        if disableFKcheck:
            tempCursor.execute("SET FOREIGN_KEY_CHECKS=1")
        self.commit()

    def fetchgenerator(self, selectQry,parameters=None,
                       batchSize=1000,batch=None):
        """return a generator that iterates over the rows in a 
        query result, yielding a tuple for each row.
        """

        if type(batch) == IntType and batch > 0:
            if type(batch) != IntType:
                raise TypeError, "batchSize must be an integer"
            selectQry += ' LIMIT %d OFFSET %d' % (batch,batchSize*(batch-1))


        tempCursor = self.cursor()
        tempCursor.execute(selectQry,parameters)
        while True:
            row = tempCursor.fetchone()
            if row == None:
                break
            else:
                yield row
        

    def fetchall (self,selectQry,parameters=None):
        """return all rows from running query as tuple
        of tuples.
        """

        tempCursor = self.cursor()
        tempCursor.execute(selectQry,parameters)
        return tempCursor.fetchall()

    def fieldsAndRows(self,selectQry,parameters=None):
        """Return a 2-tuple containing the field descriptions (see
        PEP-0249) and the fetchall tuple of tuples. 
        """
        tempCursor = self.cursor()
        tempCursor.execute(selectQry,parameters)
        return (tempCursor.description,tempCursor.fetchall())

    def fieldNamesRows(self,selectQry,parameters=None):
        """Return a 2-tuple containing the field names and
        the fetchall tuple of tuples. 
        """
        first = lambda x: x[0]
        tempCursor = self.cursor()
        tempCursor.execute(selectQry,parameters)

        fieldNames = map(first,tempCursor.description)
        return (fieldNames,tempCursor.fetchall())


    def fieldValueDict(self,selectQry,parameters=None):
        """Return a list of dictionaries of the form:
        fieldName:fieldValue
        """
        
        first = lambda x: x[0]
        
        tempCursor = self.cursor()
        tempCursor.execute(selectQry,parameters)
        
        fieldNames = map(first,tempCursor.description)
        rows = tempCursor.fetchall()

        fieldNames = [fieldNames] * len(rows)

        return map(dict,map(zip,fieldNames,rows))


    def uniqueKeyFieldDict(self,keyFieldName,selectQry,parameters=None):
        """Return a dictionary of the matching rows (each row is
        represented as a fieldName:fieldValue dictionary.  The keys
        of the row dictionary are the values of the keyField, specified
        by name as the 1st parameter.
        """

        getKeyValue = lambda x: x[keyFieldName]
        listOfDicts = self.fieldValueDict(selectQry,parameters)

        return dict(zip(map(getKeyValue,listOfDicts),listOfDicts))

    def generalKeyFieldDict(self,keyFieldName,selectQry,parameters=None):
        """Return a dictionary of _lists_ of matching rows, expressed as
        dictionaries, keys to the KeyField value.  Keys need not be unique
        since lists of matching records are the dictionary's values. 
        """
        rv = {}

        getKeyValue = lambda x: x[keyFieldName]
        listOfDicts = self.fieldValueDict(selectQry,parameters)

        for row in listOfDicts:
            k = getKeyValue(row)
            if k not in rv:
                rv[k] = [row]
            else:
                rv[k].append(row)

        return rv
    

    def cursor (self):
        """returns a cursor object.
        """
        self.verifyConnection()
        return self.con.cursor()

    def commit(self):
        """commit transaction.
        """
        self.con.commit()

    def rollback(self):
        """rollback transaction
        """
        self.con.rollback()

    def close (self):
        """Closes the connection.
        """
        return self.con.close()

    def escape(self,values):
        """Escape values for use in query. Values can be a list, tuple
        or a single escapable thing (e.g. string, int, long, float, None, etc.).
        """

        if type(values) not in (LIST,TUPLE):
            return self.con.escape(values,self.con.encoders)
        else:
            return tuple(map (self.escape,values))
        

    def __repr__ (self):
        table_seperator = ', '
        tl = ''
        for name in self.table_names:
            if tl != '':
                tl = tl + table_seperator

            tl = tl + name
            
        return "Tables in %s:\n" % self.name + tl


    def __getitem__ (self,table):
        if not self.tables.has_key(table):
            self.tables[table] = Table(db=self, name=table)
        return self.tables[table]

    def __getattr__ (self,table):
        try:
            return self.tables[table]
        except:
            if table in self.table_names and not self.tables.has_key(table):
                self.tables[table] = Table(db=self, name=table)
                return self.tables[table]
            else:
                raise AttributeError

    def globalSetting(self,settingName):
        """return the matching Value_Text from the Global_Settings table, if any.
        """
        if 'Global_Settings' not in self.tables:
            raise KdbomDatabaseError, "Database has no Global_Settings table"
        else:
            rows = self.tables['Global_Settings'](Name=settingName)
            if len(rows) == 0:
                raise KdbomLookupError, "Global_Settings table has no '%s' setting" % settingName
            else:
                if len(rows) == 1:
                    return rows[0].Value_Text
                else:
                    return [x.Value_Text for x in rows]

    def makeDBSQL(self, newDBName):
        """Return SQL to clone the design of the database.
        """

        rv = [ """CREATE DATABASE `%s` """ % newDBName ]

        for t in self.tables.values():
            rv.append(t.SQLdefinition)
        return ';\n\n'.join(rv)


class Table:
    """MySQL Table object."""
    def __init__ (self, db = None, name = None):
        """Returns a Table object."""
        if db:
            self.db = db
            self.name = name
            self.field_names = []
            self.fields = {}
            self.children = []
            self.parents = []

            cur = self.db.cursor()
            cur.execute("SHOW CREATE TABLE %s" % self._dbQualName())
            self.SQLdefinition = cur.fetchone()[1]  

            cur.execute("EXPLAIN %s" % self._dbQualName())
            c2 = db.con.cursor()
            ExplainRows = cur.fetchall()

            for F in ExplainRows:
                (Field_Name, Data_Type,Null_Allowed,Indexing,Default,Extra) = F

                if Null_Allowed == 'NULL':
                    Null_Allowed = 'Y'
                else:
                    Null_Allowed = 'N'

                self.field_names.append(Field_Name)
                self.fields[Field_Name] = field(db=db, table=self, name=Field_Name,
                                                type=Data_Type, nullOK=Null_Allowed,
                                                idx=Indexing, extra=Extra)

            self.primary_key = self.__getprimarykey__()
            cur.close()
            c2.close()
            
        else:
            pass
        
    def _dbQualName(self):
        return "`%s`.`%s`" % (self.db.name,self.name)

    def __getprimarykey__(self):
        """Returns the primary key field object for this table. 
        """
        PKre = re.compile('PRIMARY KEY \s*\(\`(\w+)\`\)',re.MULTILINE)
        mObj = PKre.search(self.SQLdefinition)
        if mObj:
            return self.fields[mObj.group(1)]
        else:
            return None

    def parentPath(self,relative,appendToPath=None):
        """Return a list of tables whos relationships specify 
        a path to a 'distant parent'."""
        if appendToPath == None:
            appendToPath = []
        firstParents = self.parentTables()
        if firstParents:
            if relative in firstParents:
                return appendToPath
            for parent in firstParents:
                ancestors = parent.__allParents__()
                if ancestors:
                    if relative in ancestors:
                        appendToPath.append(parent)
                        parent.parentPath(relative,appendToPath)

        return appendToPath

    def joinClause(self,relative):
        """Returns the join clause for linking this table
        to an immediate relative."""

        rv = ''
        for rel in self.parents:
            if relative == rel.parent.table:
                return rel.join2parent()
        for rel in self.children:
            if relative == rel.child.table:
                return rel.join2child()

        raise Relationship_Error, "%s not an immediate relative of %s" % (relative, self)
            


    def joinPath(self,relative,dontVisit=None,joinOrder = None):
        """Returns a join clause suitable for use in an SQL query,
        linking this table to any relative.
         - dontVisit is a list of tables not to visit in joinPath.
         - joinOrder is a explicit list of intervening tables in
           the order to join them"""
        joins = []

        table0 = self

        if joinOrder == None:
            joinOrder = self.relationshipPath(relative,dontVisit=dontVisit)

        try:
            for table1 in joinOrder + [relative]:
                joins.append(table0.joinClause(table1))
                table0 = table1
        except:
            joinOrder.reverse()
            for table1 in joinOrder + [relative]:
                joins.append(table0.joinClause(table1))
                table0 = table1
            
        return string.join(joins,' ')
    

    def relationshipPath(self,relative, appendToPath=None, dontVisit = None):
        """ Return list of tables that who's relationships specify
        a path the the relative"""
        possiblePaths =[]
        if appendToPath == None:
            appendToPath = []
        if dontVisit == None:
            dontVisit = []

        dontVisit.append(self)
        F1 = self.F1tables()

        if F1:
            if relative in F1:
                return appendToPath
            
            for table in F1:
                if table in dontVisit:
                    continue
                rels = table.__allRelatives__(dontVisit=dontVisit)
                if len(rels) > 0:
                    if relative in rels:
                        appendToPath.append(table)
                        possiblePath = copy(appendToPath)
                        possiblePaths.append(table.relationshipPath(relative,
                                                                    appendToPath=possiblePath,
                                                                    dontVisit=dontVisit))
            if len(possiblePaths) > 0:               
                appendToPath = possiblePaths    
                return shortest(possiblePaths)
            else:
                return appendToPath
        
        
    def __allParents__(self, appendTo = None):
        """Return a recursive list of all parent tables of a table.
        If appendto is given the results are added to that list."""
        if appendTo == None:
            appendTo = []
        parents = self.parentTables()
        if parents:
            for parent in parents:
                appendTo.append(parent)
                parent.__allParents__(appendTo)
            return appendTo
        else:
            return None

    def __allRelatives__(self, appendTo=None, dontVisit=None,
                         childLimit=4):
        """Return a recursive list of all related tables.
        If appendto is given the results are added to that list;
        dontVisit specifies a list of tables on to recurse through."""
        if appendTo == None:
            appendTo = []
        if dontVisit == None:
            dontVisit = []
        else:
            dontVisit = copy(dontVisit)

        #don't come back to this table
        dontVisit.append(self)

        # enumerate family
        imFamily = []
        kids = self.childTables()
        parents =  self.parentTables()

        if kids == None:
            kids = []
        if parents == None:
            parents = []

        imFamily = kids + parents

        if imFamily:
            for fMember in imFamily:
                if fMember not in dontVisit and len(kids) <= childLimit:
                    # ignore children of tables with MANY children
                    appendTo.append(fMember)
                    fMember.__allRelatives__(appendTo,dontVisit)
                    
            return appendTo

        return None
            

    def parentTables(self):
        """Return a list of parent table objects."""
        rv = []
        for rel in self.parents:
            rv.append(rel.parent.table)

        if len(rv) == 0 :
            return None
        else:
            return rv

    def childTables(self):
        """Return a list of parent table objects."""
        rv = []
        for rel in self.children:
            rv.append(rel.child.table)

        if len(rv) == 0 :
            return None
        else:
            return rv

    def F1tables (self):
        """Return a list of parent and child Tables
        ('F1' from genetics)"""
        rv = []
        for rel in self.parents:
            rv.append(rel.parent.table)
        for rel in self.children:
            rv.append(rel.child.table)
            
        if len(rv) == 0 :
            return None
        else:
            return rv


    def PKvalues(self,criteria={},whereLiteral='',**Values):
        """Returns a list of primary key values.
        criteria can be specified or field=value pairs can be
        specified, per Table.__call__.  If none of thos are
        specified all primary key values will be selected.
        """
        if criteria != {}:
            Values = criteria
        if Values == {} and whereLiteral == '':
            return self.primary_key.values
        else:
            keyRows = self(criteria=Values,whereLiteral=whereLiteral,selectExpr="`" + self.primary_key.name + "`")
            return [x[0] for x in keyRows]
        
    def GetValues(self,PKvalue):
        """Returns a tuple of the values from the record with primary key = PKvalue"""

        cur = self.db.cursor()
        if self.primary_key.isString:
            cur.execute("""SELECT * FROM %s WHERE `%s` LIKE "%s" """ % (self._dbQualName(), self.primary_key.name, PKvalue))
        else:
            cur.execute("SELECT * FROM %s WHERE %s = %s" % (self._dbQualName(), self.primary_key.name, PKvalue))
        row= cur.fetchone()
        cur.close()
        return row

        
    def __repr__ (self):
        return self.name


    def __getitem__ (self,PKvalue):
        return record(table=self, PKvalue=PKvalue)


    def __getattr__ (self,field):
        try:
            return self.fields[field]
        except:
            raise AttributeError

    def insert(self, data={},ignore=False, **Values):
        """Insert a record into the table.  Either a dictionary containing the
        field/data pairs (keyed on the field names), a number of Field=Value
        parameters are the arguments."""
        #print Values.keys()
        if data != {}:
            Values = data

        if ignore == False:
            ignore = ''
        else:
            ignore = 'IGNORE'
        
        fields = Values.keys()
        values = Values.values()

        fieldList = "`" + string.join(fields,"`, `") + "`"
        valueSub = string.join(['%s']*len(values),",")

        cur = self.db.cursor()
        #print "INSERT %s INTO %s (%s) VALUES (%s) " % \
        #            (ignore, self.name, fieldList, valueSub)
        if len(values) > 0:
            cur.execute("INSERT %s INTO %s (%s) VALUES (%s) " % \
                        (ignore, self._dbQualName(), fieldList, valueSub),
                        (values))
        else:
                   cur.execute("INSERT %s INTO %s " % \
                        (ignore, self._dbQualName()))
        cur.close()
        self.db.commit()
        return cur.lastrowid


    def insertMany(self,fieldNames,rows,callback=lambda x: x,
                   disableFKcheck=False,chunkSize=10000,
                   ignore=False,onDupKeyLiteral=''):
        """insert many rows into the table. callback will be
        called on rows before the insert.
        """
        if ignore == False:
            ignore = ''
        else:
            ignore = 'IGNORE'
        
        fieldList = "`" + string.join(fieldNames,"`, `") + "`"
        valueSub = string.join(['%s']*len(fieldNames),",")

        qryText = ("INSERT %s INTO %s (%s) VALUES (%s) %s" %  
                   (ignore, self._dbQualName(), fieldList,
                    valueSub, onDupKeyLiteral))

        if len(rows) == 1:
            self.db.executemany(qryText,
                                (callback(rows[0]),),
                                disableFKcheck=disableFKcheck,
                                chunkSize=chunkSize)
            
        else:
            for start in range(0,len(rows),chunkSize):
                print len(rows[start:start+chunkSize])
                self.db.executemany(qryText,
                                    map(callback,
                                        rows[start:start+chunkSize]),
                                    disableFKcheck=disableFKcheck,
                                    chunkSize=chunkSize)

        self.db.commit()
    


    def findFromForm(self, filterNames, formData):
        """Return Records that match from input.  filter name is a tuple or
        list of the form (input-name,field-name).  Field names in parent
        tables are allowed.  When the input-name and the field name are
        identical in may be specified as a string outside a tupple.  fromData
        should be a dictionary containing the GET/POST data.

        This is a great function but should be moved in to a www app framework
        """

        tableName = None

        if type(filterNames) == TUPLE:
            (inputName, fieldName) = filterNames
            if len(string.split(fieldName,'.')) == 2:
                (tableName, fieldName) = string.split(fieldName,'.')
        else:
            inputName = fieldName = filterNames

        if not formData.has_key(inputName) or \
               formData[inputName] == 'filter' or \
               formData[inputName] == '':
            # no form data for this field
            return None


        # if table specified
        if tableName:
            #raise Exception, tableName + " " + fieldName
            t = self.db.tables[tableName]
            if fieldName in t.field_names:
                rv = []
                for pMatch in t.fields[fieldName].search(formData[inputName]):
                    rv += pMatch.children(self)
                return union(rv)
            else:
                return None

        else:
            if fieldName in self.field_names:
                # easy case this field name is in the this table
                return self.fields[fieldName].search(formData[inputName])

            # or search parent tables
            pTables = []
            for relat in self.parents:
                pTables.append(relat.parent.table)


            # search for field name
            for t in pTables:
                if fieldName in t.field_names:
                    rv = []
                    for pMatch in t.fields[fieldName].search(formData[inputName]):
                        rv += pMatch.children(self)
                    return union(rv)
        # no matching parents
        return None

    

    def count(self, criteria={}, **Values):
        """return count of records that match criteria given as
        field value pairs or a criteria dictionary"""
        rv=0
        if criteria != {}:
            Values = criteria
            
        fields = Values.keys()
        values = Values.values()

        wheres = []
        for i in range(len(fields)):
            wheres.append("%s = %s" % (fields[i], self.db.con.escape(str(values[i]),self.db.con.encoders)))

        if len(wheres) > 0:
            whereClause = "WHERE " +  string.join(wheres,' AND ')
        else:
            whereClause = ''

        cur = self.db.cursor()
         
        cur.execute("SELECT count(*) FROM %s.%s %s" \
                    % (self.db.name, self.name, whereClause))

        (rv,) =  cur.fetchone()
        return rv


    def delete(self, criteria={}, **Values):
        """delete records that match criteria given as field value pairs or is a
        criteria dictionary. Returns # of rows effected.
        """
        rv=0
        if criteria != {}:
            Values = data
            
        fields = Values.keys()
        values = Values.values()

        wheres = []
        for i in range(len(fields)):
            wheres.append("%s = %s" % (fields[i], self.db.con.escape(str(values[i]),self.db.con.encoders)))

        if len(wheres) > 0:
            whereClause = "WHERE " +  string.join(wheres,' AND ')
        else:
            whereClause = ''

        cur = self.db.cursor()
         
        rv = cur.execute("DELETE FROM %s.%s %s" \
                    % (self.db.name, self.name, whereClause))

        self.db.commit()
        return rv
       

    def __call__ (self, criteria={}, selectExpr = None, iterator=False,
                  expectOneRecord=False,returnLastRecord=False,
                  returnFirstRecord=False,batchSize=1000, batch=None ,
                  whereLiteral='', **Values):
        """return records that match criteria given as field value pairs
        or as criteria dictionary"""

        if sum((iterator,returnFirstRecord,returnLastRecord,expectOneRecord)) > 1:
            raise ValueError, ("Only one of these flasg may be set for Table.record retreival\n"
                               "may be set: iterator,returnFirstRecord,returnLastRecord,expectOneRecord")
        rv=[]
        if criteria != {}:
            Values = criteria

        if selectExpr == None:
            selectExpr = "`" + self.primary_key.name + "`"
            returnRecords = True
        else:
            returnRecords= False
        
            
        select = self._buildSelect(criteria=Values,whereLiteral=whereLiteral,
                                   batchSize=batchSize, batch=batch) % selectExpr

        if returnLastRecord:
            select += self._buildOrderBy('Timestamp') + " LIMIT 1"

        if returnFirstRecord:
            select += self._buildOrderBy('Timestamp')+" DESC LIMIT 1"

        cur = self.db.cursor()
         
        if type(batch) == IntType and batch > 0:
            if type(batch) != IntType:
                raise TypeError, "batchSize must be an integer"

        recCount = cur.execute(select)

        if not iterator:
            if expectOneRecord and recCount  > 1:
                raise KdbomError, "More that one record returned"

            selectrows =  cur.fetchall()
            if not returnRecords:
                return selectrows
            
            for row in selectrows:
                rv.append(record(table=self, PKvalue=row[0]))
            return rv
        else:
            self.__iter__(cur)


    def _buildSelect(self, criteria = {}, batchSize=1000, batch=None,
                     whereLiteral='',**Values):
        """Returns the text for a select from this table. Has %s in place
        for the field list 
        """
        if whereLiteral == '':
            wheres=[]
        else:
            wheres=[whereLiteral]
        
        if criteria != {}:
            Values = criteria
        fields = [self.fields[fName] for fName in Values.keys()]
        values = Values.values()
        for i in range(len(fields)):
            if values[i] == None:
                wheres.append("`%s` IS NULL" % (fields[i].name))
            else:
                wheres.append("`%s` = %s" %
                              (fields[i].name,
                               fields[i].escapeForDB(values[i])))
        if len(wheres) > 0:
            whereClause = "WHERE %s" % ' AND'.join(wheres)
        else:
            whereClause = ''

        if type(batch) == IntType and batch > 0:
            if type(batch) != IntType:
                raise TypeError, "batchSize must be an integer"
            limitClause = ' LIMIT %d OFFSET %d' % (batchSize,batchSize*(batch-1))
        else:
            limitClause = ''

        return ("SELECT %%s FROM `%s`.`%s` %s %s" 
                % (self.db.name,
                   self.name, whereClause,
                   limitClause))


    def _buildOrderBy(self,orderBy=""):
        """
        """
        if orderBy == None or orderBy == '':
            obTxt = ''
        elif type(orderBy) in  (StringType,UnicodeType):
            obTxt = "`%s`" % orderBy
        elif isinstance(orderBy,field):
            obTxt = "`%s`" %orderBy.name
        elif type(orderBy) in (ListType,TupleType):
            obTxt = ', '.join(map(self._buildOrderBy,orderBy))
        else:
            raise ValueError, ("orderBy must be a string, field or sequence of those, got type %s"
                               % str(type(orderBy)))

        if obTxt == '':
            return ''
        else:
            return " ORDER BY %s " % obTxt
        
                               

    def __iter__(self,criteria = {}, **Values):
        """Return a generator over records, specified as in __call__. 
        """
        if criteria != {}:
            Values = criteria

        if not isinstance(criteria, MySQLdb.cursors.BaseCursor):
            cur=criteria
        else:
            cur = self.db.cursor()

            recCount = cur.execute(self._buildSelect(Values))

        while True:
            row = cur.fetchone()
            if row == None:
                return
            else:
                yield  record(table=self, PKvalue=row[0])
        
        


    def records(self,iterator=False):
        """Return all the records in the table."""
        if iterator:
            return self.__iter__()
        else:
            rv = []
            for pk in self.PKvalues():
                rv.append(self[pk])
            return rv

    def factor(self, newTableName ,fieldNames = [],useExistingTable=False,useExistingFields=[]):
        """Create a new table in the database that contains the
        distinct data from the specified fields. Fields are specified
        as a list of field names.

        The original fields are dropped and replaced by a foreign key. 
        """


        tblCount = self.db.execute("""SHOW TABLES LIKE %s""" %
                                   (self.db.escape(newTableName)))

        if (tblCount != 0 and not useExistingTable):
            raise KdbomError, "Table exists: %s" % (newTableName)
        elif (useExistingTable and tblCount != 1):
            raise KdbomError, "Table doesn't exist: %s" % (newTableName)
        


        selectSQL = "SELECT DISTINCT %s FROM %s.%s" % \
                    ('`' + string.join(fieldNames,'`,`') + '`',self.db.name,self.name)

        if not useExistingTable:
            # create the table and instert the data in one wack
            # easy and fast
            createTableSQL = """CREATE TABLE %s (%s_ID INTEGER AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP, UNIQUE (`%s`) ) ENGINE=INNODB
            %s""" % (newTableName, newTableName,'`,`'.join(fieldNames)
                     ,selectSQL)


        addFkField = """ALTER TABLE %s
        ADD %s_ID INTEGER AFTER %s""" % (self.name,
                                         newTableName,
                                         self.primary_key.name)

        addFkConstraint = """ALTER TABLE %s
        ADD CONSTRAINT FOREIGN KEY (%s_ID)
        REFERENCES %s (%s_ID)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
        """ % (self.name,newTableName,newTableName,newTableName )

        if not useExistingTable:
            # make the new table with data
            self.db.execute(createTableSQL)
            self.db.tables[newTableName] = Table(db=self.db,name=newTableName)      
        else:
            # just insert the data w/o table creation
            if not useExistingFields:
                useExistingFields = fieldNames
            self.db.execute("""INSERT IGNORE INTO `%s` (`%s`) %s""" %
                            (newTableName,'`,`'.join(useExistingFields),selectSQL))
            newTable = self.db.tables[newTableName]

        # insert new field for fk
        self.db.execute(addFkField)
        
        # update records with fk values
        for pk in newTable.PKvalues():
            #print pk
            rec = newTable[pk]
            data = rec.data
            
            for k in data.keys():
                if not k in useExistingFields:
                    del data[k]

            fields = data.keys()
            values = data.values()

            wheres = []
            for i in range(len(fields)):
                fIdx = useExistingFields.index(fields[i])
                if values[i] == None:
                    wheres.append("%s IS NULL" % (fieldNames[fIdx]))
                else:
                    wheres.append("`%s` = %s" % (fieldNames[fIdx],
                                                 self.db.con.escape(str(values[i]),self.db.con.encoders)))
            if len(wheres) > 0:
                whereClause = "WHERE %s" % string.join(wheres,' AND ')
            else:
                whereClause = ''

            cur = self.db.cursor()

            cur.execute("UPDATE `%s`.`%s` SET `%s_ID`=%%s %s" \
                        % (self.db.name,self.name,newTableName,whereClause),pk)
            

        # alter table to add fk formally
        self.db.execute(addFkConstraint)

        # drop original fields
        for f in fieldNames:
            self.db.execute("""ALTER TABLE %s
                               DROP COLUMN `%s`""" % (self.name, f))

        # update me and db
        del self.db.tables[self.name]
        self.db.tables[self.name] = Table(db=self.db, name=self.name)
        self.db.refresh()


    def valueIdDict(self,field,**Values):
        """Return a dictionary of fieldValue:pkValue pairs.
        """

        sqlTxt = self._buildSelect(Values) % ( '`'+field.name+'`,`'+
                                               self.primary_key.name +'`')
                                               
        return dict(self.db.fetchall(sqlTxt))
    



    def idValueDict(self,field,**Values):
        """Return a dictionary of pkValue:fieldValue pairs.
        """

        sqlTxt = self._buildSelect(Values) % ( '`'+self.primary_key.name+'`,`'+
                                               field.name +'`')
                                               
        return dict(self.db.fetchall(sqlTxt))


    def idValueTuples(self,field,orderBy=None):
        """This actually returns lists not tuples(?!?)
        """
        orderByTxt = self._buildOrderBy(orderBy)
        return self.db.fetchall("""SELECT `%s`,`%s` from %s %s""" %
                                (self.primary_key.name, field.name,self._dbQualName(),orderByTxt) )


    def ksqlStub (self):
        """Return a KSqlObject class stub with this table as its
        base.
        """
        emptyDoc = '\t"""\n\t"""'

        stubString = """
class %s (KSqlObject):
%s

\t_table = %s
"""
        return stubString

        
class field:
    """MySQL field """
    def __init__ (self,db=None, table=None, name=None, type=None,
                  nullOK=None, idx=None, extra=None ):
        self.db = db
        self.table = table
        self.name = name
        self.type = type
        self.nullOK = nullOK
        self.idx = idx
        self.extra = extra
        self.isNumeric = False
        self.isFloat = False
        self.isString = False
        self.isTime = False
        self.parentFields = []
        self.childFields = []

        if self.db != None:
            if re.search('int',type, re.IGNORECASE):
                self.isNumeric = True

            elif re.search('double',type, re.IGNORECASE) or \
               re.search('float',type, re.IGNORECASE) or \
               re.search('fixed',type, re.IGNORECASE) or \
               re.search('dec',type, re.IGNORECASE) or \
               re.search('real',type, re.IGNORECASE) or \
               re.search('numeric',type, re.IGNORECASE) or \
               type in ['bit', 'bool', 'boolean']:
                self.isNumeric = True
                self.isFloat=True

            elif re.search('date',type, re.IGNORECASE) or \
                 re.search('time',type, re.IGNORECASE)or \
                 re.search('year',type, re.IGNORECASE) :
                self.isTime = True

            elif re.search('char',type, re.IGNORECASE) or \
                 re.search('text',type, re.IGNORECASE) or \
                 re.search('blob',type, re.IGNORECASE) or \
                 re.search('^enum',type, re.IGNORECASE):
                self.isString = True


            self.longName = "%s.%s.%s" %(self.db.name,self.table.name,self.name)
            # am I a foreign key?
            foreignMatch = re.search('FOREIGN KEY \(`%s`\) REFERENCES `(?P<table>\w+)` \(`(?P<field>\w+)`\)' %
                                     (self.name),self.table.SQLdefinition)
            if foreignMatch:
                fTable = foreignMatch.groupdict()['table']
                fField = foreignMatch.groupdict()['field']

                # if parent table does not exist
                # build it
                if not self.db.tables.has_key(fTable) :
                    self.db.tables[fTable] = Table(db=self.db, name=fTable)

                # add relationship information
                newR = relationship(child=self,
                                    parent=self.db[fTable].fields[fField])

                # adding to table level objects
                # and field objects
                newR.insert()
    
    
    def convertForDB (self,value):
        """
        """
        if self.isString:
            return str(value)
        elif self.isNumeric and not self.isFloat:
            return int(value)
        elif self.isFloat:
            return float(value)
        else:
            return value
    
    def escapeForDB (self,value):
        """
        """
        return self.db.con.escape(self.convertForDB(value)
                                  ,self.db.con.encoders)
    
    
    def search(self, criteria, operator = '='):
        """Return a list of record objects that match the criteria."""
        rv = []

        cur = self.db.cursor()
         
        cur.execute("SELECT %s FROM %s.%s \
                     WHERE %s %s %%s" % (self.table.primary_key.name,
                                           self.db.name, self.table.name,
                                           self.name, operator),criteria)

        selectrows =  cur.fetchall()
        for row in selectrows:
            rv.append(record(table=self.table, PKvalue=row[0]))
        return rv

    def subSearch(self,substring):
        """Return a list of record objects that match the substring."""
        rv = []
        
        cur = self.db.cursor()
         
        cur.execute("SELECT %s FROM %s.%s \
                     WHERE %s %s '%%%s%%'" % (self.table.primary_key.name,
                                           self.db.name, self.table.name,
                                           self.name, 'LIKE',substring))

        selectrows =  cur.fetchall()

        for row in selectrows:
            rv.append(record(table=self.table, PKvalue=row[0]))
        return rv
        

    def aggregateFunction(self,operation='',where=None):
        '''wrapper for SQL aggregate functions: min,
        max, sum, avg, std and count.
        '''
        if operation not in ('min','max','sum','avg','std',
                             'count','MIN','MAX','SUM','AVG',
                             'STD','COUNT'):
            raise ArgumentError ,"Aggregate function operattion must be one of min, max, sum, avg, std or count"
        
        rv = []
        whereClause = ''
        if where != None:
            whereClause = ' WHERE ' + where
            
        cur = self.db.cursor()         
        cur.execute("SELECT %s(%s) FROM %s.%s %s" %
                    (operation, self.name, self.db.name, self.table.name, whereClause))
        rv = cur.fetchone()[0]
        return rv
        
        
    def max(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='max',where=where)
        
    def min(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='min',where=where)
        
    def sum(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='sum',where=where)
        
    def std(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='std',where=where)
        
    def count(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='count',
                                      where=where)

    def countX (self,value=None):
        '''
        '''
        if value == None:
            where = None
        elif type(value) == STRING:
            where = "`%s` = '%s'" % (self.name,value)
        else:
            where = "`%s` = %s" % (self.name,value)

        return self.aggregateFunction(operation='count',
                                      where=where)
        
    
        
    def avg(self,where=None):
        '''
        '''
        return self.aggregateFunction(operation='avg',where=where)
        
    def __repr__ (self):
        rv =  """\t%s
        type:\t\t%s
        null?\t\t%s
        indexing:\t%s
        extra:\t\t%s""" % (self.longName,self.type,self.nullOK,
                           self.idx,self.extra)
        if len(self.parentFields) > 0:
            parString = '\n        parent fields:'
            for f in self.parentFields:
                parString = parString + '\n\t\t\t%s' % f.longName
            rv = rv + parString

        if len(self.childFields) > 0:
            childString = '\n        child fields:'
            for f in self.childFields:
                childString = childString + '\n\t\t\t%s' % f.longName
            rv = rv + childString

        return rv
        
    
    def __getattr__ (self,name):
        if name == "values":
            rv = []
            enumMatch = re.match(r'^enum\((.+)\)',self.type, re.IGNORECASE)
            if enumMatch:
                enumArg = enumMatch.group(1)
                for choice in enumArg.split(','):
                    rv.append(choice.strip(r'\'"'))
            else:                    
                cur = self.db.cursor()
                cur.execute("SELECT %s FROM %s.%s" % (self.name, self.db.name,
                                                      self.table.name))
                for row in cur.fetchall():
                    rv.append(row[0])

            return rv
            
        elif name == "distinct_values":
            rv = []
            cur = self.db.cursor()
            cur.execute("SELECT DISTINCTROW %s FROM %s.%s" %
                        (self.name, self.db.name, self.table.name))
            for row in cur.fetchall():
                rv.append(row[0])
            return rv

        elif name == "isUnique":
            return len(self.distinct_values) == len(self.values)
        
        else:
            raise AttributeError
        
        
        

class record:
    """A MySQL record class """
    def __init__ (self, table=None, PKvalue=None,query=None,params= tuple()):
        """Constructor requires a table object and either a primary key 
        value, or an SQL query and params tuple, the query must return only a 
        primary key for this table.
        e.g. record(table=products, PKvalue=99)
        """
        self.__dict__['data'] = {}
        self.table=table
        self.db = table.db
        if type(PKvalue) != NoneType:
            self.PKvalue=PKvalue
        else:
            # use query    
            cur=self.db.cursor()
            cur.execute(query,params)
            rowOne=cur.fetchone()
            if type(rowOne) != NoneType:
               self.PKvalue=rowOne[0]
            else:
               self.PKvalue=None                 

        self.refresh()
            
    def refresh (self):
        """Update data in the object"""
        self.values = self.table.GetValues(self.PKvalue)
        self.keys = self.table.field_names
        self.data = PackDict(self.keys,self.values)

    def children(self,foreginTable,where=None,fieldNames=None,
                 dontVisit=None,joinOrder=None,justPKvalues=False):
        """returns a list of records, or just primay key values of the
        records that are children of this record.  If you specify fieldNames
        the values of those fields in the child table will be returned in
        tuples, rather than the records of PK vales which are returnd in a
        single, unnested, list.
        """

        if where != None and where != '':
            moreWhere = "AND %s" % where
        else:
            moreWhere = ''
            
        rv = []
        cur = self.db.cursor()
        if fieldNames == None:
            cur.execute("""SELECT DISTINCT %s.%s FROM %s.%s %s
            WHERE %s.%s = %%s %s""" % (foreginTable.name,
                                       foreginTable.primary_key.name,
                                       foreginTable.db.name,
                                       foreginTable.name,
                                       foreginTable.joinPath(self.table,
                                                             dontVisit=dontVisit,
                                                             joinOrder=joinOrder),
                                       self.table.name,
                                       self.table.primary_key.name,
                                       moreWhere),
                        self.PKvalue)

            selectrows =  cur.fetchall()
            if justPKvalues:
                return map(collapseSingleton,selectrows)
            else:
                for row in selectrows:
                    rv.append(record(table=foreginTable, PKvalue=row[0]))
                    return rv
        else:
            cur.execute("""SELECT DISTINCT %s FROM %s.%s %s
            WHERE %s.%s = %%s %s""" % (','.join(fieldNames),
                                       foreginTable.db.name,
                                       foreginTable.name,
                                       foreginTable.joinPath(self.table),
                                       self.table.name,
                                       self.table.primary_key.name,
                                       moreWhere),
                        self.PKvalue)
            return cur.fetchall()
            

    def parents(self,foreginTable, collapseSingleton=True,
                dontVisit=None, joinOrder=None):
        """returns a list of records that are parents of this record."""
        rv = []
        cur = self.db.cursor()
         
        cur.execute("""SELECT DISTINCT %s.%s FROM %s.%s %s
        WHERE %s.%s = %%s""" % (foreginTable.name,
                                foreginTable.primary_key.name,
                                foreginTable.db.name,
                                foreginTable.name,
                                foreginTable.joinPath(self.table,
                                                      dontVisit=dontVisit,
                                                      joinOrder=joinOrder),
                                self.table.name,
                                self.table.primary_key.name),self.PKvalue)

        selectrows =  cur.fetchall()
        for row in selectrows:
            rv.append(record(table=foreginTable, PKvalue=row[0]))

        if len(rv) == 1 and collapseSingleton == True:
            return rv[0]
        else:
            return rv

    def relatives(self,tableFilter=None):
        """returns a list of records that are either
        parents or children."""
        p = self.parents(tableFilter, collapseSingleton=False)
        c =  self.children(tableFilter)
        rv = []
        if type(p) == LIST:
            rv+=p
        if type(c) == LIST:
            rv+=c
        return rv

    def __getattr__ (self,name):
        # Search Data
        if name in self.data:
            return self.data[name]

        # Search Parent Tables
        for rel in self.table.parents:
            if name == rel.parent.table.name:
                return self.parents(rel.parent.table)

        # Search Children Tables
        for rel in self.table.children:
             if name == rel.child.table.name:
                 return self.children(rel.child.table)
                    
        else:
            raise AttributeError

    def __setattr__ (self, fieldName, value):
        if fieldName in self.data:
            cur = self.db.cursor()
            rc = cur.execute("UPDATE `%s`.`%s` SET `%s` = %%s WHERE `%s` = %%s" %
                        (self.db.name, self.table.name,
                         fieldName, self.table.primary_key.name),
                        (value, self.PKvalue))
            if rc == 0:
                return 0
            else:
                self.refresh()
                return rc
        else:
            self.__dict__[fieldName] = value


    def update (self, data={}):
        """Update the fields of a record with the values
        in the data dictionary"""
        try:
            for key in data.keys():
                self.__setattr__(key,data[key])

        except Exception, details:
            self.db.con.rollback()
            raise
        
        else:
            self.db.con.commit()

    def touchTimestamp(self):
        """Update the record's Timestamp to sql NOW()
        """
        try:
            cur = self.db.cursor()
            cur.execute(
                """UPDATE `%s`.`%s` SET `Timestamp` = NOW()
                WHERE `%s` = %s""" %
                    (self.db.name,
                     self.table.name,
                     self.table.primary_key.name,
                     self.PKvalue) )
        except:
            raise
            cur.close()
            self.db.con.rollback()
            
      
        cur.close()
        self.db.con.commit()
        

    def delete (self):
        """Deletes the record from the databases."""

        cur = self.db.cursor()
        cur.execute('DELETE FROM %s.%s WHERE %s = %s' %
                    (self.db.name,
                     self.table.name,
                     self.table.primary_key.name,
                     self.PKvalue) )
        cur.close()
        self.db.con.commit()

    def __getitem__ (self,name):
        return self.data[name]


    def __eq__ (self,rec2):
        if isinstance(rec2,record):
            if self.table != rec2.table:
                return False

            if self.PKvalue != rec2.PKvalue:
                return False

            return True
        else:
            return False


    def __repr__(self):
        return str(self.data)

KSqlCache = {}
KSqlCacheIdx = {}

            
class KSqlObject:
    """ This is the skeleton for objects which are represented by
    single records in a database.

    This has to be subclassed.  At a minimum the class variable _table
    MUST be set to a valid kdbom table.  Similarly, _strField may be set
    to a field in _table.  _strField can be used single parameter initialization,
    and is the value displayed when self.__str__() is called. _table's 'Name'
    field is used by default is _strField is None.

    Because of the integrated lookup/load from database feature of the
    initialize code, should not overwrite __init__.  Post init code can be
    included in a __post_init__ method of the subclass. __post_init__ is
    a null-op in KSqlObject itself.

    A many to many tagging system for objects can be used if there is a tag table in
    which the Tag Names are contained in a character field called 'Name'.  There must
    also be a linking table.  The subclass must specify these as class variables,
    _tagTable and _tagLinkTable respectively.

    """

    # _table should be defined in subclasses
    _table=None
    
    # these may be defined for a simple many to many
    # table of string tags
    _tagTable=None
    _tagLinkTable=None




    _strField=None   # this will be the value returned by __str__
                     # this is anther way to lookup the record.
                     # if the subclass doesn't set it 'Name'
                     # will be used if present 


    def count(cls,*args,**kwargs):
        """the underlying table's count method.
        """
        return cls._table.count(*args,**kwargs)

    count = classmethod(count)

    def __new__ (KSqlObject,criteria={},cacheOnInit=False,
                 loadFromCache=False, cacheSize=0,
                 insertIfNeeded=False,**values):
        """ This handles the optional cacheing backend see __init__ for object
        creation options.
        """
        
        if (loadFromCache and type(criteria) in (IntType, LongType)
            and (self.__class__,str(criteria)) in KSqlCacheIdx):
            return KSqlCache[self.__class.__][KSqlCacheIdx[self.__class__][criteria]]
        else:
            return KSqlObject()

    def __init__ (self,criteria={}, cacheOnInit=False, loadFromCache=False,
                  cacheSize=0,insertIfNeeded=False,**values):
        """Initialize new object.  When called with no arguments a
        generic object is returned.

        A SQL record to be loaded can be specified as a kdbom record,
        or a Table and matching criteria can be specified (if the only
        criteria is an integer or a long it is implicit that it is
        specifying the primary key value), as a criteria dictionary
        or as field=value pairs.  Alternately, criteria can be a tuple
        of the form (queryText, params), in which the query must return
        only primary key values for the corresponding table, and params 
        is a tuple containing a set of parameters that will be substituted 
        in for %s in the query using the normal quoting engine for the 
        database connection.   

        When an object is initialized it may be cached in memory,if
        cacheOnInit is True, for later use.  Cached objects are only
        used if loadFromCache is True.  In some applications this may
        cause a lot of memory use, but lookup is about 1000-2000x faster
        when bypassing the SQL layer altogether in this way.
        """

        # set string field default, if needed
        if self._strField == None:
            if 'Name' in self._table.field_names:
                    self._strField=self._table.Name                

        if 'SQLfields' not in self.__dict__:
            self._dirty = False
            self._record = None
            self._deleated = False
            self.SQLfields = {}


            # load if needed
            if criteria == {}:
                criteria = values

            if criteria != {}:
                if self._table == None:
                    raise KdbomUsageError, "Can't load SQL data. Table unknown."

                try:                    
                    self.load(criteria=criteria)
                except KdbomDatabaseError:
                    if not insertIfNeeded:
                        raise
                    id = insert_KSqlObject(table=self._table,data=criteria)
                    self.load(id)

            self._init_criteria = criteria
            self.__post_init__()

            if cacheOnInit:
                if self.__class__ not in KSqlCacheIdx:
                    KSqlCacheIdx[self.__class__]={}
                    KSqlCache[self.__class__] = []
                else:
                    while len(KSqlCache[self.__class__]) >= cacheSize:
                        for k,v in KSqlCacheIdx[self.__class__].items():
                            if v == len(KSqlCache[self.__class__]):
                                del KSqlCacheIdx[self.__class__][k]
                                break
                            del KSqlCache[self.__class__][-1]
                        for k,v in KSqlCacheIdx[self.__class__].items():
                            KSqlCacheIdx[self.__class__][k] += 1

                KSqlCache[self.__class__].insert(0,self)
                KSqlCacheIdx[self.__class__][str(criteria)]= 0 


        else:
            # mark this object as not usable as an actual data container
            self._deleated = True
                
    def __post_init__(self):
        """This is a 'no op' called at the end of __init__.  Subclasses should
        define as necessary.
        """
        pass
     

    def load (self,criteria={},**Values):
        """load data from the SQL layer.
        See __init__ for allowable criteria.
        """
        self._record=None
        if self._deleated:
            raise KdbomUsageError, "KSqlObjedt has been deleted"
        
        if self._table == None:
            raise KdbomDatabaseError, "Can't load SQL data. Table unknown."
        else:
            self._db = self._table.db

        # Different ways of specifing a record to base the object on
        #
        # kdbom.record object has been specified
        if isinstance(criteria,record):
            if criteria.table != self._table:
                raise KdbomDatabaseError,\
                      "Can't make KSqlObject from kdbom record, tables do not match"
            self._record = criteria
            self.SQLfields = self._record.data

        # Primary Key value has been specified  
        elif type(criteria) in (IntType,LongType):  
            try:
                self._record = record(table=self._table,PKvalue=criteria)
            except:
                raise KdbomLookupError , "no matching MySQL record found"

        # _strField Lookup
        elif self._strField != None and type(criteria) not in (DictType,TupleType,ListType):  
            try:
                if isinstance(self,VersionedKSqlObject):
                    self._record = self._table(criteria=criteria,returnLastRecord=True)[0]
                else:
                    self._record=self._table(criteria={self._strField.name:criteria},
                                             expectOneRecord=True)[0]
            except IndexError:
                raise ValueError , "Record Not Found. Table: %s, Record Name: %s" %(self.__class__,criteria)

        # a tuple like (SQL query,(params))
        # has been specified 
        elif ((type(criteria) == TupleType and len(criteria) ==2 and
               ( type(criteria[0])==StringType and type(criteria[1])==TupleType) and
               (re.match(r'SELECT\s+`?%s`?'%self._table.primary_key.name,criteria[0],re.IGNORECASE) != None or 
                re.match(r'SELECT\s+`?%s`?\.`?%s`?'%(self._table.name,self._table.primary_key.name),criteria[0],
                         re.IGNORECASE) != None))):
                # it is assumed that we have been passed a tuple with 
                # (Qry, params)
                cur=self._db.cursor()
                cur.execute(criteria[0],criteria[1])
                rowOne=cur.fetchone()
                if type(rowOne) != NoneType:
                    self._record=record(table=self._table,PKvalue=rowOne[0])                
        
        # a dictionary of field:value pairs or fcn.function arguments
        # like field=values have been specified
        else:
            if criteria == {}:
                criteria=Values
            try:
                if isinstance(self,VersionedKSqlObject):
                    self._record = self._table(criteria=criteria,returnLastRecord=True)[0]
                else:
                    self._record = self._table(criteria=criteria,expectOneRecord=True)[0]
            except IndexError:
                pass
        # record has been found, or maybe not
        
        if type(self._record) == NoneType:
            raise KdbomLookupError , "no matching MySQL record found"
        else:
            self.SQLfields = self._record.data
            self.update = self._record.update

    def __str__ (self):
        """Returns object's Name (contents of _strField) from atributes or from SQLfields.
        If None is in the field, __SQL_NULL__ is returned.  If you have foolishly specified
        a non string field as the _strField, a conversion to string will be attemped.
        """
        if self._strField != None:
            rv = self.SQLfields[self._strField.name]
            if type(rv) == StringType:
                return rv
            if rv == None:
                return '__SQL_NULL__'
            else:
                return str(rv)
        else:
            return str(self.SQLfields)

    def __int__(self):
        """returns the primary key value as an integer
        """
        return int(self.ID())

    def store (self):
        """store back to the database.
        save() and store() are the same method.
        This method does not commit the change!
        """
    
        if self._record != None and self._dirty:
            try:
                self._record.update(self.SQLfields)
                self._dirty = False
            except:
                raise KdbomDatabaseError, ("SQL update failed for the following table and data-\n%s.%s:%s" %
                                              (self._db.name,self._table.name,self.SQLfields))

    # save is an alias for store
    save = store

    def ID(self):
        """Return the value of the primary key of the underlying
        MySQL record.
        """
        try:
            return self._record.PKvalue
        except:
            return None

    def table(self):
        """ return the object's Table object.
        """
        return self._table
    
    table = classmethod(table)

    def db (self):
        """Return the object's Db object.
        """
        return self._table.db
    
    db=classmethod(db)

    def touchTimestamp(self):
        """Update timestamp of underlying record
        """
        self._record.touchTimestamp()
        self.load(self.ID())
        
    def __getattr__ (self,name):
        """Return a value from SQL fields if possible.
        """
        foundIt = False
        value = None

        if 'SQLfields' not in self.__dict__:
            raise KdbomProgrammingError, "Object has no SQLfields"
        
        if name in self.SQLfields:
            value = self.SQLfields[name]
            foundIt = True

        if foundIt:
            return value
        else:
            raise AttributeError, str(name)


    def __setattr__ (self,name,value):
        """Set value that will be stored back when the object's store
        method is called.  Error checking is deferred until the store call.

        Remember all the persistent values are capitalized!
        (if our MySQL naming conventions are followed)
        """

        try:
            if name in self.SQLfields:
                self.SQLfields[name] = value
                self._dirty = True

            else:
                self.__dict__[name] = value
        except:
            self.__dict__[name] = value


    def __eq__ (self,other):
        """Instances are equal if their underlying record is the same and
        neither are dirty.
        """

        if other.__class__ != self.__class__:
            return False

        if (self._record == other._record):
            if (not (self._dirty or other._dirty)):
                return True
        return False


    def mostlyEqual(self,other):
        """Returns true if class is the same and SQLfields are equal ignoring
        the primary Key and any timestamp (if the timestamp field is named "Timestamp"
        """

        myFields=copy(self.SQLfields)
        otherFields = copy(other.SQLfields)

        myFields['Timestamp']=None
        myFields[self._table.primary_key.name]=None

        otherFields['Timestamp']=None
        otherFields[self._table.primary_key.name]=None

        return myFields==otherFields


    def __cmp__ (self,other):
        return cmp(str(self),str(other))


    def __ne__ (self,other):
        return not self.__eq__(other)


    def __hash__ (self):
        """return a UID for this instance bases on db, db host, db port, table
        and primary key.
        """

        # shift each element of hash
        host = hash(self._record.db.host) >> 4
        port =  hash(self._record.db.port) >> 3
        db = hash( self._record.db.name)  >> 2
        table = hash(self._record.table.name) >> 1 
        pk = hash(int(self.ID()))

        return pk^table^db^port^host


    def __getstate__(self):
        """Return a picklable dictonary that __setstate__ uses to restore
        a serialized KSqlObject.
        """
        if self._deleated:
            return None
        
        rv = { 'ID' : self.ID() }
        for k,v in self.__dict__.items():
            if k in ('_db','_record','_strField'):
                continue
            if type(v) == MethodType:
                continue
            rv[k]=v
        return rv

    def __setstate__(self,state):
        """rebuild instance from __getstate__ data.
        """

        self._record=self._table[state['ID']]
        del state['ID']
        self._db=self._table.db

        for k,v, in state.items():
            self.__dict__[k] = v
        


    def delete(self):
        """delete the SQL record for this object and make the object unuseable.
        """
        self._dirty = False
        self.SQLfields = {}
        if not self._deleated:
            self._delete()
            self._deleated = True
        self._record = None
        
        

    def _delete(self):
        """handle the SQL part of the delete.  Some sublasses should define to
        take care of child records.
        """
        self._record.delete()
        
    def generator(cls,*params,**kwValues):
        """Returns a generator of objects of the same class.
        This is currently a wrapper for the module global function
        ksqlobject_generator.  See that doc string for calling
        information.
        """
        
        return ksqlobject_generator(cls,*params,**kwValues)

    generator = classmethod(generator)

    def randomInstance(cls,criteria={},**Values):
        """Returns a randomly selected instance of this class.
        """

        for k,v in criteria.items():
            if k not in Values:
                Values[k]=v

        keyField = cls._table.primary_key.name

        if Values == {}:
            query = "SELECT `%s` FROM %s" % (keyField,
                                             cls._table._dbQualName())
        else:
            query= cls._table._buildSelect(Values) % ('`' + keyField + '`')

        query += "\nORDER BY RAND()\nLIMIT 1"

        pkValue = cls._table.db.fetchall(query)[0][0]

        return cls(pkValue)

    randomInstance=classmethod(randomInstance)
    
    def oneFromQuery(cls,qry):
        """return one object corresponding matching the query.
        Uses ksqlobject_generator.  See that doc string for calling
        information.
        """
        pass 
    
    def friendOf(cls,friend):
        """Return a generator of instances of this class referenced by friend.
        friend must be a KSqlObject.  Friend can be a KSqlObject, or a list
        or tuple of them.  They can't be iterators more generally than that.
        If friend is a sequence a list of generators is returned.
        "Bosom friends" have their primary keys as foreign keys in this table,
        otherwise None is returned.
        """
        if type(friend) in (ListType,TupleType):
            return [cls.friendOf(f) for f in friend ]
        else:
            if not isinstance(friend,KSqlObject):
                raise ValueError, "friend must be a KSqlObject.  %s ,given instead" % friend.__class__

            if cls._table.primary_key.name in friend._table.fields.keys():
                # real friends have their primary keys as foreign keys
                # in this table.
                keyName = cls._table.primary_key.name
                return cls.generator(criteria={keyName:friend.SQLfields[keyName]})
            else:
                return None

    friendOf = classmethod(friendOf)
        

    def tableIDStrDict(self):
        """Return a dictionary of pkValue:_strField value pairs
        from the underlying table.
        """
        if self._strField != None:
            return self._table.idValueDict(self._strField)
        else:
            return {}

    def tableIDStrTuples(self,orderBy=''):
        """return a list of (pkValue,_strField value) tuples.  By default
        they are ordered by the _strField values, set orderBy=None for
        arbitrary ordering.

        ummm, actually this returns a list of lists not tuples.
        """
        if orderBy == '':
            orderBy == self._strField

        return self._table.idValueTuples(self._strField,orderBy=orderBy)
        


    def children(self,foreignClass):
        """Return child KSqlObjects.
        
        """
        rv = {}

        foreignTable = foreignClass._table

        for c in self._record.children(foreignTable):
            rv[foreignClass(c)]=None
        return rv.keys()
            

    def parents(self,foreignClass):
        """Return parent KSqlObjects.
        
        """
        rv = {}

        foreignTable = foreignClass._table
        
        for c in self._record.parents(foreignTable,collapseSingleton=False):
            rv[foreignClass(c)]=None
        return rv.keys()

    def relatives(self,foreignClass):
        """Return child and parent KSqlObjects.
        
        """
        rv = {}

        foreignTable = foreignClass._table

        for c in self._record.relatives(foreignTable):
            rv[foreignClass(c)] = None
        return rv.keys()


    def applyTag(self, tagStr):
        """Apply tag to object, inserting into database.
        Changes are pushed to db _immediately_.
        """

        try:
            flagID =self._tagTable(Name=tagStr)[0].PKvalue
        except:
            flagID = self._tagTable.insert(Name=tagStr)
            self._tagLinkTable.insert({self._table.name+'_ID': self.ID(),
                                       self._tagTable.name+'_ID':flagID})

        ct = self._tagLinkTable.count({self._table.name+'_ID': self.ID(),
                                       self._tagTable.name+'_ID':flagID})
        if ct == 0L:
            self._tagLinkTable.insert({self._table.name+'_ID': self.ID(),
                                       self._tagTable.name+'_ID':flagID})
        else:
            pass


    def hasTag(self,tagStr):
        """True if this object had the tag, otherwise False.
        """
        try:
            flagID = self._tagTable(Name=tagStr)[0].PKvalue
            ct = self._tagLinkTable.count({self._table.name+'_ID': self.ID(),
                                           self._tagLinkTable.name+'_ID':flagID})
            if ct >= 1L:
                return True
            else:
                return False
        except:
            return False


    def listTags(self):
        """
        """
        
        rv = []
        for tagRec in self._tagLinkTable({self._table.name+'_ID': self.ID()}):
            rv.append(self._tagTable[tagRec[self._tagTable.name+"_ID"]].Name)
        return rv
    tags=listTags


    def unlinkTag(self,tagStr):
        """Remove the tag from the object.
        Changes are pushed to db _immediately_.
        """

        try:
            flagID = self._tagTable(Name=tagStr)[0].PKvalue
            ct = self._tagLinkTable.delete({self._table.name+'_ID': self.ID(),
                                            self._tagTable.name+'_ID':flagID})
            if ct >= 1L:
                return True
            else:
                return False
        except:
            return False

    def unlinkAllTags(self):
        """Remove all tags from the object.
        Changes are pushed to db _immediately_.
        """

        self._tagLinkTable.delete({self._table.name+'_ID': self.ID()})


    def getByTag(cls, includeTags=[],excludeTags=[],showQuery=False):
        """Returns a generator of objects which are tagged with the include tags
        but do not have the exclude tags.  The tags should be given strings or
        as lists of strings.
        
        The underlying query will be printed if showQuery is True.
        """

        if type(includeTags) in StringTypes:
            includeTags = (includeTags,)
        if type(excludeTags) in StringTypes:
            excludeTags = (excludeTags,)

        inIDs = [cls._tagTable(Name=tagStr)[0].PKvalue for tagStr in includeTags]
        outIDs = [cls._tagTable(Name=tagStr)[0].PKvalue for tagStr in excludeTags]

        tagCount = len(includeTags) + len(excludeTags)

        # set up for query build
        joins=[]
        wheres=[]
        tblIdx=0
        
        for inID in inIDs:
            joins.append("LEFT OUTER JOIN %s tht%d ON tht%d.%s_ID = %s.%s_ID" %
                                     (cls._tagLinkTable._dbQualName(),tblIdx,tblIdx,
                                      cls._table.name,cls._table.name,cls._table.name))
            wheres.append("tht%d.%s_ID=%d" % (tblIdx,cls._tagTable.name,inID)) 
            tblIdx+=1
            
        for outID in outIDs:
            joins.append("""LEFT OUTER JOIN (SELECT * FROM %s WHERE %s_ID=%d ) tht%d
ON tht%d.%s_ID = %s.%s_ID""" %
                (cls._tagLinkTable._dbQualName(),cls._tagTable.name,outID,
                 tblIdx,tblIdx,cls._table.name,cls._table.name,cls._table.name))

            wheres.append("tht%d.%s_ID is Null" % (tblIdx,cls._tagTable.name)) 
            tblIdx+=1
            
        
        joinClause = '\n'.join(joins)
        whereClause = '\nAND '.join(wheres)

        qry = "SELECT DISTINCT %s.%s_ID FROM %s\n%s\nWHERE %s" % (cls._table.name,cls._table.name,cls._table._dbQualName(),
                                                                  joinClause,whereClause)
        if showQuery:
            print qry
        return ksqlobject_generator(cls,qry)
        

    getByTag = classmethod(getByTag)
    
    def knownTags(cls):
        """Returns a list of tag names in the tag table.
        """
        return [r.Name for r in cls._tagTable.records() ]
    
    knownTags = classmethod(knownTags)

def ksqlobject_generator(subclass,query=None,params=(),db=None,criteria={},
                         whereLiteral='',**Values):
    """Return a generator for KSqlObjects. query can be either:
    1) an SQL query string that returns the primary key values (note the
    params tuple will be passed to the database API in the usual way or
    2) a list/tuple of primary key values.

    The query (if any) will be executed using a cursor derived from db
    (a kdbom db instance) or if db=none the database of the  subclasse's
    underlying table.

    If query is none and there are no **Values all the records in the subclass's
    _table will be used, but if **Values are specified, a simple query wil be built
    automatically. See docs for kdbom.Table._buildSelect and __call__.

    """

    #whereLiteral=whereLiteral.replace('_','\_')  # not needed ?
    whereLiteral=whereLiteral.replace('%','%%%%') # needed to protect from python

    for k,v in criteria.items():
        if k not in Values:
            Values[k]=v

    
    keyField = subclass._table.primary_key.name

    if type(query) == NoneType:
        if Values == {} and len(whereLiteral) ==0 :
            query = "SELECT `%s` FROM %s" % (keyField,
                                             subclass._table._dbQualName())
                                             
        else:
            query= subclass._table._buildSelect(Values,whereLiteral=whereLiteral) % ('`' + keyField + '`')

    if type(query) == StringType:
        if db != None:
            cur = db.cursor()
        else:
            cur = subclass._table.db.cursor()
            
        cur.execute(query,params)

        row = cur.fetchone()
        while row != None:
            yield subclass(row[0])
            row = cur.fetchone()

    elif type(query) in (TupleType, ListType):
        for PKvalve in query:
            if (subclass,PKvalve) in KSqlObjectCache:
                yield KSqlCache[(subclass,PKvalve)]
            else:
                yield subclass(PKvalve)

    else:
        pass




def ksqlobject_list(subclass,query,params=(),db=None):
    """
    !!Deprecated!!  Use list(ksqlobject_generator)!

    Returns a list of KSqlObjects returned from ksqlobject_generator
    called with the same arguments. 
    """
    rv=[]
    rv.extend(ksqlobject_generator(subclass,query,params=params,db=None))
    return rv



def insert_KSqlObject(table=None,mustHave=(),
                       data={},**values):
    if data == {}:
        data=values

    for needs in mustHave:
        if needs not in data:
            raise KdbomDatabaseError , needs + ' required'

    _id = table.insert(data)

    return _id


class VersionedKSqlObject(KSqlObject):
    """
    """

    _table = None
    _tagTable=None
    _tagLinkTable=None
    _strField=None

    def __post_init__(self):
        """Lookup PK values of other matching records. Store them as
        self.versionPKvalues
        """

        self.PKvalues=[]
        for r in self._table(criteria=self._init_criteria):
            self.PKvalues.append(r.PKvalue)

        self.versionIdx = self.PKvalues.index(self.ID())
        

    def allVersions(self):
        """Returns a generator of record objects matching the originally
        specified criteria.
        """
        for pkv in self.PKvalues:
            yield self._table({self._table.primary_key.name:pkv})

                
class relationship:
    """table/field relationships."""
    def __init__ (self,parent=None, child=None):
        """Table to table relationship superclass"""
        field_class = field().__class__
        if parent.__class__ != field_class or child.__class__ != field_class:
            raise TypeError, "Parent and child must be fields"
        
        self.parent = parent
        self.child = child


    def insert(self):
        """Make parent and child tables aware of relationship."""
        # adding to table level objects
        # and field objects
        if self not in self.child.table.parents:
            self.child.table.parents.append(self)
            self.child.parentFields.append(self.parent)
            
        if self not in self.parent.table.children:
            self.parent.table.children.append(self)
            self.parent.childFields.append(self.child)

    def join2parent(self):
        rv = 'LEFT JOIN %s.%s ON %s.%s = %s.%s' % (self.parent.db.name,
                                                   self.parent.table.name,
                                                   self.child.table.name,
                                                   self.child.name,
                                                   self.parent.table.name,
                                                   self.parent.name)
        return rv

    def join2child(self):
        rv = 'LEFT JOIN %s.%s ON %s.%s = %s.%s' % (self.parent.db.name,
                                                   self.child.table.name,
                                                   self.parent.table.name,
                                                   self.parent.name,
                                                   self.child.table.name,
                                                   self.child.name)
        return rv

    
class one2many (relationship):
    """One to many table relationship""" 
    def __init__ (self,parent=None, child=None):
        relationship.__init__(self,parent=parent, child=child)
        if not self.parent.isUnique:
            raise Relationship_Error, "Parent must not have duplicate values"
        

        #count offspring
        # e.g. each parent key relates to how many
        # child records
        self.offspring_count = {}
        offspring = self.child.values
        self.parent_keys = self.parent.distinct_values
        for parent_key in self.parent_keys:
            self.offspring_count[parent_key] = 0
            while parent_key in offspring:
                self.offspring_count[parent_key] =  self.offspring_count[parent_key] + 1
                offspring.remove(parent_key)
                
        #count orphans
        self.orphan_count = {}
        while len(offspring) > 0 :
            orphan_key = orphans[0]
            if orphan_key in orphan_count:
                self.orphan_count[orphan_key] = self.orphan_count[orphan_key] + 1
            else:
                 self.orphan_count[orphan_key] = 1
            offspring.remove(orphan_key)

            
    def CheckParent(self):
        pass
    
class many2many (relationship):
    """Many to many table relationship"""
    def __init__ (self):
        pass
    
        
def PackDict(keys,values):
    if len(keys) != len(values):
        raise KeyError, "Keys and values must be same length"
    else:
        rv = {}
        count = len(values)
        i = 0
        while i < count:
            rv[keys[i]] = values[i]
            i = i + 1
        return rv


def connection (host=defaulthost, user=defaultuser, passwd=defaultpw,db=defaultDB):
        return MySQLdb.Connection(host=host, user=user, passwd=passwd, db=db)


def main ():
    print __doc__
    return 0

if __name__ == '__main__':
    sys.exit(main())

