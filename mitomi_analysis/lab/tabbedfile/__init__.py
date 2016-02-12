"""Classes for an object model based on tab separated values in a flat file.
"""

from types import *
import os
import random
import re
import warnings

BOL_COMMENT_CHARS = '#'
DEFAULT_ITEM_SEP=','
DEFAULT_KEY_SEP=':'
DEFAULT_KEY_STRIP=True
DEFAULT_VALUE_STRIP=True

PY_KEYWORDS = ('and','del','from','not','while',
               'as','elif','global','or','with',
               'assert','else','if','pass','yield',
               'break','except','import','print',
               'class','exec','in','raise',
               'continue','finally','is','return',
               'def','for','lambda','try')

RE_NOT_ALPHANUM = re.compile('[^A-Za-z0-9_]')



class FieldDefinitionError (Exception):
    pass

class FieldParseError (Exception):
    pass

class FieldSpec:
    """An object that has 2 methods fromTxt, and _toTxt and knows the
    name of the field. 
    """
    def __init__ (self,name,typeSpec='',defaultValue=None,strictParse=False):
        """Return an appropriate object for the given typeSpec (e.g. 'int', 'str',...)
        If a field is blank in the file, and the datatype is not str, the converted value
        will be set to defaultValue unless strictParse is True, in which case ValueError
        is raised.
        """
        if type(name) != StringType:
            raise FieldDefinitionError("field name must be a string.")
        if type(typeSpec) != StringType:
            raise FieldDefinitionError("field typeSpec must be a string.")

        if RE_NOT_ALPHANUM.search(name) != None:
            warnings.warn (
                """field name %s has a character in it that is not allowed.
                Only letters, numbers and underscores are allowed, other characters will be removed""" % name)
            name=RE_NOT_ALPHANUM.sub('',name,count=len(name))

        if len(name)==0:
            name = 'field'+ str(random.randint(1000000,10000000))
            warnings.warn (
                """field name no charters left! A random name hass ben assigned to the field: %s""" %name)

        if name in PY_KEYWORDS:
            raise FieldDefinitionError(
                "field name '%s' is a python keyword - THAT IS FORBIDDEN! " % name)
           
            
        self.name=name
        self.typeSpec=typeSpec
        self.defaultValue = defaultValue
        self.strictParse = strictParse
        
        if typeSpec ==  'int':
            self._fromTxt = int
            self._toTxt = str
        elif typeSpec == 'float':
            self._fromTxt=float
            self._toTxt = str
        elif typeSpec == 'date' or typeSpec.startswith('date '):
            raise NotImplementedError('date fields not supported yet')
        elif typeSpec.startswith('datetime '):
            raise NotImplementedError('datetime fields not supported yet')
        elif typeSpec.startswith('list'):
            raise NotImplementedError('list fields not supported yet') 
        elif typeSpec.startswith('dict'):
            raise NotImplementedError('dict fields not supported yet') 
        elif typeSpec == '' or typeSpec == 'str':
            self._fromTxt=lambda x: x
            self._toTxt=lambda x: x
        else:
            raise FieldDefinitionError("type specifier '%s' unknown" % typeSpec)



    def fromTxt(self,text):
        """Convert text to proper data type
        """
        try:
            return self._fromTxt(text)
        except ValueError:
            if not self.strictParse:
                return self.defaultValue
            else:
                raise


    def toTxt(self,value):
        """Convert a value to text.
        """
        if value == None:
            return ''
        else:
            return self._toTxt(value)

def floatOrString(text):
    try:
        return float(text)
    except:
        return text


class NumberOrString(FieldSpec):
    """A lazy class that returns a float if possible, if not a string will do
    """
    def __init__(self,name):
        self.name=name
        self._toTxt = str
        self._fromTxt = floatOrString
    

