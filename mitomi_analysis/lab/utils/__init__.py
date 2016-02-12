#!/usr/local/bin/python
#
# utilities
#
# DeRisi Lab 2007
#
__version__  ="$Revision: 1.3 $".split()[1]



import sys, os, re
from kdbom.kdbom import unique,union,intersection,shortest
from tabbedfile import tabbifyMatrix
from functools import reduce

__all__=["CommandLine","timeprofile",'readArgsOrFiles','flatten','unique',
         'union','intersection','shortest','tabbifyMatrix']

def flatten(sequence):
    """flatten a n-dimentional sequence.
    """
    return reduce(lambda x,y: x+y, sequence)


def readArgsOrFiles (args,
                    CL_INPUT_ALLOWED = True,
                    STDIN_ALLOWED = True,
                    PATHS_ALLOWED = True,
                    CGI_OVERRIDE=False,
                    cgiParam='data',
                    extraCGIDelimChars = ''):
    """Takes a list of strings, normally command line arguments.
    Each may be a path to a file, '-' indicating standard input,
    or if neither of these, it is taken to be a direct input to
    the program.  It the argument is stdin or a file, each line
    is returned, one at at time to the program.

    A generator is returned, yielding lines of the file like things
    (whitespace stripped), or values for args if they can not be
    evaluated as files.

    These flags control the fine points:
        CL_INPUT_ALLOWED - If False, args which are not paths
                           or '-' will raise an error.
        STDIN_ALLOWED    - If False, '-' will not open sys.stdin.
                           '-' will be interpreted as a non-file arg
        PATHS_ALLOWED    - If False, args will not be interpreted as
                           path names.
     Caller can set CGI_OVERRIDE and cgiParam to allow data to come
    via the CGI interface rather than file or stdin.  When the input
    is from cgiParam, extraCGIDelimChars can be set to allow parsing
    on non-whitspace.
    """


    if CGI_OVERRIDE:
        import cgi,cgitb; cgitb.enable()
        import re
        fieldExp = re.compile('[\s%s]' % extraCGIDelimChars)
        fields = cgi.FieldStorage()
        cgiValues= fields.getlist(cgiParam)
        for value in cgiValues:
            for item in fieldExp.split(value):
                yield item


    else:
        for arg in args:
            if arg == '-' and STDIN_ALLOWED:
                while True:
                    l = sys.stdin.readline()
                    if l == '':
                        break
                    else:
                        yield l.rstrip().lstrip()

            elif (os.path.exists(arg) and PATHS_ALLOWED) or \
                 (PATHS_ALLOWED and not CL_INPUT_ALLOWED) :
                # that is kind of ugly, bc I want an
                # exception here if command line 
                # arguments aren't allowed but the arg 
                # doesn't translate to a path name that works
                f = file(arg,'r')
                while True:
                    l = f.readline()
                    if l == '':
                        break
                    else:
                        yield l.rstrip().lstrip()

            elif CL_INPUT_ALLOWED :
                yield arg
            else:
                raise Exception

def batchList(iterable,batchSize=None,batchCount=None):
    """ return a list of lists representing batches of items from
    iterable. Either batchSize or batchCount should be an integer.
    """
    if batchCount == None and batchSize == None:
        raise ValueError("only batchSize or batchCount may be specified")
    elif batchCount != None and batchSize != None:
        raise ValueError("only batchSize or batchCount may be specified")

    rv=[]
    try:
        inList=list(iterable)
    except TypeError:
        # got non sequence type
        return [[iterable]]
        
    if batchSize != None:
        batchSize = int(batchSize)
    else:
        if len(inList)%batchCount==0:
            batchSize=len(inList)/batchCount
        else:
            batchSize=(len(inList)/batchCount) +1

    for start in range(0,len(inList),batchSize):
        rv.append(inList[start:start+batchSize])
    return rv
