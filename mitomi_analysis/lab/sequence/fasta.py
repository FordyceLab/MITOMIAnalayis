"""fasta
sequence utilities

kael and dale

$Id: fasta.py,v 1.22 2008/04/17 22:01:30 kael Exp $

"""
__version__ ="$Revision: 1.22 $"

import subprocess
import re
import string
import os
import tempfile
from types import *

from .__init__ import *

#import kdbom.exceptions 


#
# FASTA regular expressions
#
titlePat = re.compile(r'^>(?P<titleStr>.*)$',re.MULTILINE)
fTitlePat = re.compile(r'^>',re.MULTILINE)
seqPat = re.compile(r'^>(?P<titleStr>.*)$(?P<rawSeqStr>.*)>|',(re.MULTILINE|re.DOTALL))

#
# re helpers
#

def titleMatch(rec,exps):

    for pattern in reTransformer(exps):
        mObj = pattern.search(rec.title)
        if mObj != None:
            return True
    return False



#
# Fasta Record Class
# For the timebeing this is derived from BioPython
# For heaven's sake don't use the BioPython parser!
#
class Record (StringSequence):
    """The Fasta Record class.
    
    Members:
    title       Title line ('>' character not included).
    sequence    The sequence.

    Record acts like a string in these cases:
    len(rec)
    rec[x:y]

    str(rec) returns a valid fasta formatted string

    """

    def __init__ (self,title='',sequence='',colwidth=60):
        """Create a new Record.  colwidth specifies the number of residues
        to put on each line when generating FASTA format.
        """
        #Fasta.Record.__init__(self,colwidth=colwidth)
        self.colwidth=colwidth
        self.title=title
        self.sequence=sequence

    def __str__(self):
        s = []
        s.append('>%s' % self.title)
        i = 0
        while i < len(self):
            s.append(self[i:i+self.colwidth])
            i = i + self.colwidth
        return os.linesep.join(s)
   

    def gi (self):
       
        """attempt to deuce gi from the title.
        """
        ff = self.fastaFields()
        if 'gi' in ff:
            return int(ff['gi'])
        else:
            return None

    def appendField(self,name,value):
        """
        """
        self.title += '|%s|%s' %(name,value)
        
       
    def fastaFields(self):
        """
        """
        rv = {}
        f = self.title.split('|')
        start = len(f)%2
        if f[0] == 'gi':
            start = 0
        for i in range(start,len(f),2):
            try:
                rv[f[i]] = f[i+1]
            except:
                rv[f[i]]=''
        return rv

       
    def m8name(self):
        return self.title.split()[0]

    def m8annotation(self):
        fields = self.title.split(None,1)
        if len(fields) == 2:
            return fields[1]
        else:
            return ''

    def split(self,sliceBases=100000):
        """Returns an iterator of slices of the record
        """
        n=0
        for start in range(0,len(self.sequence),sliceBases):
            rec = Record()
            rec.title = self.title 
            rec.sequence = self.sequence[start:start+sliceBases]
            rec.slice=n
            yield rec
            n+=1
        

    def DRNAsubrecords (self,titleCallback=None):
        """Returns an iterator of records made from the DRNA(i.e. not XXX) stretches
        of this record.

        If titleCallback is provided it should take this, the parent, record and the
        nucleotide offset of the subrecord (sequence starts at 1 (not 0) per biology.

        The default tile callback is giTileTitle.
        """

        if titleCallback == None:
            titleCallback = giTileTitle
        
        for subMatch in self.reSearch(DRNAbasesPat):
            rec = Record(
                title=titleCallback(self,subMatch.start()+1),
                sequence=subMatch.group(0))
            yield rec

    def tile(self, tileLength, startOffset=None,
             minLength=None,allDRNA=False, titleCallback=None,
             returnEndTile=False,colwidth=60):
        """simple tiling of current record, returns a generator.

        tileLength is an integer (all tiles are the same size).

        startOffset can be an integer specifying the tiles'
        start position relative to the prior tile's start, or
        it can be None for end-to-end tiling.

        minLength specifies the smallest of the tail records that
        will be return, if None, tileLength is used.

        titleCallback requirements are the sam as for DRNAsubrecords.

        If allDRNA is true no tiles with invalid or degenerate bases
        will be generated.  The tile ennumeration begins after stretches
        of such bases.

        chopper is a historical alias for tile.
        """

        if titleCallback == None:
            titleCallback = giTileTitle

        if startOffset == None:
            startOffset = tileLength

        if minLength == None:
            minLength = tileLength

        if len(self.sequence) >= minLength:

            startPos=list(range(0,len(self)-(minLength)+1,startOffset))

            if returnEndTile:
                endStartPos = len(self)-tileLength
                if endStartPos not in startPos:
                    startPos.append(endStartPos)


            for start in startPos:
                yield Record(
                    title=titleCallback(self,start+1),
                    sequence=self.sequence[start:start+tileLength],
                    colwidth=colwidth
                    )

    # alias in honor of dave's C program
    chopper = tile
    
    def titleMatch(self,patterns):
        """True if title matches any of the given patterns
        """ 
        return titleMatch(self,patterns)


            
