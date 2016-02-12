"""
sequence utilities
kael and dale

$Id: __init__.py,v 1.15 2008/04/17 19:59:22 kael Exp $

"""
__version__ ="$Revision: 1.15 $"

import math
import re
import random
import string
import os
import tempfile
from types import *


class SequenceError (Exception):
    pass

class FastqParseError (Exception):
    pass

#
# Sequencetranslations
#
DNAcomplement = string.maketrans('aAcCgGtT','tTgGcCaA')
RNAcomplement = string.maketrans('aAcCgGuU','uUgGcCaA')
DRNAcomplement = string.maketrans('aAcCgGuUtT','uUgGcCaAaA')
NAcomplement=DRNAcomplement

#
# Sequence regular expressions
#
DNAbasesPat = re.compile(r'[ACGT]+',re.IGNORECASE)
RNAbasesPat = re.compile(r'[ACGU]+',re.IGNORECASE)
DRNAbasesPat = re.compile(r'[ACGUT]+',re.IGNORECASE)


NAbases = ('A','T','U','G','C')
DRNAbases = NAbases
DNAbases = ('A','T','G','C')
RNAbases = ('A','U','G','C')
wc_pairs = (('A','T'),
            ('T','A'),
            ('A','U'),
            ('U','A'),
            ('G','C'),
            ('C','G'))
purines = ('A','G')
pyrimidines = ('T','C','U')

notNA =  re.compile('[^%s]' % string.join(NAbases,''))
notDRNA = notNA
notDNA = re.compile('[^%s]' % string.join(DNAbases,''))
notRNA = re.compile('[^%s]' % string.join(RNAbases,''))


def isAllDNA(seq):
    """True if all of sequence is valid unambiquious DNA.
    """
    if notDNA.search(seq) == None:
        return True
    else:
        return False

def isAllRNA(seq):
    """True if all of sequence is valid unambiquious RNA.
    """
    if notRNA.search(seq) == None:
        return True
    else:
        return False

def isAllDRNA(seq):
    """True if all of sequence is valid unambiquious RNA or DNA.
    """
    if notDRNA.search(seq) == None:
        return True
    else:
        return False

isAllNA = isAllDRNA
    

def reverseComplement(seq):
    """return the reverse complement of a sequence"""
    if not isAllDRNA(seq):
        raise SequenceError("Non-DRNA character in seq: %s" % (seq))

    # complement
    compl = complement(seq)
    # reverse
    rv = list(compl)
    rv.reverse()
    return ''.join(rv)

def reverse(seq):
    """return a copy of the reversed seq
    """
    rv = list(seq)
    rv.reverse()
    return ''.join(rv)

def complement(seq,transl=None):
    """Return complement of seq.
    """
    if isAllDNA(seq):
        transl=DNAcomplement
    elif isAllRNA(seq):
        transl=RNAcomplement

    if transl == None:
        raise ValueError("sequence is not all DNA or RNA bases.") 
    
    compl = seq.translate(transl)
    return compl

#
# re sequence helper
#
RePatternType = type(re.compile(''))
def _reTransformer (patterns):
    rv = []
    if type(patterns) not in (ListType,TupleType):
        patterns = (patterns,)
    
    for pattern in patterns:
        if type(pattern) == RePatternType:
            rv.append(pattern)
        elif type(pattern) in StringTypes:
            rv.append(re.compile(pattern))
    return rv
reTransformer = _reTransformer

#
# File Size Calculation Functions
#
def toString(thing):
    """takes a file object or a file name/path.
    returns a string with the contents of the file.
    files are not rewound or seek'ed to their previous
    positions.
    """
    thingType = type(thing)

    if thingType == FileType:
        return thing.read()
    elif thingType in StringTypes:
        return file(thing).read()
    

    
