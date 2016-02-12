"""BLAST utilities
BLAST result storage and retrieval.
"""

import commands
import os
import os.path
import datetime
from types import *

from __init__ import *
from fasta import *
from blastNoSQL import *

from kdbom import kdbom

try:
    blastDB = kdbom.db(host='derisi-b14',
                       db='Blast_Results')

except:
    try:
        blastDB =  kdbom.db(host='derisi-b14',
                            db='Blast_Results',
                            user='readonly',
                            passwd='')
    except:
        print 'blast mysqldb not found'

class Db (kdbom.KSqlObject):
    """
    """
    _table = blastDB.Db

    def sequenceMap(self):
        return FastaFile(self.Fasta_File_ID).sequenceMap()


class FastaFile (kdbom.KSqlObject):
    """
    """
    _table = blastDB.Fasta_File

    def sequenceMap(self):
        """retuns a dictionary of these - m8Name:Sequence_ID,
        for all Sequences in a FastaFile or Db.
        """
        st = Sequence._table
        return st.valueIdDict(st.Name,Fasta_File_ID=self.Fasta_File_ID)
        

    def insertSequences(self,chunkSize=1):
        def recCb(rec):
            return (self.ID(),
                    rec.m8name(),
                    rec.m8annotation(),
                    len(rec.sequence),
                    rec.gi(),
                    rec.sequence)

        track=0 # debug

        recs=[]
        for rec in FastaIterator(file(self.Filename)):
            recs.append(rec)

            if len(recs) == chunkSize:
                #print len(recs)
                self._db.Sequence.insertMany(
                    ('Fasta_File_ID','Name','Annotation',
                     'Length','Gi','Sequence_Text'),recs,
                    recCb,chunkSize=chunkSize
                    )
                track += len(recs)
                recs=[]
        #print len(recs)
        if len(recs) > 0:
            self._db.Sequence.insertMany(
                ('Fasta_File_ID','Name','Annotation',
                 'Length','Gi','Sequence_Text'),recs,
                recCb,chunkSize=chunkSize
                )
            track+= len(recs)
        self._db.commit()

        #print track
        #print Sequence._table.count(Fasta_File_ID=self.ID())



class Search (kdbom.KSqlObject):
    """
    """
    _table = blastDB.Search

    def __post_init__(self):
        self.__sMap=None

    def hitMap(self,requery=False):
        """retuns a dictionary of these - (Query_Sequence_ID,Subject_Sequence_ID):Hit_ID,
        for all Hit in a search.
        """
        hitRows = blastDB.Hit({"Search_ID":self.ID()},
                              selectExpr="Hit_ID,Query_Sequence_ID,Subject_Sequence_ID")
        return dict(map(lambda x: ((x[1],x[2]),x[0]),hitRows))

    def hitSequenceNameMap(self):
         """retuns a dictionary of these - (Query m8Name ,Subject m8Name):Hit_ID,
         for all Hit in a search.
         """
         sMap = dict(zip(self.sequenceMap().values(),
                         self.sequenceMap().keys()))
         

         hitRows = blastDB.Hit({"Search_ID":self.ID()},
                               selectExpr="Hit_ID,Query_Sequence_ID,Subject_Sequence_ID")
         return dict(map(lambda x: ((sMap[x[1]],sMap[x[2]]),x[0]),hitRows))
        
       

    def sequenceMap(self,requery=False):
        """retuns a dictionary of these - m8Name:Sequence_ID,
        for all Sequences in a search.
        """

        if requery or self.__sMap == None:
            self.__sMap = dict(FastaFile(self.Fasta_File_ID).sequenceMap().items() +
                               Db(self.Db_ID).sequenceMap().items())
        return self.__sMap

class Sequence (kdbom.KSqlObject):
    """
    """
    _table = blastDB.Sequence

    def fastaRecord(self):
        return Record(title=self.Name,
                      sequence=self.Sequence_Text)
    

    def hsps(self,search,whereClause=None):
        """Return a generator of Hsp Objects.
        There whereClause may be specified for maximum
        flexability. e.g.:
        seq1.hsps("E < 1e-20")
        """

        if whereClause == None:
            whereClause = """WHERE Hit Search_ID = %s
            AND Hit.Query_Sequence_ID=%s""" % (search.ID(),self.ID())
        else:
            whereClause = """WHERE Hit Search_ID = %s
            AND Hit.Query_Sequence_ID=%s
            AND %s""" % (search.ID(),self.ID(),whereClause) 


        return Hsp.generator(
            """SELECT Hsp_ID from Hit
            LEFT JOIN Hsp ON Hit.Hit_ID = Hsp.Hit_ID
            %s""" % whereClause )

        


