#!/usr/local/bin/python2.2
#
# NCBI.py
#
# Written by Michelle and Kael, February 2007
#
# Library for dealing with Platform, Sample and Series files
# for submitting to GEO.
# See http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html#SOFTtext
# for a description of the required file formats.
#
__version__ = "$Revision: 1.10 $"

from . import nomad
from geo.exceptions import *

ALL_LINES = -1

LIST = type([])
STR = type("")

VALID_NCBI_TYPES = ["Platform", "Sample", "Series"]

VALID_PLATFORM_DISTRIBUTIONS = ["commercial", "non-commercial", "custom-commercial",
                                "virtual"]
VALID_PLATFORM_TECHNOLOGIES = ["spotted DNA/cDNA", "spotted oligonucleotide",
                               "in situ oligonucleotide", "antibody", "tissue",
                               "SARST", "RT-PCR", "MS", "MPSS"]
VALID_SAMPLE_MOLECULES = ["total RNA", "polyA RNA", "cytoplasmic RNA", "nuclear RNA",
                          "genomic DNA", "protein", "other"]

REQUIRED_SAMPLE_TABLE_COLUMNS = ["ID_REF", "VALUE"]

class NCBIDataFile:
    """Base class for all the NCBI GEO Files types.  _fileType must be set for all
    subclasses and should be one of the VALID_NCBI_TYPES above."""
    def __init__(self, id):
        self.id = id
        self.params = {}
        self.dataIterator = None

    def addParameter(self, name, value):
        """Adds a parameter.  Adds the initial ! if it's not included in the name."""
        if not name.startswith("!"):
            name = "!" + name
			
        # if this is the second value of this name, convert this name into a list
        if name in list(self.params.keys()):
	    if type(self.params[name]) != LIST:
                self.params[name] = [self.params[name], value]
            else:
                self.params[name].append(value)
        else:
            self.params[name] = value

    def setDataTable(self, headerNames, headerDescriptions, valueIterator):
        """headerNames should be a list of the header names, headerDescriptions should describe 
        those names (in the same order) and each value from the valueIterator should return a list
        with one entry for each of the headerNames."""

        if len(headerNames) != len(headerDescriptions):
            raise NCBI_Attribute_Error("headerNames and headerDescriptions needs to be the same length.")
        self.headerNames = headerNames
        self.headerDescriptions = headerDescriptions
        self.dataIterator = valueIterator

    def checkValidity(self):
        """ Should be overwritten to check the validity specific to the file type.
        Instead of returning true or false, raises an exception if there is a problem
        so the user can see what the error was."""
        pass
	
    def __str__(self, numlines = ALL_LINES):
        # create all the lines, required first, then optional, then spots
        lines = []

        lines.append("^" + self._fileType.upper() + "=" + self.id)
	
        for (name, value) in self.params.items():
            if type(value) == LIST:
                for subvalue in value:
                    lines.append(name + "=" + self._getValue(subvalue))
            else:
                lines.append(name + "=" + self._getValue(value))

        # the series file doesn't have a data table so don't require it
        # the checkValidity functions for Platform and Series should check for it
        if self.dataIterator:
            for i in range(0, len(self.headerNames)):
                lines.append("#" + self.headerNames[i] + "=" + self.headerDescriptions[i])
                        
            lines.append("!" + self._fileType + "_table_begin")
            lines.append("\t".join(self.headerNames))
            i = 0
            # while True is to keep looping if there is a KeyError
            while True:
                try:
                    for row in self.dataIterator:
                        if (numlines > ALL_LINES) and (i > numlines):
                             break
                        lines.append("\t".join(row))
                        i = i + 1
                    break
                except KeyError:
                    pass

            lines.append("!" + self._fileType + "_table_end")

        return "\n".join(lines)

    def _getValue(self, value):
        firstCurly = value.find("{")

        while firstCurly >= 0:
            endCurly = value.find("}")
            newval = self.getCustomParam(value[firstCurly+1:endCurly])
            value = value[:firstCurly] + newval + value[endCurly+1:]
            firstCurly = value.find("{")

        return value


    def dump(self, filename, numLines):
        """Checks that all the required variables are set and then dumps the class
        to the given filename, appending to the end of the file."""
       
        self.checkValidity()

        # open the file
        f = open(filename, "a")
        f.write(self.__str__(numLines))
        f.write("\n\n")
        f.close()

    def confirmParam(self, name):
        if name not in self.params:
            raise NCBI_Attribute_Error(name + " must be set.")

    def getCustomParam(self, key):
        """Can be overridden to return a value from a key.  For example, 
           in the Sample class, a key of Array_Description would return
           the current array's Array_Description from nomad."""
        return key
                     