def giTileTitle (rec,n):
    """Make titles for tile based on gi and start of tile
    (sequence starts at 1 (not 0) per biology."""
    # has the record already been mangled?
    mangleMatch=re.match('(?P<gi>[0-9]+)_nt(?P<pos>[0-9]+)',rec.title)
    if mangleMatch != None:
        recOffset = int( mangleMatch.group('pos'))-1
        nStrLength = str(len(mangleMatch.group('pos')))
        base = mangleMatch.group('gi')

    else:
        recOffset=0
        # the string rep of the length of the longest n for this record
        nStrLength = str(len(str(len(rec))))
        
        base = rec.gi()
        if base == None:
            base = rec.m8name()

    fmtStr = "%s_nt%0" + nStrLength +"d"
    return fmtStr % (base,n+recOffset)

#
# Iterator
#
def FastaIterator(fh,raw=False):
    """return an iterator of Records found in file handle, fh.
    if records are not needed raw can be set to True, and then 
    you can get (titleStr, seqStr).  With raw output, the sequence 
    string has the newlines still in it.
    """
    def readTotitle(fh):
        """returns a tuple ([lines before the next title line], next tile line)
        """
        preLines = []
        while True:
            l = fh.readline()
            if l.startswith('>'):
                return (preLines,l)
            elif l == '':
                return preLines,None
            else:
                preLines.append(l)

    if type(fh) in StringTypes:
        fh = file(fh)
    
    preLines,nextTitleLine =readTotitle(fh)

    while nextTitleLine != None:
        title = nextTitleLine[1:].rstrip()
        preLines,nextTitleLine=readTotitle(fh)
        if raw:
            yield (title,''.join(preLines))
        else:
            rec=Record()
            rec.title=title
            rec.sequence=''.join([x.rstrip() for x in preLines])
            yield rec

iterator=FastaIterator
#
# File Size Calculation Functions
#

def fastaCount(things):
    """Count the number of titles in a file-like things.

    file like things can be one of more (in a list of tuple)
    file objects or paths .
    """
    if type(things) in (ListType,TupleType):
        return list(map(fastaCount,things))
    return len(fTitlePat.findall(toString(things)))


def fastaTitles(things):
    """Return the titles in file like things.

    file like things can be one of more (in a list of tuple)
    file objects or paths .
    """
    if type(things) in (ListType,TupleType):
        return list(map(fastaTitles,things))
    return titlePat.findall(toString(things))


def countRecsAndBases(things):
    """return the total # of fasta records and the number of
    valid DNA and RNA bases in fasta file-like things.

    file like things can be one of more (in a list of tuple)
    file objects or paths .
    """
    if type(things) in (ListType,TupleType):
        manyRslts = list(map(countRecsAndBases,things))
        tRecs = sum([x[0] for x in manyRslts])
        tBases = sum([x[1] for x in manyRslts])
        return (tRecs,tBases)
        
    recCount  = 0 
    baseCount = 0
    for t,s in FastaIterator(things,raw=True):
        recCount += 1
        baseCount += DRNABaseCount(s)
    
    return (recCount,baseCount)

def baseComposition(things,caseSensitive=False):
    """return the total of occurrences of each 'base' over every sequence
    in fasta file-like things, a dictionary is returned for each file.
    The dict. keys are the bases/letters (don't have to be valid D/RNA)
    values are the # of times seen.

    file like things can be one of more (in a list of tuple)
    file objects or paths .
    """
    if type(things) in (ListType,TupleType):
        return list(map(fastaCount,things))

    else:
        counts={}
        for t,s in FastaIterator(things,raw=True):
            for letter in s:
                if letter not in counts:
                    counts[letter]=0
                counts[letter]+=1

        for k in list(counts.keys()):
            if k not in string.letters:
                del counts[k]
            else:
                if not caseSensitive:
                    if k!=k.upper():
                        K=k.upper()
                        if K not in counts:
                            counts[K] = 0
                        counts[K] = counts[k]
                        del counts[k]
                        

        return counts
        
   
    
