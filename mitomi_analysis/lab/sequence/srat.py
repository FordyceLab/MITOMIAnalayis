#!/usr/local/bin/python

##########################################
#
# srat.py (short read assembly tool)
# name subject to change.
# 
# This file includes several classes used
# for the assembly of short (~35mer) reads
# into contigs using an algorithm very
# similar to the amazing 'SSAKE' program:
# Bioinformatics. 2007 Feb 15;23(4):500-1
#
# There is also a main function for testing
# purposes that functions as a single-thread
# assembly program.
#
# Dale Webster,
# Kael Fischer,
# Other peeps (add yourself!)
#
# 07/31/2007
#
##########################################

"""
Usage:
./srat.py [-m minOverlap] [-x maxMismatchesPerBase] [-n nmerTableN] sequenceFile outFile
"""

import os, sys
import getopt
import solexa
import fasta
import copy
from utils.timeprofile import *
from compact import CompactSequence
from compact import N

class FakeProfiler:
    agg = []
    def mark( self, time ):
        pass
    def diff( self, a, b ):
        return 0.0
    def elapsed( self, time ):
        return 0.0
    def observe( self, a, b, c ):
        pass
    def total( self, a ):
        return 1.0
    def count( self, a ):
        return 0.0
    def averageElapsed( self, a ):
        return 0.0

DEBUG = False
DEBUG_PROFILER = False
DEBUG_STATS = True
PROFILER = FakeProfiler() # timeprofile()
USE_COMPACT_SEQUENCE = False

#############
#
# Debug

def log( text, p=False, s=False ):
    if p and DEBUG_PROFILER:
        print text
    elif s and DEBUG_STATS:
        print text
    elif DEBUG:
        print text
        
#############

comp = { "A":"T",
         "T":"A",
         "G":"C",
         "C":"G",
         "N":"N" }

class SequenceImporter:
    """This is the parent class for the
    different types of sequence
    importation I'm currently supporting."""

    def getReads( self, filename ):
        """This function should be called to get the
        reads."""
        return self.parse( filename )

    def parse( self, filename ):
        """Returns a list of Sequences."""
        pass

class FastaImporter( SequenceImporter ):
    """Uses Kael's sequence.fasta.FastaIterator."""

    def parse( self, filename ):
        """Given a name for a FASTA file, returns the sequences therein"""
        fastas = fasta.FastaIterator( open( filename, "r" ) )
        return map( lambda x: x.sequence, fastas )

class FlatFileImporter( SequenceImporter ):
    """Reads in a file containing one sequence per line."""

    def parse( self, filename ):
        """Given a flat file, returns the sequences in it."""
        inF = open( filename, "r" )
        lines = inF.readlines()
        inF.close()
        return map( lambda x: x.strip(), lines )

class BustardImporter( SequenceImporter ):
    """Reads in a Solexa formatted sequence file."""

    def parse( self, filename ):
        """Ignores all information that is not sequence,
        and returns the sequences."""
        return solexa.parseBustard( filename )
                
class GeraldImporter( SequenceImporter ):
    """Reads in a Solexa formatted sequence file."""

    def parse( self, filename ):
        """Ignores all information that is not sequence,
        and returns the sequences."""
        return solexa.parseGerald( filename )
                
def revComplement( seq ):
    """Returns the reverse complement sequence
    of the input."""

    PROFILER.mark( 'rcStart' )
    if type(seq) == str:
        newString = ""
        for i in range( len(seq)-1, -1, -1 ):
            newString = newString + comp[ seq[i].upper() ]
    else:
        newString = copy.copy( seq )
        newString.reverse()
        newString.complement()
    PROFILER.mark( 'rcEnd' )
    PROFILER.observe( 'rcStart', 'rcEnd', 'rc' )
    return newString
    
