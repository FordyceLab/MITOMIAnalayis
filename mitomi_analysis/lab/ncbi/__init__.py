#!/usr/local/bin/python
#
# NCBI Tools
#
# DeRisi Lab 2007
#
# Read This:
# http://www.ncbi.nlm.nih.gov/books/bv.fcgi?rid=coursework.chapter.eutils
#

import os
import sys
import StringIO
import types
import urllib
import datetime, time

import sys, os, re
from kdbom import kdbom

from xml.dom import minidom
import utils

__cvs_revsion__ = "$Revision: 1.29 $"
__version__ = "0.0.1"

################################
# Request Throttling Constants
REQUEST_DELAY = 3
BATCH_SIZE = 500
LOCK_STRING = "ncbiRequest"
LOCK_WAIT_TIMEOUT = 30

######################
# NCBI URLs
EUTILS_URL = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
ESUMMARY_URL = EUTILS_URL + "esummary.fcgi?"
EFETCH_URL = EUTILS_URL + "efetch.fcgi?"
ESEARCH_URL = EUTILS_URL + "esearch.fcgi?usehistory=y&"

########################
# Global URL Parameters

if 'MAILTO' in os.environ:
    _author_email_ = os.environ[MAILTO]
else:
    _author_email_="ncbitools@derisilab.ucsf.edu"

_tool_str_=os.path.split(sys.argv[0])[-1]
if not _tool_str_: # this doesn't seem right
    _tool_str_="derisilab_ncbitools"

# WARNING ncbiID is now a function!!
# Scripts can set ncbi._author_email_ and ncbi._tool_str
#
def ncbiID():
    """returns url escaped (quoted) email and tool
    parts of the web URL for various etools.

    Scripts can set ncbi._author_email_ and ncbi._tool_str. to
    override the default values.
    """
    return "&email=%s&tool=%s" % tuple([urllib.quote_plus(x)
                                        for x in (_author_email_,_tool_str_)])

#
# This seems like a necessary
# evil, since importing this
# module should essentially always
# result in an NCBI request, which
# requires the database.
#
try:
    ncbiDB = kdbom.db(host='derisi-b14',
                       db='NCBI')
except:
    try:
        ncbiDB =  kdbom.db(host='derisi-b14',
                           db='NCBI',
                           user='readonly',
                           passwd='')
    except:
        print 'NCBI mysqldb not found'

try:
    taxDB = kdbom.db(db='taxonomy_2008_03_06',
                     reuseDBconnection=ncbiDB)
except:
    print 'taxonomy mysqldb not found'


##########################################################
#
# Support for etools queries
#
# For a good time read
# See: http://www.ncbi.nlm.nih.gov/books/bv.fcgi?rid=coursework.chapter.eutils
#

# Generic Error specific to this interface
class NCBIRequestError( Exception ):
    pass

# This replaces urlopen()
def throttleRequest( url,debug=False,**args ):
    """Given a request url, grabs the
    server-wide NCBI Lock from blade-14, performs the request,
    and returns the result as an open file like object
    ( just like urlopen() )

    Raises an NCBIRequestError on failure."""

    grabLock = ncbiDB.execute("SELECT GET_LOCK(%s,%s)",
                              (LOCK_STRING, LOCK_WAIT_TIMEOUT) )
    if grabLock != 1:
        raise NCBIRequestError, ("Error acquiring NCBI request lock: " +
                                 str(grabLock))
    #TODO:  What about this??
    #_mysql_exceptions.OperationalError:
    #(1142, "UPDATE command denied to user
    #'readonly'@'derisi-b1' for table 'NCBI_Lock'")
    
    lastLookup = ncbiDB.fetchall("SELECT Last_Lookup FROM NCBI_Lock")[0][0]
    minimumWaitTime = datetime.timedelta( seconds=REQUEST_DELAY )

    if lastLookup > datetime.datetime.today():
        raise NCBIRequestError, ("Time incongruity in NCBI_Lock table: "
                                 "%s > %s" %
                                 (lastLookup, datetime.datetime.today()))
    while( datetime.datetime.today() - lastLookup  < minimumWaitTime ):
        time.sleep( 1 )

    # Now we're ready to make the request...
    url = (url +
           '&'.join([(k)+'='+(str(v)) for k,v in args.items()]) +
           ncbiID())

    if debug:
        print "url: %s" %url
    
    output = urllib.urlopen( url )
    
    ncbiDB.execute("UPDATE NCBI_Lock SET Last_Lookup=NOW();")
    ncbiDB.execute("SELECT RELEASE_LOCK(%s)", (LOCK_STRING) )
    ncbiDB.commit()
    
    return output