#
# Eaiser temp files
#
def mystemp(**args):
    """Like tempfile.mkstemp but returns:
    (fileobject, path) not (filedescriptor,path)

    tempfile.mkstemp documentation:

    mkstemp(suffix='', prefix='tmp', dir=None, text=False)
    mkstemp([suffix, [prefix, [dir, [text]]]])

    User-callable function to create and return a unique temporary
    file.  The return value is a pair (fd, name) where fd is the
    file descriptor returned by os.open, and name is the filename.
    
    If 'suffix' is specified, the file name will end with that suffix,
    otherwise there will be no suffix.
    
    If 'prefix' is specified, the file name will begin with that prefix,
    otherwise a default prefix is used.
    
    If 'dir' is specified, the file will be created in that directory,
    otherwise a default directory is used.
    
    If 'text' is specified and true, the file is opened in text
    mode.  Else (the default) the file is opened in binary mode.  On
    some operating systems, this makes no difference.
    
    The file is readable and writable only by the creating user ID.
    If the operating system uses permission bits to indicate whether a
    file is executable, the file is executable by no one. The file
    descriptor is not inherited by children of this process.
    
    Caller is responsible for deleting the file when done with it.

"""
    
    tmp = tempfile.mkstemp(**args)
    return (os.fdopen(tmp[0],'w'),tmp[1])


#
# Sequence Generation
#
def randomBase (excludeList = []):
    """Return a random DNA/RNA base, but not if it is in the excludeList.
    """
    choices = []
    
    for b in (DRNAbases):
        if b not in excludeList:
            choices.append(b)
    return random.choice(choices)


def randomBaseGenerator(pDict={'A':1, 'T':1, 'G':1, 'C':1}):
    """return a generator for random bases not in the exclude list.
    Can specify relative ferquencies for each base (this overrides excludeList),
    of the form: {'A':int,'T':int,'G',int,'C',int}.
    """
    choices =[]
    freqs=[]
    sumf=0
    
    for c,f in list(pDict.items()):
        choices.append(c)
        if len(freqs) == 0:
            freqs.append(f)
        else:
            freqs.append(f+freqs[-1])
        sumf+=f
        

    while True:
        n = random.randint(1,sumf)
        for i in range(len(freqs)):
            if n <= freqs[i]:
                yield choices[i]
                break
    
    

def randomSequence (length, excludeList=['U'],excludeSites=[],
                    maxAT=None,minAT=None,ATwindow=None,maxHomo=None):
    """Return a string of random DNA/RNA bases, but no bases from the
    excludeList.  Multibase sites can be excluded by specifying them
    in excludeSites.
    By default 'U' is excluded.
    """
    siteFound = True
    
    while siteFound:
        seq = []
        siteFound = False
        
        while length > len(seq):
            seq.append(randomBase(excludeList = excludeList))
        sStr = string.join(seq,'')
        
        # check for excluded sites
        for baddie in excludeSites:
            if sStr.find(baddie) != -1:
                siteFound = True
                break
            
        # check for TA
        if  siteFound == False and (maxAT != None or minAT != None):
            if ATwindow==None:
                ATwindow = length
            for start in range(length-ATwindow+1):
                window = sStr[start:ATwindow+start]
                ATcount =  window.count("A")+window.count("T")
                if maxAT != None:
                    window = sStr[start:ATwindow+start]
                    ATcount =  window.count("A")+window.count("T")
                    while ATcount > maxAT:
                        ats = []

                        idx=0
                        while idx != -1:
                            idx = window.find('A',idx+1)
                            if idx != -1:
                                ats.append(idx)

                        idx=0
                        while idx != -1:
                            idx = window.find('T',idx+1)
                            if idx != -1:
                                ats.append(idx)

                        target = random.choice(ats)
                        target += start
                        replacement = random.choice(('C','G'))
                        sStr=sStr[:start+target]+replacement+sStr[start+target+1:]
                        window = sStr[start:ATwindow+start]
                        ATcount =  window.count("A")+window.count("T")




                if minAT != None:
                    window = sStr[start:ATwindow+start]
                    ATcount =  window.count("A")+window.count("T")
                    while ATcount < minAT:
                        gcs = []

                        idx=0
                        while idx != -1:
                            idx = window.find('C',idx+1)
                            if idx != -1:
                                gcs.append(idx)

                        idx=0
                        while idx != -1:
                            idx = window.find('G',idx+1)
                            if idx != -1:
                                gcs.append(idx)
                        
                        target = random.choice(gcs)
                        target += start
                        replacement = random.choice(('A','T'))
                        sStr=sStr[:start+target]+replacement+sStr[start+target+1:]
                        window = sStr[start:ATwindow+start]
                        ATcount =  window.count("A")+window.count("T")


                
        if siteFound == False and (maxHomo != None and lenHomo(sStr)>maxHomo):
            siteFound=True

            
                
    return sStr



