#!/usr/local/bin/python
"""gridIt.py

Kael Fischer, 2008

Make a command into an SGE array job.

Usage:
    gridIt.py [-b|s -e -t SGE_Task_Spec | -h?] '<command and options>' arrayTaskInput_1 arrayTaskInput_2 ... arrayTaskInput_N

Options (must come before command):
    -b    limit job to blade queues
    -s    limit job to SecondLife queues
    -m    send you email when the job finishes or dies
    -t    override qsub -t option to only run a subset of tasks (e.g. "-t 32", means run only task 32)
    -h    print this help message
    -?    print this help message

Notes:
    Name.oJob_ID.Task_ID and Name.eJob_ID.Task_ID files are created with the output and error
    from each task.  Name is taken from the the command.

    The exact command run for each task is copied to the error stream for that task. 

    Multiple arguments per task can be quoted like this example:

    gridIt.py 'myProgram -x 0.1 -y 5' 'input1 output1' 'input2 output2' 'input3 output3'

Another Trivial Example:
    This should work, producing ls output in chronological and reverse chronological order.
    It runs on the grid, one command ls in each of 2 "slots." 
        gridIt.py ls -ltr -lt 

    This reproduces one but not the other:
        gridIt.py -t 2 ls -ltr -lt

Advanced Command Argument Substitution:
    Rather that appending the contents of arrayTaskInput to the end of the 'command and
    options', you can insert '%s' in the command and have the substitutions happen at those
    points with additional arguments being added to the end of the command.

    In this mode, spaces are used to determine argument boundaries.  IF YOU USE PATH AND FILE
    NAMES WITH SPACES, THIS FUNCTIONALITY IS NOT FOR YOU.

    Usage example:
        gridIt.py 'ls %s %s' '-ltr /tmp' '-l /tmp' '-1 /tmp'
    Is the same as:
        gridIt.py ls '-ltr /tmp' '-l /tmp' '-1 /tmp'
    And it's the same as:
        gridIt.py 'ls %s' '-ltr /tmp' '-l /tmp' '-1 /tmp'
    This is also the same:
        gridIt.py 'ls %s /tmp' -ltr -l -1

    BLAST example:
        gridIt.py -e 'blastall -p blastn -W %s -i' '8 pombe.fasta' '16 pombe.fasta' '10 unknown.fasta'  

        That runs 3 different word/query combinations through blastn, and emails you when they are done.

Bugs:
    Doing stupid things will break gridIt.py.  In particular, including spaces in arguments
    when '%s' substitution is being used will probably break unpredictably.  This is UNIX,
    don't use spaces in your path and file names. Get over it.
    

""" 
__version__ = "$Revision: 1.13 $".split()[1]


import os
import sys
import types


def __runJob(cmd,cArgs):


    subCt = cmd.count('%s')
    if subCt > 0:
        cArgs=cArgs.split()
        subArgs=tuple(cArgs[:subCt])
        subCmd=cmd % subArgs
        if len(cArgs) > subCt:
            sysCmd = subCmd + ' ' + ' '.join( cArgs[subCt:])
        else:
            sysCmd = subCmd
    else:
        sysCmd = "%s %s" % (cmd, cArgs) 
    
    print >> sys.stderr, "# gridIt Command: %s" % sysCmd
    sys.stderr.flush()
    return os.system(sysCmd)




if __name__ == "__main__":

    from getopt import getopt, GetoptError

    try:
        opts,args = getopt(sys.argv[1:],'mbst:h?')
    except GetoptError:
        print >> sys.stderr, "*unknown option found*"
        print >> sys.stderr, __doc__
        sys.exit(1)
        
    try:
        cmd = args[0]
        jobArgs = args[1:]
    except IndexError:
        cmd=[]

    if len(args) ==0 or len(jobArgs) == 0:
            print __doc__
            sys.exit(1)

    # defaults
    tValue = "1-%s"% len(jobArgs)
    limit = ''
    mail = 'n'

    for o,a in opts:
        if o == '-t':
            tValue=a
        elif o=='-b':
            limit='-l arch=fbsd-amd64'
        elif o =='-s':
            limit ='-l arch=lx24-x86'
        elif o=='-m':
            mail = 'ea'
        elif o in ('-h','-?'):
            print __doc__
            sys.exit(2)


    if 'SGE_TASK_ID' in os.environ:
        sys.exit(__runJob(cmd,jobArgs[int(os.environ['SGE_TASK_ID'])-1]))

    else:
        cmd = ("echo python \\'%s\\' | qsub -cwd -t %s -N %s %s -m %s" %
               ("\\' \\'".join(sys.argv),tValue,
                os.path.splitext(os.path.split(cmd.split()[0])[1])[0],limit,mail))
        sys.exit(os.system(cmd))

    
