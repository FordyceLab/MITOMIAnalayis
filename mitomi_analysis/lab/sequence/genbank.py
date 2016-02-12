#!/usr/local/bin/python
#
#
#
# $Id: genbank.py,v 1.7 2008/02/25 23:12:44 peter Exp $ 
#
from sequence import complement

__version__ =  '$Revision: 1.7 $'

import sys
import re
import time
import types
import urllib.request, urllib.parse, urllib.error

from .__init__ import *

from datetime import datetime
from io import StringIO
from traceback import print_exc

class GenBank_Lookup_Error (Exception):
    pass

class GenBank_Insertion_Error (Exception):
    pass


sectionStub = r'^(%s.+?)^\S'
subsectionStub = r'(^ {5}%s.+?)^ {5}\S'

sectionRE = re.compile(r'^(\w+) +',re.MULTILINE)
subsectionRE = re.compile('^ {5}(\w+) +',re.MULTILINE)

giRE =  re.compile(r'^VERSION.* GI:(\d+)',re.MULTILINE)

def txt2GI (recText):
    return int(giRE.search(recText).group(1))
               

class Record(StringSequence):
    """Simple GenBank Representation.
    """
    def __init__(self,recordContent=None):
        """Make a new genbank record.
        recordContent can be a string or a file like thing.
        if recordContent is file like the files position will be moved 
        forward to the beginning of the next record (if any) of to EOF.
        """
        if recordContent != None:
            if type(recordContent) in (str,):
                self.gbr=recordContent
            else:
                recFound = False
                recLines = []
                
                for l in recordContent:
                    if not recFound:
                        if l.startswith('LOCUS'):
                            recFound=True
                        else:
                            continue
                    recLines.append(l)    
                    if l=='' or l.startswith('//'):
                        self.gbr=''.join(recLines)
                        break
            self.sequence=self.parseSequence()
    
    def GI(self):
        """return the gi (integer) of the record
        """
        return txt2GI(self.gbr)
        
                    
    def features(self):
        """generator of Feature 
        """
        for s,c in self.sections():
            if s == 'FEATURES':
                fSplit = subsectionRE.split(c)
                fSplit.pop(0)
                while len(fSplit) > 1:
                    yield(Feature(self,fSplit.pop(0),fSplit.pop(0)))
                


    def sourceNCBITaxID (self,debugLevel=0):
        """get the taxon of the 'source' organism"""

        try:
            for f in self.features():
                 if f.ftype == 'source':
                     for ref in f.qualifiers['db_xref']:
                         (db,id) = ref.split(':')
                         if db == 'taxon':
                             return int(id)
            return None

        except:
            if debugLevel != 0:
                print_exc(None,sys.stdout)
            
            return None

    def sections(self):
        """Generator of sections
        """
        secSplit =  sectionRE.split(self.gbr)[1:]
        while len(secSplit) >1:
            yield(secSplit.pop(0),secSplit.pop(0))

    def section(self,sectionStr):
        """Returns the string content of a particular section.
        """
        return re.search(r'^(%s.+?)^\S'%sectionStr, self.gbr,re.MULTILINE | re.DOTALL).groups()[0]

    def subsection(self,sectionStr,subsectionStr):
        """Returns the string content of a particular subsection.
        """
        mySection = self.section(sectionStr)

    def parseSequence(self):
        oLines = self.section("ORIGIN").split('\n')[1:]
        return ''.join([''.join(l.split()[1:]) for l in oLines]).upper()
    
    def fasta(self):
        """ return a fasta Record
        """
        from . import fasta
        return fasta.Record(title=str(self.GI),sequence=self.sequence())

class Feature :
    """GenBank Feature representation.
    """
    def __init__ (self,record,featureType,featureTxt):
        self.record=record
        self.qualifiers={}
        lineOne, remainder = featureTxt.split('\n',1)
        self.type=featureType
        self.ftype=self.type
        self.location = Location(record,lineOne.strip())
        refs =remainder.split('                     /')
        for r in refs[1:]:
            kv = r.strip().split('=',1)
            if len(kv) ==1:
                k=kv[0]
                v=None
                self.qualifiers[k]=v
            else:
                k,v = r.strip().split('=')
                k = k.strip('"')
                v = v.strip('"')
                if k=='db_xref' and 'db_xref' not in self.qualifiers:
                    self.qualifiers[k] = [v]
                elif k in self.qualifiers:
                    if type(k) != type([]):
                        self.qualifiers[k] = [ self.qualifiers[k],v]
                    else:
                        self.qualifiers[k].append(v)
                else:
                    self.qualifiers[k.strip('"')]=v.strip('"')
                    
    def sequence(self):
        """return the 
        """
        recSeq = self.record.sequence
        sections = []
        for region in self.location.regions:
            s = recSeq[region.start-1:region.end]
            if region.complement:
                s=reverseComplement(s)
            sections.append(s)
            
        return ''.join(sections)
    
    def regions(self):
        """return location.regions
        """
        return self.location.regions


class Location :
    """Feature Location
    """
    
    complementRE = re.compile(r'^complement\((.*)\)$')
    joinRE = re.compile(r'^join\((.*)\)$')
    orderRE = re.compile(r'^order\((.*)\)$')
    singleBaseRE = re.compile(r'^(\d+)$')
    locRE = re.compile(r'^(<?)(\d+)([<.^>]+)(\d+)(>?)$')
    
    def __init__(self,record,locText):
        """Return a new location
        """
        self.record=record
        self.regions=[]
        self._parseRegions(locText)
        
    def _parseRegions(self,txt,complement=False):
        cMatch = self.complementRE.match(txt)
        jMatch = self.joinRE.match(txt)
        oMatch = self.orderRE.match(txt)
        sbMatch = self.singleBaseRE.match(txt)
        locMatch = self.locRE.match(txt)
              
        #print cMatch,jMatch,oMatch,sbMatch,locMatch,1000
        
        if cMatch != None:
            #print 'complement'
            self._parseRegions(cMatch.group(1),complement=True)
        elif jMatch != None:
            #print 'join'
            self._parseRegions(jMatch.group(1),complement=complement)
        elif oMatch != None:
            #print 'order'
            self._parseRegions(oMatch.group(1),complement=complement)
        else:
            # no parens
            locs = txt.split(',')
            if len(locs) > 1:
                for loc in locs:
                    self._parseRegions(loc,complement=complement)
    
            elif sbMatch != None:
                start = int(sbMatch.group(1))
                self.regions.append(Region(start,start,complement))        
            elif  locMatch != None:
                start=int(locMatch.group(2))
                end=int(locMatch.group(4))
                midA = locMatch.group(3)
                if midA == '..':
                    ambigStr =''
                else:
                    ambigStr = midA
                if locMatch.group(1) != None:
                    ambigStr += locMatch.group(1)
                if locMatch.group(5) != None:
                    ambigStr += locMatch.group(5)    
                    
                self.regions.append(Region(start,end,complement,ambiguity=ambigStr))
            
class Region:
    """A subregion of a location
    """        
    def __init__(self,start,end,complement,ambiguity=''):
        self.start=int(start)
        self.end=int(end)
        self.complement=complement
        self.ambiguity=ambiguity
        
    def range(self):
        return (self.start,self.end)

        
        
def GenBankIterator(fh):
    """A GenBank Record generator
    """
    try:
        while True:
            yield Record(fh)
    except AttributeError:
        raise StopIteration
iterator=GenBankIterator
        
        
        
        
        
        