def bashSequence(seqString,mutablePositions,
                 excludeList=[],
                 allowSameBase=False,
                 allowSameRings=True,
                 allowNonBase=True):
    """Retuns a mutated DNA sequence (as a string).
    mutable postions are specified as a single index or a
    list or tupple of same.
    """

    if type(mutablePositions) == IntType or \
       type(mutablePositions) == LongType:
        mutablePositions = [mutablePositions]

    
    seq = []
    for c in seqString:
        if allowNonBase == False:
            if c not in bases:
                raise SequenceError("%s at position %s is not a DNA base, try one of %s" % \
                      (c,seqString.find(c),bases))
        seq.append(c)
        

    for pos in mutablePositions:
        
        if allowSameRings == False:
            if seq[pos] in purines:
                seq[pos] = randomBase(excludeList=purines+excludeList)
            elif seq[pos] in pyrimidines:
                seq[pos] = randomBase(excludeList=purines+excludeList)
            elif seq[pos] not in bases :
                raise SequenceError("%s at position %s is not a DNA base, try one of %s" % \
                      (seq[pos],pos,bases))
            else:
                print(seq[pos])
                raise Exception("this should never happen, evacuate the building!\n************NOW**********\n")
        elif allowSameBase == True:
            seq[pos] = randomBase(excludeList=excludeList)

        else:
            seq[pos] = randomBase(excludeList=[seq[pos]]+excludeList)

    return string.join(seq,'')

def longestStretch(seqString, bases=()):
    """Returns the longest stretch of the sequence that contains
    only the bases in the string,tupple or list bases.  Returns the
    first sequence if more that one strech are tied for longest.
    """
    
    longest = ''
    
    if len(bases) == 0:
        return longest
    
    reBases = re.compile(r'[%s]+' % (string.join(bases,'')))
    matches = reBases.findall(seqString)
    for m in matches:
        if len(m) > len(longest):
            longest = m

    return longest
        

#
# Useful Sequences
#
primerB   = 'GTTTCCCAGTCACGATA'
primerBrc = reverseComplement(primerB)

SPIKE70 = 'ACCTCGCTAACCTCTGTATTGCTTGCCGGACGCGAGACAAACCTGAACATTGAGAGTCACCCTCGTTGTT'
PROBE70 = reverseComplement(SPIKE70)

M13Forward = 'GTAAAACGACGGCCAG'
M13Reverse = 'CAGGAAACAGCTATGAC'

T7Promoter = 'TAATACGACTCACTATAGGG'

#
# other useful functions
#