class ReadManager:

    def __init__( self ):
        """Simple constructor. Nothing to see here. Move along."""
        self.reads = []
        self.mrl = -1

    def __str__( self ):
        """The string representation of a read manager is a long output of the
        internal read table across multiple lines."""
        return "\n".join( map( str, self.reads ) )

    def count( self, readID ):
        """Given a read ID, returns the number of times
        that read occurs in the input read set."""
        return self.reads[ readID ][1]

    def sequence( self, readID, rc=False ):
        """Given a read ID, returns the sequence of
        said read. Reverse Complements the sequence if
        specified."""
        if rc:
            return revComplement( self.reads[ readID ][0] )
        else:
            return self.reads[ readID ][0]

    def fromFile( self, seqFile, qualityFile=None, loadReverseComplement=True ):
        """Builds the ReadManager from a file with
        one read sequence per line. An optional quality
        file contains a tab-separated list of qualities
        for each base in each read. (one read per line)"""

        log( "Building ReadManager from %s..." % seqFile )
        PROFILER.mark('startRMB')

        seqImporter = FastaImporter()
        reads = seqImporter.getReads( seqFile )
        
        tempHugeDict = {}

        def addRead( r ):
            if r in tempHugeDict:
                tempHugeDict[ r ] = tempHugeDict[ r ] + 1
            else:
                rc = revComplement( r )
                if rc in tempHugeDict:
                    tempHugeDict[ rc ] = tempHugeDict[ rc ] + 1
                else:
                    tempHugeDict[ r ] = 1

        numReads = 0
        for read in reads:
            if read.count("N") > 5:
                continue
            if read.count("G") > 12:
                continue
            if read.count("C") > 12:
                continue

            self.checkMRL( read )
            addRead( read )
            numReads = numReads + 1
            
        for seq in tempHugeDict:
            self.reads.append( ( seq, tempHugeDict[seq] ) )

        numCollapsedReads = len( self.reads )

        log( "Done Building." )
        PROFILER.mark('endRMB')
        log( "Elapsed ReadManager Build Time: %.6f" % float(PROFILER.diff('startRMB', 'endRMB')), p=True )
        log( "Initial Reads: %d, Collapsed Reads: %d, Compression: %.2f" % ( numReads, numCollapsedReads, 100*(1.0-float(numCollapsedReads)/float(numReads)) ) , s=True )

    def checkMRL( self, read ):
        """Checks to see if we need to update the stored max read length."""
        if len( read ) > self.mrl:
            self.mrl = len( read )

    def maxReadLength( self ):
        """Returns the length of the longest read."""
        return self.mrl

class NmerIndexing:

    def __init__( self, readManager, N ):
        """This class requires the presence of
        a ReadManager instance, supplied here
        in the constructor."""

        self.rm = readManager
        self.n = N
        self.nmers = {}
        self.buildFromReadManager()

    def __str__( self ):
        """Shows the entire indexing table."""
        return "\n".join( map( lambda x: str( "%s\t[ %s ]" % ( x, ", ".join( map( str, self.nmers[x] ) ) ) ) , self.nmers.keys() ) )

    def buildFromReadManager( self ):
        """Builds the internal lookup table
        based on self.n and self.rm."""

        log("Building lookup table...")
        PROFILER.mark( 'startIndexing' )
        for (i,read) in enumerate(self.rm.reads):
            prefix = self.rm.sequence( i, rc=False )[:self.n]
            if not prefix in self.nmers:
                self.nmers[ prefix ] = ( [ i ], [] )
            else:
                self.nmers[ prefix ][0].append( i )
            rcPrefix = self.rm.sequence( i, rc=True )[:self.n]
            if not rcPrefix in self.nmers:
                self.nmers[ rcPrefix ] = ( [], [ i ] )
            else:
                self.nmers[ rcPrefix ][1].append( i )

        log("Done Building.")
        PROFILER.mark('endIndexing')
        log("Elapsed Indexing Time: %.6f" % float(PROFILER.diff('startIndexing','endIndexing')), p=True )
        log("Prefix Table Occupancy: %d/%d (%.2f)" % ( len( self.nmers ), pow( 5, self.n ), float(len(self.nmers))/float(pow(5,self.n)) ), s=True )
        sumOfLengths = sum( map( lambda x: len(x[0])+len(x[1]), self.nmers.values() ) )
        numLengths = len(self.nmers)
        log("Average Entry Length: %.2f" % (float(sumOfLengths) / float(numLengths)), s=True )

    def extensionOptions( self, nmer ):
        """Returns the list of all readIDs beginning
        with the specified nmer."""
        
        if nmer in self.nmers:
            return self.nmers[ nmer ]
        else:
            return ( [], [] )

    def nextSeed( self ):
        """Returns the next un-used read in an
        unspecified order."""

        PROFILER.mark('seedStart')
        readID = None
        for key in self.nmers:
            ( f, r ) = self.nmers[ key ]
            if len(f) > 0:
                readID = f[0]
            else:
                readID = r[0]
            break
        
        PROFILER.mark('seedEnd')
        PROFILER.observe('seedStart', 'seedEnd', 'seed')
        return readID

    def deleteRead( self, prefix, readID ):
        """Removes the specified read pointer from the
        table, removing the entire prefix if appropriate."""

        PROFILER.mark('deleteStart')
        ( f, r ) = self.nmers[ prefix ]
        found = False
        for i in range(len(f)):
            if f[i] == readID:
                del f[i]
                found = True
                break
        if not found:
            for i in range(len(r)):
                if r[i] == readID:
                    del r[i]
                    break

        if len(f) + len(r) == 0:
            del self.nmers[ prefix ]

        PROFILER.mark('deleteEnd')
        PROFILER.observe('deleteStart', 'deleteEnd', 'delete')
        return