#
# Fasta File Filtering and Partitioning
#
def fastaPartition(inFile,trueFile,notTrueFile,callback):
    """partition a fasta file based on callback(Record)'s return
    value.

    inFile must be a file object.  trueFile and notTrueFile may
    be file objects or None if coresponding records are to be
    discarded.

    returns (trueCount,notTrueCount)
    """

    tCount = 0
    ntCount = 0

    for rec in FastaIterator(inFile):
        if callback(rec):
            tCount +=1
            if trueFile !=None:
                trueFile.write(str(rec))
                trueFile.write('\n')
        else:
            ntCount+=1
            if notTrueFile != None:
                notTrueFile.write(str(rec))
                notTrueFile.write('\n')

    return tCount,ntCount


def screenHSPs(fastaFile,outFileName,MBfile,shortyLength=0,debug=False,excludeTitles=[]):
    """replace sequences that are query HSPs in megablast -D3 (or blast -m8)
    output file.

    Records are not output if: 1) they have fewer ACGTU bases than shortyLength or
    2) their titles are in excludeTitles.

    output file will be opened for writing and then closed, on return.
    
    """

    from . import blastNoSQL

    filesToClose=[]

    if type(fastaFile) in StringTypes:
        fastaFile = file(fastaFile)
        filesToClose.append(fastaFile)
    if type(MBfile) in StringTypes:
        MBfile = file(MBfile)
        filesToClose.append(MBfile)
    outFile = file(outFileName,'w')
    filesToClose.append(outFile)
    
    hsps={}
    # read in HSPs
    i=0
    for hsp in blastNoSQL.m8generator(MBfile):
        if i % 10000 ==0 and debug: 
            print(i)
        i+=1
        if hsp['query'] not in hsps:
            hsps[hsp['query']]={hsp['q_start']: hsp['q_end']}

        else:
            if hsp['q_start'] in hsps[hsp['query']]:
                if hsp['q_end'] > hsps[hsp['query']][hsp['q_start']]:
                    hsps[hsp['query']][hsp['q_start']]= hsp['q_end']
            else:
                starts = list(hsps[hsp['query']].keys())
                starts.sort()
                for start in starts:
                    if hsp['q_start'] < start and  hsp['q_end'] > start:
                        end = hsps[hsp['query']][start]
                        del hsps[hsp['query']][start]
                        hsps[hsp['query']][hsp['q_start']]=end
                        break
                    elif hsp['q_start'] > start and  hsp['q_end'] <= hsps[hsp['query']][start]:
                        # do nothing
                        break
                    elif hsp['q_start'] > start and  hsp['q_end'] > hsps[hsp['query']][start]:
                        hsps[hsp['query']][ hsp['q_start']] = hsp['q_end']
                        break
    #print hsps.keys()

    for rec in FastaIterator(fastaFile):
        if rec.title in excludeTitles:
            continue
        if  rec.title.split()[0] in hsps:
            newSeq = list(rec.sequence)
            for start,end in list(hsps[rec.title.split()[0]].items()):
                #print start, end
                newSeq[start-1:end] = 'X'*(end-start+1)
            rec.sequence = ''.join(newSeq)
        if shortyLength == 0 or max(rec.matchLengths('[AGCTU]+')) >= shortyLength:
            print(str(rec), file=outFile)    
    for f in filesToClose:
        f.close()    
    

            
screenMegaBLASThits = screenHSPs

def titleReSplit(inFile,matchFile,nomatchFile,patterns):
    """Partition a fasta file based on matching title to pattern(s).
    See also fastaPartition.
    """
    def cb (rec):
        return rec.titleMatch(patterns)
    
    return fastaPartition(inFile,matchFile,nomatchFile,cb)

def splitShorties(inFile,outFile,minDRNAStretch=50):
    """Partition a fasta file based on the length of the
    longest stretch of valid bases in each record.  Records
    with fewer than  minDRNAStretch bases in their longest
    tract of valid bases are dropped. Others are place in
    outFile.
    
    See also fastaPartition.
    """    
    def cb (rec):
        if max(rec.matchLengths('[AGCTU]+')) < minDRNAStretch:
            return False
        else:
            return True
        
    return fastaPartition(inFile,outFile,None,cb)


def dropLowLZW(inFile,outFile,minLZW):
    """Drop records with LZW sizes(or raitos if minLZW is a
    float) below minLZW.
    """
    if type(minLZW) in (int,int):
        cb = lambda r: r.LZWsize() >= minLZW
    elif type(minLZW) == float:
        cb = lambda r: r.LZWratio() >= minLZW

    return fastaPartition(inFile,outFile,None,cb)