def Tm(s,dnac=50,saltc=50,rna=False,debug=False):
    """Returns DNA/DNA tm using nearest neighbor thermodynamics. dnac is
    DNA concentration [nM] and saltc is salt concentration [mM].
    rna=0 is for DNA/DNA (default), for RNA, rna should be True.
    Sebastian Bassi <sbassi@genesdigitales.com>"""
    
    #Credits: 
    #Main author: Sebastian Bassi <sbassi@genesdigitales.com>
    #Overcount function: Greg Singer <singerg@tcd.ie>
    #Based on the work of Nicolas Le Novere <lenov@ebi.ac.uk> Bioinformatics. 17:1226-1227(2001)

    #This function returns better results than EMBOSS DAN because it uses updated
    #thermodinamics values and take into account inicialization parameters from SantaLucia
    #works (1998).
    
    #Things to do:
    #+Add a function to detect complementary sequences. Change K according to result.
    #+Add support for heteroduplex (see Sugimoto et al. 1995).
    #+Correction for Mg2+. Now supports only monovalent ions.
    #+Put thermodinamics table in a external file for users to change at will
    #+Add support for danglings ends (see Le Novele. 2001) and mismatches.
    
    dh=0 #DeltaH. Enthalpy
    ds=0 #deltaS Entropy

    def tercorr(stri):
        deltah=0
        deltas=0
        if rna==0:
            #DNA/DNA
            #Allawi and SantaLucia (1997). Biochemistry 36 : 10581-10594
            if stri[0]=="G" or stri[0]=="C":
                deltah=deltah-0.1
                deltas=deltas+2.8
            elif stri[0]=="A" or stri[0]=="T":
                deltah=deltah-2.3
                deltas=deltas-4.1
            if stri[-1]=="G" or stri[-1]=="C":
                deltah=deltah-0.1
                deltas=deltas+2.8
            elif stri[-1]=="A" or stri[-1]=="T":
                deltah=deltah-2.3
                deltas=deltas-4.1
            dhL=dh+deltah
            dsL=ds+deltas
            return dsL,dhL
        elif rna==1:
            #RNA
            if stri[0]=="G" or stri[0]=="C":
                deltah=deltah-3.61
                deltas=deltas-1.5
            elif stri[0]=="A" or stri[0]=="T" or stri[0]=="U":
                deltah=deltah-3.72
                deltas=deltas+10.5
            if stri[-1]=="G" or stri[-1]=="C":
                deltah=deltah-3.61
                deltas=deltas-1.5
            elif stri[-1]=="A" or stri[-1]=="T" or stri[0]=="U":
                deltah=deltah-3.72
                deltas=deltas+10.5
            dhL=dh+deltah
            dsL=ds+deltas
            if debug:
                print("delta h=",dhL)
            return dsL,dhL

    def overcount(st,p):
        """Returns how many p are on st, works even for overlapping"""
        ocu=0
        x=0
        while 1:
            try:
                i=st.index(p,x)
            except ValueError:
                break
            ocu=ocu+1
            x=i+1
        return ocu

    sup=string.upper(s)
    R=1.987 # universal gas constant in Cal/degrees C*Mol
    vsTC,vh=tercorr(sup)
    vs=vsTC
    
    k=(dnac/4.0)*1e-8
    #With complementary check on, the 4.0 should be changed to a variable.
    
    if rna==0:
        #DNA/DNA
        #Allawi and SantaLucia (1997). Biochemistry 36 : 10581-10594
        vh=vh+(overcount(sup,"AA"))*7.9+(overcount(sup,"TT"))*7.9+(overcount(sup,"AT"))*7.2+(overcount(sup,"TA"))*7.2+(overcount(sup,"CA"))*8.5+(overcount(sup,"TG"))*8.5+(overcount(sup,"GT"))*8.4+(overcount(sup,"AC"))*8.4
        vh=vh+(overcount(sup,"CT"))*7.8+(overcount(sup,"AG"))*7.8+(overcount(sup,"GA"))*8.2+(overcount(sup,"TC"))*8.2
        vh=vh+(overcount(sup,"CG"))*10.6+(overcount(sup,"GC"))*10.6+(overcount(sup,"GG"))*8+(overcount(sup,"CC"))*8
        vs=vs+(overcount(sup,"AA"))*22.2+(overcount(sup,"TT"))*22.2+(overcount(sup,"AT"))*20.4+(overcount(sup,"TA"))*21.3
        vs=vs+(overcount(sup,"CA"))*22.7+(overcount(sup,"TG"))*22.7+(overcount(sup,"GT"))*22.4+(overcount(sup,"AC"))*22.4
        vs=vs+(overcount(sup,"CT"))*21.0+(overcount(sup,"AG"))*21.0+(overcount(sup,"GA"))*22.2+(overcount(sup,"TC"))*22.2
        vs=vs+(overcount(sup,"CG"))*27.2+(overcount(sup,"GC"))*27.2+(overcount(sup,"GG"))*19.9+(overcount(sup,"CC"))*19.9
        ds=vs
        dh=vh
        
    else:
        #RNA/RNA hybridisation of Xia et al (1998)
        #Biochemistry 37: 14719-14735         
        vh=vh+(overcount(sup,"AA"))*6.82+(overcount(sup,"TT"))*6.6+(overcount(sup,"AT"))*9.38+(overcount(sup,"TA"))*7.69+(overcount(sup,"CA"))*10.44+(overcount(sup,"TG"))*10.5+(overcount(sup,"GT"))*11.4+(overcount(sup,"AC"))*10.2
        vh=vh+(overcount(sup,"CT"))*10.48+(overcount(sup,"AG"))*7.6+(overcount(sup,"GA"))*12.44+(overcount(sup,"TC"))*13.3
        vh=vh+(overcount(sup,"CG"))*10.64+(overcount(sup,"GC"))*14.88+(overcount(sup,"GG"))*13.39+(overcount(sup,"CC"))*12.2
        vs=vs+(overcount(sup,"AA"))*19.0+(overcount(sup,"TT"))*18.4+(overcount(sup,"AT"))*26.7+(overcount(sup,"TA"))*20.5
        vs=vs+(overcount(sup,"CA"))*26.9+(overcount(sup,"TG"))*27.8+(overcount(sup,"GT"))*29.5+(overcount(sup,"AC"))*26.2
        vs=vs+(overcount(sup,"CT"))*27.1+(overcount(sup,"AG"))*19.2+(overcount(sup,"GA"))*32.5+(overcount(sup,"TC"))*35.5
        vs=vs+(overcount(sup,"CG"))*26.7+(overcount(sup,"GC"))*36.9+(overcount(sup,"GG"))*32.7+(overcount(sup,"CC"))*29.7
        ds=vs
        dh=vh

    ds=ds-0.368*(len(s)-1)*math.log(saltc/1e3)
    tm=((1000* (-dh))/(-ds+(R * (math.log(k)))))-273.15
    if debug:
        print("ds="+str(ds))
        print("dh="+str(dh))
        print("Tm="+str(tm))
        
    return tm


