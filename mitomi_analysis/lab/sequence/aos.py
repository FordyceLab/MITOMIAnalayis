#
# AOS Calculations
#
# Access to the ArrayOligoSelector compiled libraries.
#
# Smith Waterman uses the PAM47 matrix:
#              gap_open = -7
#              gap_extend = 0
#              match = 5
#              mismatch = -4
#
#
# Energy Calcultaions - comments from the C code (data.c):
#
#/* All energy parameters are in kcal/mol unit 
#   All energy parameters are in 37 degree C standard condition
#*/
#
#/*N. Sugimoto et.al.  NAR  1996, Vol 24, No22 4501-4505*/ [wc base pair energies]
#
#/*N. Peyret et.al. Biochemistry 1999, 38, 3468-3477
#  Biochemistry Vol37, No 26, 1998
#  NAR 1998, Vol 26, No.11
#  Biochemistry, Vol 37, No. 8, 1998
#  Biochemistry, Vol 36, No. 34, 1997 [internal mismatches]
#*/
#
# [loop params seem to come for Zuker web pages that are gone]
#/* [also] 
#   Peritz et. al. Biochemistry 1991 30, 6428-6436
#*/
#

__version__ = "$Revision: 1.6 $"

from types import *
import ctypes

import sequence

__aos = _aos=ctypes.cdll.LoadLibrary("libaos.so.1.0.1")
__aos.energy.restype=ctypes.c_double



def SW(s1,s2):
    """Return (alignment string, sw score).
    sequences are taken as read - no complementing or reversing.
    returns ('',-1) if there is no alignment.
    """

    if type(s1) != StringType or type(s2) != StringType:
        raise AttributeError, "s1  and s2 must be strings"
        
    sLen = len(s1)
    if len(s2) != sLen:
        raise SequenceLengthError, "s1 and s2 are different lengths."

    outBuffer =  ctypes.create_string_buffer(sLen*5)

    __aos.SW(ctypes.c_char_p(s1),
             ctypes.c_char_p(s2),
             ctypes.c_int(1),
             ctypes.c_int(sLen),
             outBuffer)

    outLines = outBuffer.value.split('\n')
    if len(outLines) > 3:
        alignment = '\n'.join(outLines[0:2])
        score = int(outLines[2])
        return (alignment,score)
    else:
        return ('',-1)

def selfSW(s):
    """Return the self-alignment, i.e. the sequence to the complement sequence.
    The better the alignment the more secondary structure.
    """
    return SW(s,sequence.complement(s))



def LZWsize(s):
    """Return size of LZW compresses string.
    A smaller size means lower complexity if you are
    comparing 2 sequences of the same length.
    """

    sLen=len(s)
    return __aos.LZWsize(ctypes.c_char_p(s),ctypes.c_int(sLen))


                        
def energy(s1,s2):
    """Return melting energy for association os s1/s2.
    """

    if type(s1) != StringType or type(s2) != StringType:
        raise AttributeError, "s1  and s2 must be strings"

    if len(s2) != len(s1):
        raise SequenceLengthError, "s1 and s2 are different lengths."

    s2=sequence.reverse(s2)

    return __aos.energy(ctypes.c_char_p(s1),ctypes.c_char_p(s2),ctypes.c_int(0))


def selfEnergy(s):
    """return the melting energy of 's' with itself.
    """
    return energy(s,s)

class AOSError(Exception):
    pass

class SequenceLengthError (AOSError):
    pass

class SequenceBaseError(AOSError):
    pass
