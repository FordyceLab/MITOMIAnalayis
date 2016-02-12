
import sys
import os
from getopt import getopt
import fileIOUtils
import numpy as N


HELP_STRING = """
outputDataForfREDUCE_v4.py

Authored by: Polly Fordyce, August 2010
Uodated by: Tyler Shimko, February 2016

This program takes a concat_processed filename and outputs
input files for fREDUCE.

     -h    print this help message
     -c    concat_processed filename

"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    cFN = ""

    try:
        optlist, args = getopt(argv[1:], "hc:")
    except:
        print("")
        print(HELP_STRING)
        sys.exit(1)

    if len(optlist) == 0:
        print("")
        print(HELP_STRING)
        sys.exit(1)

    for (opt, opt_arg) in optlist:
        print(opt)
        print(opt_arg)
        if opt == '-h':
            print("")
            print(HELP_STRING)
            sys.exit(1)
        elif opt == '-c':
            cFN = opt_arg

    if cFN == "":
        print(HELP_STRING)
        sys.exit(1)

    curDir = os.path.split(cFN)[0] + '/'
    tName = os.path.split(cFN)[1].split('_')[0]

    seq, rNN, DNAN = [], [], []
    f = open(cFN, 'r')
    lineIndex = 0
    for line in f:
        lineIndex = lineIndex + 1
        if lineIndex != 1:
            tempList = line.strip().split('\t')
            if tempList[17] != '' and not N.isnan(float(tempList[20])):
                seq.append(tempList[17])
                rNN.append(tempList[20])
                DNAN.append(tempList[18])
            else:
                pass
    f.close()

    sFileName = curDir + tName + '_Seq.fas'
    sFile = open(sFileName, 'w')
    rFileName = curDir + tName + '_rNN.txt'
    rFile = open(rFileName, 'w')
    dFN = curDir + tName + '_DNAN.txt'
    dFile = open(dFN, 'w')
    for b in range(0, len(seq)):
        sFile.write('>Seq_' + str(b) + '\n' + seq[b] + '\n')
        rFile.write('Seq_' + str(b) + '\t' + rNN[b] + '\n')
        dFile.write('Seq_' + str(b) + '\t' + DNAN[b] + '\n')
    sFile.close()
    rFile.close()
    dFile.close()

    fileIOUtils.createNewDir(curDir + '/fREDUCE/')
    os.system('mv ' + sFileName + ' ' + curDir + '/fREDUCE/')
    os.system('mv ' + rFileName + ' ' + curDir + '/fREDUCE/')
    os.system('mv ' + dFN + ' ' + curDir + '/fREDUCE/')

    return 0


##############################################
if __name__ == "__main__":
    sys.exit(main())
