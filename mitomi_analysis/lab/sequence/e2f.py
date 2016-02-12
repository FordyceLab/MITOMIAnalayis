#!/usr/local/bin/python -u
"""e2f.py [-h|-?] | [[-t <title file>] [eland results flies]]

Transform eland results to fasta format
Input can be 1 or more files or it can be stdin.
Output is on stdout.

\teland results flies can be names of files or can be omitted to use stdin


\t-t title file\tname of file containg tiles to extract, - for stdin.
\t\tstdion can only be used for titles or eland records, not both.

"""
import sys
from getopt import getopt

if __name__ == "__main__":
    tFile = None

    opts,args = getopt(sys.argv[1:],'t:h?')
    for o,a in opts:
        if o in ('-h','-?'):
            print(__doc__)
            sys.exit(2)
        elif o == '-t':
            if a == '-':
                if len(args) == 0:
                    print(__doc__)
                    raise GetoptError(
                        "both eland results and title file are stdin")
                else:
                    tFile=sys.stdin
            else:
                tFile=file(a)
        else:
            print(__doc__)
            raise GetoptError('unknown option: %s'%(o))

    from . import solexa

    if tFile == None:
        if len(args)==0:
            try:
                print(''.join(solexa.eland2fastaString(sys.stdin)), end=' ')
            except KeyboardInterrupt:
                print() 
                print(__doc__)
                sys.exit(2)

        else:
            for fn in args:
                print(''.join(solexa.eland2fastaString(file(fn))), end=' ')
        
    else:
        titles = {}
        for t in tFile:
            if not t.startswith('>'):
                t = '>' + t
            t=t.strip()
            titles[t]=None

        if len(args)==0:
            files=sys.stdin
        else:
            files = [file(fn) for fn in args]

        for f in files:
            for eLine in f:
                eSplit=eLine.split()
                if eSplit[0] in titles:
                    print("%s\n%s" %(eSplit[0],eSplit[1]))
        
        
            
            