class Record:
    """A line (row) from a file of tabbed records.
    
    Fields are accessible for reading or setting as attributes, record.thing,
    or like a dictionary: record['thing'].
    """

    def __init__(self,tableFile,rawText=None):
        """Make a new Record.  Add the record to the
        tableFile's record list.
        """
        self.data={}
        self.tableFile = tableFile
        self.fieldSpecs = tableFile.fieldSpecs
        self.fieldDict = dict(list(zip([x.name for x in self.fieldSpecs],
                              self.fieldSpecs)))
        self.fields=[]
        

        if rawText != None:
            rawFields = rawText.split('\t')
            myLength = min(len(self.fieldSpecs), len(rawFields))
            self.__lenght = myLength
            for i in range(myLength):

                fieldDef = self.fieldSpecs[i]
                fieldText=rawFields[i]
                try:
                    myData = fieldDef.fromTxt(fieldText)
                    self.data[fieldDef.name]=myData
                    self.fields.append(myData)
                except ValueError:
                    raise FieldParseError("Error converting '%s' to '%s' on line %d of %s" %
                                            (rawFields[i],self.fieldSpecs[i].typeSpec,
                                             tableFile._fileLine,tableFile.rawFile.name))
        for k in list(self.fieldDict.keys()):
            if k not in self.data:
                self.data[k]=None

        tableFile.records.append(self)

        self.__post_init__()


    def sum(self):
        """
        """
        

    def __post_init__(self):
        '''
        '''
        pass

    def __len__(self):

        return len(self.fields)

    def __getattr__(self,name):
        """Read attribute interface
        """
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(str(name))


    def __setattr__(self,name,value):
        """Set attribute interface.
        """
        if name != 'data' and name in self.data:
            self.data[name]=self.fieldDict[name]._fromTxt(value)
        else:
            self.__dict__[name]=value

    def __getitem__(self,name):
        """Dictionary interface
        """
        if type(name) == StringType:
            return self.data[name]
        else:
            return self.fields[name]
        

    def __str__ (self):
        """The record as a string.
        """
        rv=[]
        for f in self.fieldSpecs:
            rv.append(f.toTxt(self.data[f.name]))
        return '\t'.join(rv)


class SimpleRecord(list):
    """A record interface for files with no field specs, hence no field names and no
    dictionary interface.  This is just a list
    """
    def __init__(self,tableFile,rawText=None):
         list.__init__(self,rawText.split('\t'))
         self.tableFile=tableFile
         tableFile.records.append(self)
        