class StringSequence:
    """Base class for sequences objects that represent sequence information as
    strings in a .sequence property.
    Provides stringy stuff like slicing.
    """

    def __init__(self,sequence=''):
        self.sequence=sequence
        
    def __len__(self):
        """Return the length of sequence.
        """
        return len(self.sequence)

    def __getitem__(self,item):
        return self.sequence[item]
    
    def wrappedSequence(self):
        """returns the wordwrapped sequence.
        """
        s=[]
        i = 0
        while i < len(self):
            s.append(self[i:i+self.colwidth])
            i = i + self.colwidth
        return os.linesep.join(s)


    def scramble(self):
        """randomly permute sequence.
        """
        self.sequence = ''.join(random.sample(self.sequence,len(self.sequence))) 
    

    def screenedLen(self,screenChrs=None):
        """Return the length of the sequence, less any
        of the characters in screenChrs.
        """
        if screenChrs == None:
            return len(self)

        count = 0
        for c in screenChrs:
            count += self.sequence.count(c)
        return len(self)-count

    def matchLengths(self,patterns):
        """return a list of lengths of the sequences matches to
        each pattern.  If patterns is a sequence of patterns a
        list of lists of matching lengths is returned otherwise
        an unnested single list of match lengths is returned.
        """
        return sequenceMatchLengths(self,patterns)

    def reSearch(self,patterns):
        """Return a list of Match Objects to the patterns given.
        If patterns is a sequence of patterns a
        list of lists of Match Objects is returned, otherwise
        an unnested single list of Match Objects is returned.
        """
        patterns = reTransformer(patterns)
        rv = []
        for pattern in patterns:
            matches = list(pattern.finditer(self.sequence))
            if len(matches) == 0:
                rv.append([])
            else:
                rv.append(matches)

        if len(patterns) == 1:
            return rv[0]
        else:
            return rv


    def DNABaseLengths(self):
        """return a list of the lengths of DNA base streatches in
        the sequence. 
        """
        return self.matchLengths(DNAbasesPat)
    
    def DNABaseCount(self):
        """return the number of DNA bases in
        the sequence. 
        """
        return sum(self.matchLengths(DNAbasesPat))

    def RNABaseLengths(self):
        
        """return a list of the lengths of RNA base stretches in
        the sequence. 
        """
        
        return self.matchLengths(RNAbasesPat)

    def RNABaseCount(self):
        """return the number of RNA bases in
        the sequence. 
        """
        return sum(self.matchLengths(RNAbasesPat))

    def DRNABaseLengths(self):
        """return a list of the lengths of RNA or DNA base streatches in
        the sequence. 
        """
        #print DRNAbases
        return self.matchLengths(DRNAbasesPat)

    def DRNABaseCount(self):
        """return the number of RNA and DNA bases in
        the sequence. 
        """
        #print self.matchLengths(DRNAbasesPat)
        return sum(self.matchLengths(DRNAbasesPat))

    def blastSequence(self):
        from . import blast
        import kdbom.exceptions
        try:
            return blast.Sequence(Name=self.m8name())
        except kdbom.exceptions.KdbomLookupError:
            return None

    def LZWsize(self):
        """return the size of the LZW compressed sequence
        """
        from . import aos
        return aos.LZWsize(self.sequence)

    def LZWratio(self):
        """Return the LZW compression ratio.
        """
        from . import aos
        return float(self.LZWsize())/float(self.sequence)
    
    def __getitem__(self,y):
        """
        """
        return self.sequence[y]