class Platform (NCBIDataFile):
    """Holds the information for a platform file.  Required values
    include everything in the constructor plus one or more organisms.
    http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html#SOFTtext 
    lists details on the required values."""

    _fileType = "Platform"
            
    def setRequiredParams(self, platform_title, platform_distribution,
            platform_technology, platform_manufacturer,
            platform_manufacture_protocol, platform_organism):
        """ This can also be done by setting each parameter individually."""
        
        self.params["!Platform_title"] = platform_title
        self.params["!Platform_distribution"] = platform_distribution
        self.params["!Platform_technology"] = platform_technology
        self.params["!Platform_manufacturer"] = platform_manufacturer
        self.params["!Platform_manufacture_protocol"] = platform_manufacture_protocol
        self.params["!Platform_organism"] = platform_organism
        

    def checkValidity(self):
        self.confirmParam("!Platform_title")
        if len(self.params["!Platform_title"]) < 1 or len(self.params["!Platform_title"]) > 120:
            raise NCBI_Attribute_Error(
                "The Platform_title must be between 1 and 120 characters")    
        self.confirmParam("!Platform_distribution")
        if self.params["!Platform_distribution"] not in VALID_PLATFORM_DISTRIBUTIONS:
            raise NCBI_Attribute_Error("The Platform_Distrubtion must be one of " + 
                                        str(VALID_PLATFORM_DISTRIBUTIONS))
        self.confirmParam("!Platform_technology")
        if self.params["!Platform_technology"] not in VALID_PLATFORM_TECHNOLOGIES:
            raise NCBI_Attribute_Error("The Platform_Technology must be one of " + 
                                        str(VALID_PLATFORM_TECHNOLOGIES))
        self.confirmParam("!Platform_manufacturer")
        self.confirmParam("!Platform_manufacture_protocol")
        self.confirmParam("!Platform_organism")
            
        if self.dataIterator == None:
            raise NCBI_Attribute_Error("The spots header and values must be set.")


class Sample (NCBIDataFile):


    _fileType = "Sample"

    def __init__(self, sampleID, platformID, plugin):
        NCBIDataFile.__init__(self, sampleID)
        self.plugin = plugin
        self.platformID = platformID

    def setArray(self, arr, arrName):
        self.array = arr
        self.dataIterator = SampleIterator(self.array, self.fieldNames, self.plugin)
        self.id = arrName

    def setDataFields(self, headerNames, headerDesc, fieldNames):
        self.headerNames = headerNames
        self.headerDescriptions = headerDesc
        self.fieldNames = fieldNames

    def checkValidity(self):
        self.confirmParam("!Sample_title")
        if len(self.params["!Sample_title"]) < 1 or len(self.params["!Sample_title"]) > 120:
            doPrint("Chopping title to 120 chars:" + self.params["!Sample_title"])
            self.params["!Sample_title"] = self.params["!Sample_title"][:119]
            #raise NCBI_Attribute_Error(
            #    "The Sample_title must be between 1 and 120 characters")    
        self.confirmParam("!Sample_source_name_ch1")
        self.confirmParam("!Sample_organism_ch1")
        self.confirmParam("!Sample_characteristics_ch1")
        self.confirmParam("!Sample_molecule_ch1")
        if self.params["!Sample_molecule_ch1"] not in VALID_SAMPLE_MOLECULES:
            raise NCBI_Attribute_Error("The Sample_molecule_ch1 must be one of " + 
                                        str(VALID_SAMPLE_MOLECULES))
        self.confirmParam("!Sample_extract_protocol_ch1")
        self.confirmParam("!Sample_label_ch1")

        # some arrays only have one channel -- don't require 2
        # and, of course, long run these should be in a function of their own per channel
        #self.confirmParam("!Sample_source_name_ch2")
        #self.confirmParam("!Sample_organism_ch2")
        #self.confirmParam("!Sample_characteristics_ch2")
        #self.confirmParam("!Sample_molecule_ch2")
        #if self.params["!Sample_molecule_ch2"] not in VALID_SAMPLE_MOLECULES:
        #    raise NCBI_Attribute_Error("The Sample_molecule_ch2 must be one of " + 
                #                        str(VALID_SAMPLE_MOLECULES))        
        #self.confirmParam("!Sample_extract_protocol_ch2")
        #self.confirmParam("!Sample_label_ch2")

        self.confirmParam("!Sample_hyb_protocol")
        self.confirmParam("!Sample_scan_protocol")
        self.confirmParam("!Sample_data_processing")
        self.confirmParam("!Sample_description")
        self.confirmParam("!Sample_platform_id")

        # this one's a bit special -- it's required, but it can be "none".  annoying
        try:
            self.confirmParam("!Sample_supplementary_file")
        except NCBI_Attribute_Error:
            self.addParameter("!Sample_supplementary_file", "none")

        # allow data iterator to be none so we can verify before dumping
        #if self.dataIterator == None:
        #    raise NCBI_Attribute_Error("The spots header and values must be set.")


        # confirm that the data table has the required params
        for column in REQUIRED_SAMPLE_TABLE_COLUMNS:
            if not column in self.headerNames:
                raise NCBI_Attribute_Error("The Sample data table must contain the column %s" % column)
                

    def getCustomParam(self, key):
        if key == "Platform_id":
            return self.platformID
        else:
            return str(self.array[key])