class Hit (kdbom.KSqlObject):
    """Represents a Blast Hit"""
    
    _table = blastDB.Hit

    def __iter__ (self):
        """Iterator for all HSPs in the Hit"""
        return kdbom.ksqlobject_generator(
            Hsp, ("""SELECT Hsp_ID FROM Hsp WHERE Hit_ID=%s"""
                  % blastDB.escape(self.ID())))

    def _dropHsps(self):
        """Delete HSPs from database. 
        """
        return self._db.execute(
            """DELETE FROM Hsp WHERE Hit_ID=%s""",self.ID())

    def hspCount( self ):
        """Returns the number of recorded Hsps for this Hit."""
        return self._db.Hsp.count(Hit_ID=self.ID())

    def processHsps( self, hspList, maxHsp ):
        """Given a list of Hsp tuples, minus the subject and query,
        generates the correct Hsp objects."""

        hspList = hspList[:maxHsp]
        self._dropHsps()
        self._db.executemany(
            """INSERT IGNORE INTO Hsp
            (Hit_ID,Ident,Length,Gaps,Mismatch,
            Q_Start,Q_End,T_Start,T_End,E,Score)
            VALUES (%s, %%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,)
            """ % self.ID(),hspList)
        
        self.computeHspID()


    def computeHspID( self ):
        """Determines the Hsp with the highest bit score and stores its
        ID in Hsp_ID."""
    
        self.Hsp_ID = self._db.fetchall(
            """SELECT Hsp_ID FROM Hsp WHERE Hit_ID=%S
            ORDER BY SCORE DESC LIMIT 1
            """ % self.ID())[0][0]
        self.store()


    def getSubjectName( self ):
        """Returns the name of the subject of this Hit."""
        return Sequence( Sequence_ID=self.Subject_Sequence_ID ).Name

    def subject (self):
        """Returns the subject Sequence object."""
        return Sequence( Sequence_ID=self.Subject_Sequence_ID )

    def query(self):
        """Returns the query Sequence object."""
        return Sequence( Sequence_ID=self.Query_Sequence_ID )
        



class Hsp (kdbom.KSqlObject):
    """
    """
    _table = blastDB.Hsp

    def hit(self):
        """
        """
        return Hit(self.Hit_ID)

    def qrySequence(self):
        """
        """
        return Sequence(self.hit().Query_Sequence_ID)

    def dbSequence(self):
        """
        """
        return Sequence(self.hit().Subject_Sequence_ID)

    



def insertFastaFile(fastaFilePath,
                    source=None,
                    downloadDate=None,
                    version=None,
                    description=None):
    """
    """
    if blastDB.Fasta_File.count(Filename=fastaFilePath) > 0:
        raise Warning, "Fasta File %s is already in %" %(fastaFilePath,blastDB.name)

    ff=file(fastaFilePath)
    fi=FastaIterator(ff)

    fObj = FastaFile(Filename=fastaFilePath,
                     Source=source,
                     Downloaded=downloadDate,
                     Version=version,
                     Description=description,
                     insertIfNeeded=True)
    return fObj
    
    
    

def newSearch(dbFilePath,
              qryFilePath,
              blastRunParameters,
              dbDescription=None,
              qryDescription=None):
    
     def fileMtime(path):
         mts = os.stat(path).st_mtime
         return datetime.datetime.fromtimestamp(mts)
     today = datetime.datetime.today()
            