# Basic call to esummary. Hides the throttling,
# batching, and XML parsing, returning a nice
# dict-of-dicts.
# TODO: Add support for WebEnv/query_key
def esummary( eDB,*idList,**kwargs):
    """Makes an eSummary request to NCBI and returns
    a dict of dictionaries containing the results -
    one dictionary per ID, indexed on the ID, containing
    all of the information NCBI returns in a summary query."""

    output = {}

    def addToOutput(xmlRslt):
        document = minidom.parse( xmlRslt )
        xmlRslt.close()
        summaries = document.getElementsByTagName("DocSum")
        for summary in summaries:
            myID = int(summary.getElementsByTagName("Id")[0].firstChild.data)
            output[myID] = {}
            items = summary.getElementsByTagName("Item")
            for item in items:
                name = item.getAttribute("Name")
                if item.firstChild:
                    value = item.firstChild.data
                else:
                    value = None
                if item.getAttribute("Type") == "Integer":
                    value = int(value)
                output[myID][name] = value


    if len(idList) > 0:
        idList=utils.flatten(idList)
        idLists = utils.batchList( idList, batchSize=BATCH_SIZE )
        for idL in idLists:
            result = throttleRequest( ESUMMARY_URL, retmode='xml',db=eDB,
                                      id=",".join(map(str,idL)))
            addToOutput(result)

    elif ('count' in kwargs and
          'WebEnv' in kwargs and
          'query_key' in kwargs):
        count =kwargs['count']
        i=1
        while i <= count:
            result = throttleRequest(ESUMMARY_URL,
                                     db=eDB,
                                     retmode='xml',
                                     WebEnv =kwargs['WebEnv'],
                                     query_key=kwargs['query_key'],
                                     retmax=BATCH_SIZE,
                                     retstart=i)
            addToOutput(result)
            i+=BATCH_SIZE
    else:
        raise ValueError, "nothing to fetch, esearch result or iterable of IDs required"
       
    

    return output


def esearch(eDB,searchTerm,field="[All Fields]"):
    """Takes an entrez database abd search term.  Returns a dictionary,
    with 'count', 'query_key' and 'WebEnv'.

    Put these right in to efetch (others???) as keyword arguments.
    """

    result=throttleRequest(ESEARCH_URL,
                           db=eDB,
                           term=searchTerm,
                           field=field)

    sDoc = minidom.parse(result)

    return {'count':int(sDoc.getElementsByTagName('Count')[0].firstChild.data),
            'query_key':sDoc.getElementsByTagName('QueryKey')[0].firstChild.data,
            'WebEnv':sDoc.getElementsByTagName('WebEnv')[0].firstChild.data}


def efetch(eDB,rettype,oFile,*args,**kwargs):
    """takes a entrez database and a return type.
    records to be fetched can be an iterable of primary identifiers
    for the database specified, or count, query_key and WebEnv, from
    esearch can be specified as keyword arguments.


    Since large datasets are expected, an open file or file like thing
    (StingIO) must be specified as oFile the returned data are put in that
    buffer.
    """
    
    args=utils.flatten(args)
    if len(args) > 0:
        # IDs specified in call
        idLists = utils.batchList( args, batchSize=BATCH_SIZE )
        for idL in idLists:
            result = throttleRequest(EFETCH_URL,
                                     db=eDB,
                                     retmode=rettype,
                                     id= ','.join([str(x) for x in idL]))
            oFile.write(result.read())
    elif ('count' in kwargs and
          'WebEnv' in kwargs and
          'query_key' in kwargs):
        count =kwargs['count']
        i=1
        while i <= count:
            result = throttleRequest(EFETCH_URL,
                                     db=eDB,
                                     rettype=rettype,
                                     WebEnv =kwargs['WebEnv'],
                                     query_key=kwargs['query_key'],
                                     retmax=BATCH_SIZE,
                                     retstart=i)
            oFile.write(result.read())
            i+=BATCH_SIZE
        else:
            raise ValueError, "nothing to fetch, esearch result or iterable of IDs required"


