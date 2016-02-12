import sys
from getopt import getopt
import chipSingleconcUtils


HELP_STRING = """
gprFilesToConcatFile_v2.py

Authored by: Polly Fordyce, August 2010
Updated by: Tyler Shimko, February 2016

Converts a series of gpr files output from Genepix into a concatenated file for
further analysis.  Required inputs are (1) a gpr file gridded for protein
intensities under the button, (2) a gpr file gridded for DNA intensities under
the button, (3) a gpr file gridded for DNA intensities within the chambers, and
(4) an output file name (usually ProteinName_Concat.txt).  Optional inputs
include flags to specify precisely how the gridding was done and the
orientation of the tiff file.

    -h    print this help message
    -p    protein button filename (required)
    -d    DNA button filename (required)
    -c    chamber filename (required)
    -o    output filename (required)
    -m    files were not gridded in a single block
    -r    renumber concat file so that columns are numbered from RH side of
          .tiff file
    -R    renumber concat file so that rows are numbered from bottom of
          .tiff file

Example usage:
python gprFilesToConcatFile.py -p Pho4_Protein.gpr -d Pho4_DNA.gpr -c Pho4_Chambers.gpr -o Pho4_Concat.txt -m
"""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    sF = 0
    rlF = 0
    tbF = 0
    pFN = ""
    dFN = ""
    cFN = ""
    oFN = ""

    try:
        optlist, args = getopt(argv[1:], "hp:c:d:o:amRr")
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
        elif opt == '-p':
            pFN = opt_arg
        elif opt == '-c':
            cFN = opt_arg
        elif opt == '-d':
            dFN = opt_arg
        elif opt == '-o':
            oFN = opt_arg
        elif opt == '-m':
            sF = 1
        elif opt == '-r':
            rlF = 1
        elif opt == '-R':
            tbF = 1

    if pFN == "" or dFN == "" or cFN == "" or oFN == "":
        print(HELP_STRING)
        sys.exit(1)

    chipSingleconcUtils.concatGprFiles_v3(pFN, cFN, dFN, oFN,
                                          singleF=sF, rlF=rlF, tbF=tbF)

    return 0

# Run the main() function
if __name__ == "__main__":
    sys.exit(main())
