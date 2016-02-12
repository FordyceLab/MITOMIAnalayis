"""BLAST Utilities that are free of DB connections.
"""
import os, os.path
import subprocess
import sys
import types
from .__init__ import *

from types import StringType,UnicodeType,StringTypes





class M8Set:
    """A set of -m 8 formated BLAST results
    """

    def __init__(self):
        self.alignments={}
        pass

    def parse(self,m8file):
        """
        """
        for l in m8file:
            (qryName,subjName,ident,length,gaps,mismatch,
             q_start,q_end,t_start,t_end,e,score)   =  l.split()

            ident,e,score = list(map(float,(ident,e,score)))
            length,gaps,mismatch,q_start,q_end,t_start,t_end = list(map(
                int,(length,gaps,mismatch,q_start,q_end,t_start,t_end)))

            if (qryName,subjName) not in self.alignments:
                self.alignments[(qryName,subjName)] = []
            self.alignments[(qryName,subjName)].append([ident,length,gaps,mismatch,
                                                        q_start,q_end,t_start,t_end,e,score])

    def insertSearchHits(self,search):
        sequenceMap = search.sequenceMap()
        searchID=search.ID()

        rows = [(searchID,sequenceMap[x[0]],sequenceMap[x[1]]) for x in list(self.alignments.keys())]

        
        blastDB.Hit.insertMany(('Search_ID','Query_Sequence_ID','Subject_Sequence_ID'),
                               rows,
                               disableFKcheck=True,
                               ignore=True)

    def insertSearchHsps(self,search):
        
        sequenceMap = search.sequenceMap()
        hitMap = {}
        

        def prepRow (alignmentItem):
            keySequences,myAlignments = alignmentItem
            (qryName,subjName) = keySequences
            try:
                hitID = hitMap[(qryName,subjName)]
            except KeyError:
                hitID = Hit._table(
                    Query_Sequence_ID=sequenceMap[qryName],
                    Subject_Sequence_ID=sequenceMap[subjName],
                    Search_ID=search.ID())[0].Hit_ID
                hitMap[(qryName,subjName)]=hitID
                
            return [[hitID] + x for x in myAlignments]

        rows = []
        for a in list(self.alignments.items()):
            rows.extend(prepRow(a))


        blastDB.Hsp.insertMany(('Hit_ID','Ident','Length',
                                'Gaps','Mismatch',
                                'Q_Start','Q_End',
                                'T_Start','T_End',
                                'E','Score'),
                               rows,
                               disableFKcheck=True,
                               ignore=True)


        

  
def m8dict(m8file):
    """parse an m8 file and return a list of dictionaries of results
    """
    return list(m8generator(m8file))


def m8generator(m8file):
    """An iterator over a file of -m 8 formatted BLAST results
    """
    for l in m8file:
        if (l.startswith('#') or l.startswith('Mega BLAST run') or
            l.startswith('Warning: no access to tty (Bad file descriptor).') or
            l.startswith('Thus no job control in this shell.')):
            continue
        try:
            (qryName,subjName,ident,length,gaps,mismatch,
             q_start,q_end,t_start,t_end,e,score)   =  l.split()
        except ValueError:
            continue
        
        yield {
            'query':qryName,
            'subject':subjName,
            'pctIdent':float(ident),
            'length':int(length),
            'gaps':int(gaps),
            'mismatch':int(mismatch),
            'q_start':int(q_start),
            'q_end':int(q_end),
            's_start':int(t_start),
            's_end':int(t_end),
            'e':float(e),
            'score':float(score),
            '_str_': l.strip()
            }

class disposableMB:
    """Run MEGABLAST but do not store results in a database"""

    def __init__ (self,query,db,options='-W24 -E10 -FF',deferJob=False, runOnGrid=True):

        self._tmpFiles=[]

        self.options=options
        if type(query) in (StringType,UnicodeType):
            # is the query a valid path?
            if os.path.exists(query) and os.access(query,os.F_OK):
                self.qPath=query
                self.qFile=file(query)
            else:
                self.qFile,self.qPath=mystemp(suffix=".fasta",dir='')
                self.qFile.write(query)
                #os.path
                self.qFile.write("\n")
                self.qFile.flush()
                self._tmpFiles.append(self.qPath)
                self.qFile.close()
                
        elif type(query) == FileType:
            self.qFile = query
            self.qPath = query.name

        if not (os.path.exists(db) and os.access(db,os.F_OK)):
            raise ArgumentError("db: %s Not Found" %db)
        else:
            self.dPath=db
            
        self.oFile,self.oPath=mystemp(suffix=".dmblast",dir='')
        self._tmpFiles.append(self.oPath)
        self.grid=runOnGrid
        

    def run(self):
        if self.grid:
            sgeCmd = "qrsh -cwd -N megablast "
        else:
            sgeCmd = ''
        self.blastCmd = ("%s/usr/local/bin/megablast  -i %s -d %s -o %s -D 3 %s -f -R" 
                         % (sgeCmd,self.qPath,self.dPath,
                            self.oPath,self.options))
        self.blastStat,self.blastOut = subprocess.getstatusoutput(self.blastCmd)
                
        if self.blastStat != 0:
            raise RuntimeError("---MEGABLAST FAILED---\nMEGABLAST command:%s\nEnd of output: %s\nExit Status: %s"
                                 % (self.blastCmd,self.blastOut[-25:],self.blastStat))
        
        return m8generator(file(self.oPath))


    def __del__ (self):
        for fn in self._tmpFiles:
            os.unlink(fn)

