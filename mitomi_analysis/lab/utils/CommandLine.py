#!/usr/local/bin/python

"""
This class was designed to remove some of the repetetiveness from re-writing the same old command-line processing in every python script I write.

It is meant to require fewer lines, and to be a bit moe readable, during the extraction of information from the user command line. It should also increase the readability of the Usage: messages, as well as standardizing them for all of my scripts.

The class should be used like this:

---
cl = CommandLine()

inFile = cl.requiredArg( "Input_Filename" )
outFile = cl.requiredArg( "Output_Filename", "-o" )
count = cl.optionalArg( "Desired_Count", 10, "-c" )
verbose = cl.optionalFlag( "-v", "Verbose" )
otherFiles = cl.infiniteArg( "Other_Files" )

cl.execute() # dies here if something goes wrong.
---

If the user screws up in this case, she sees this:

---
Usage: script.py Input_Filename -o Output_Filename [-c Desired_Count] Other_Files...
defaults:
    Desired_Count = 10
---

NOTE: All arguments should be requested in the proper order.


Author: Dale Webster, March 8, 2006
"""

import sys

class CommandLine:
    """Simplifies the process of extracting information from the user via the command line."""

    def __init__( self ):
        """Extracts the command-line information and waits for further input"""

        self.usage = "Usage: " + sys.argv[0]
        self.defaults = []
        self.failed = 0

        self.args = []
        for i in range( 1, len(sys.argv) ):
            self.args.append( sys.argv[i] )


    def __repr__( self ):
        """Returns the usage line constructed so far"""
        return self.usage

    def __str__( self ):
        """Returns the usage line constructed so far"""
        return self.usage

    def requiredArg( self, optionName, flag="" ):
        """Requests and defines a required argument. OptionName is required and used in the Usage line. An optional flag may be specified. (ie -o)."""

        if flag != "":
            self.usage = self.usage + " " + flag
        self.usage = self.usage + " " + optionName

        if len( self.args ) <= 0:
            return self.fail()

        if flag == "":
            return self.args.pop(0)

        else: # flag defined
            for i in range( len(self.args) - 1 ):
                if self.args[i] == flag:
                    self.args.pop(i)
                    return self.args.pop(i)

            # If we get here they didnt provide a required flag.
            return self.fail()

    def optionalArg( self, optionName, default, flag="" ):
        """Requests and defines an optional argument. OptionName is required and used in the Usage line. An optional flag may be specified. (ie -o). If the arg is not found, returns the default value."""

        if flag != "":
            self.usage = self.usage + " [" + flag + " " + optionName + "]"
        else:
                        self.usage = self.usage + " [" + optionName + "]"

        self.defaults.append( optionName + " = " + str(default) )

        if len( self.args ) <= 0:
            return default

        if flag == "":
            return self.args.pop(0)

        else: # flag defined
            for i in range( len(self.args) - 1 ):
                if self.args[i] == flag:
                    self.args.pop(i)
                    return self.args.pop(i)

            # If we get here they didnt provide a required flag.
            return default

    def infiniteArg( self, optionName ):
        """Requests and defines an infinite argument. This is basically an argument list of any size. Must be the last argument of course. Returns an array."""

        self.usage = self.usage + " " + optionName + "..."

        argList = []
        while len(self.args) > 0:
            argList.append( self.args.pop(0) )

        return argList

    def optionalFlag( self, flag, description=None ):
        """Allows for optional flags (ie -h). Returns True if the flag exists, else False.
        Description goes into the usage message if specified."""

        if description:
            description = " (" + description + ")"
        else:
            description = ""

        self.usage += " [%s]" % ( flag )
        self.defaults.append( "%s%s" % ( flag, description ) )

        for i in range( len(self.args) ):
            if self.args[i] == flag:
                self.args.pop(i)
                return True

        # No flag.
        return False

    def fail( self ):
        """Internal method used to signal a failure at some point."""
        self.failed = 1

    def execute( self ):
        """Basically this function just checks to see if any of the required arguments were not found. If that is the case, it outputs the usage method and exits the script."""
        if self.failed:
            print self.usage + "\n"
            for default in self.defaults:
                print default
            sys.exit(0)
