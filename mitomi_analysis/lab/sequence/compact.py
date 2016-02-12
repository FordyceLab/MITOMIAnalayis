# compact.py
# Compact Sequence Representation
#
# by Kael Fischer
#
# This was an intersting excercise but turns out to be a memory hog and very slow
#
# 3-bit sequence representation
# stored in python long Objects
#
# the most significant bit is a 1 (placeholder)
# after that the most significant bit group is the 5' end
# 
# bit group is 'ABC'
# A  = ambiguity bit (call is 'low quality'), 0=high quality. 1=low quality.
# BC = the base call
#      00 -> A
#      01 -> C
#      10 -> G
#      11 -> T 
#
__version__ = "$Id: compact.py,v 1.11 2008/02/04 18:11:37 kael Exp $"

import math
from types import *

BASES = {
    'A':0,
    'a':0,
    'C':1,
    'c':1,
    'G':2,
    'g':2,
    'T':3,
    't':3,
    '.':4,
    'N':4,
    'n':4,
    0:'A',
    1:'C',
    2:'G',
    3:'T',
    4:'N'
    }

BASEMASK=7         # 111
AMBIGUOUS = 4      # 100
NOTAMBIGUOUS = 0   # 0
COMPLEMENT = 3     # 011 xor a base to the the complement 


def appendOnBits(thing,count) :
    """shift thing left puting 1's in the right most postions after shifting.
    """
    while count > 0:
        thing = (thing << 1) | 1
        count -= 1
    return thing


def bitMap(thing):
    """Show the bitmap of the thing
    """
    rl=[]
    while thing:
        rl.append(str(int(thing & 1)))
        thing = thing >> 1

    rl.reverse()
    return ''.join(rl)
        
        
