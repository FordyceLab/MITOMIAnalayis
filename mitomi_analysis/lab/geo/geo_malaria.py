#!/usr/local/bin/python2.2
#
# 

import os
from . import MalariaUtils
import MySQLdb

####  Malaria Specific Globals
YEAST = "S.cervisiae"
PLASMODIUM = "P. falciparum"
hostName = "malaria.ucsf.edu"
dbName = "OLIGO"
option_file = os.environ["HOME"] + "/scripts/" + ".my.cnf"
MAX_ENERGY = -35  # oligos with an energy < MAX_ENERGY kJ will be considered hits
SEQ_SQL = """SELECT os.oligoid, os.DNA, oo.targetid, oo.energy
           FROM OLIGO_SEQ os LEFT JOIN OLIGO_ORF oo ON os.oligoid=oo.oligoid
           WHERE os.oligoid=%s;"""


class UnknownColumnIdentifier (Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

###### PLUGIN API ####################
def getSpotIterator(array, headerNames):
	return MalariaSpotIterator(array, headerNames)


def getLongID(spot):
    """So we always use the same long ID between all file types, here's how we get a long
       		ID from a spot record."""
    return spot["ID"] + "_" + str(spot["Element_Occurrence"])



def parseExistingPlatform(platformFilename):
    """Takes an existing platform file and creates a mapping of the unique id in the
      platform file to a unique id that can be created based only on the spot record.
      This method isn't necessary for malaria because the unique id in the platform can be created from 
      the spot record already."""
    pass


######## HELPER CLASSES/FUNCTIONS #############

class MalariaSpotIterator:
	def __init__ (self, array, headerNames):
		# connect to OLIGO
		self.conn = MySQLdb.connect(host=hostName, db=dbName, read_default_file=option_file ) 
		self.cursor = self.conn.cursor()

    		# pull out the first spotset
		spotSet = array.result().spots()  
		self.spots = spotSet.__iter__()
		self.headerNames = headerNames

	def __iter__(self):
		return self

	def __next__(self):
		spot = next(self.spots)
		oligoid = spot["ID"]
        	longID = getLongID(spot)

		names, seq = getNamesAndSeqFromOLIGO(oligoid, self.cursor)
        	if oligoid.startswith("Y_"):
            		species = YEAST
            		# for yeast, use the oligoid (without the "Y_") as the name
            		names = oligoid[2:]
        	elif oligoid == "EMPTY":
            		species = ""
        	else:
            		species = PLASMODIUM

		# now build up the array in the order the user wants it
		retList = []
		for column in self.headerNames:
			if column == "ID":
				retList.append(longID)
			elif column == "NAME":
				retList.append(names)
			elif column == "SPECIES":
				retList.append(species)
			elif column == "SEQUENCE":
				retList.append(seq)
			else:
				raise UnknownColumnIdentifier("Unknown column identifier for spots: " + column)

		return retList


def getNamesAndSeqFromOLIGO(oligoid, cursor):
    """Returns (Name, Sequence) for the oligoID from the OLIGO database.

       Name may be a comma separated string of names if the oligo hits more than one
       ORF."""

    # first, the ID from Nomad may need to be adjusted for OLIGO
    oligo_oligoid = MalariaUtils.NomadIdToOligoid(oligoid)
    
    cursor.execute(SEQ_SQL, (oligo_oligoid,))

    row = cursor.fetchone()

    # HACK CODE: for some yeast oligos, the ending character is a "1" in NOMAD and an "I" in OLIGO
    if not row and oligo_oligoid.startswith("Y_"):
        new_oligoid = oligo_oligoid[:-1] + "I"
        cursor.execute(SEQ_SQL, (new_oligoid,))
        row = cursor.fetchone()
    
    names = []
    sequence = ""

    if not row and oligoid.find("EMPTY") < 0:
        print("Unable to find oligoid:", oligoid, ".  Tried", oligo_oligoid)

    used_names = []  # I'm sure there's a way to do this in SQL, but we'll do it here for now
                     # If an oligo hits the same target in multiple places, we only want to list it once
    while row:
	if len(sequence) == 0:
            sequence = row[1]
        targetid = row[2]
        if targetid not in used_names:
            used_names.append(targetid)
            energy = row[3]
            if not targetid is None and energy < MAX_ENERGY:
                names.append(targetid)
            
        row = cursor.fetchone()

    return ", ".join(names), sequence