def dropDuplicates(inFile,outFile):
    """Count duplicate sequences in fasta file. Output
    distinct sequences.  Record titles are modified with |# . 
    returns number of unique sequences.
    """
    seqs={}
    for rec in FastaIterator(infile):
        if rec not in seqs:
            seqs[rec]=1
        else:
            seqs[rec]+=1

    for rec,count in list(seqs.items()):
        rec.title+='|%s'%count
        outfile.write(str(rec))
        outfile.write('\n')

    return len(seqs)            

def dropShorties(fileNames,minDRNAStretch=50):
    """Drop Records with fewer than  minDRNAStretch bases in
    their longest tract of valid bases are dropped, per splitShorties.
    But the operation is done 'inplace'.  File Names is one or more
    paths of file to operate on.  Those file should be closed when
    this function is called.
    """

    if type(fileNames) in StringTypes:
        fileNames = [fileNames]
    for fileName in fileNames:
        tmpFile,tmpPath = mystemp(
            dir=os.path.split(fileName)[0])
        inFile = file(fileName)
        splitShorties(inFile,tmpFile,
                      minDRNAStretch=minDRNAStretch)
        os.unlink(fileName)
        os.link(tmpPath,fileName)
        os.unlink(tmpPath)

            
def getLongestRecord(inFile):
    """Return the longest record (total valid D/RNA
    bases) from a file object.   
    """
    baseCount = 0
    longestRec = Record()
    for rec in FastaIterator(inFile):
        #print rec.DRNABaseCount()
        if len(rec) < baseCount:
            continue
        else:
            recCount = rec.DRNABaseCount()
            if recCount > baseCount:
                baseCount=recCount
                longestRec = rec
    return longestRec

def extractLongestRecord(inFileNames,leaveInFile=False):
    """Given one or more fasta file paths, find the longest
    record in the set.  remove it from the file it is found in
    and return the record.
    """

    if type(inFileNames) not in (ListType,):
        if type(inFileNames) in StringTypes:
            inFileNames = [inFileNames]
        else:
            inFiles = list(inFileNames)
         
    baseCount = 0
    longestRec = Record()
    recFileName = None
     
    for inFileName in inFileNames:
        inFile = file(inFileName)
        for rec in FastaIterator(inFile):
            if len(rec) < baseCount:
                continue
            else:
                recCount = rec.DRNABaseCount()
                if recCount > baseCount:
                    baseCount=recCount
                    longestRec = rec
                    recFileName = inFileName

    if recFileName != None and not leaveInFile:
        tmpFile,tmpPath = mystemp(
            dir=os.path.split(recFileName)[0])
        recFile = file(recFileName)
        for rec in FastaIterator(file(recFileName)):
            if rec.title != longestRec.title:
                tmpFile.write(str(rec))
                tmpFile.write('\n')
        recFile.close()
        os.unlink(recFileName)
        os.link(tmpPath,recFileName)
        os.unlink(tmpPath)

    return longestRec
       

def splitFasta(filename,splitCt=None,splitSize=None,
               tmpDir=None,dropTitles=[],nameGenerator=None):
    """Split fasta file into splitCt temporary files.  Return
    a list of paths to the files.

    If splitSize is specifed and splitCt is not, the file is split in
    to files with number of records equal to or less than splitSize (any
    remaining records are put in seperate file).

    A generator object can be specified
    which allows the user to specity custom paths for the slices.
    The generator must provide a file open for writing, and the path
    to the file.

    This could be as simple as:

    def mySpecialNames():
        choices = ['my','little','pony']
        for n in choices:
            yield (file(n,'w'),n)

    Unless tmpDir is set, new files are created in the current working
    directory.
            
    """


    if splitCt == None and splitSize == None:
        raise ValueError("Either splitCt or splitSize mut be an integer") 
    

    rv=[]

    if tmpDir == None:
        tmpDir = os.getcwd()

    if nameGenerator == None:
        def nameFcn():
            while True:
                yield mystemp(suffix='.fasta',dir=tmpDir)
        nameGenerator = nameFcn()

    ff = file(filename)

    if splitCt != None:
        #make files
        LengthsAndFiles = []
        for n in range(splitCt):
            LengthsAndFiles.append([0,next(nameGenerator)])



        for rec in FastaIterator(ff):
            if rec.title in dropTitles:
                continue
            LengthsAndFiles.sort()
            LengthsAndFiles[0][1][0].write(str(rec))
            LengthsAndFiles[0][1][0].write('\n\n')
            LengthsAndFiles[0][0] += len(rec.sequence)


        for length,tft in LengthsAndFiles:
            fObject, fPath = tft
            if length == 0:
                os.unlink(fPath)
            else:
                fObject.close()
            rv.append(fPath)
            
    elif splitSize != None:
        i=0
        oFile=None
        for rec in FastaIterator(ff):
            if oFile == None:
                oFile = nameGenerator.next()[0]
            oFile.write(str(rec))
            oFile.write('\n\n')
            i+=1

            if i >= splitSize:
                i=0
                oFile.close()
                oFile=None
            
    else:
        raise ValueError("Either splitCt or splitSize mut be an integer") 
    
    return rv


