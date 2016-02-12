#!/usr/local/bin/python -u
#
# retreive info about oligos from the viroinfo database
# Kael Fischer
#
# 	$Id: oInfo.py,v 1.3 2008/02/07 00:38:39 kael Exp $	
#
import sys,string,os.path

from getopt import getopt

import utils
import sequence,sequence.fasta
from viroinfo import oligo



def usage():
    return """Usage: %s [options] <Unique IDs>

Description:
    Print information about oligos in the viro database.  By
    default a FASTA representation is printed.  Failed lookups
    are reported on stderr (also see Exit Status below).

Arguments:
    User must specify the UIDs of interest.  The can be specified in any of
    the following ways:
    \t1. Separated by whitespace on the command line.
    \t2. As a path of a file that has one UID per line.
    \t3. On stdin with UIDs separated by newlines.
    \t   Use '-' to indicate stdin (or if no arguments
    \t   other than options are given, stdin will be
    \t   read by default).

Options:
    \t-h\tprint this message.
    \t-t\tuse tab delimited format rather than FASTA.
    \t-H\tprint a header row for tab delimeted format.
    \t-U\tdo NOT print the UIDs in the first column.
    \t-i\tprint taxID.
    \t-n\tprint taxons scientific name.
    \t-r\tprint rank.
    \t-k\tprint rank number.
    \t-d\tprint design set designation.
    \t-s\tprint sequence.
    \t-a\tusing tab delimited format, print ALL of the above.
    \t-w\toutput output format as webpage.
    \t-C\tuse CGI interface uids are taken from a comma seperated
    \t\tlist of uids.

Exit Status:
      0 - all oligos found
      1 - no oligos processed (e.g. help requested with -h)
      2 - usage error
  other - 10 + (# of oligos that were NOT found)
          (Note that depending on the shell in use this my be unreliable
          for numbers larger than 254) 
""" % sys.argv[0]

failureCt = 0

minIdentities = 35

# output formats
FASTA = True
TAB_DELIM = False
HTML_OUTPUT = False

# input flags
USE_CGI = False

#fields
D_HEADER = False
D_UID = True
D_TAXID = False
D_TAXON = False
D_RANK = False
D_RANK_NUMBER = False
D_DESIGN = False
D_SEQUENCE = False
D_ALL = False



if os.path.split(sys.argv[-1])[-1] == 'oInfo_cgi.py':
    import cgitb; cgitb.enable()
    USE_CGI = True
    HTML_OUTPUT = True
    D_ALL = True
    HEADER_ROW_DONE = False
else:

    try:
        optlist, args = getopt(sys.argv[1:],'taUinrkdhsHwC')
    except:
        print
        print usage()
        sys.exit(2)

    for (opt,opt_arg) in optlist:
        if opt == '-h':
                print
                print usage()
                sys.exit(1)
        elif opt == '-t':
            FASTA =  False
            TAB_DELIM = True
        elif opt == '-H':
            D_HEADER = True
        elif opt == '-U':
            D_UID = False
        elif opt == '-i':
            D_TAXID = True
        elif opt == '-n':
            D_TAXON = True
        elif opt == '-r':
            D_RANK = True
        elif opt == '-k':
            D_RANK_NUMBER = True
        elif opt == '-d':
            D_DESIGN = True
        elif opt == '-s':
            D_SEQUENCE = True
        elif opt == '-a':
            D_ALL = True
        elif opt == '-w':
            HTML_OUTPUT = True
        elif opt == '-C':
            USE_CGI = True
        else:
            print
            print usage()
            sys.exit(2)



#
# Final formatting options
#
if D_ALL:
    FASTA = False
    TAB_DELIM = True
    D_UID = True
    D_TAXID = True
    D_TAXON = True
    D_RANK = True
    D_RANK_NUMBER = True
    D_DESIGN = True
    D_SEQUENCE = True


D_DESIGN=False

if HTML_OUTPUT:
    FASTA = False
    TAB_DELIM = False
    cmdArgs = ()
   
else:
    cmdArgs = args
    if len(cmdArgs) == 0:
        cmdArgs = ['-']

if HTML_OUTPUT:
    HEADER_ROW_DONE = False

for uid in  utils.readArgsOrFiles(cmdArgs,CGI_OVERRIDE=USE_CGI,
                                  cgiParam='OligosAll',extraCGIDelimChars=','):
    try:
        o = oligo.Oligo(uid)
        s = o.Sequence
        oRec=sequence.fasta.Record(title=o.Uid,sequence=s,colwidth=70)
        
    except:
        failureCt += 1
        if not HTML_OUTPUT:
            sys.stderr.write(uid + " not found in database\n")
    
    fields = []
    fastaFields =[]
    labels = []
    
    try:
        o.lct = o.v4Assignment()
    except:
        o.lct = None
    
    if D_UID:
        fields.append(uid)
        labels.append('UID')
        
    if D_TAXID:
        try:
            lctI = str(o.lct.NCBI_TaxID)
        except:
            lctI = "not found"
              
        fields.append(lctI)
        oRec.appendField('taxid',lctI)
        labels.append('Taxon ID')
         
    if D_TAXON:
        try:
            lctI = str(o.lct.Name)
        except:
            lctI = "not found"
              
        fields.append(lctI)
        oRec.appendField('tax name',lctI)
        labels.append('Taxon Name')
        
    if D_RANK:
        try:
            lctI =str(o.lct.rank())
        except:
            lctI= "not found"
        fields.append(lctI)
        oRec.appendField('rank',lctI)
        labels.append('Taxon Rank')
         
    if D_RANK_NUMBER:
        try:
            lctI = str(o.lct.rankIndex())
        except:
            lctI = "not found"
              
                         

        fields.append(lctI)
        oRec.appendField('rank number',lctI)
        labels.append('Rank Number')
        
    if D_DESIGN:
        dStr = ''
        try:
            methods = o.method.split(',')
            if 'ViroBlast' in methods:
               dStr = 'ViroBlast'
            elif '0.5Filter' in methods:
                dStr = 'ViroTax'
            else:
                dStr = 'unknown'
        finally:
            fields.append(dStr)
            oRec.appendField('design method',str(dStr))
            labels.append('Design Method')

    if D_SEQUENCE:
        fields.append(o.Sequence)
        labels.append('Sequence')

    if FASTA:
        print oRec
    elif TAB_DELIM:
        if D_HEADER:
            print string.join(labels,'\t')
            D_HEADER = False
        print string.join(fields,'\t')        

    elif HTML_OUTPUT:
        if not HEADER_ROW_DONE:
            print """Content-type: text/html\n

<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
<title>Virochip Oligo Details</title>
</head>
<body>
<table>
<tr>
"""
        for l in labels:
            print """<td>%s</td>""" % (l)
            print """</tr>"""
            HEADER_ROW_DONE = True
        
        print """<tr>"""
        for f in fields:
            print """<td>%s</td>""" % (f)
        print """</tr>"""

          
if failureCt == 0:
    sys.exit(0)
else:
    sys.exit(failureCt + 10)

    