def insertBlastResults(dbFilePath,
                       qryFilePath,
                       blastRunParameters,
                       m8resultPaths,
                       dbDescription=None,
                       qryDescription=None):
    """Insert results from a blast run in to the Blast_Results
    database.
    """

    def fileMtime(path):
        mts = os.stat(path).st_mtime
        return datetime.datetime.fromtimestamp(mts)


    batchSize = 20000

    today = datetime.datetime.today()

    if type(m8resultPaths) in StringTypes:
        m8resultPaths = [m8resultPaths]

    # check paths
    dataPaths = map(os.path.abspath,[ dbFilePath,qryFilePath] + m8resultPaths)
    for fpath in dataPaths:
        if not os.access(fpath,os.R_OK):
            raise IOError, "%s is unreadable" % fpath
    #
    # Blast Database
    #
    fastaDb = FastaFile({'Filename':dbFilePath,
                         'Version' : fileMtime(dbFilePath),
                         'Description':dbDescription},
                        insertIfNeeded=True)
    
    if Sequence._table.count(Fasta_File_ID=fastaDb.ID()) == 0:
        fastaDb.insertSequences()

    print "db sequences inserted"

    try:
        db = Db({'Path':dbFilePath,
                 'Fasta_File_ID':fastaDb.ID()})
    except:
        
        db = Db({'Path':dbFilePath,
                 'Date': fastaDb.Version,
                 'Fasta_File_ID':fastaDb.ID()},
                insertIfNeeded=True)

    #
    # Blast Query
    #
    fastaQry = FastaFile({'Filename':qryFilePath,
                         'Version' : fileMtime(qryFilePath),
                         'Description':qryDescription},
                         insertIfNeeded=True)

    if Sequence._table.count(Fasta_File_ID=fastaQry.ID()) == 0:
        fastaQry.insertSequences()

    print "qry sequences inserted"

    #
    # Sequence ID Caches
    #
    qrySequences = dict(blastDB.Sequence({"Fasta_File_ID":fastaQry.ID()},selectExpr="Name,Sequence_ID"))
    dbSequences=dict(blastDB.Sequence({"Fasta_File_ID":fastaDb.ID()},selectExpr="Name,Sequence_ID"))

    print "sequence caches initilized"

    #
    # Blast Search Record
    #
    search = Search({'Parameters':blastRunParameters,
                     'Fasta_File_ID':fastaQry.ID(),
                     'Db_ID':db.ID()},
                    insertIfNeeded=True)
    searchID=search.ID()


    #
    # For each result file from this search
    # insert hits and hsps
    for m8resultPath in m8resultPaths:

        # insert hits,hsps
        i=0


        #key is (Search_ID,qry_seq_ID,subj_qry_id)
        hitDict = {}
        for l in file(m8resultPath):

            (qryName,subjName,ident,length,gaps,mismatch,
             q_start,q_end,t_start,t_end,e,score)   =  l.split()

            ident,e,score = map(float,(ident,e,score))
            length,gaps,mismatch,q_start,q_end,t_start,t_end = map(
                int,(length,gaps,mismatch,q_start,q_end,t_start,t_end))

            qryID = qrySequences[qryName]
            subjID = dbSequences[subjName]

            if (searchID,qryID,subjID) not in hitDict:
                hitDict[(searchID,qryID,subjID)] = [[ident,length,gaps,mismatch,q_start,q_end,t_start,t_end,e,score]]
            else:
                hitDict[(searchID,qryID,subjID)].append([ident,length,gaps,mismatch,q_start,q_end,t_start,t_end,e,score])


        print "m8 results read in yo"

        blastDB.Hit.insertMany(('Search_ID','Query_Sequence_ID','Subject_Sequence_ID'),
                               hitDict.keys(),
                               disableFKcheck=True,
                               ignore=True)

        print "hits inserted"

        #
        # unfortunately the hitID lookup has to be rebuilt after each file
        #
        hitRows = blastDB.Hit({"Search_ID":searchID},
                              selectExpr="Hit_ID,Query_Sequence_ID,Subject_Sequence_ID")
        hitIDmap={}
        for row in hitRows:
            hitID,qryID,subjID= row
            hitIDmap[(qryID,subjID)] = hitID

        hsps=[]
        for hit,alignments in hitDict.items():
            hitID = hitIDmap[(hit[1],hit[2])]
            for alignment in alignments:
                hsps.append([hitID]+alignment)


        blastDB.Hsp.insertMany(('Hit_ID','Ident','Length',
                                'Gaps','Mismatch',
                                'Q_Start','Q_End',
                                'T_Start','T_End',
                                'E','Score'),
                               hsps,
                               disableFKcheck=True,
                               ignore=True)


        print "hsps inserted"
        print "%s done" % m8resultPath

            

