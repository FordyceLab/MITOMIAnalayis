#!/usr/local/bin/python
#
# script_example.py
# Kael Fischer
# July 2007
#
# This is the 'Little Indians" problem in the script_template format.
#
# The usage message should show the name of the program (sys.argv[0]),
# the argument the program requires and any options.
#
# Put the usage message right below here.
#
"""USAGE
        script_example.py [-h?I] [adjective plural1 plural2 ]

        Print a simple poem.
        
        OPTIONS
                -h      print help message
                -?
                -I      Indian boys version (no arguments allowed)
"""
__version__ = "$Revision: 1.4 $".split(':')[-1].strip(' $') # don't edit this line.
                                                            # cvs will set it.

# modules for command line handling
import sys
import getopt

def main(args=None):
    # This runs only if the program is run for the command line

    # set default runtime values here
    # default is _not_ Indians
    indians = False


    
    # parse command line options like '-h'
    shortOptions="h?I"  # see pydoc getopt for option formats
    longOptions = []
    try:
        optlist, args = getopt.getopt(args, shortOptions, longOptions)
    except getopt.error as msg:
        # there is an unknown option!
            print(msg)      # prints the option error
            print(__doc__)  # prints the usage message from the top
            return (-2)

    # process options
    for option,optionArg in optlist:
        if option=='-h' or option=='-?':
            print(__doc__)
            return(0)     # '0' = no error in UNIX
        elif option == '-I':
            indians = True
        else:
            print("%s option not implemented" % option)

    # check arguments
    # correct #, etc
    # the remaining command line agruments (after the
    # option processing) are in 'args'
    minArgs = 0
    maxArgs = 3
    argProblem = False
    if len(args) > maxArgs:
        print("Wrong number of arguments: %s found (expected max of %s)" % (len(args),
                                                                            maxArgs))
        argProblem = True
    elif len(args) < minArgs:
        print("Wrong number of arguments: %s found (expected min of %s)" % (len(args),
                                                                            minArgs))
        argProblem = True

    if indians and len (args) > 0 :
        print("Sorry no arguments if you use -I.") 
        argProblem = True
    if not indians and len(args) != 3:
        print("You must specifiy 3 arguments or -I.") 
        argProblem = True
        
    if argProblem:
        print(__doc__)
        return(-1)


    # print poem
    if indians:
        print(poem("little","Indians","boys"))
    else:
        print(poem(args[0],args[1],args[2]))


    return(0)  # we did it!


def poem(adjective, pluralNoun1, pluralNoun2):
    """Returns a poem.
    """
    # make a list to hold bits of the poem
    strings=[]
    for boyNumber in (1,2,3,4,5,6,7,8,9,10):
        # append poem bits to the list 
        strings.append("%s %s" %(boyNumber,adjective))
        if boyNumber % 3 == 0:
            strings.append(" %s.\n" % (pluralNoun1))
        elif boyNumber == 10:
            strings.append(" %s %s." % (pluralNoun1[:-1],pluralNoun2))
        else:
            strings.append(", ")
            
    # return the bits, joined together in to a magnificent opus! 
    return ''.join(strings)


#
# If run directly as a program
# this block calls the main function.
#
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
