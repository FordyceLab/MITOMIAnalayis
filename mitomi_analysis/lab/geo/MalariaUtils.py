#!/usr/local/bin/python2.2

#######################################################
#  MalariaUtils
#  ------------
#  This is a library of small utility functions for working
#  with the malaria data.  For example, the first function in
#  this library will translate between an OLIGO database oligoid
#  and a NOMAD ID, since these IDs are not the same in some cases.
#
#  Created July, 2006.
########################################################

import re

# For NomadIdToOligoid.  These changes are more trouble than they
# are worth to pattern match, there's only a few so we'll hard code them.
# the key is the NOMAD version and the value is the OLIGO version
nonPatternDict = {"pchr5.rRNA118sA_675":"chr5.rRNA-1-18s-A_675",
                  "pchr7.rRNA1ITS1_17":"chr7.rRNA-1-ITS1_17",
                  "pchr8.rRNA228spseudo_5803":"chr8.rRNA-2-28s-pseudo_5803",
                  "snRNA1":"snRNA-1",
                  "Pplad_tRNAAsn":"tRNA-Asn",
                  "Ppla_ORF51_0":"ORF51_0",
                  "Ppla_rpoC_1027":"rpoC_1027",
                  "Ppla_SSU_882":"SSU_882",
                  "pchr14.gen_473_MND1_168":"chr14.gen_473MND1_168",
                  "Ppla_LSU_rRNA_2194":"LSULocation=2335..5116_2194",
                  "pchr5.rRNA1ITS1A_17":"chr5.rRNA-1-ITS1-A_17",
                  "pchr8.rRNA328spseudo_451":"chr8.rRNA-3-28s-pseudo_451",
                  "pchr8.rRNA15.8spseudo_90":"chr8.rRNA-1-5.8s-pseudo_90",
                  "pchr7.rRNA118s_470":"chr7.rRNA-1-18s_470",
                  "Ppla_rps2_277":"rps2_277",
                  "Ppla_ORF101_110":"ORF101_110",
                  "Ppla_rpoB_2142":"rpoB_2142",
                  "Ppla_ORF470_854":"ORF470_854",
                  "pchr13_2.rRNA5.8sS_98":"chr13_2.rRNA-5.8s-S_98"
                  }


def NomadIdToOligoid(oligoid):
    """The Ids in the NOMAD database and the OLIGO database are slightly
       different in some cases.  This method takes a NOMAD id and changes into
       the OLIGO version."""
    
    # first, see if this is a case without a good pattern:
    if oligoid in nonPatternDict:
        return nonPatternDict[oligoid]

    
    # this code adapted from "addExtraKeys.py" written by Kael
    k = oligoid
    if k[:4] == 'pMAL' or k[:3] == 'pPF' or k[:4] == 'pHRP':
        #print k, "-->", k[1:]
        k = k[1:]
                
    # and for tRNAs with the 'p'-fix
    if k.find('tRNA') != -1 and k[0] == 'p':
        #print k, "-->", k[1:]
        k = k[1:]

    # and key
    # pfcrt_X_YYY
    # to
    # pfcrt_YYY
    mObj = re.match(r'ppfcrt_\d_(\d+)',k)
    if mObj != None:
        newk = 'pfcrt_%s' % mObj.group(1)
        #print k, "-->", newk
        k = newk


    # New Code
    # add some dashes in various places within tRNA pieces

    #  example: tRNA1 to tRNA-1
    mObj = re.match(r'tRNA(\d)', k)
    if mObj != None:
        newk = "tRNA-%s" % mObj.group(1)
        #print k, "-->", newk
        k = newk

    # example: chr11tRNAGly1_2 to chr11-tRNA-Gly-1_2
    mObj = re.match(r'chr(\d+)tRNA([A-Z,a-z]{3})(\d_\d+)', k)
    if mObj != None:
        newk = "chr%s-tRNA-%s-%s" % (mObj.group(1), mObj.group(2), mObj.group(3))
        #print k, "-->", newk
        k = newk

    # example: PtRNAAsp to PtRNA-Asp OR PtRNAGly2 to PtRNA-Gly2
    mObj = re.match(r'PtRNA([A-Z,a-z]{3})(\d?)', k)
    if mObj != None:
        newk = "PtRNA-%s%s" % (mObj.group(1), mObj.group(2))
        #print k, "-->", newk
        k = newk

    # example: Ppla_tRNAAla_1 to tRNA-Ala_1
    # example: Ppla_tRNAArgPrime_2 to tRNA-Arg'-2
    mObj = re.match(r'Ppla_tRNA([A-Z,a-z]{3})(.*)', k)
    if mObj != None:
        replacePrime = mObj.group(2).replace("Prime", "'")
        newk = "tRNA-%s%s" % (mObj.group(1), replacePrime)
        #print k, "-->", newk
        k = newk

    # example: unmapped1tRNAArg1_3 to unmapped-1-tRNA-Arg-1_3
    mObj = re.match(r'unmapped(\d)tRNA([A-Z,a-z]{3})(.*)', k)
    if mObj != None:
        newk = "unmapped-%s-tRNA-%s-%s" % (mObj.group(1), mObj.group(2), mObj.group(3))
        #print k, "-->", newk
        k = newk

    # return the OLIGO version of the ID
    return k
