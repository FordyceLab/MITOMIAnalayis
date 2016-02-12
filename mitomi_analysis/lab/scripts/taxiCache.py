#!/usr/local/bin/python
#
# taxiCache.py
# Kael Fischer
# 2008
#
# CLI tool calculate and cache taxi results
#
"""taxiCache.py

Calculate and cache vTaxI results for multiple chips.  Using a single set of
vTaxI settings (chip set, intensity cutoff, etc.) taxon and branch p-values
are calculated and cached for all the chips in specified study or one or more
specified chips; see EXAMPLES below.

Users should take care to put quotes around chip set names and study names
that probably have spaces in them which will break command line tools.

Some parameters are not accessible using this interface.  These parameters
are always used by taxiCache:
     ignore HERVs - Always True
     taxa with no assigned oligos - Always False
     taxa with no significant oligos - Always False
     Outlier oligo p - Always < 1e-50

USAGE
taxiCache.py -p # -i # -d YYYY-MM-DD -n [T|F] -s "chip set name" <study|chip ..>

EXAMPLE (all chips in a study):
taxiCache.py -t -p 0.005 -i 200 -d 2013-01-14 -nT -s"Cy3 All" "Cal. Colds 2012" 

EXAMPLE (multiple chips):
taxiCache.py -g -p0.5 -i200 -d 2013-01-14 -nF -s"Cy3 All" Viro7P1-001 ViroP7-002

OPTIONS
    -h      print this help message.
    -?        "    "    "      "
    -t      use Non-Centered t fits
    -g      use Gamma fits
    -p      p-value cutoff for significance.
    -i      intensity cutoff (lower intensities are ignored).
    -d      reference set date.
    -s      reference set.
    -n      normalize chip intensities to mean for reference. (T/F)
    -X      Don't submit job to grid engine.  Check arguments,
            chips, etc. and exit.
    -f      Submit job to the grid engine without asking for confirmation.
    -G      Run calculations locally, do not submit to grid engine.

"""
__version__ = "$Revision: 1.1 $".split(':')[-1].strip(' $') # don't edit this line.
                                                            # cvs will set it.

import datetime
import getopt
import os
import sys
import time

import utils
import grid

def quoteArgs(arg):
    if arg.find(' ') == -1:
        return arg
    if arg.startswith('-'):
        return arg[:2] + ' \\\"'+arg[s:]+'\\\"'
    else:
        return '\\\"'+arg+'\\\"'