class CompactSequence:
    """3-bit sequence representation
    
    the most significant bit is a 1 (placeholder)
    most significat bit group is the 5' end
     
    bits are 'ABC'
    A = ambiguity bit (call is 'low quality'). 0=high quality. 1=low quality.
    BC = the base call
      00 -> A
      01 -> C
      10 -> G
      11 -> T

      When A=1, BC are not significant. 
    """

    def __init__(self,bases=[],qualityStr='',qualityCutoff=0):
        """bases can be a list of Base objects, or a string of [ACGT]s.
        """
        self._seqBits=1

        if type(bases) == StringType:
            self.appendSeqStr(bases)
        else:
            self.appendBases(bases)


    def ambigMask(self):
        """Returns a bit mask of repeated 100 for the full length of the
        sequence.
        """
        rv=1
        for n in range(len(self)):
            rv =  rv << 3 | AMBIGUOUS
        return rv

    def nonAmbigBits(self):
        """Returns a mask of 1's in non-ambiguous positions.
        """
        rv=1
        for b in self:
            if b.ambiguity() == True:
                rv=rv << 3
            else:
                rv=rv << 3 |  BASEMASK
        return rv


    def placeHolderMask(self):
        """Returns a bit mask of 100000...000.
        """
        rv=1
        return rv << self._bitCount()-1
    

    def unambiquious(self):
        """True if CompactSequence has no N's.
        """
        return self.placeHolderMask()==self.ambigMask() & self._seqBits
    
 
    def appendSeqStr(self,seqStr):
        """Add bases to the 3' end given a string.
        """

        for base in seqStr:
            self._seqBits = (self._seqBits << 3) | BASES[base] 

    def appendBases(self,bases):
        """Add bases to the 3' end given a list of Base objects.
        """

        if type(bases) not in (TupleType,ListType):
            bases = (bases,)
        while len(bases) > 0:
            base=bases.pop(0)
            if not isinstance(base,Base):
                raise ArgumentError("% is not a base" % base)
            self._seqBits=self._seqBits << 3 | base._bits


    def _bitCount(self):
        """Including the leftmost placeholder return how many bits _seqBits is.
        """
        return int(math.ceil(math.log((self._seqBits),2)))
    
    def __len__(self):
        return (self._bitCount()-1)/3

    def __cmp__(self,other):
        return cmp(self._seqBits,other._seqBits)
    
    def  __str__(self):
        """Normal string representation of sequence.
        """
        return ''.join([x.letter() for x in self])

    def __getitem__(self, key):
        """Single index return a base.
        Slices return a CompactSequence.
        """
        l = len(self)

        # slice returns a sequence
        if type(key) == SliceType:
            if key.start < 0:
                raise IndexError
            start = key.start
            if key.step == None:
                step = 1
            else:
                step=key.step
            if key.stop > l:
                stop=l
            else:
                stop=key.stop
            return CompactSequence([self[i] for i in range(start,stop,step)])

        if key > l-1 or key < -1*l:
            raise IndexError
        baseOffset = l-key-1
        return Base(self._seqBits>>(baseOffset*3) & BASEMASK)
        
    def __setitem__ (self,key,base):
        """set a position to a particular base (Base or [ACGT])
        """
        if type(base) == StringType:
            base=Base(BASES[base])  # wow what unfortunate syntax!

        if not isinstance(base,Base):
            raise ArgumentError("% is not a base" % base)
        
        mask = 0
        mask = appendOnBits(mask,len(self)*3 +1) # all 1 mask
        submask = BASEMASK << (3*(key)) # 1's in target location
        mask = mask ^ submask
        self._seqBits = self._seqBits & mask # target bits = 0
        newBits = base._bits << (3*(key))

        self._seqBits = self._seqBits |  newBits
        
    def __iter__(self):
        """bases 5'->3.
        """
        for n in range(len(self)):
            yield(self[n])

    def __hash__(self):
        return hash(self._seqBits)

    def find5(self,query,start=0):
        """search for query sequence starting from start inthe 5'->3' direction.
        query can be a CompactSequence or a string.
        the sequence index is returned or -1 if not found (python style)
        """

        if not isinstance(query,CompactSequence):
            query = CompactSequence(query)
        
        passThough = 0
        passThough = appendOnBits(passThough,query._bitCount()) << (self._bitCount() - query._bitCount()-1-start*3)
        queryBits = query._seqBits << (self._bitCount() - query._bitCount() - start*3) & passThough
        
        pos=start
        while pos < len(self):
            #print "%35s" % bitMap(self._seqBits)
            #print "%35s" %  bitMap(passThough)
            #print "%35s" %  bitMap(queryBits)
            if self._seqBits & passThough ^ queryBits == 0:
                return pos
            pos += 1
            passThough = passThough >> 3
            queryBits = queryBits >> 3
            #print
        return -1
                
    def find3(self,query):
        """excercise for the reader. (not written yet)
        """
        pass

    def reverse(self):
        """Reverse sequence in place (returns None).
        """
        
        bases=list(self)
 
        self._seqBits=1
        while len(bases) > 0:
            self._seqBits=self._seqBits << 3 | bases.pop(-1)._bits
        
    
    def complement(self):
        """Complement in place (returns None).
        """
        mask = 0
        for l in range(len(self)):
            mask = mask <<3 | COMPLEMENT

        self._seqBits= self._seqBits ^ mask
        

    def compareWith(self,other,ignoreN=True):
        """return long integer representing XOR'ed
        seq bits.  The sequences must be the same length.
        
        0L==identical

        if not identical, the place holder bit is retained.


        If ignoreN is true (default) ambiguous postitions
        are set to 000.
        """

        if len(other) != len(self):
            return ValueError , "sequences must be the same length"
        
        rslt = self._seqBits ^ other._seqBits

        if rslt == 0:
            return rslt

        if not ignoreN or (self.unambiquious() and other.unambiquious()):
            return rslt | self.placeHolderMask()
        else:
            rslt = rslt & self.nonAmbigBits() & other.nonAmbigBits()
            if rslt == 0:
                return rslt
            else:
                return rslt | self.placeHolderMask()

    def countDiff(self,other,ignoreN=True):
        """return the number of sequence differences
        with other.
        """
        count=0

        diffBits = self.compareWith(other,ignoreN=ignoreN)
        if diffBits == 0:
            return count
        
        mask=BASEMASK
        for n in range(len(self)):
            if diffBits & mask > 0:
                count+=1
            diffBits = diffBits >> 3
        return count
            

    def count(self,base):
        """Return the number of times a base occurs.
        """

        count=0
        
        if not isinstance(base,Base):
            base = Base(BASES[base])

        bBits=base._bits
        mask = BASEMASK
        myBits = self._seqBits
        for n in range(len(self)):
            if (myBits & mask) ^ bBits == 0:
                count += 1
            myBits = myBits >> 3
        return count
                

            

class Base:
    """A base.  CompactSequence.__iter__() returns these,
    and the CompactSequence constructor takes them.
    """

    def __init__ (self,bits,showN=True):
        self._bits = bits
        self.showN = showN


    def ambiguity(self):
        return self._bits & AMBIGUOUS >= AMBIGUOUS

    def letter(self):
        if self.showN and self.ambiguity():
            return 'N'
        else:
            return BASES[self._bits & 3]

    def __str__ (self):
        return self.letter()

    def __cmp__ (self, other):
        return cmp(self._bits, other._bits)
    
    
    
    
A = Base(0)
C = Base(1)
G = Base(2)
T = Base(3)
N = Base(AMBIGUOUS)