class DisposableNCBIBLAST:
    """Run blast /megablast
    """
    def __init__ (self,query,db,options='-p blastn',deferJob=False):

        self._tmpFiles=[]

        self.options=options
        if type(query) in (StringType,UnicodeType):
            if os.path.exists(query) and os.access(query,os.F_OK):
                self.qPath=query
                self.qFile=file(query)
            else:
                self.qFile,self.qPath=mystemp(suffix=".fasta")
                self.qFile.write(query)
                #os.path
                self.qFile.write("\n")
                self.qFile.flush()
                self._tmpFiles.append(self.qPath)
                
        elif type(query) == FileType:
            self.qFile = query
            self.qPath = query.name

        if not (os.path.exists(db) and os.access(db,os.F_OK)):
            raise ArgumentError("db: %s Not Found" %db)
        else:
            self.dPath=db
            
        self.oFile,self.oPath=mystemp(suffix=".dblast")
        self._tmpFiles.append(self.oPath)
 
    def __del__ (self):
        for fn in self._tmpFiles:
            os.unlink(fn)
    


class disposableBLAST (DisposableNCBIBLAST):
    """Run BLAST but do not store results in a database"""

    def run(self):
        blastCmd = ("/usr/local/bin/blastall  -i %s -d %s -o %s -m 8 %s" 
                    % (self.qPath,self.dPath,
                       self.oPath,self.options))
        blastStat,blastOut = subprocess.getstatusoutput(blastCmd)
                
        if blastStat != 0:
            raise RuntimeError("---BLAST FAILED---\nBLAST command:%s\nEnd of output: %s\nExit Status: %s"
                                 % (blastCmd,blastOut[-500:],blastStat))
        
        return m8generator(file(self.oPath))



DisposableBlast = disposableBLAST

class DisposableMB(DisposableNCBIBLAST):
    """Run MEGABLAST but do not store results in a database"""
    

    def run(self):
        blastCmd = ("/usr/local/bin/megablast  -i %s -d %s -o %s -D 3 %s -f -R" 
                    % (self.qPath,self.dPath,
                       self.oPath,self.options))
        blastStat,blastOut = subprocess.getstatusoutput(blastCmd)
                
        if blastStat != 0:
            raise RuntimeError("---MEGABLAST FAILED---\nMEGABLAST command:%s\nEnd of output: %s\nExit Status: %s"
                                 % (blastCmd,blastOut[-25:],blastStat))
        
        return m8generator(file(self.oPath))