##############################################################
#
# Classes that represent efetch data returned with retmode=xml
# where each instance is isomorphous to one given id
#

#
# Taxon Objects
#
class Taxon :
    def __init__(self,xml=None):
        """Returns an object representing information for a taxon downloaded from NCBI.
        xml can be text or a minidom element that is a child of a TaxaSet element.

        Attributes:
            taxID (int)
            scientificName (str)
            synonyms (list)
                [syn1,syn2,...]
            otherNames (dict)
                {typeTag1:name1,...} 
            rank (str)
            division (str)
            geneticCodeID (int)
            geneticCodeName (str)
            mitoGeneticCodeID (int)
            mitoGeneticCodeName (str)
            lineage (list)
                [(taxID1,name1,rank1),(taxID2,name2,rank2),...]
            createDate (datetime.date)
            updateDate (datetime.date)
            pubDate (datetime.date)
        
        """

        # make empty object
        
        self.taxID=None
        self.scientificName=None
        self.synonyms =[]
        self.otherNames = {}
        self.rank=None 
        self.division =None
        self.geneticCodeID =None
        self.geneticCodeName =None
        self.mitoGeneticCodeID =None
        self.mitoGeneticCodeName=None
        self.lineage =[]
        self.createDate=None
        self.updateDate=None
        self.pubDate=None

        
        if xml != None:
            # if input is text it should be the
            # raw result of an efetch,
            # i.e. a TaxaSet.  Parse and grab the 
            # first Taxon
            if type(xml) in types.StringTypes:
                doc = minidom.parseString(xml)
                
                #print doc.toxml()
                for n in doc.childNodes:
                    #print n.nodeName
                    #print n.childNodes
                    if n.nodeName == 'TaxaSet':
                        #print n.childNodes
                        for cn in n.childNodes:
                            #print cn.nodeName
                            if cn.nodeName == 'Taxon':
                                xml=cn
                                #print cn.__class__
                                break
                        break
            # now we have an xml.minidom thing
            # call all the microparsers
            if not isinstance(xml,minidom.Element):
                raise ValueError, "can't parse input XML, or not a minidom.Element"
            elif xml.parentNode.nodeName != 'TaxaSet':
                raise ValueError, "dom element not a child of a TaxaSet"
            else:
                self.taxID,self.scientificName,self.rank,self.division=idNameRankDivFromTaxonElem(xml)
                self.createDate,self.updateDate,self.pubDate=datesFromTaxonElement(xml)
                self.synonyms,self.otherNames=otherNamesFromTaxonElement(xml)
                self.lineage=lineageFromTaxonElement(xml)
                try:
                    self.mitoGeneticCodeID,self.mitoGeneticCodeName=idNameFromCodeElement(
                        xml.getElementsByTagName('MitoGeneticCode')[0])
                except IndexError:
                    pass
                try:
                    self.geneticCodeID,self.geneticCodeName,=idNameFromCodeElement(
                        xml.getElementsByTagName('MitoGeneticCode')[0])
                except:
                    pass
                
    def rankLookup(self,rank):
        """returns the (taxID, name) of the taxon in lineage that
        matches rank.
        
        Returns None if rank isn't found.
        """
        # if I am this rank, rank will not be
        # in the lineage --- return info for self 
        if self.rank == rank:
            return self.taxID,self.scientificName
        
        for taxID,name,r in self.lineage:
            if r==rank:
                return(taxID,name)
        #default
        return None
    
    def family(self):
        """
        """
        return self.rankLookup("family")

    def genus(self):
        """
        """
        return self.rankLookup("genus")

    def species(self):
        """
        """
        return self.rankLookup("species")

#
# Taxon microparsers; Taxon needs these.
# They could also be useful independently.
#
def idNameRankDivFromTaxonElem(e):
    """Returns [taxid,scientific name, rank, division]
    e is a Taxon xml.minidom.Element of type Taxon.
    """
    rv = [None,None,None,None]

    idx = {'TaxId':0,
           'ScientificName':1,
           'Rank':2,
           'Division':3}

    for n in e.childNodes:
        if None not in rv:
            break
        
        if n.nodeName in idx:
            try:
                rv[idx[n.nodeName]]= int(n.childNodes[0].nodeValue)
            except:
                rv[idx[n.nodeName]]= n.childNodes[0].nodeValue        
    return rv


