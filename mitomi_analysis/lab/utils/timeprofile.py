"""
A module that helps to inject time profiling code
in other modules to measures actual execution times
of blocks of code.

Modified by Dale Webster 1/07

"""

__author__ = "Anand B. Pillai"
__version__ = "0.1"

import time

def timeprofile():
    """ A factory function to return an instance of TimeProfiler """

    return TimeProfiler()

class TimeProfiler:
    """ A utility class for profiling execution time for code """
    
    def __init__(self):
        # Dictionary with times in seconds
        self.timedict = {}

        # Dictionary of aggregated elapsed times for inside loops.
        self.agg = {}

    def mark(self, slot=''):
        """ Mark the current time into the slot 'slot' """

        # Note: 'slot' has to be string type
        # we are not checking it here.
        
        self.timedict[slot] = time.time()

    def unmark(self, slot=''):
        """ Unmark the slot 'slot' """
        
        # Note: 'slot' has to be string type
        # we are not checking it here.

        if self.timedict.has_key(slot):
            del self.timedict[slot]

    def lastdiff(self):
        """ Get time difference between now and the latest marked slot """

        # To get the latest slot, just get the max of values
        return time.time() - max(self.timedict.values())
    
    def elapsed(self, slot=''):
        """ Get the time difference between now and a previous
        time slot named 'slot' """

        # Note: 'slot' has to be marked previously
        return time.time() - self.timedict.get(slot)

    def diff(self, slot1, slot2):
        """ Get the time difference between two marked time
        slots 'slot1' and 'slot2' """

        return self.timedict.get(slot2) - self.timedict.get(slot1)

    def maxdiff(self):
        """ Return maximum time difference marked """

        # Difference of max time with min time
        times = self.timedict.values()
        return max(times) - min(times)
    
    def timegap(self):
        """ Return the full time-gap since we started marking """

        # Return now minus min
        times = self.timedict.values()
        return time.time() - min(times)

    def cleanup(self):
        """ Cleanup the dictionary of all marks """

        self.timedict.clear()


    def observe(self, mark1, mark2, key):
        """ Record an observation for averaged time of multiple runs. """
        ( n, total ) = ( 0, 0 )
        if self.agg.has_key( key ):
            ( n, total ) = self.agg[key]
            
        self.agg[key] = ( n+1, total + self.diff( mark1, mark2 ) )

    def averageElapsed(self, key):
        """ Returns the average elapsed time over all calls
        to 'observe' using this key."""

        ( n, total ) = self.agg[key]
        return float(total)/float(n)

    def count( self, key ):
        """ Returns the number of times this key has been
        observed."""
        ( n, total ) = self.agg[ key ]
        return n

    def total( self, key ):
        """ Returns the total time taken for observations
        based on the provided key."""
        ( n, total ) = self.agg[ key ]
        return total

if __name__ == "__main__":
    # Demo code
    profiler = timeprofile()
    # Mark time
    profiler.mark()
    # Execute large loop
    for x in xrange(10000):
        pass
    # Get time
    print profiler.elapsed()
    # Do other things
    profiler.mark('t')
    for x in range(10000):
        for y in range(10000):
            pass
    print profiler.elapsed('t')

    # Get total time elapsed
    print profiler.timegap()

    # Get maximum diff for marks
    print profiler.maxdiff()