class TaxHitDistribution:
    """
    """
    def __init__(self,m8paths=[],m8eMax=10,m8eMin=0,subjCountPaths=[]):
        
        import ncbi, ncbi.giInfo
    
        self.totalHits=0
        self.giCount = {}
        self.speciesCount={}
        self.genusCount = {}
        self.familyCount = {}

        # these are populated when a reference is
        # specified
        self.speciesExpect = None
        self.genusExpect = None
        self.familyExpect = None

        if type(m8paths) in (str,):
            m8paths=(m8paths,)

        for p in m8paths:
            for r in m8generator(file(p)):
                if r['e'] > m8eMax or r['e'] < m8eMin:
                    continue
                gi=int(r['subject'].split('|')[1])

                if gi not in self.giCount:
                    self.giCount[gi] = 1
                else:
                    self.giCount[gi] +=1

                self.totalHits+=1

        for p in subjCountPaths:
            for l in file(p):
                l=l.strip()
                try:
                    gi,n = [int(x) for x in l.split()]
                except ValueError:
                    
                    continue
                if gi not in self.giCount:
                    self.giCount[gi] = n
                else:
                    self.giCount[gi] +=n
            print('2')

                

        taxMap=ncbi.giInfo.taxMap(list(self.giCount.keys()))
        for gi in list(self.giCount.keys()):
            try:
                t,s,g,f  = taxMap[gi]
            except KeyError:
                continue
            if s not in self.speciesCount:
                self.speciesCount[s] = 1
            else:
                self.speciesCount[s] +=1

            if g not in self.genusCount:
                self.genusCount[g] = 1
            else:
                self.genusCount[g] +=1

            if f not in self.familyCount:
                self.familyCount[f] = 1
            else:
                self.familyCount[f] +=1

    def setBlastDBSizeExpected(self,DBpath):
        """
        """
        from . import blast
        ffRec = blast.FastaFile(Filename=DBath)

        sRows = ncbi.ncbiDB.fetchall (
            """SELECT G.Species_Tax_ID, sum(G.Length) FROM Blast_Results.Fasta_File F
            LEFT JOIN Blast_Results.Sequence S ON S.Fasta_File_ID=F.Fasta_File_ID
            LEFT JOIN NCBI.Gi_Info G ON S.Gi=G.Gi
            WHERE F.Fasta_File_ID = %s
            Group By G.Species_Tax_ID
            """ %(ffRec.ID()))
        self.speciesExpect=dict(sRows)

        gRows = ncbi.ncbiDB.fetchall (
            """SELECT G.Genus_Tax_ID, sum(G.Length) FROM Blast_Results.Fasta_File F
            LEFT JOIN Blast_Results.Sequence S ON S.Fasta_File_ID=F.Fasta_File_ID
            LEFT JOIN NCBI.Gi_Info G ON S.Gi=G.Gi
            WHERE F.Fasta_File_ID = %s
            Group By G.Genus_Tax_ID
            """ %(ffRec.ID()))
        self.genusExpect=dict(gRows)

        fRows = ncbi.ncbiDB.fetchall (
            """SELECT G.Family_Tax_ID, sum(G.Length) FROM Blast_Results.Fasta_File F
            LEFT JOIN Blast_Results.Sequence S ON S.Fasta_File_ID=F.Fasta_File_ID
            LEFT JOIN NCBI.Gi_Info G ON S.Gi=G.Gi
            WHERE F.Fasta_File_ID = %s
            Group By G.Family_Tax_ID
            """ %(ffRec.ID()))
        self.familyExpect=dict(fRows)


    def setExpected(self,refDist):
        """Set the espected hit distribution to another TaxHitDistribution.
        """

        if not isinstance(refDist,TaxHitDistribution):
            raise ValueError("refDist must be a  TaxHitDistribution instance")

        self.speciesExpect = refDist.speciesCount
        self.genusExpect = refDist.genusCount
        self.familyExpect = refDist.familyCount

        
        
    def chiSquared(self,obsDict,expectedDict,key):
        from scipy import stats
        from scipy import array,float64

        try:
            oOfKey =  obsDict[key]
        except KeyError:
            oOfKey = 0

        try:
            eOfKey = expectedDict[key]
        except KeyError:
            eOfKey = 0
       
        obs = array((oOfKey, sum(obsDict.values())-oOfKey),dtype=float64)
        expt = array((expectedDict[key], sum(expectedDict.values())-expectedDict[key]),dtype=float64)
        expt*=sum(obs)/sum(expt)

        x2,p = stats.chisquare(obs,expt*sum(obs)/sum(expt))

        if obs[0] > expt[0]:
            overObs = True
            
        else:
            overObs = False
            
        return x2,p,obs[0],expt[0]


    def cladeReport (self,obsDict,expectedDict,pLimit=1,overCalledOnly=False,taxIDs=None):
        from viroinfo import taxon
        rows = []
        if taxIDs == None:
            taxIDs = list(expectedDict.keys())
        
        for s in taxIDs:
            x2,p,o,e = self.chiSquared(obsDict,expectedDict,s)
            if p > pLimit or (overCalledOnly and not o):
                continue
            try:
                tax=taxon.Taxon(NCBI_TaxID=s)
            except:
                tax = s

            rows.append((tax,p,o,e))

        rows.sort(key=lambda x: (x[2]<x[3],x[1]))


        return '\n'.join(['\t'.join([str(tax), str(p),"%.2f"%o,"%.2f"%e]) for tax,p,o,e in rows] )
    

        
    def familyReport(self,**args):
        return self.cladeReport(self.familyCount,self.familyExpect,**args)

    def genusReport(self,**args):
        return self.cladeReport(self.genusCount,self.genusExpect,**args)

    def speciesReport(self,**args):
        return self.cladeReport(self.speciesCount,self.speciesExpect,**args)

