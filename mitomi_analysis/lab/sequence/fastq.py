"""fastq
sequence utilities

kael and dale

$Id: fastq.py,v 1.2 2008/04/08 21:21:29 dale Exp $

"""
__version__ ="$Revision: 1.2 $"

import re
import os

from types import *

from __init__ import *
from utils import flatten

import fasta

#
# Fastq Record Class incorporating quality values.
# Built on top of the fasta.Record class.
#
class Record (fasta.Record):
    """The Fastq Record class.
    
    Members:
    title       Title line ('@' character not included).
    sequence    The sequence.
    quality     The quality values.

    Record acts like a string in these cases:
    len(rec)
    rec[x:y]

    str(rec) returns a valid qfastq formatted string

    """

    def __init__ (self,title='',sequence='',colwidth=60,quality=[]):
        """Create a new Record.  colwidth specifies the number of residues
        to put on each line when generating qfastq format. Quality is an array
        of integers representing the quality of each base.
        """
        fasta.Record.__init__(self,title=title,sequence=sequence,colwidth=colwidth)
        self.quality=quality

    def __str__(self):
        s = []
        s.append('@%s' % self.title)
        i = 0
        while i < len(self):
            s.append(self[i:i+self.colwidth])
            i = i + self.colwidth
        s.append('+%s' % self.title)
        i = 0
        while i < len(self.quality):
            s.append( "".join( intToQual( self.quality[i:i+self.colwidth] ) ) )
            i = i + self.colwidth
        return os.linesep.join(s)
   
    def split(self,sliceBases=100000):
        """Returns an iterator of slices of the record
        """
        n=0
        for start in range(0,len(self.sequence),sliceBases):
            rec = Record()
            rec.title = self.title 
            rec.sequence = self.sequence[start:start+sliceBases]
            rec.quality = self.quality[start:start+sliceBases]
            rec.slice=n
            yield rec
            n+=1

    def fasta( self ):
        """Returns a fasta.Record version of this fastq.Record.
        Basically removes the quality scores but allows you
        to use the fasta.Record specific functions."""

        return fasta.Record( title=self.title,sequence=self.sequence,colwidth=self.colwidth )

def qualToInt( quals ):
    """Given one or more quality characters, returns the corresponding
    list of integer values, as defined by Solexa.
    """
    return map( lambda x: ord(x)-64, quals )

def intToQual( ints ):
    """Given a list of integers, returns the corresponding
    quality string as defined by Solexa."""
    return "".join( map( lambda x: chr(x+64), ints ) )

#
# Identifier
# 
def looksLikeFastq( path ):
    """Returns true if the given file handle appears to be a Fastq file.
    DOES NOT VALIDATE THE FILE. JUST CHECKS THE FIRST RECORD TO SEE IF
    IT LOOKS LIKE A FASTQ RECORD."""
    try:
        for record in FastqIterator( fh ):
            return True
    except:
        return False
    
#
# Iterator
#
def FastqIterator(fh,raw=False):
    """return an iterator of Records found in file handle, fh.
    if records are not needed raw can be set to True, and then 
    you can get (titleStr, seqStr, qualityStr).  With raw output,
    the sequence and quality strings have the newlines still in them.
    """
    def readTotitle(fh, titleChar):
        """returns a tuple ([lines before the next title line], next tile line)
        """
        preLines = []
        while True:
            l = fh.readline()
            if l.startswith(titleChar):
                return (preLines,l)
            elif l == '':
                return preLines,None
            else:
                preLines.append(l)

    if type(fh) in StringTypes:
        fh = file(fh)
    
    preLines,nextTitleLine =readTotitle(fh,'@')

    while nextTitleLine != None:
        seqTitle = nextTitleLine[1:].rstrip()
        preLines,nextTitleLine=readTotitle(fh,'+')
        qualTitle = nextTitleLine[1:].rstrip()
        if len(qualTitle.strip()) > 0 and seqTitle != qualTitle:
            raise FastqParseError, "Error in parsing: @title sequence entry must be immediately followed by corresponding +title quality entry."
        seqLines = preLines
        qualLines = []
        for i in range(len(seqLines)): # Quality characters should be the same length as the sequence
            qualLines.append( fh.readline() )
        
        preLines,nextTitleLine=readTotitle(fh,'@')

        if raw:
            yield (seqTitle, ''.join(seqLines), ''.join(qualLines))
        else:
            rec=Record()
            rec.title=seqTitle
            rec.sequence=''.join(map(lambda x: x.rstrip(),seqLines))
            rec.quality=flatten(map(lambda x: qualToInt(x.rstrip()),qualLines))
            yield rec

iterator=FastqIterator

