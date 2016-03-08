import sys
import os
from getopt import getopt

HELP_STRING = """
runMultiFREDUCE.py

Authored by: Polly Fordyce, June 2010
Updated by: Tyler Shimko, February 2016

This program runs fREDUCE under a variety of different conditions for a given
expression file and sequence file. The program must be run from the
subdirectory containing both the expression file and the seq file.

    -h    print this help file
    -e    expression file
    -s    seq file

You must specify expression and sequence filenames using their full paths.

"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    expFN, seqFN = "", ""

    try:
        optlist, args = getopt(argv[1:], "he:s:f:")
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
        elif opt == '-e':
            expFN = opt_arg
        elif opt == '-s':
            seqFN = opt_arg

    if expFN == "" or seqFN == "":
        print(HELP_STRING)
        sys.exit(1)

    os.system('cp ' + seqFN + ' ' + seqFN + 'ta')

    for a in range(6, 10):
        for b in range(0, 3):
            print('working on ' + str(a) + ' ' + str(b))
            print('freduce -r -x ' + expFN + ' -s ' + seqFN + 'ta ' +
                  str(a) + ' ' + str(b) + ' > ' + expFN[:-4] + '.r-' + str(a) +
                  '-' + str(b) + '.txt')
            os.system('freduce -r -x ' + expFN + ' -s ' + seqFN + 'ta ' +
                      str(a) + ' ' + str(b) + ' > ' + expFN[:-4] + '.r-' +
                      str(a) + '-' + str(b) + '.txt')
            print('freduce -x ' + expFN + ' -s ' + seqFN + 'ta ' + str(a) +
                  ' ' + str(b) + ' > ' + expFN[:-4] + '.nr-' + str(a) + '-' +
                  str(b) + '.txt')
            os.system('freduce -x ' + expFN + ' -s ' + seqFN + 'ta ' +
                      str(a) + ' ' + str(b) + ' > ' + expFN[:-4] + '.nr-' +
                      str(a) + '-' + str(b) + '.txt')

    return 0


##############################################
if __name__ == "__main__":
    sys.exit(main())
