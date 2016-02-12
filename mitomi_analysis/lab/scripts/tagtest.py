#!/usr/local/bin/python

from kdbom import kdbom

ttDB=kdbom.db(host="meebo2",user="guest",passwd='',db="Tag_Test")

class TaggedThing (kdbom.KSqlObject):
    """Testing the tagging facilities ported from viroinfo.oligo.Oligo.
    """

    _table=ttDB.Thing
    _tagTable=ttDB.Thing_Tag
    _tagLinkTable=ttDB.Thing_has_Thing_Tag




if __name__ == "__main__":
    print "Running %s" % __file__
    print "\ndb is %s on %s.  Connected as: %s" % (ttDB.name,
                                                   ttDB.host,
                                                   ttDB.user)
    print "\nThe database has these tables: [%s]" % (', '.join([str(t) for t in ttDB.tables]))

    print "\nTaggedThing is a class: %s" % TaggedThing
    
    print "\n%s table has these taggedThings: [%s]" % (TaggedThing._table.name,', '.join([str(t) for t in TaggedThing.generator()]))

    print "\nAll the tags TaggedThing knows about are: [%s]" % (', '.join([str(t)
                                                                         for t in TaggedThing.knownTags()]))
    print "\nThe taggedThings have these tags:"
    for thing in TaggedThing.generator():
        print "\t"+ "\t".join([str(x) for x in (thing, thing.listTags())])


    print "\nThese tags have these taggedThings:"
    for tag in  TaggedThing.knownTags():
           print "\t"+ tag + "\t[%s]" % (", ".join([str(x) for x in TaggedThing.getByTag(tag)]))


    
    print "\nThese tags are _not_ applied to these taggedThings:"
    for tag in  TaggedThing.knownTags():
           print "\t"+ tag + "\t[%s]" % (", ".join([str(x) for x in TaggedThing.getByTag(excludeTags=tag)]))


 
    

     
    
