###########################################
#
# Interface to the Gi_Info table
# Includes functions for updating and
# accessing it.
#
# Dale Webster
# 03/03/2008
#
###########################################

import os, sys, re
import time
import urllib.request, urllib.parse, urllib.error

from utils import unique
from kdbom import kdbom

from .__init__ import ncbiDB, throttleRequest, esummary,getTaxa

## NCBI_GI_INFO_URL = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=CoreNucleotide"
## MAX_GIS_PER_REQUEST = 100

class GiInfoAmbiguityError (Exception):
    pass


class GiInfo(kdbom.VersionedKSqlObject):
    """Gi Info Object caches information on GI numbers pulled down
    from NCBI.

    To lookup by Gi you must use GiInfo(Gi=########), because the use of an bare integer
    in kdbom table lookups retrieves on primary key.

    This is a versioned class/table. Retrevial of an object from the database
    returns the most recent version by default.
    """
    _table = ncbiDB.Gi_Info


def cacheBlastSearch( search ):
    """Given a Blast_Results.Search object, finds all of the NCBI
    sequences hit in that search and caches them in the Gi_Info
    table."""
    #TODO: Broken??  Looking in Wrong Database?? [kf]
    giList = {}

    sql = """SELECT Sequence.Name FROM
                Sequence
                LEFT JOIN Hit ON Sequence.Sequence_ID = Hit.Subject_Sequence_ID
                LEFT JOIN Search ON Hit.Search_ID = Search.Search_ID
            WHERE Search.Search_ID=%d""" % ( search.ID() )

    nameList = [x[0] for x in ncbiDB.fetchall( sql )]

    for name in nameList:
        hasGi = re.search("gi\|(\d+)\|", name)
        if hasGi:
            giList[ hasGi.group(1) ] = 1

    fastHitGiInfo( list(map(int, list(giList.keys()) )) )
    return
    

def getGi( gi ):
    """Given a single GI, returns the corresponding GiInfo object
    if it exists, else returns None."""
    try:
        return GiInfo(Gi=gi)
    except:
        return None
    

def cacheGis( giList ):
    """Given a list of GI numbers, looks up their
    info in NCBI and populates the Gi_Info database
    with the results. For existing GI numbers, it
    will insert new records representing the current
    information"""

    success = False

    giInfo = esummary( giList, "CoreNucleotide" )

    taxIDList = unique([ x["TaxId"] for x in giInfo])
    lineageInfo = lineage(taxIDList)
    

    toInsert = []
    for gi in giInfo:
        myData = [ giInfo[gi]["Title"],
                   giInfo[gi]["TaxId"],
                   giInfo[gi]["Length"] ]
        toInsert.append( tuple( [ int(gi) ] + myData + myData ) )

    ncbiDB.executemany("INSERT INTO Gi_Info SET Gi=%s, Title=%s, Tax_ID=%s, Length=%s ON DUPLICATE KEY UPDATE Title=%s, Tax_ID=%s, Length=%s;", toInsert )

    ncbiDB.commit()


def checkMissingGis(giList):
    """Returns a list of gis in giList for which there is no data in Gi_Info.
    """

    try:
        db = GiInfo.db()

        # make a fast memory table for the gi list
        db.execute(
            """CREATE TEMPORARY TABLE `Tmp_Gi` (
            `Gi` int(11) NOT NULL,
            PRIMARY KEY(`Gi`)
            )
            ENGINE=HEAP""")

        db.executemany(
            """INSERT IGNORE INTO Tmp_Gi (Gi) VALUES (%s)""",
            [[int(gi)] for gi in giList ])

        # get the gis that dont match 
        rows = db.fetchall(
            """SELECT T.`Gi` FROM Tmp_Gi AS T
            LEFT JOIN `%s`.`Gi_Info` AS G
            ON T.Gi = G.Gi
            Where G.GI_Info_ID IS NULL
            """ %(db.name))
    finally:
        db.execute(
            """DROP TEMPORARY TABLE `Tmp_Gi`"""
            )
    
    return [r[0] for r in rows]