#
# Functions that operate on SequenceRecords (or simply strings)
#

def sequenceMatchLengths(rec,patterns):
    
    if hasattr(rec, "sequence"):
        sequence = rec.sequence
    else:
        sequence=rec
    
    #print patterns
    patterns = reTransformer(patterns)
    rv = []
    for pattern in patterns:
        #print patterns
        mLengths = list(map(len,pattern.findall(sequence)))
        if len(mLengths) == 0:
            rv.append(0)
        else:
            rv.extend(mLengths)

    if len(patterns) == 1 and False:
        return rv[0]
    else:
        return rv
    
def DNABaseLengths(s):
    """return a list of the lengths of DNA base streatches in
    the sequence. 
    """
    return sequenceMatchLengths(s,DNAbasesPat)

def DNABaseCount(s):
    """return the number of DNA bases in
    the sequence. 
    """
    return sum(sequenceMatchLengths(s,DNAbasesPat))

def RNABaseLengths(s):
    
    """return a list of the lengths of RNA base stretches in
    the sequence. 
    """
    
    return sequenceMatchLengths(s,RNAbasesPat)

def RNABaseCount(s):
    """return the number of RNA bases in
    the sequence. 
    """
    return sum(sequenceMatchLengths(s,RNAbasesPat))

def DRNABaseLengths(s):
    """return a list of the lengths of RNA or DNA base streatches in
    the sequence. 
    """
    #print DRNAbases
    return sequenceMatchLengths(s,DRNAbasesPat)

def DRNABaseCount(s):
    """return the number of RNA and DNA bases in
    the sequence. 
    """
    #print sequenceMatchLengths(DRNAbasesPat)
    return sum(sequenceMatchLengths(s,DRNAbasesPat))

def LZWsize(s):
    """return the size of the LZW compressed sequence
    """
    from . import aos
    return aos.LZWsize(self.sequence)

def LZWratio(s):
    """Return the LZW compression ratio.
    """
    from . import aos
    return float(self.LZWsize())/float(self.sequence)

