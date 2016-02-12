#/usr/local/bin/python
#
#
#
#
import urllib
import sys
import os.path
import xml.dom.minidom

from ncbi import *

from utils import readArgsOrFiles

retType = 'fasta'

def fetchBatchByUI(batch,eDB,retType):
     fQry = fURL%(eDB) + '&rettype=%s' %(retType) + ncbiID+'&id='+','.join(batch)
     sys.stdout.write(urllib.urlopen(fQry).read())
     sys.stdout.flush()

eDB = 'NucCore'

fURL="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=%s"

gis = readArgsOrFiles(sys.argv[1:])
#print list(gis)

#print utils.batchList(gis,BATCHSIZE)

for batch in  utils.batchList(gis,BATCHSIZE):
    #print batch
    fetchBatchByUI(batch,eDB,retType)