class Series(NCBIDataFile):
    _fileType = "Series"

    def __init__(self, seriesID, arrays):
        NCBIDataFile.__init__(self, seriesID)
        self.arrays = arrays

    def checkValidity(self):
        self.confirmParam("!Series_title")
        if len(self.params["!Series_title"]) < 1 or len(self.params["!Series_title"]) > 120:
            raise NCBI_Attribute_Error("The Series_title must be between 1 and 120 characters")
        self.confirmParam("!Series_summary")
        self.confirmParam("!Series_type")
        self.confirmParam("!Series_overall_design")

class Family:

    def __init__(self, platformID, seriesID, plugin, arrayNames=[],
                 experimentNames=[], projectNames=[]):
        self.platform = Platform(platformID)
	
        self.arrays = self.getNomadArrays(arrayNames, experimentNames, projectNames)
        self.verifySamePlatform()

        # to save memory, keep one sample file to represent the template
        # and then set the data table and changing params for every array during the write
        self.sample = Sample("placeholder", platformID, plugin)

        self.series = Series(seriesID, self.arrays)
        for (arrName, arr) in self.arrays.items():
            self.series.addParameter("!Series_sample_id", arrName)

    def getNomadArrays(self, arrayNames, experimentNames, projectNames):
            
        n = nomad.nomadDB()
        
        arrays = self.getArraysFromArrayNames(arrayNames, n)
        self.addArraysFromExperimentNames(experimentNames, n, arrays)
        self.addArraysFromProjectNames(projectNames, n, arrays)
 
        return arrays


    def getArraysFromArrayNames(self, arrayNames, n):
        """
        Gets an Array object for every array name
            Also checks that the arrays are the same platform (all ids used once per array).  
        """

        # get arrays out of Nomad for each of the ids in arrayIds
        arrays = {}
        for i in arrayNames:
            arrays[i] = n.getArray(i)

        return arrays


    def addArraysFromExperimentNames(self, experimentNames, n, arrays):
        """Gets the array from the experiment names.  Returns a list."""
       
        for expName in experimentNames:
            exp = nomad.experiment(n, expName)
            arrayIds = exp.arrayIDs()
            for arrayId in arrayIds:
                array = nomad.array(n, arrayID=arrayId)
                arrays[arrayId] = array
            

    def addArraysFromProjectNames(self, projectNames, n, arrays):
        """Gets the array from the project names.  Returns a list."""
        for projectName in projectNames:
            proj = nomad.project(n, projectName)
            expIds = proj.experimentIDs()  
            for expId in expIds:
                exp = nomad.experiment(n, experimentID=expId)
                arrayIds = exp.arrayIDs()
                for arrayId in arrayIds:
                    array = nomad.array(n, arrayID=arrayId)
                    arrays[arrayId] = array


    def verifySamePlatform(self):
        # check that the arrays are the same platform.  In other words, each
        # id should be used once on each array.
        idCounts = {}
        for array in list(self.arrays.values()):
            result = array.result()
            idlist = result.idList()
            for i in idlist:
                if i in idCounts:
                    idCounts[i] += 1
                else:
                    idCounts[i] = 1

        for i, num in idCounts.items():
            if num != len(self.arrays) and (i[0] != "EMPTY") and ("Y_" not in i[0]):
                errStr = "WARNING: For ID %s, the count is %d instead of %d" % (i, num, len(self.arrays))
                doPrint(errStr)
                #raise DifferentPlatformsException(errStr)

    def setPlatformDataTable(self, headerNames, headerDesc, plugin):
        self.platform.setDataTable(headerNames, headerDesc, 
        plugin.getSpotIterator(list(self.arrays.values())[0], headerNames))

    def setSampleDataFields(self, headerNames, headerDesc, fieldNames):
        self.sample.setDataFields(headerNames, headerDesc, fieldNames)

    def dump(self, writePlatform, outfileName, numLines = ALL_LINES):

        # delete the previous version of the file
        f = open(outfileName, "w")
        f.write("")
        f.close()

        # write out the new version (dump appends)
        if writePlatform:
            doPrint("Creating platform file...")
            self.platform.dump(outfileName, numLines)

        for (arrName, arr) in self.arrays.items():
            doPrint("Creating sample file for array:" + arrName)
            self.sample.setArray(arr, arrName)
            self.sample.dump(outfileName, numLines)

        doPrint("Creating series file...")
        self.series.dump(outfileName, numLines)

class SampleIterator:
    def __init__(self, array, fieldNames, plugin):
        spotSet = array.result().spots()  
        self.spots = spotSet.__iter__()
        self.field_names = fieldNames
        self.plugin = plugin

    def __iter__(self):
        return self

    def __next__(self):
        spot = next(self.spots)
        fields = []
        for field in self.field_names:
            if field == "ID_REF":
                fields.append(self.plugin.getLongID(spot))
            else:
                try:
                    fields.append(str(spot[field]))
                except KeyError:
                    doPrint("KEY ERROR with key:" + field)
                    doPrint("     found with fieldnames:" + self.field_names)

        return fields


def doPrint(str):
    print(str)            