def cacheMissingGis(giList):
    """Inset Gi_Info data for Gis not in table.
    """
    giList=checkMissingGis(giList)
    if len(giList) > 0:
        insertGiInfo(giList)

def insertGiInfo(giList,dontTouchDB=False):
    """insert new rows with current NCBI data GiInfo
    for gis in giList.

    Only 'live' NCBI records will be updated.
    Dict of Failures is returned {status1:[gi,gi],...}
    """
    gbSummaries=esummary("CoreNucleotide",giList)

    taxIDs = unique([int(r['TaxId']) for r in list(gbSummaries.values()) if int(r['TaxId'])>0])
    taxaList=getTaxa(taxIDs)
    taxa={}
    for t in taxaList:
        taxa[t.taxID]=t


    failures={}
    rows = []
    liveGis = []
    for gi in list(gbSummaries.keys()):
        gis = gbSummaries[gi]
        try:
            status = gis['Status']
        except:
            if 'no status' not in failures:
                failures['no status'] = []
            failures['no status'].append(gi)
            continue

        if status == 'live':
            liveGis.append(gi)
        else:
            if status not in failures:
                failures[status] = []
            failures[status].append(gi)
            continue
        try:
            title = gis['Title'][:255]
        except TypeError:
            title = None
        taxID = int(gis['TaxId'])
        try:
            f = taxa[taxID].family()[0]
        except (TypeError,KeyError):
            f=None
        try:
            g=taxa[taxID].genus()[0]
        except (TypeError,KeyError):
            g=None
        try:
            s=taxa[taxID].species()[0]
        except (TypeError,KeyError):
            s=None

        if None in (f,g,s):
            matches = GiInfo._table(Gi=int(gi),
                                    Title=title,
                                    Tax_ID=taxID,
                                    Length=int(gis['Length']),
                                    Family_Tax_ID =f,
                                    Genus_Tax_ID=g,
                                    Species_Tax_ID=s)
            if len(matches) == 1:
                matches[0].touchTimestamp()
                continue
            if len(matches) > 1:
                raise GiInfoAmbiguityError("failed updating timestamp - more that one match")

        row = (int(gi),
               title,
               taxID,
               int(gis['Length']),
               f,
               g,
               s )
        rows.append(row)

    
##     # this is broken in MySQLdb 1.2.1 - Fixed in 1.2.2
##     GiInfo._table.insertMany(('Gi','Title','Tax_ID','Length',
##                               'Family_Tax_ID','Genus_Tax_ID',
##                               'Species_Tax_ID'),rows,
##                              onDupKeyLiteral="ON DUPLICATE KEY UPDATE Timestamp=NOW()")

        # so we have to do it one at a time
    for row in rows:
        if dontTouchDB:
            print(row)

        else:
            GiInfo._table.insertMany(('Gi','Title','Tax_ID','Length',
                                      'Family_Tax_ID','Genus_Tax_ID',
                                      'Species_Tax_ID'),(row,),
                                     onDupKeyLiteral="ON DUPLICATE KEY UPDATE Timestamp=NOW()")
            
    return failures

def cacheIfNecessary( giList ):
    """This function takes in a list of GIs. It quickly checks with a single SQL call
    whether or not we have info for ALL of these GIs. If we do not, then it updates them
    ALL. If we do have info on all of them, it returns."""

    #TODO: this function calls lookupGiInfo which does not exist
    # 

##     if len(giList) == 0:
##         return

##     sql = "SELECT Gi, COUNT(*) FROM Gi_Info WHERE"
##     orClause = " OR ".join( map( lambda x: "Gi=%d" % (int(x)), giList ) )

##     cachedList = ncbiDB.fetchall( "%s %s GROUP BY Gi;" % (sql, orClause) )

##     if len( cachedList ) < len( giList ):
##         lookupGiInfo( giList )

##     return
    pass
