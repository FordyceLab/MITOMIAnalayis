#!/usr/local/bin/python
#
# <program name>
# <author name(s)>
# <date>
#
# <other stuff - like what code program depends on, kdbom, blast, etc>
#
# The usage message, below,  should show the name of the program,
# the arguments the program requires and any options.
#
# PUT THE USAGE MESSAGE RIGHT BELOW HERE. 
#
"""USAGE
        script_template.py [-h?]
        
        OPTIONS
                -h      print help message
                -?
"""
__version__ = "$Revision: 1.7 $".split(':')[-1].strip(' $') # don't edit this line.
                                                            # cvs will set it.

# modules for command line handling
import sys
import getopt

# IMPORT OTHER STANDARD LIBRARY MODULES BELOW HERE
# e.g. "import math"

# IMPORT OTHER LAB MODULES BELOW
# e.g. "from lab import sequence"

def main(args=None):
    # This runs only if the program is run form the command line
    # you can import this 'program' as a module, to reuse the
    # functions in another program or to debug in the python
    # interpreter.

    ## SET DEFAULT RUNTIME VALUES HERE
    # e.g. outPath = '/tmp'

    # parse command line options like '-h'
    # see pydoc getopt for option formats
    shortOptions="h?"  ## SET THAT
    longOptions = []   ## SET THAT 
    try:
        opts, args = getopt.getopt(args, shortOptions, longOptions)
    except getopt.error, msg:
        # there is an unknown option!
            print msg      # prints the option error
            print __doc__  # prints the usage message from the top
            return (-2)

    # process options

    # use option processing to 
    # change the values of the
    # defaults you set at the top of "main"
    # e.g. you might let someone set the value of outPath
    # using the -o option on the command line
    for option,optionArg in opts:
        if option=='-h' or option=='-?':
            print __doc__
            return(0)     # '0' = no error in UNIX
        else:
            print "%s option not implemented" % option

    # check arguments
    # correct #, etc
    # the remaining command line arguments (after the
    # option processing) are in 'args'

    minArgs = 0 ## SET THAT
    maxArgs = 0 ## SET THAT
    
    argProblem = False
    if len(args) > maxArgs:
        print "Wrong number of arguments: %s found (expected max of %s)" % (lan(args),
                                                                            maxArgs)
        argProblem = True
    elif len(args) < minArgs:
        print "Wrong number of arguments: %s found (expected min of %s)" % (len(args),
                                                                            minArgs)
        argProblem = True
    # put in other argument checks here
    # print help set argProbem if there is a problem

    ## PUT MORE ARGUMENT CHECKING HERE

    if argProblem:
        print __doc__
        return(-1)



    ## THIS IS ALL YOU AFTER HERE!
    # then call the functions that
    # do the work
    somethingUsefull(args)
    
    return(0)  # we did it!


def somethingUsefull(args):
    somethingImportant = 1
    

####### LEAVE THIS ALONE ###########
# If run directly as a program
# this block calls the main function.
# 
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# end program - beep!