def tmpFile( fastaRecords, tmpDir=None ):
    """Given a fasta.Record or list of fasta.Records, creates
    a fasta file in the specified tmp directory containing said
    sequence(s), and returns the filename."""

    if not isinstance( fastaRecords, ( tuple, list ) ):
        fastaRecords = list(fastaRecords)
        
    if tmpDir == None:
        tmpDir = os.getcwd()
        
    (of, name) = mystemp(suffix='.fasta', dir=tmpDir)
    for record in fastaRecords:
        of.write( str(record) + "\n" )
    of.close()
    return name


def removeRecordsFromFile(fileName,recTitles,tmpDir=None):
    """Given a path to a fasta file and a title (or titles) of fasta record(s),
    all matching fasta records for each title will be removed from the file.
    Leading '>' should should be removed (automatically stripping it causes
    ambiguious cases).  Trailing whitespace is not significant.
    Return value is the number (int) of records removed from the file. 
    """
    import shutil
    if not os.access(fileName,os.W_OK):
        raise IOError("no write access for fasta file: %s" % fileName)

    inFile = file(fileName)

    (of, ofName) = mystemp(suffix='.fasta', dir=tmpDir)

    if type(recTitles) in StringTypes:
        recTitles = [recTitles]

    # remove training whitspace
    recTitles = [t.rstrip() for t in recTitles]


    

    BADREC = False
    rmCount=0
    for l in inFile:
        if l.startswith('>'):
            if l[1:].rstrip() in recTitles:
                BADREC=True
                rmCount += 1
            else:
                BADREC=False

        if not BADREC:
            of.write(l)
        
    of.flush()
    inFile.close()
    os.unlink(fileName)
    shutil.copyfile(ofName,fileName)
    os.unlink(ofName)
    return rmCount
    

    
class IterativeScreen:
    """framework for iteratively screening through a fasta file.
    """

    def __init__ (self,inPath=None,MBparams="-W24 -D3 -E10 -G24 -FF"):
        """
        """
        self.MBparams = MBparams
        self.longestRemaining=Record()
        if inPath != None:
            self.setup(inPath)


    def setup(self,inPath):
        """inFile is a Path.
        returns self.longestRemaining.DRNABaseCount() on success.
        """
        self.inPath = inPath
        localFile,self.localPath=mystemp(suffix='.fasta')
        s,o = subprocess.getstatusoutput("cp %s %s" %(inPath,self.localPath))
        if s==0:
            self.longestRemaining=getLongestRecord(file(self.localPath))
            return self.longestRemaining.DRNABaseCount()
        else:
            raise RuntimeError("setup copy failed -  cp said: %s" %o)

        #localFile.write(file(self.inPath).read())
        #localFile.close()


    def screen(self,screenFastaPath):
        """screen with MegaBLAST
        The longest record (largest DRNABaseCount) it  in stored as
        self.longestRemaining.
        Returns longestRemaining.DRNABaseCount() on success
        """

        dbTitles = fastaTitles(screenFastaPath)

        
        mbCmd = ('megablast %s -d %s -f -R -i %s > %s'
                 % (self.MBparams,screenFastaPath,self.localPath,self.localPath+'.MBout'))
        s,o = subprocess.getstatusoutput(mbCmd)

        if s != 0:
            raise RuntimeError("---MEGABLAST FAILED---\nMEGABLAST command:%s\nEnd of output: %s\nExit Status: %s"
                                 % (mbCmd,o[-250:],s))
        
        screenOutFile,screenOutPath = mystemp()
        screenHSPs(self.localPath,screenOutPath,self.localPath+'.MBout',shortyLength=35,
                   excludeTitles=dbTitles)
        s,o = subprocess.getstatusoutput("mv %s %s" %(screenOutPath,self.localPath))
        if s==0:
            self.longestRemaining=getLongestRecord(file(self.localPath))
            return self.longestRemaining.DRNABaseCount()
        else:
            raise RuntimeError("file replacment after screening failed-  mv said: %s" %o)
     
    
    def cleanUp(self):
        os.unlink(self.localPath)
        