class Contig:

    def __init__( self, readManager, nmerIndexing, initialReadID ):
        """Class representing a contig made up of one or more
        Reads. Knows how to extend itself. The sequence variable
        is maintained throughout assembly to avoid recomputing
        it constantly from the reads."""

        self.reads = []
        self.overlaps = []
        self.sequence = None
        self.rm = readManager
        self.ni = nmerIndexing

        self.sequence = self.rm.sequence( initialReadID )
        self.ni.deleteRead( self.sequence[:self.ni.n], initialReadID )
        self.ni.deleteRead( revComplement(self.sequence)[:self.ni.n], initialReadID )

    def __str__( self ):
        """The string representation of a contig is simply its sequence."""
        return str(self.sequence)

    def extend( self, minOverlap, maxMismatchesPerBase=0.0 ):
        """Given the listed parameters, extends the contig
        if possible. Returns True if extension occured, otherwise
        False. By default this method will mark Reads as used when
        they are used for extension."""

        PROFILER.mark('feoStart')
        option = self.findExtendOptions( minOverlap, self.rm.maxReadLength(), maxMismatchesPerBase )
        PROFILER.mark('feoEnd')
        PROFILER.observe('feoStart', 'feoEnd', 'feo')

        if not option:
            return False

        ( extendRead, mpb, overlap, rc ) = option

        readSequence = self.rm.sequence( extendRead, rc=rc )
        self.sequence = self.sequence + readSequence[overlap:]
        self.ni.deleteRead( readSequence[:self.ni.n], extendRead )
        self.ni.deleteRead( revComplement(readSequence)[:self.ni.n], extendRead )

        return True

    def findExtendOptions( self, minO, maxO, mmpb ):
        """An internal helper function for extend, this method takes the
        first 3 arguments to extend and returns a list of the best reads
        with which we can extend this oligo."""

        options = []
        rcOptions = []
        overlap = 0
        for overlap in range( maxO, minO-1, -1 ):
            if overlap > len( self.sequence ):
                continue
            log("overlap: " + str(overlap))
            overlapSeq = self.sequence[-overlap:]
            log("overlapSeq: " + str(overlapSeq))
            PROFILER.mark('eoStart')
            ( options, rcOptions ) = self.ni.extensionOptions( overlapSeq[:self.ni.n] )
            PROFILER.mark('eoEnd')
            PROFILER.observe('eoStart','eoEnd','eo')
            log("options: " + "\t".join( map(str, options ) ))
            log("RC options: " + "\t".join( map(str, rcOptions ) ))
            if (len( options ) + len( rcOptions )) > 0:
                PROFILER.mark('voStart')
                bestOption = self.validateOptions( options, rcOptions, overlap, mmpb )
                PROFILER.mark('voEnd')
                PROFILER.observe('voStart', 'voEnd', 'vo')
                if bestOption:
                    return bestOption

        return None

    def validateOptions( self, options, rcOptions, overlap, mmpb ):
        """Given a list of potential oligos to extend with, checks to see
        that they meet the required overlap length and mismatch %. Returns
        a list of the valid ones."""

        possibleExtenders = []

        def getMPB( seq ):
            mySequence = self.sequence[-overlap:]
            readSequence = seq[:overlap]
            m = 0
            # skip the first N bases because we know they must
            # be an exact match.
            for i in range( self.ni.n, len( mySequence) ):
                if mySequence[i] != readSequence[i] and not( mySequence[i] == "N" or readSequence[i] == "N" ):
                    m = m+1
            mpb = float(m)/float(len(mySequence))
            return mpb
        
        for option in options:
            seq = self.rm.sequence( option )
            if overlap > len( seq ) or overlap > len( self.sequence ):
                continue
            mpb = getMPB( seq )
            if mpb <= mmpb:
                possibleExtenders.append( ( option, mpb, overlap, False ) )

        for option in rcOptions:
            seq = self.rm.sequence( option, rc=True )
            if overlap > len( seq ) or overlap > len( self.sequence ):
                continue
            mpb = getMPB( seq )
            if mpb <= mmpb:
                possibleExtenders.append( ( option, mpb, overlap, True ) )

        if len( possibleExtenders ) == 0:
            return None

        possibleExtenders.sort( cmp= lambda x,y: cmp( x[1], y[1] ) )
        return possibleExtenders[0]

    def reverseComplement( self ):
        """Reverse complements the contig in place. The read order
        is reversed, and the overlap values are adjusted accordingly.
        The sequence is rebuilt based on the new reads (slow)"""

        PROFILER.mark('contigRCStart')
        self.sequence = revComplement( self.sequence )
        PROFILER.mark('contigRCEnd')
        PROFILER.observe('contigRCStart', 'contigRCEnd', 'contigRC' )