class TabbedFile :
    """A file full of records of tab separated fields.
    """

    _recordClass=Record

    def __init__ (self,fileOrPath=None,bolComment=BOL_COMMENT_CHARS,
                  fieldSpecs=None,strictParse=False,noFieldLine=False):
        """
        Note: none of the 'list' ro 'dict' or date stuff below is implemented yet.

        Make a new TabbedFile object.  A file like object may be specified.
        In which case the structure of the fields will be deduced, using the first
        non-comment line. The structure of that line should be.

        name1%%%datatype1<TAB>name2%%%datatype2<TAB>...<TAB>nameN%%%datatypeN

        Datatypes are all strings by default.  Optionally, 'int', 'float', 'date',
        'datetime','list X', 'dict X Y', may be specified, after '%%%'.  For  list X
        and  dict X Y,replace X and Y with the appropriate character separating elements.

        X = item separator
        Y = key/value separator

        Note the user is responsible for ensuring that the delimiter characters do not,
        appear in the data.  There is no quoting mechanism.  <TAB> and '%%%' are not
        valid values for X or Y.

        The object is iteratable and parses the file on an as needed basis.  Iteration
        returns records one at a time.  During initial iteration the records list grows,
        and the sorting methods will operate on the incomplete list. Additional parsing,
        by iteration or the parse method will append records to the previously sorted
        list.

        """
        
        self.BOFcommentLines=[]
        self.fieldSpecs=[]
        self.records=[]
        self.rawFile=None
        self.strictParse = strictParse
        self._parsed=False
        self._fileLine=0


        if fileOrPath != None:
            if type(fileOrPath) == FileType:
                self.rawFile = fileOrPath
                
            elif type(fileOrPath) == StringType:
                if not os.access(fileOrPath,os.R_OK):
                    raise IOError("Couldn't open file: %s" % fileOrPath)
                self.rawFile=file(fileOrPath)

            else:
                raise IOError("Couldn't open file: %s.  fileOfPath must be a string or a file object."
                                % fileOrPath)
            
            bolPos=self.rawFile.tell()
            for l in self.rawFile:
                l=l.rstrip('\n')
                if re.match('^[%s]'% bolComment,l) != None:
                    self.BOFcommentLines.append(l)
                    bolPos=self.rawFile.tell()
                    continue
                elif not noFieldLine:
                    # read fieldspec line
                    fields = l.split('\t')
                    for f in fields:
                        subF = f.split('%%%',1)
                        name = subF[0]
                        if len(subF) == 2:
                            typeStr=subF[1]
                        else:
                            typeStr = ''
                        self.fieldSpecs.append(FieldSpec(name,typeStr))
                    # stop reading file
                    break
                else:
                    fields = l.split('\t')
                    for f in fields:
                        self.fieldSpecs.append(NumberOrString(''))
                    self.rawFile.seek(bolPos)
                    break
            
        # run post init code of the subclass if any
        self.__post_init__()

    def __post_init__(self):
        """This is a method the subclasses can overwrite to preform
        any housekeeping that needs to run when the object is created.
        
        __init__ runs it when it is finished.
        """
        pass
    
    def __len__ (self):
        """Returns the number of records that have been parsed.
        """
        return len(self.records)

    def __iter__(self):
        """Return a record at a time.
        """
        if not self._parsed:
            for l in self.rawFile:
                self._fileLine+=1
                self._recordClass(self,l.rstrip('\n'))
                yield self.records[-1]

            self._parsed=True
            self.rawFile.close()
            return
        else:
            for r in self.records:
                yield r

    def getFields(self,fields):
        """list of lists, where each inner list is a column vector.
        If only a single field is given the result is not nested.
        """
        if type(fields) not in (TupleType,ListType):
            fields = (fields,)

        if len(fields) == 1:
            return [x[fields[0]] for x in self.records]
        else:
            return list(map(self.getFields, fields))
                

    def parse(self):
        """Read the file into the file's record list.
        """
        for r in self.__iter__():
            pass
        self._parsed=True


    def __str__(self):
        """The file in text format.
        Records are provided in the current, sorted or not, order. 
        """
        rLines = self.BOFcommentLines[:]
        rLines.append('\t'.join(["%s %s" % (x.name,x.typeSpec) for x in self.fieldSpecs]))
        rLines.extend(list(map(str,self.records)))
        rLines.append('')
        return '\n'.join(rLines)
        

    def sort(self, cmp=None, key=None, reverse=False):
        """Sort records using the list.sort method.
        """
        self.records.sort(cmp=cmp,key=key,reverse=reverse)
        

    def fieldSort(self,fields,reverse=False):
        """Sort the records by the values of the specified field(s).
        """
        def makeKey(rec):
            rv = []
            for f in fields:
                rv.append(rec[f])
            return rv
        
        if type(fields) not in (TupleType,ListType):
            fields = (fields,)

        self.records.sort(key=makeKey,reverse=reverse)

    def dump(self,outPath=None,overwrite=False,saveBackup=True):
        """Write the file back to the disk.
        If outPath is given, the file is saved under that name.

        If no outPath is given, and overwirte is True, the file is
        saved under the same name and path that it was loaded from;
        if save backup is true a backup copy (.bak) is made first.
        """
        if type(outPath) == StringType:
            if os.path.exists(outPath) and saveBackup:
                bakName = outPath+'.bak'
                if os.path.exists(bakName):
                    os.unlink(bakName)
                os.link(outPath,bakName)
                os.unlink(outPath)
            file(outPath,'w').write(str(self))
        else:
            if overwrite:
                outPath=self.rawFile.name
                if not self.rawFile.closed:
                    self.rawFile.close()
                self.dump(outPath=outPath,overwrite=overwrite,saveBackup=saveBackup)
                
            else:
                warnings.warn ("dump: must specify outPath or set overwrite to True")

    def __getitem__ (self,idx):
        """return a record by index.
        """
        return self.records[idx]

    def slab(self,rows=None,cols=None):
        if len(self) == 0:
            return [[]]

        rv = []
        if rows == None:
            rows = list(range(len(self)))
        if cols == None:
            cols = list(range(len(self[0])))

        for y in rows:
            row = []
            for x in cols:
                row.append(self[y][x])
            rv.append(row)
        return rv
                       


class SimpleTabbedFile(TabbedFile):
    """
    """

    _recordClass=Record


def tabbifyMatrix(mat):
    """return a list of tab-delimited elements and
    new line seperated line taken from a nested 2D
    set of lists ."""

    lines=[]

    for l in mat:
        lines.append('\t'.join([str(f) for f in  l]))
    return '\n'.join(lines)
    
    
