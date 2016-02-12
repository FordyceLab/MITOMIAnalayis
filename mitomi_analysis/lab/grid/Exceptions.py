###############################
#
# exceptions.py contains all
# Exceptions defined within
# the grid package.
#
# Dale Webster
# 3/7/2007
#
###############################

class GridThreadError( Exception ):
    """All custom errors raised in the GridThreads module are GridThreadErrors."""
    pass

class GridRuntimeError( GridThreadError ):
    """All custom errors raised by bad things happening to SGE or jobs running on SGE are GridErrors."""
    pass

class InvalidArgumentError( GridThreadError ):
    pass

class ThreadNameError( GridThreadError ):
    pass

class QStatFailureError( GridThreadError ):
    pass

class ThreadControlError( GridThreadError ):
    pass

class ThreadStatusError( GridRuntimeError ):
    pass

class JobStatusError( GridRuntimeError ):
    pass

class ThreadTimeoutError( GridRuntimeError ):
    pass
