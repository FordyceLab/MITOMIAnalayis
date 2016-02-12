#KDBOM exceptions#
__version__="$Id: exceptions.py,v 1.5 2007/10/30 23:16:21 kael Exp $"	
class KdbomError(Exception):
    pass
                 
class Relationship_Error (Exception):
    pass

class DateConversionError (Exception):
    pass

class ArgumentError (Exception):
    pass

class KdbomDatabaseError (KdbomError):
    pass

class KdbomInsertError (KdbomDatabaseError):
    pass

class KdbomLookupError (KeyError,KdbomDatabaseError):
    pass

class KdbomUsageError (KdbomError):
    pass

class KdbomProgrammingError (KdbomError):
    pass

