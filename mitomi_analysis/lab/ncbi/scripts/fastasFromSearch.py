#/usr/local/bin/python
#
#
#
#
import urllib
import sys
import os.path
import xml.dom.minidom

_author_email_="kael@derisilab.ucsf.edu"
_tool_str_=os.path.split(__file__)[-1]

ncbiID="&email=%s&tool=%s" % tuple([urllib.quote_plus(x) for x in (_author_email_,_tool_str_)])

BATCHSIZE=100

sURL="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=%s&term=%s&usehistory=y"
fURL="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=%s"

##############################
# these control what you get #
retType='fasta'              
sTerm="txid10239[Organism:exp]"
eDB="NucCore"
#                            #
##############################


sDoc=xml.dom.minidom.parse(urllib.urlopen(sURL%(eDB,urllib.quote_plus(sTerm))+ncbiID))

count=sDoc.getElementsByTagName('Count')[0].firstChild.data
count=int(count)
queryKey=sDoc.getElementsByTagName('QueryKey')[0].firstChild.data
webEnv=sDoc.getElementsByTagName('WebEnv')[0].firstChild.data

i=1
while i <= count:
    fQry = fURL%(eDB,) + "&WebEnv=%s&query_key=%s"%(webEnv,queryKey) + "&retmax=%s&retstart=%s" %(BATCHSIZE,i) + '&rettype=%s' %(retType) + ncbiID
    i=i+BATCHSIZE

    sys.stdout.write(urllib.urlopen(fQry).read())


sys.stdout.flush()