def __main__(args=None):

    chips=[]
    chipSet=None
    fitProtocol=None
    pCutoff=None
    iCutoff=None
    normalize=None
    refDate=None

    force=False
    noSubmit=False
    noGrid=False
    
    shortOptions="h?p:i:d:s:n:fXGtg" 
    longOptions = []   
    try:
        opts, args = getopt.getopt(args, shortOptions, longOptions)
    except getopt.error as msg:
        # there is an unknown option!
            print(msg)      # prints the option error
            print(__doc__)  # prints the usage message from the top
            return (-2)

    for option,optionArg in opts:
        if option=='-h' or option=='-?':
            print(__doc__)
            return(-1)     # '0' = no error in UNIX
        elif option == '-t':
            if fitProtocol != None:
                print("only -t or -g can be specified, not both.")
                return -2
            fitProtocol = 4
        elif option == '-g':
            if fitProtocol != None:
                print("only -t or -g can be specified, not both.")
                return -2
            fitProtocol = 1
        
        elif option == '-p':
            try:
                pCutoff = float(optionArg)
            except:
                print("-p argument must be a float")
                return -2
        elif option == "-i":
            try:
                iCutoff = int(optionArg)
            except:
                print("-i argument must be an integer")
                return -2
        elif option=='-d':
             try:
                 y,m,d = [int(x) for x in optionArg.split('-')]
                 refDate = datetime.date(y,m,d)
             except:
                 print("-d must be date like YYYY-MM-DD")
                 return -2
        elif option == '-s':
            chipSet = optionArg
        elif option=='-n':
            if optionArg == 'T':
                normalize = True
            elif optionArg == 'F':
                normalize = False
            else:
                print("-n argument must be either T of F")
                return (-2)
        elif option == "-X":
            noSubmit = False
        elif option == '-f':
            force = True
        elif option == '-G':
            noGrid = True
        else:
            print("%s option not implemented" % option)


    if None in (chipSet,fitProtocol,refDate,pCutoff,iCutoff,normalize):
        print("\nRequired options/arguments missing.")
        print("chip set, ref. date, both cutoffs and a normalize choice are required.")
        print()
        print(__doc__)  # prints the usage message from the top
        return (-2)

    #
    # since viroinfo is slow to import
    # put it here after the fast argument checks
    # like -h
    #
    import viroinfo
    from viroinfo import megachip,analysis,oligo

    fitProtocol=oligo.OligoFitProtocol(fitProtocol)

    try:
        chipSet = megachip.ChipSet(chipSet)
    except:
        print("-s argument '%s' is not a known chip set." % chipSet)
        return -2

    for thing in args:
        try:
            study = megachip.Study(thing)
            chips.extend(study.chips())
        except:
            try:
                chips.append(megachip.Chip(thing))
            except:
                print("%s is neither a study or a chip" % thing)
                return -2
    chips = utils.unique(chips)

    # logging
    print(sys.argv[0], datetime.datetime.now().isoformat())
    print("PARAMETERS")
    params = (("chip set:",chipSet),
              ("fit protocol:",fitProtocol),
              ("ref date:",refDate),
              ("p-cutoff:",pCutoff),
              ("I-cutoff:",iCutoff),
              ("norm:",normalize))
    print(utils.tabbifyMatrix(params))
    print()
    print("CHIPS")
    for c in chips:
        print(c)
    print() 

    # on to the run
    # submit to the grid, etc
    if ( noGrid or
         ("ENVIRONMENT" in  os.environ and os.environ["ENVIRONMENT"] == "BATCH")):
        # confirm if run is local
        # if already on the grid, there is no use to confirm
        if noGrid and not force:
            confirm=''
            while confirm not in ('y','n'):
                confirm=input("Run job locally[y/n] ?")
            if confirm == 'n':
                print("taxiCache.py job aborted.")
                return 1
        return calcQueries(chips,chipSet,fitProtocol,refDate,pCutoff,iCutoff,normalize)

    else:
        #
        # is this job ready for grid submission?
        #
        if noSubmit:
            print("No job submitted to the Grid Engine.\nRerun taxiCache.py without '-X' to submit job.")
            return 0

        # get  user confirmation for grid submission
        if not force:
            confirm=''
            while confirm not in ('y','n'):
                confirm=input("Submit job [y/n] ?")
            if confirm == 'n':
                print("taxiCache.py job not submitted to Grid Engine.")
                return 1

        cmd = "echo %s | qsub -cwd -N taxiCache" % (' '.join([quoteArgs(x) for x in sys.argv]))
        gs=grid.GridSubmission(cmd)
        print("Your taxiCache job has been submitted to the Grid Engine like:\n%s" % cmd)
        print("The Job ID is %s" % gs.jobID)
        print("A log of the results called taxiCache.o%s will be in the current directory." % gs.jobID)
        return 0





def calcQueries(chips,chipSet,fitProtocol,refDate,pCutoff,iCutoff,normalize):

    from viroinfo import analysis
    
    print('\t'.join([str(x) for x in ("chip","chip set","fit protocol",
                                      "ref date","p-cutoff","I-cutoff","norm")]))
    for c in chips:
        try:
            tq = analysis.TaxiQuery(c,chipSet,
                                    pcutoff=pCutoff,
                                    intensCutoff=iCutoff,
                                    centerI=normalize,
                                    timestamp=refDate,
                                    fitProtocol=fitProtocol
                                    )
        except:
            print('\t'.join([str(x) for x in ("*FAILED*",c,chipSet,fitProtocol,
                                              refDate,pCutoff,iCutoff,normalize)]))
            raise
            continue
        else:                        
            print('\t'.join([str(x) for x in (c,chipSet,fitProtocol,
                                              refDate,pCutoff,iCutoff,normalize)]))
    print("taxiCache job finished")
    return (0)

if __name__ == "__main__":
    sys.exit( __main__(sys.argv[1:]))