def idNameFromCodeElement(e):
    """Returns [Id,Name]
    e is a Taxon xml.minidom.Element of type like:
    'GeneticCode', 'MitoGeneticCode', etc. .
    """
    rv = [None,None]

    idx = {'GCId':0,
           'MGCId':0,
           'GCName':1,
           'MGCName':1 }
    
    for n in e.childNodes:
        if None not in rv:
            break
        
        if n.nodeName in idx:
            try:
                rv[idx[n.nodeName]]= int(n.childNodes[0].nodeValue)
            except:
                rv[idx[n.nodeName]]= n.childNodes[0].nodeValue        
    return rv


def otherNamesFromTaxonElement(e):
    """Returns ([syn1,syn2,...],{NameType1:name1,..})
    generated from the OtherNames section,if any, of a
    Taxon element.
    e is a Taxon xml.minidom.Element of type Taxon.
    """
    syn=[]
    others={}
    try:
        oNames = e.getElementsByTagName('OtherNames')[0]
    except IndexError:
        pass
    else:
        for e in oNames.childNodes:
            if e.nodeName != '#text':
                if e.nodeName == 'Synonym':
                    syn.append(e.childNodes[0].nodeValue)
                else:
                    others[e.nodeName]=e.childNodes[0].nodeValue
    return syn,others


def lineageFromTaxonElement(e):
    """Returns a list of (taxid,name,rank) tuples from
    the lineage of a Taxon element.
    e is a Taxon xml.minidom.Element of type Taxon.
    """
    rv=[]

    try:
        lEx=e.getElementsByTagName('LineageEx')[0]
        lTaxa = lEx.getElementsByTagName('Taxon')
        for t in lTaxa:
            rv.append(idNameRankDivFromTaxonElem(t)[:3])
    except IndexError:
        pass
    return rv



def datesFromTaxonElement(e):
    """returns [CreateDate,UpdateDate,PubDate] where each
    date is a datetime.date object, from a Taxon element.
    e is a Taxon xml.minidom.Element of type Taxon.
    """
    rv = [None,None,None]

    idx = {'CreateDate':0,
           'UpdateDate':1,
           'PubDate':2 }
    
    for n in e.childNodes:
        if None not in rv:
            break
        
        if n.nodeName in idx:
            y,m,d = [int(x) for x in n.childNodes[0].nodeValue.split('/')] 
            rv[idx[n.nodeName]]= datetime.date(y,m,d)

    return rv


def getTaxa( idList ):
    """returns Taxa for taxIDs in idList.
    """

    rv=[]
    
    sioBuffer = StringIO.StringIO()
    efetch('taxonomy','xml',sioBuffer,idList)

    sioBuffer.seek(0)
    doc = minidom.parse(sioBuffer)
    ts = doc.getElementsByTagName('TaxaSet')[0]

    for t in ts.childNodes:
        if t.nodeName == 'Taxon':
            rv.append(Taxon(t))
    return rv
    
#
# CoreNucleotide Objects
#

#
# Other (pubmed, etc)
#



########################################################
#
# Other Functions
#

def giTaxid(gi,tables=[taxDB.gi_taxid_nucl]):
    """Returns the source ncbi taxid of a gi,
    searching though  the tables specified
    tables.
    """

    giTaxon=None
            
    
    for t in tables:
        dbRecs = t(gi=gi)
        if len(dbRecs) > 0:
            giTaxon = dbRecs[0].tax_id
            break
    return giTaxon
    


def accession2gi(accList):
    """returns a dictionary of {accession:GI}.
    """
    rv = {}
    for acc in accList:
        rv[acc]=None

    
    searchRslt = esearch('nuccore','+or+'.join(accList),
                         field="ACCN")

    esRslt = esummary('nuccore',WebEnv=searchRslt['WebEnv'],
                      query_key=searchRslt['query_key'],
                      count=searchRslt['count'])
    print esRslt

    for gi,summary in esRslt.items():
        rv[summary['Caption']]=gi

    return rv
                         

    
