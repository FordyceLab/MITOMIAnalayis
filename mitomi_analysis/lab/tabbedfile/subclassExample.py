#!/usr/local/bin/python

import tabbedfile

class MySpecialRecord (tabbedfile.Record):
    """Here is a record that knows how to calculate something
    interesting about itself.
    """

    def secretScore(self):
        """This is a super secret thing that this kind of record
        must know how to do.  It returns the value of the i1 field
        raised to the f1 power.

        If the calculation throws an error, None is returned.
        """
        try:
            return self.i2**self.f1
        except:
            return None
    

class TFExample (tabbedfile.TabbedFile):
    """This is an example subclass of the TabbedFile class.
    """

    _recordClass=MySpecialRecord


# if run as a test script/program calculate score and print it out
if __name__ == '__main__':
    testFilePath = '/sumo/home/kael/lib/python-dev/tabbedfile/test.txt'
    myFile = TFExample(testFilePath)
    print "name\tscore"
    # you don't have to parse it you can just start iterating.
    for rec in myFile:
        print "%s\t%s" %(rec.s1,rec.secretScore())

