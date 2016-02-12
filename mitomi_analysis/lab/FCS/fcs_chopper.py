import sys
from getopt import getopt
import FCS3

USAGE = """
FCS_Chopper [-dh] <-w window size> <-t threshold factor> <-s statistic> <file1, file2, ...>
where:
   window size\t\tis a positive integer less than 2000
   threshold factor\tis a float
   statistic\t\tis "mean" or "median"

   -d\t\t\tturn on debugging output
   -h\t\t\tprint this message
   
   This program reads .fcs files, searches for the FITC-A and Time channels
   then eliminates data windows with average fitc counts greater than the
   overall fitc average * threshold_factor.
   Testmode will print statistics without printing the data with these columns:
   Events, Median before filtering, Median after filtering, Windows censored,
   Percent of total data censored."""

try:
    optlist, fileNames = getopt(sys.argv[1:],'hdw:t:s:')
except:
    print USAGE
    sys.exit(2)

DEBUG=False
windowSize=None
statistic=None
thresholdFactor=None

for opt,opt_arg in optlist:
    if opt == '-h':
        print USAGE
        sys.exit(1)
        
    elif opt == '-d':
        DEBUG = True
        
    elif opt == '-w':
        try:
            windowSize = int(opt_arg)
            if windowSize < 1 or windowSize > 2000:
                raise Exception
        except:
            print "%s: bad window size (%s)" % (sys.argv[0],opt_arg)
            print USAGE
            sys.exit(2)
            
    elif opt == '-t':
        try:
            thresholdFactor = float(opt_arg)
        except:
            print "%s: bad threshold factor (%s)" % (sys.argv[0],opt_arg)
            print USAGE
            sys.exit(2)
    elif opt == '-s':
        try:
            if opt_arg == 'mean':
                statistic = FCS3.MEAN
            elif opt_arg == 'median':
                statistic = FCS3.MEDIAN
            else:
                raise Exception
        except:
            print "%s: bad statistic (%s)" % (sys.argv[0],opt_arg)
            print USAGE
            sys.exit(2)

if windowSize == None or thresholdFactor == None or statistic == None:
            print "%s: required parameter missing" % (sys.argv[0])
            print USAGE
            sys.exit(2)
    



for fn in fileNames:
    fcsObj=FCS3.FCS()
    fcsObj.parseFCSfile(fn)
    finalCount = fcsObj.smoothConstantData(['FITC-A'],
                                           windowSize=windowSize,
                                           thresholdFactor=thresholdFactor)
    fcsObj.displayParameters=['Time','FITC-A']
    print fn
    print fcsObj

    if DEBUG:
        print "Total Events:\t\t%s" % fcsObj.eventCount
        print "Overall Average:\t%s" % fcsObj.median('FITC-A',unfiltered=True)
        print "Threshold Factor:\t%s" % thresholdFactor
        print "Window Size:\t\t%s" % windowSize
        print "Final Event Count:\t%s" % finalCount
        

    
    
