#!/usr/local/bin/python2.2
#
# 

from .exceptions import *

idMap = {}

###### PLUGIN API ####################
def getSpotIterator(array, headerNames):
	return []


def getLongID(spot):
    """So we always use the same long ID between all file types, here's
    how we get a long ID from a spot record.
    """
    try:
        key = spot["ID"] + ":" + str(spot["Element_Occurrence"])
    except:
        raise PluginError("\nSpot lookup failed.\nSpot String:\n%s\n" %
                            (str(spot)))
    return idMap[key]



def parseExistingPlatform(platformFilename,idCol=0,keyCol=1):
    """Takes an existing platform file and creates a mapping of the
    unique id in the platform file to a unique id that can be created
    based only on the spot record.  This method isn't necessary if the
    unique id in the platform can be created from  the spot record
    already."""

    global idMap
    try:
        pFile = file(platformFilename)
    except:
        # better exception?
        raise

    IDFOUND=False
    idCount = 0
    for line in pFile:
        if IDFOUND:
            if line.startswith("!"):
                break
            fields = line.split('\t')
            idMap[fields[keyCol]]=fields[idCol]
            idCount+=1
        else:
            if line.startswith("ID\t"):
                IDFOUND=True

    return idCount
    
    

class VirochipSpotIterator:
    """An iterator for spots on Virochip arrays using the GPL3429 platform file.
    -TO BE VRITTEN-
    """

    def __init__(self,array,headerNames):
        """I take a NOMAD array object and a list of header names"""
        pass