class ShortReadAssembler:
    """This class ties together the module to present a simple
    interface for short read assembly."""

    def __init__( self, inputFile, n=9, minOverlap=10, maxMismatchesPerBase=0.0 ):
        """All assembly input is handed to the object upon creation. Iterating
        over the object triggers the assembly process, yielding contigs as they are
        generated. (keeps us from having to store all of the contigs in memory, which
        can be unpleasant)"""

        self.rm = ReadManager()
        self.rm.fromFile( inputFile )

        self.indexing = NmerIndexing( self.rm, n )
        self.minO = minOverlap
        self.mmmpb = maxMismatchesPerBase

    def __iter__( self ):
        """Iterates over the contigs as Strings, assembling them on the fly."""

        contigs = []
        seed = self.indexing.nextSeed()
        while seed != None:
            c = Contig( self.rm, self.indexing, seed )
            log( "Seeded contig as %s" % c )
            while c.extend( self.minO, self.mmmpb ):
                log( "Extended contig to %s" % c )
                pass
            c.reverseComplement()
            log( "Reversed Contig to %s" % c )
            while c.extend( self.minO, self.mmmpb ):
                log( "Extended contig to %s" % c )
                pass
            yield( str(c) )
            log( "No more extension possible." )
            seed = self.indexing.nextSeed()

#####
#
# Where have you seen this before?
#
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def process( opts, args ):
    """Process uses every available (unused) read in the read manager
    as a seed for a new contig. Once all reads have been used, it
    reports statistics on the distribution of contig lengths, etc."""

    seqFile = args[0]
    outFile = args[1]

    n = "-n" in opts and int(opts["-n"]) or 10
    minO = "-m" in opts and int(opts["-m"]) or 10
    mmmpb = "-x" in opts and float(opts["-x"]) or 0.0

    log( "All inputs satisfied, beginning assembly." )

    sra = ShortReadAssembler( seqFile, n, minO, mmmpb )
    i = 0
    out = open( outFile, "w" )
    for contig in sra:
        out.write(">Contig%d[%d]\n" % ( i, len(contig) ) )
        out.write(contig+"\n")
        i = i + 1
    
    log("Profiler Aggregated Results:", p=True)
    for key in PROFILER.agg:
        log("%s stats: %.4f seconds/%d iterations = %.6f average." % ( key, PROFILER.total( key ), PROFILER.count( key ), PROFILER.averageElapsed( key ) ), p=True )

    log("Total Run Time: %s" % PROFILER.elapsed('start'), p=True)

def main(argv=None):
    """Callable main function parses command line options then
    passes the buck to process()."""

    PROFILER.mark('start')
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hx:m:n:", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage(__doc__)
            
        if len(args) != 2:
            raise Usage("Invalid number of arguments")
        process( dict(opts), args )
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())


